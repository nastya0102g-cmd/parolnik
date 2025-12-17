from fastapi import FastAPI, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os, secrets, json, datetime
from typing import Optional

from database import db

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# === Вспомогательные функции ===
def get_current_user(request: Request):
    """Получаем текущего пользователя из сессии"""
    user = None
    email = request.session.get("user_email")
    if email:
        user = db.get_user_by_email(email)
    return user


def require_auth(request: Request):
    """Декоратор для проверки авторизации"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# === Основные страницы ===
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/navigation", response_class=HTMLResponse)
def navigation_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("navigation.html", {"request": request, "user": user})


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    if get_current_user(request):
        return RedirectResponse(url="/navigation", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("register.html", {"request": request, "errors": None, "data": {}})


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if get_current_user(request):
        return RedirectResponse(url="/navigation", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "errors": None, "data": {}})


@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if get_current_user(request):
        return RedirectResponse(url="/navigation", status_code=status.HTTP_302_FOUND)
    errors = []
    user = db.verify_user(email, password)
    if not user:
        errors.append("Неверный email или пароль")
        return templates.TemplateResponse("login.html",
                                          {"request": request, "errors": errors, "data": {"email": email}})
    request.session["user_email"] = user["email"]
    request.session["user_id"] = user["id"]
    return RedirectResponse(url="/navigation", status_code=status.HTTP_302_FOUND)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/trainer", response_class=HTMLResponse)
def trainer(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("trainer.html", {"request": request, "user": user})


@app.get("/check-password", response_class=HTMLResponse)
def check_password(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("check_password.html", {"request": request, "user": user})


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Получаем сохраненные пароли для профиля
    saved_passwords = []
    try:
        saved_passwords = db.get_saved_passwords(user["id"], limit=5)
    except Exception as e:
        print(f"Error loading saved passwords: {e}")

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "saved_passwords": saved_passwords
    })


@app.get("/info", response_class=HTMLResponse)
def info(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("info.html", {"request": request, "user": user})


@app.post("/register", response_class=HTMLResponse)
def register_post(request: Request, name: str = Form(...), email: str = Form(...),
                  password: str = Form(...), password2: str = Form(...)):
    if get_current_user(request):
        return RedirectResponse(url="/navigation", status_code=status.HTTP_302_FOUND)

    errors = []
    data = {"name": name, "email": email}

    # Проверка совпадения паролей
    if password != password2:
        errors.append("Пароли не совпадают")

    # Кастомные правила пароля
    if len(password) < 8:
        errors.append("Пароль должен быть минимум 8 символов")
    if not any(c.isupper() for c in password):
        errors.append("Пароль должен содержать хотя бы одну заглавную букву")
    if not any(c.islower() for c in password):
        errors.append("Пароль должен содержать хотя бы одну строчную букву")
    if not any(c.isdigit() for c in password):
        errors.append("Пароль должен содержать хотя бы одну цифру")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Пароль должен содержать хотя бы один специальный символ (!@#$%^&*()_+-=[]{}|;:,.<>?)")

    # Проверка email
    if "@" not in email or "." not in email:
        errors.append("Некорректный email")

    if errors:
        return templates.TemplateResponse("register.html",
                                          {"request": request, "errors": errors, "data": data})

    # Создание пользователя
    ok = db.create_user(name, email, password)
    if not ok:
        errors.append("Пользователь с таким email уже существует")
        return templates.TemplateResponse("register.html",
                                          {"request": request, "errors": errors, "data": data})

    request.session["user_email"] = email
    user = db.get_user_by_email(email)
    request.session["user_id"] = user["id"]
    return RedirectResponse(url="/navigation", status_code=status.HTTP_302_FOUND)


# === НОВЫЕ СТРАНИЦЫ ===
@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: Optional[str] = None, category: Optional[str] = None):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    tips = []
    categories = []

    try:
        tips = db.search_tips(query=q, category=category)
        categories = db.get_tip_categories()
    except Exception as e:
        print(f"Error loading search data: {e}")

    return templates.TemplateResponse("search.html", {
        "request": request,
        "user": user,
        "tips": tips,
        "query": q,
        "category": category,
        "categories": categories
    })


@app.get("/favorites", response_class=HTMLResponse)
def favorites_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    saved_passwords = []
    try:
        saved_passwords = db.get_saved_passwords(user["id"])
    except Exception as e:
        print(f"Error loading favorites: {e}")

    return templates.TemplateResponse("favorites.html", {
        "request": request,
        "user": user,
        "saved_passwords": saved_passwords
    })


# === API ДЛЯ СОХРАНЕНИЯ ПРОГРЕССА И ПАРОЛЕЙ ===
@app.get("/api/progress")
def get_progress_api(request: Request):
    """Получаем прогресс пользователя"""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Для упрощения пока возвращаем только статусы из localStorage
        # В реальном приложении нужно хранить в базе данных
        return {
            "info_viewed": False,
            "trainer_score": 0,
            "trainer_passed": False,
            "password_checked": False,
            "last_activity": None
        }
    except Exception as e:
        print(f"Error in get_progress_api: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/progress")
async def update_progress_api(request: Request):
    """Обновляем прогресс пользователя"""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        body = await request.body()
        data = json.loads(body.decode())

        # В реальном приложении сохраняем в базу данных
        print(f"Progress updated for user {user['id']}: {data}")

        return {"success": True}
    except Exception as e:
        print(f"Error in update_progress_api: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/save-password")
async def save_password_api(request: Request):
    """Сохраняем проверенный пароль"""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        body = await request.body()
        data = json.loads(body.decode())

        success = db.save_password(
            user_id=user["id"],
            password=data["password"],
            strength_score=data["score"]
        )

        return {"success": success}
    except Exception as e:
        print(f"Error in save_password_api: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/saved-passwords")
def get_saved_passwords_api(request: Request):
    """Получаем сохраненные пароли"""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        passwords = db.get_saved_passwords(user["id"])
        return {"passwords": passwords}
    except Exception as e:
        print(f"Error in get_saved_passwords_api: {e}")
        return {"passwords": []}


@app.delete("/api/saved-passwords/{password_id}")
def delete_saved_password_api(request: Request, password_id: int):
    """Удаляем сохраненный пароль"""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        success = db.delete_saved_password(password_id, user["id"])
        return {"success": success}
    except Exception as e:
        print(f"Error in delete_saved_password_api: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/tips")
def search_tips_api(request: Request, q: Optional[str] = None, category: Optional[str] = None):
    """Поиск советов"""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        tips = db.search_tips(query=q, category=category, limit=50)
        return {"tips": tips}
    except Exception as e:
        print(f"Error in search_tips_api: {e}")
        return {"tips": []}


# === ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ ===
@app.get("/api/version")
def get_version():
    """Возвращает версию приложения"""
    return {"version": "1.0.0", "timestamp": datetime.datetime.now().isoformat()}


@app.get("/health")
def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "ok", "time": datetime.datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)