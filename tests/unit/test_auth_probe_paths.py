import pathlib
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient


SRC_DIR = pathlib.Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

import auth


def test_kubernetes_health_and_readiness_probes_remain_unauthenticated(monkeypatch):
    monkeypatch.setattr(auth, "AGENT_AUTH_TOKEN", "test-token")
    app = FastAPI()
    app.add_middleware(auth.TokenAuthMiddleware)

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.get("/ready")
    def ready():
        return {"status": "ready"}

    @app.get("/api/v1/workflow")
    def workflow():
        return {"status": "protected"}

    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    assert client.get("/api/v1/workflow").status_code == 401
