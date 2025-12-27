from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ===============================
# API: طلای ۱۸ عیار از tgju
# ===============================
@app.route("/api/gold18")
def gold18():
    try:
        url = "https://www.tgju.org/profile/geram18"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        price_el = soup.select_one("span[data-col='info.last_trade.PDrCotVal']")
        change_el = soup.select_one("span[data-col='info.price_change_percent']")

        if not price_el:
            return jsonify({"ok": False, "error": "price not found"})

        return jsonify({
            "Currency": "gold18",
            "Price": price_el.text.strip(),
            "Changes": change_el.text.strip() if change_el else None,
            "Ok": True,
            "Source": "tgju.org"
        })

    except Exception as e:
        return jsonify({
            "Ok": False,
            "error": str(e)
        })


# ===============================
# سایت (UI)
# ===============================
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<title>قیمت طلای ۱۸ عیار</title>
<style>
body {
    margin: 0;
    background: radial-gradient(circle at top, #0f172a, #020617);
    color: #fff;
    font-family: Tahoma;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}
.card {
    background: #020617;
    padding: 30px 40px;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 0 40px rgba(255,215,0,0.25);
    min-width: 260px;
}
h1 {
    color: gold;
    margin-bottom: 15px;
}
.price {
    font-size: 30px;
    margin: 15px 0;
}
.info {
    font-size: 14px;
    color: #94a3b8;
}
.error {
    color: #ff4d4d;
}
</style>
</head>
<body>

<div class="card">
    <h1>طلای ۱۸ عیار</h1>
    <div class="price" id="price">در حال دریافت...</div>
    <div class="info" id="change"></div>
    <div class="info" id="source"></div>
</div>

<script>
function loadGold() {
    fetch("/api/gold18")
        .then(r => r.json())
        .then(d => {
            if (!d.Ok) {
                document.getElementById("price").innerHTML =
                    '<span class="error">خطا ❌</span>';
                return;
            }

            document.getElementById("price").innerText =
                d.Price + " تومان";

            document.getElementById("change").innerText =
                "تغییر: " + (d.Changes ?? "-");

            document.getElementById("source").innerText =
                "منبع: " + d.Source;
        })
        .catch(() => {
            document.getElementById("price").innerHTML =
                '<span class="error">خطا ❌</span>';
        });
}

loadGold();
setInterval(loadGold, 60000);
</script>

</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
