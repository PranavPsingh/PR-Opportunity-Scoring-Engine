def get_health_status() -> dict[str, str]:
    """Return service metadata without coupling the HTTP view to business logic."""
    return {"service": "backend"}
