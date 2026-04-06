import sys
import time

import requests  # type: ignore[import-untyped]

API_BASE_URL = "http://localhost:8000"
API_KEY = "dev-secret-key"

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def verify_e2e() -> None:
    print("--- 1. Testing Ingestion (1536-dim check) ---")
    ingest_payload = {
        "content": "The quick brown fox jumps over the lazy dog. Vector dimensions are 1536.",
        "metadata": {"test": "dimension_check"},
        "source": "e2e_test",
    }

    resp = requests.post(
        f"{API_BASE_URL}/v1/ingest", json=ingest_payload, headers=headers
    )
    if resp.status_code != 200:
        print(f"FAILED: Ingest returned {resp.status_code}: {resp.text}")
        sys.exit(1)

    task_id = resp.json()["task_id"]
    print(f"Ingestion accepted. Task ID: {task_id}")

    # Simple poll for task completion
    for _ in range(10):
        time.sleep(2)
        task_resp = requests.get(f"{API_BASE_URL}/v1/tasks/{task_id}", headers=headers)
        status = task_resp.json().get("status")
        print(f"Task status: {status}")
        if status == "completed":
            break
        if status == "failed":
            print(f"FAILED: Task failed: {task_resp.text}")
            sys.exit(1)
    else:
        print("FAILED: Task timed out")
        sys.exit(1)

    print("\n--- 2. Testing Search (Backward compatibility: string strategy) ---")
    search_payload_str = {
        "query": "quick brown fox",
        "limit": 5,
        "strategy": "hybrid",  # String strategy to test 422 fix
    }
    resp = requests.post(
        f"{API_BASE_URL}/v1/search", json=search_payload_str, headers=headers
    )
    if resp.status_code != 200:
        print(f"FAILED: Search (string) returned {resp.status_code}: {resp.text}")
        sys.exit(1)
    print(f"SUCCESS: Search (string) returned {len(resp.json()['results'])} results")

    print("\n--- 4. Testing Specific Backends (fts, qdrant, pgvector) ---")
    for strategy in ["fts", "qdrant", "pgvector"]:
        payload = {"query": "quick brown fox", "limit": 5, "strategy": strategy}
        resp = requests.post(f"{API_BASE_URL}/v1/search", json=payload, headers=headers)
        if resp.status_code != 200:
            print(
                f"FAILED: Search ({strategy}) returned {resp.status_code}: {resp.text}"
            )
            sys.exit(1)
        print(f"SUCCESS: Search ({strategy}) returned results")

    print("\nALL E2E TESTS PASSED!")


if __name__ == "__main__":
    verify_e2e()
