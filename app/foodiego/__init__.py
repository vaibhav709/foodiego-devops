"""FoodieGo - online food-ordering platform (restaurants, menus, orders)."""
import os
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request, render_template_string

RESTAURANTS = [
    {"id": 1, "name": "Punjabi Tadka", "cuisine": "North Indian", "rating": 4.5, "eta_min": 30},
    {"id": 2, "name": "Dosa Plaza", "cuisine": "South Indian", "rating": 4.3, "eta_min": 25},
    {"id": 3, "name": "Wok Express", "cuisine": "Chinese", "rating": 4.1, "eta_min": 35},
    {"id": 4, "name": "Pizza Piazza", "cuisine": "Italian", "rating": 4.4, "eta_min": 40},
]

MENU = {
    1: [{"item": "Paneer Butter Masala", "price": 260}, {"item": "Dal Makhani", "price": 220}, {"item": "Butter Naan", "price": 45}, {"item": "Gulab Jamun", "price": 80}],
    2: [{"item": "Masala Dosa", "price": 120}, {"item": "Idli Sambar", "price": 90}, {"item": "Filter Coffee", "price": 50}],
    3: [{"item": "Veg Hakka Noodles", "price": 180}, {"item": "Chilli Paneer", "price": 230}, {"item": "Spring Rolls", "price": 150}],
    4: [{"item": "Margherita Pizza", "price": 299}, {"item": "Farmhouse Pizza", "price": 399}, {"item": "Garlic Bread", "price": 129}],
}

DELIVERY_FEE = 40
FREE_DELIVERY_ABOVE = 499

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>FoodieGo</title>
<style>
body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#fff7f0;color:#1f1f1f}
header{background:{{ bar }};color:#fff;padding:20px 28px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
header h1{margin:0;font-size:26px}.tag{background:rgba(255,255,255,.22);border-radius:999px;padding:4px 12px;font-size:13px;font-weight:600;margin-left:6px}
main{max-width:1000px;margin:24px auto;padding:0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px}
.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 6px rgba(0,0,0,.07);border-top:4px solid {{ bar }}}
.card h3{margin:0 0 4px}.muted{color:#6b6b6b;font-size:14px}.menu{margin:10px 0 0;padding-left:18px;font-size:14px}
footer{max-width:1000px;margin:10px auto 30px;padding:0 16px;color:#666;font-size:13px}
</style></head><body>
<header><h1>🍔 FoodieGo</h1><div>{% if color != 'none' %}<span class="tag">{{ color|upper }} slot</span>{% endif %}<span class="tag">{{ version }}</span></div></header>
<main><p class="muted">Order from your favourite restaurants · free delivery above ₹{{ free }}</p><div class="grid">
{% for r in restaurants %}<div class="card"><h3>{{ r.name }}</h3><div class="muted">{{ r.cuisine }} · ⭐ {{ r.rating }} · {{ r.eta_min }} min</div>
<ul class="menu">{% for m in menu[r.id] %}<li>{{ m.item }} — ₹{{ m.price }}</li>{% endfor %}</ul></div>{% endfor %}
</div></main>
<footer>Pod <b>{{ pod }}</b> · version <b>{{ version }}</b> · GitHub → Jenkins → Docker → Helm/Kubernetes</footer>
</body></html>"""


def quote(items):
    """Validate order lines and return a price breakdown, or raise ValueError."""
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    subtotal = 0
    lines = []
    for line in items:
        rid, name, qty = line.get("restaurant_id"), line.get("item"), line.get("qty", 1)
        if not isinstance(qty, int) or not 1 <= qty <= 20:
            raise ValueError("qty must be an integer between 1 and 20")
        match = next((m for m in MENU.get(rid, []) if m["item"] == name), None)
        if match is None:
            raise ValueError(f"unknown item: {name}")
        subtotal += match["price"] * qty
        lines.append({"item": name, "qty": qty, "amount": match["price"] * qty})
    fee = 0 if subtotal >= FREE_DELIVERY_ABOVE else DELIVERY_FEE
    return {"lines": lines, "subtotal": subtotal, "delivery_fee": fee, "total": subtotal + fee}


def create_app():
    app = Flask(__name__)
    version = os.environ.get("APP_VERSION", "dev")
    color = os.environ.get("SLOT_COLOR", "none").lower()
    orders = []

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/version")
    def ver():
        return jsonify(app="foodiego", version=version, slot=color, pod=socket.gethostname())

    @app.get("/api/restaurants")
    def restaurants():
        cuisine = request.args.get("cuisine")
        data = [r for r in RESTAURANTS if not cuisine or r["cuisine"].lower() == cuisine.lower()]
        return jsonify(data)

    @app.get("/api/restaurants/<int:rid>/menu")
    def menu(rid):
        if rid not in MENU:
            return jsonify(error="restaurant not found"), 404
        return jsonify(MENU[rid])

    @app.post("/api/orders")
    def place_order():
        body = request.get_json(silent=True) or {}
        try:
            q = quote(body.get("items"))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        order = {"order_id": len(orders) + 1001, "status": "PLACED", "placed_at": datetime.now(timezone.utc).isoformat(), **q}
        orders.append(order)
        return jsonify(order), 201

    @app.get("/")
    def home():
        bar = {"blue": "#2563eb", "green": "#16a34a"}.get(color, "#ea580c")
        return render_template_string(PAGE, restaurants=RESTAURANTS, menu=MENU, version=version, color=color,
                                      bar=bar, pod=socket.gethostname(), free=FREE_DELIVERY_ABOVE)

    return app
