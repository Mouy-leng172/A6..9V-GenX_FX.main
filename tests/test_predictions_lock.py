import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Set testing mode BEFORE importing app
os.environ["TESTING"] = "1"

from api.main import app

# Mock dependencies
from api.utils.auth import get_current_user

app.dependency_overrides[get_current_user] = lambda: {"username": "testuser"}

# Setup TestClient after overrides
client = TestClient(app)


@pytest.mark.asyncio
async def test_get_model_metrics_cache_hit():
    """Test Case 1: Successful cache hit"""
    with patch(
        "api.routers.predictions.redis_client", new_callable=AsyncMock
    ) as mock_redis:
        # Mock cache hit
        mock_redis.get.return_value = json.dumps(
            {
                "accuracy": 0.99,
                "precision": 0.9,
                "recall": 0.9,
                "f1_score": 0.9,
                "last_updated": "2023-01-01",
            }
        )

        response = client.get("/api/v1/predictions/model/metrics")

        assert response.status_code == 200
        assert response.json()["accuracy"] == 0.99
        # Should check cache once
        mock_redis.get.assert_called_once_with("model_metrics")
        # Should not try to lock
        mock_redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_get_model_metrics_lock_acquired():
    """Test Case 2: Lock acquisition success"""
    with patch(
        "api.routers.predictions.redis_client", new_callable=AsyncMock
    ) as mock_redis, patch("api.routers.predictions.ml_service") as mock_ml_service:

        # 1. Cache miss
        # 2. Lock acquire success
        # 3. Double check cache miss
        # 4. Calculate

        # mock_redis.get is called twice. First returns None, second returns None.
        mock_redis.get.side_effect = [None, None]
        mock_redis.set.return_value = True  # Lock acquired

        mock_ml_service.get_model_metrics = AsyncMock(
            return_value={
                "accuracy": 0.88,
                "precision": 0.8,
                "recall": 0.8,
                "f1_score": 0.8,
                "last_updated": "2023-01-01",
            }
        )

        response = client.get("/api/v1/predictions/model/metrics")

        assert response.status_code == 200
        assert response.json()["accuracy"] == 0.88

        assert mock_redis.get.call_count == 2
        mock_redis.set.assert_called_once()
        mock_ml_service.get_model_metrics.assert_called_once()
        # Should set cache
        mock_redis.setex.assert_called_once()
        # Should release lock
        mock_redis.delete.assert_called_once_with("lock:model_metrics")


@pytest.mark.asyncio
async def test_get_model_metrics_lock_contention_immediate_success():
    """Test Case 3: Lock contention -> Wait -> Cache Hit (First retry)"""
    with patch(
        "api.routers.predictions.redis_client", new_callable=AsyncMock
    ) as mock_redis:

        # 1. Cache miss
        # 2. Lock acquire fail
        # 3. Wait (handled by code)
        # 4. Retry cache hit

        mock_redis.get.side_effect = [
            None,
            json.dumps(
                {
                    "accuracy": 0.77,
                    "precision": 0.7,
                    "recall": 0.7,
                    "f1_score": 0.7,
                    "last_updated": "2023-01-01",
                }
            ),
        ]
        mock_redis.set.return_value = False  # Lock failed

        response = client.get("/api/v1/predictions/model/metrics")

        assert response.status_code == 200
        assert response.json()["accuracy"] == 0.77

        # It should try to lock once
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_model_metrics_retry_loop():
    """
    Test Case 4: Lock contention with delayed cache population.
    This test verifies that the code retries multiple times.
    """
    with patch(
        "api.routers.predictions.redis_client", new_callable=AsyncMock
    ) as mock_redis, patch(
        "api.routers.predictions.ml_service"
    ) as mock_ml_service, patch(
        "asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:

        # Scenario: Cache appears only on the 3rd check.
        # Loop 1: Check (Miss), Lock (Fail), Sleep
        # Loop 2: Check (Miss), Lock (Fail), Sleep
        # Loop 3: Check (Hit) -> Return

        mock_redis.get.side_effect = [
            None,  # Initial check
            None,  # Retry 1 check
            json.dumps(
                {  # Retry 2 check
                    "accuracy": 0.66,
                    "precision": 0.6,
                    "recall": 0.6,
                    "f1_score": 0.6,
                    "last_updated": "2023-01-01",
                }
            ),
        ]

        mock_redis.set.return_value = False  # Always fail lock

        # If fallback is triggered, it will call ml_service.
        # We ensure ml_service raises error to verify we DID NOT fallback.
        mock_ml_service.get_model_metrics = AsyncMock(
            side_effect=Exception("Fallback triggered!")
        )

        response = client.get("/api/v1/predictions/model/metrics")

        # If logic is correct, it should succeed without calling ml_service
        assert response.status_code == 200
        assert response.json()["accuracy"] == 0.66

        # Verify we slept at least twice (since we hit on 3rd check, implying 2 failures)
        # Actually:
        # Check 1 (Miss) -> Lock Fail -> Sleep 1
        # Check 2 (Miss) -> Lock Fail -> Sleep 2
        # Check 3 (Hit) -> Return
        assert mock_sleep.call_count >= 2
