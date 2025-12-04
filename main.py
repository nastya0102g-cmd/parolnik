from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os, secrets

from database import db

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

def get_current_user(request: Request):
    user = None
    email = request.session.get("user_email")
    if email:
        user = db.get_user_by_email(email)
    return user

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
        return templates.TemplateResponse("login.html", {"request": request, "errors": errors, "data": {"email": email}})
    request.session["user_email"] = user["email"]
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
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@app.get("/info", response_class=HTMLResponse)
def info(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("info.html", {"request": request, "user": user})


@app.post("/register", response_class=HTMLResponse)
def register_post(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...),
                  password2: str = Form(...)):
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
        return templates.TemplateResponse("register.html", {"request": request, "errors": errors, "data": data})

    # Создание пользователя
    ok = db.create_user(name, email, password)
    if not ok:
        errors.append("Пользователь с таким email уже существует")
        return templates.TemplateResponse("register.html", {"request": request, "errors": errors, "data": data})

    request.session["user_email"] = email
    return RedirectResponse(url="/navigation", status_code=status.HTTP_302_FOUND)