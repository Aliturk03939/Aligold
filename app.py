from flask import Flask, jsonify
import requests

app = Flask(__name__)

TOKEN = "AnRomHyWSrQKZTjYfqce"
API_URL = f"https://alanchand.com/media/api?token={TOKEN}"

@app.route("/api/gold")
def gold_api():
    try:
        r = requests.get(API_URL, timeout=10)
        j = r.json()

        # حالت معمول: data -> 18ayar
        if "data" in j and "18ayar" in j["data"]:
            return jsonify(j["data"]["18ayar"])

        # حالت ساده: مستقیم 18ayar
        if "18ayar" in j:
            return jsonify(j["18ayar"])

        return jsonify({"error": "invalid api format"})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<title>قیمت روز طلا</title>
<style>
body {
    margin: 0;
    background: #0f172a;
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
    box-shadow: 0 0 30px rgba(255,215,0,0.2);
}
h1 {
    color: gold;
}
.price {
    font-size: 32px;
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
    <div class="info" id="bubble"></div>
    <div class="info" id="time"></div>
</div>

<script>
function loadPrice() {
    fetch("/api/gold")
        .then(r => r.json())
        .then(g => {
            if (g.error) {
                document.getElementById("price").innerHTML =
                    '<span class="error">خطا ❌</span>';
                return;
            }

            document.getElementById("price").innerText =
                g.price.toLocaleString() + " تومان";

            document.getElementById("bubble").innerText =
                "حباب: " + g.bubble.toLocaleString() + " تومان (" + g.bubble_per + "%)";

            document.getElementById("time").innerText =
                "بروزرسانی: " + g.updated_at;
        })
        .catch(() => {
            document.getElementById("price").innerHTML =
                '<span class="error">خطا ❌</span>';
        });
}

loadPrice();
setInterval(loadPrice, 60000);
</script>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
