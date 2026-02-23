import json
import redis
from sqlalchemy import create_mock_engine, update
from datetime import datetime

REDIS_URL = "redis://redis:6379/0"
JOB_ID = "test-manual-fail-1"

def test_sync_fail_broadcast():
    print(f"Testing SYNC fail broadcast for {JOB_ID}...")
    
    event_data = {
        "job_id": JOB_ID,
        "status": "FAILED",
        "result_url": None,
        "error": "Manual Failure Injection Test",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        r = redis.from_url(REDIS_URL)
        r.publish("asset_updates", json.dumps(event_data))
        print("Success: Broadcast sent to Redis.")
        r.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_sync_fail_broadcast()
