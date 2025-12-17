import sqlite3, os, hashlib, secrets, datetime, json

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class Database:
    def __init__(self, path=DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self._ensure_tables()
        self._ensure_default_data()

    def _ensure_tables(self):
        # Таблица пользователей
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")

        # Таблица сохраненных паролей
        self.cur.execute("""CREATE TABLE IF NOT EXISTS saved_passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            password_hash TEXT NOT NULL,
            strength_score INTEGER,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )""")

        # Таблица советов по паролям
        self.cur.execute("""CREATE TABLE IF NOT EXISTS password_tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT
        )""")

        self.conn.commit()

    def _ensure_default_data(self):
        # Проверяем тестового пользователя
        default_email = "admin@example.com"
        default_password = "TestPass123!"
        default_name = "Admin"

        self.cur.execute("SELECT id FROM users WHERE email = ?", (default_email,))
        if not self.cur.fetchone():
            salt = secrets.token_hex(16)
            password_hash = _hash_password(default_password, salt)
            self.cur.execute("""INSERT INTO users (name, email, password_hash, salt, created_at) 
                              VALUES (?, ?, ?, ?, ?)""",
                             (default_name, default_email, password_hash, salt,
                              datetime.datetime.utcnow().isoformat()))
            self.conn.commit()

        # Проверяем наличие советов
        self.cur.execute("SELECT COUNT(*) FROM password_tips")
        if self.cur.fetchone()[0] == 0:
            tips = [
                ("Как создать надежный пароль",
                 "Используйте комбинацию букв, цифр и специальных символов. Минимальная длина - 12 символов.",
                 "basic"),
                ("Менеджеры паролей",
                 "Используйте менеджеры паролей для хранения сложных уникальных паролей.",
                 "storage"),
                ("Двухфакторная аутентификация",
                 "Всегда включайте 2FA для важных аккаунтов.",
                 "advanced"),
                ("Регулярная смена паролей",
                 "Меняйте пароли каждые 3-6 месяцев для важных сервисов.",
                 "basic"),
                ("Избегайте личной информации",
                 "Не используйте имена, даты рождения, номера телефонов в паролях.",
                 "basic")
            ]
            self.cur.executemany("""INSERT INTO password_tips (title, content, category) 
                                  VALUES (?, ?, ?)""", tips)
            self.conn.commit()

    # === Пользователи ===
    def create_user(self, name, email, password):
        try:
            salt = secrets.token_hex(16)
            password_hash = _hash_password(password, salt)
            created_at = datetime.datetime.utcnow().isoformat()

            self.cur.execute("""INSERT INTO users (name, email, password_hash, salt, created_at) 
                              VALUES (?, ?, ?, ?, ?)""",
                             (name, email, password_hash, salt, created_at))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_by_email(self, email):
        self.cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = self.cur.fetchone()
        if row:
            return dict(row)
        return None

    def get_user_by_id(self, user_id):
        self.cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = self.cur.fetchone()
        if row:
            return dict(row)
        return None

    def verify_user(self, email, password):
        user = self.get_user_by_email(email)
        if not user:
            return None
        salt = user["salt"]
        if _hash_password(password, salt) == user["password_hash"]:
            return user
        return None

    # === Сохраненные пароли ===
    def save_password(self, user_id, password, strength_score):
        try:
            # Для демо сохраняем пароль как есть (в реальном приложении нужно хэшировать!)
            created_at = datetime.datetime.utcnow().isoformat()

            self.cur.execute("""INSERT INTO saved_passwords 
                              (user_id, password_hash, strength_score, created_at)
                              VALUES (?, ?, ?, ?)""",
                             (user_id, password, strength_score, created_at))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving password: {e}")
            return False

    def get_saved_passwords(self, user_id, limit=None):
        try:
            query = """SELECT id, password_hash, strength_score, created_at 
                      FROM saved_passwords 
                      WHERE user_id = ? 
                      ORDER BY created_at DESC"""

            if limit:
                query += " LIMIT ?"
                self.cur.execute(query, (user_id, limit))
            else:
                self.cur.execute(query, (user_id,))

            rows = self.cur.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting saved passwords: {e}")
            return []

    def delete_saved_password(self, password_id, user_id):
        try:
            self.cur.execute("""DELETE FROM saved_passwords 
                              WHERE id = ? AND user_id = ?""",
                             (password_id, user_id))
            self.conn.commit()
            return self.cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting password: {e}")
            return False

    # === Советы по паролям ===
    def search_tips(self, query=None, category=None, limit=20):
        try:
            conditions = []
            params = []

            if query:
                conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            if category:
                conditions.append("category = ?")
                params.append(category)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.append(limit)

            query_sql = f"""SELECT id, title, content, category 
                           FROM password_tips 
                           WHERE {where_clause}
                           ORDER BY id DESC 
                           LIMIT ?"""

            self.cur.execute(query_sql, params)
            rows = self.cur.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching tips: {e}")
            return []

    def get_tip_categories(self):
        try:
            self.cur.execute("SELECT DISTINCT category FROM password_tips WHERE category IS NOT NULL")
            rows = self.cur.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []

    def list_users(self):
        self.cur.execute("SELECT id, name, email, created_at FROM users ORDER BY id DESC")
        return [dict(r) for r in self.cur.fetchall()]


db = Database()