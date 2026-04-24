from schemas.health import HealthResponse


def get_health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")
