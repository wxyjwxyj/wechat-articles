import pytest
from api.app import create_app


def test_today_bundle_endpoint_returns_json(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "content.db")})
    client = app.test_client()

    response = client.get("/api/bundles/today")

    assert response.status_code in {200, 404}
    assert response.content_type == "application/json"


def test_bundle_by_date_endpoint_returns_404_for_missing(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "content.db")})
    client = app.test_client()

    response = client.get("/api/bundles/2099-01-01")

    assert response.status_code == 404
    assert response.content_type == "application/json"


def test_sources_endpoint_returns_list(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "content.db")})
    client = app.test_client()

    response = client.get("/api/sources")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
