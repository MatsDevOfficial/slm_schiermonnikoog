from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from auth import get_current_user, login, auth, logout
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="SUPER_SECRET_KEY")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user)):
    if not user:
        return RedirectResponse("/")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/login/{provider}")
async def oauth_login(request: Request):
    return await login(request)

@app.get("/auth/{provider}")
async def oauth_callback(request: Request):
    return await auth(request)

@app.get("/logout")
async def do_logout(request: Request):
    return await logout(request)
