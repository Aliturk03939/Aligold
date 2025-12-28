import os
import sqlite3
import requests
import google.generativeai as genai
from flask import Flask, jsonify, render_template_string
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ===============================
# تنظیمات (از Environment Variables خوانده می‌شود)
# ===============================
# اگر در رندر تنظیم نکرده باشی، از مقادیر پیش‌فرض استفاده میکنه (ولی بهتره تو رندر تنظیم کنی)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8427937062:AAGYnoVu_hEuanfGOM_EeMyX0aHBlsCBgYo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "474098524")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AnRomHyWSrQKZTjYfqce")

# تنظیم هوش مصنوعی
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Error configuring AI: {e}")

DB_NAME = "gold_history.db"

# ===============================
# دیتابیس و لاجیک (بدون تغییر)
# ===============================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prices
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  price INTEGER)''')
    conn.commit()
    conn.close()

def save_price(price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO prices (price) VALUES (?)", (price,))
    conn.commit()
    conn.close()

def get_history(limit=50):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT timestamp, price FROM prices ORDER BY id DESC LIMIT ?", (limit,))
        data = c.fetchall()
        conn.close()
        return data[::-1]
    except:
        return []

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def get_gold_price():
    try:
        # استفاده از یک منبع جایگزین یا همان منبع قبلی
        url = "https://www.tgju.org/profile/geram18"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        price_el = soup.select_one("span[data-col='info.last_trade.PDrCotVal']")
        if price_el:
            return int(price_el.text.strip().replace(',', ''))
        return None
    except:
        return None

# جاب زمان‌بندی شده
def scheduled_job():
    with app.app_context():
        price = get_gold_price()
        if price:
            print(f"Price: {price}")
            save_price(price)

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_job, trigger="interval", minutes=5) # روی رندر بهتره ۵ دقیقه باشه تا فشار نیاد
scheduler.start()

# ===============================
# روت‌ها
# ===============================
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/data")
def api_data():
    price = get_gold_price()
    history = get_history()
    prices_only = [x[1] for x in history] if history else []
    return jsonify({
        "current_price": price,
        "history_labels": [x[0][11:16] for x in history],
        "history_values": prices_only,
        "min": min(prices_only) if prices_only else 0,
        "max": max(prices_only) if prices_only else 0
    })

@app.route("/api/analyze")
def api_analyze():
    history = get_history(20)
    if not history:
        return jsonify({"analysis": "داده کافی نیست."})
    prices_str = ", ".join([str(x[1]) for x in history])
    prompt = f"تحلیل کوتاه فارسی برای تریدر طلا. قیمت‌های اخیر: {prices_str}. روند چیست؟ خرید یا فروش؟"
    try:
        response = model.generate_content(prompt)
        send_telegram_msg(f"🤖 تحلیل جدید:\n{response.text}")
        return jsonify({"analysis": response.text})
    except Exception as e:
        return jsonify({"analysis": str(e)})

# قالب HTML (همان قالب قبلی با کمی فشرده‌سازی)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gold AI</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{background:#0f172a;color:#fff;font-family:tahoma}</style>
</head>
<body class="flex flex-col items-center p-4">
<h1 class="text-2xl text-yellow-400 font-bold mb-4">Gold Trader AI</h1>
<div class="bg-slate-800 p-6 rounded-xl w-full max-w-md text-center mb-4">
<h2 id="current-price" class="text-4xl font-bold mb-2">...</h2>
<p class="text-xs text-gray-400">قیمت لحظه‌ای</p>
</div>
<div class="w-full max-w-md bg-slate-800 p-2 rounded-xl mb-4"><canvas id="c"></canvas></div>
<button onclick="askAI()" class="bg-purple-600 w-full max-w-md py-3 rounded-xl font-bold mb-4">تحلیل هوش مصنوعی</button>
<div id="res" class="w-full max-w-md bg-slate-700 p-4 rounded-xl hidden text-sm"></div>
<script>
let chart;
function u(){fetch('/api/data').then(r=>r.json()).then(d=>{
if(d.current_price)document.getElementById('current-price').innerText=d.current_price.toLocaleString();
const ctx=document.getElementById('c').getContext('2d');
if(chart){chart.data.labels=d.history_labels;chart.data.datasets[0].data=d.history_values;chart.update()}
else{chart=new Chart(ctx,{type:'line',data:{labels:d.history_labels,datasets:[{label:'Price',data:d.history_values,borderColor:'#fbbf24',tension:0.4}]},options:{scales:{x:{display:false},y:{position:'right'}}}})}
})}
function askAI(){document.getElementById('res').classList.remove('hidden');document.getElementById('res').innerText='...';fetch('/api/analyze').then(r=>r.json()).then(d=>{document.getElementById('res').innerText=d.analysis})}
u();setInterval(u,60000);
</script></body></html>
"""

# ساخت دیتابیس هنگام ایمپورت (برای Gunicorn لازم است)
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

