from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import sqlite3
import requests
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

BOT_TOKEN = "7159490173:AAEfsvxSCSLWiGqBCAm0uNNUEo7k11x3-UM"
SUCCESS_PHOTO = "https://i.pinimg.com/originals/23/50/8e/23508e8b1e8dea194d9e06ae507e4afc.gif"

def init_db():
    conn = sqlite3.connect("orders.db")
    conn.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id TEXT, username TEXT, udid TEXT, price TEXT, status TEXT, date TEXT)')
    conn.commit()
    conn.close()

init_db()

class OrderIn(BaseModel):
    user_id: str
    username: str
    udid: str
    price: str

@app.post("/api/v1/save_order")
async def save_order(order: OrderIn):
    conn = sqlite3.connect("orders.db")
    conn.execute("INSERT INTO orders (user_id, username, udid, price, status, date) VALUES (?,?,?,?,?,?)",
                 (order.user_id, order.username, order.udid, order.price, "PENDING", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/")
async def dashboard(request: Request):
    conn = sqlite3.connect("orders.db")
    conn.row_factory = sqlite3.Row
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    stats = {"total": len(orders), "pending": len([o for o in orders if o['status'] == 'PENDING']), 
             "done": len([o for o in orders if o['status'] == 'COMPLETED'])}
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "orders": orders, "stats": stats})

@app.post("/action/{action}/{order_id}/{user_id}")
async def admin_action(action: str, order_id: int, user_id: str, file: UploadFile = File(None)):
    conn = sqlite3.connect("orders.db")
    
    if action == "approve":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        requests.post(url, json={"chat_id": user_id, "photo": SUCCESS_PHOTO, "caption": "✅ ការបញ្ជាទិញត្រូវបានអនុម័ត!"})
        conn.execute("UPDATE orders SET status='APPROVED' WHERE id=?", (order_id,))
    
    elif action == "upload" and file:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        requests.post(url, data={"chat_id": user_id, "caption": "🎁 នេះជាឯកសាររបស់អ្នក!"}, files={"document": (file.filename, await file.read())})
        conn.execute("UPDATE orders SET status='COMPLETED' WHERE id=?", (order_id,))
    
    elif action == "reject":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": user_id, "text": "❌ សំណើររបស់អ្នកត្រូវបានបដិសេធ។"})
        conn.execute("UPDATE orders SET status='REJECTED' WHERE id=?", (order_id,))

    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)
