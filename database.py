import sqlite3, os, hashlib, secrets, datetime
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
    def _ensure_tables(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        self.conn.commit()
        self._ensure_default_user()
    def _ensure_default_user(self):
        default_email = "admin@example.com"
        default_password = "TestPass123"
        default_name = "Admin"
        self.cur.execute("SELECT id FROM users WHERE email = ?", (default_email,))
        if not self.cur.fetchone():
            salt = secrets.token_hex(16)
            password_hash = _hash_password(default_password, salt)
            self.cur.execute("INSERT INTO users (name,email,password_hash,salt,created_at) VALUES (?,?,?,?,?)",
                             (default_name, default_email, password_hash, salt, datetime.datetime.utcnow().isoformat()))
            self.conn.commit()
    def create_user(self, name, email, password):
        try:
            salt = secrets.token_hex(16)
            password_hash = _hash_password(password, salt)
            self.cur.execute("INSERT INTO users (name,email,password_hash,salt,created_at) VALUES (?,?,?,?,?)",
                             (name, email, password_hash, salt, datetime.datetime.utcnow().isoformat()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    def get_user_by_email(self, email):
        self.cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = self.cur.fetchone()
        return dict(row) if row else None
    def verify_user(self, email, password):
        user = self.get_user_by_email(email)
        if not user:
            return None
        salt = user["salt"]
        if _hash_password(password, salt) == user["password_hash"]:
            return user
        return None
    def list_users(self):
        self.cur.execute("SELECT id,name,email,created_at FROM users ORDER BY id DESC")
        return [dict(r) for r in self.cur.fetchall()]
db = Database()
