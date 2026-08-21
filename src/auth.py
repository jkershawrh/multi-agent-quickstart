"""Bearer token authentication middleware for A2A agents.

Validates Authorization headers on /a2a endpoints. Health checks and
agent card discovery remain unauthenticated (required for K8s probes
and A2A protocol compliance).

In production, replace the shared token with OpenShift service account
tokens or mTLS between services.
"""

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

AGENT_AUTH_TOKEN = os.environ.get("AGENT_AUTH_TOKEN", "")

OPEN_PATHS = {"/health", "/.well-known/agent-card.json", "/docs", "/openapi.json", "/mcp"}


class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not AGENT_AUTH_TOKEN:
            return await call_next(request)

        if request.url.path in OPEN_PATHS:
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid Authorization header"},
            )

        token = auth[len("Bearer "):]
        if token != AGENT_AUTH_TOKEN:
            return JSONResponse(
                status_code=403,
                content={"error": "Invalid token"},
            )

        return await call_next(request)
