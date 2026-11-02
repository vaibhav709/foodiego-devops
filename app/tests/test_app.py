import pytest

from foodiego import create_app, quote


@pytest.fixture()
def client():
    return create_app().test_client()


def test_healthz(client):
    assert client.get("/healthz").get_json() == {"status": "ok"}


def test_lists_restaurants(client):
    assert len(client.get("/api/restaurants").get_json()) == 4


def test_filter_by_cuisine(client):
    data = client.get("/api/restaurants?cuisine=chinese").get_json()
    assert [r["name"] for r in data] == ["Wok Express"]


def test_menu_404(client):
    assert client.get("/api/restaurants/99/menu").status_code == 404


def test_delivery_fee_applied_below_threshold():
    q = quote([{"restaurant_id": 2, "item": "Masala Dosa", "qty": 2}])
    assert q["subtotal"] == 240 and q["delivery_fee"] == 40 and q["total"] == 280


def test_free_delivery_above_threshold():
    q = quote([{"restaurant_id": 4, "item": "Farmhouse Pizza", "qty": 2}])
    assert q["delivery_fee"] == 0 and q["total"] == 798


def test_place_order(client):
    r = client.post("/api/orders", json={"items": [{"restaurant_id": 1, "item": "Dal Makhani", "qty": 1}]})
    assert r.status_code == 201 and r.get_json()["status"] == "PLACED"


def test_rejects_bad_quantity(client):
    r = client.post("/api/orders", json={"items": [{"restaurant_id": 1, "item": "Dal Makhani", "qty": 99}]})
    assert r.status_code == 400
