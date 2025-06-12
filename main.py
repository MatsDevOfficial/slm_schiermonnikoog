from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from models import SessionLocal, User, QuestionLog
from datetime import datetime, timedelta
from gemini import ask_gemini
import auth, payments
from dotenv import load_dotenv
import os

# Laad .env variabelen
load_dotenv()

app = FastAPI()

# Middleware voor sessies
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# Templates folder
templates = Jinja2Templates(directory="templates")

# Routers koppelen
app.include_router(auth.router)
app.include_router(payments.router)

# Homepagina
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

# Vraag stellen pagina
@app.get("/ask", response_class=HTMLResponse)
async def ask_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("ask.html", {"request": request, "user": user})

# Vraag afhandelen
@app.post("/ask")
async def handle_question(request: Request, question: str = Form(...)):
    user_data = request.session.get("user")
    if not user_data:
        return RedirectResponse(url="/", status_code=303)

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_data["id"]).first()

    # Check basic gebruikers limiet
    if user.role == "basic":
        count = db.query(QuestionLog).filter(
            QuestionLog.user_id == user.id,
            QuestionLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        if count >= 15:
            return HTMLResponse("Je hebt je dagelijkse limiet van 15 vragen bereikt.", status_code=403)

    # Vraag doorsturen naar Gemini als premium
    if user.role == "premium":
        response = await ask_gemini(question)
        answer = response["candidates"][0]["content"]["parts"][0]["text"]
    else:
        answer = f"Je vroeg: {question}. (Upgrade naar premium voor Gemini AI-antwoorden!)"

    # Log de vraag
    db.add(QuestionLog(user_id=user.id))
    db.commit()

    return HTMLResponse(f"<h2>Antwoord:</h2><p>{answer}</p><a href='/ask'>Nog een vraag stellen</a>", status_code=200)
@app.get("/success", response_class=HTMLResponse)
async def payment_success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/cancel", response_class=HTMLResponse)
async def payment_cancel(request: Request):
    return templates.TemplateResponse("cancel.html", {"request": request})
