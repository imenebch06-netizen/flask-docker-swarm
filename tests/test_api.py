import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("PDF_DIRECTORY", "/tmp/test_shared_pdf")

from app import create_app


def test_health_endpoint():
    client = create_app().test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_cv_requires_username_and_email():
    client = create_app().test_client()
    response = client.post("/api/v1/cv", json={"username": "Alice"})

    assert response.status_code == 400
    assert "requis" in response.get_json()["error"]
