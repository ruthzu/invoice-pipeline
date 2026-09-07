from unittest.mock import Mock, patch

from tests.conftest import client


def test_health_all_checks_ok():
    redis_connection = Mock()
    queue = Mock(count=3)
    with (
        patch("app.api.health.get_redis_connection", return_value=redis_connection),
        patch("app.api.health.Queue", return_value=queue),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok", "queue_depth": 3},
    }
    redis_connection.ping.assert_called_once()


def test_health_redis_down_is_degraded_but_successful():
    redis_connection = Mock()
    redis_connection.ping.side_effect = ConnectionError("Redis unavailable")
    queue = Mock(count=0)
    with (
        patch("app.api.health.get_redis_connection", return_value=redis_connection),
        patch("app.api.health.Queue", return_value=queue),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["redis"] == "error"
