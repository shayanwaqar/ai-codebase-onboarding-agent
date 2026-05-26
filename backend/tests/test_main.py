from app.main import app


def test_ask_route_is_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/repos/{repo_id}/ask" in paths
