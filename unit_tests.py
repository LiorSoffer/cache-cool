import requests
import json
import time
import os
import unittest
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

# Test configuration
reqUrl = "http://localhost:8000/groq/chat/completions"

headersList = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"
}
print(f"headersList: {headersList}")


def create_payload(content):
    """Helper function to create test payload"""
    return {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.5,
    }


def make_request(payload):
    """Helper function to make request and return response"""
    try:
        response = requests.post(reqUrl, json=payload, headers=headersList)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def check_key_exists(payload):
    """Check if key exists in cache and return boolean"""
    cache_file = "cache.json"

    if not os.path.exists(cache_file):
        return False

    try:
        # The API might add extra fields, so we need to check if our payload is a subset
        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # First try exact match
        key = json.dumps(payload, sort_keys=True)
        if key in cache_data:
            return True

        # If no exact match, check if our payload content matches any cached key
        for cached_key in cache_data.keys():
            try:
                cached_payload = json.loads(cached_key)
                # Check if our payload is essentially the same (ignoring extra fields)
                if (
                    cached_payload.get("model") == payload.get("model")
                    and cached_payload.get("messages") == payload.get("messages")
                    and cached_payload.get("temperature") == payload.get("temperature")
                ):
                    return True
            except json.JSONDecodeError:
                continue

        return False
    except:
        return False


def get_cache_size():
    """Get number of items in cache"""
    cache_file = "cache.json"
    if not os.path.exists(cache_file):
        return 0
    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
        return len(cache_data)
    except:
        return 0


class TestLRUCache(unittest.TestCase):

    def setUp(self):
        """Clear cache before each test"""
        cache_file = "cache.json"
        if os.path.exists(cache_file):
            os.remove(cache_file)

    def test_basic_caching(self):
        payload = create_payload("Test: What is the capital of France?")

        # First request should not be in cache
        self.assertFalse(
            check_key_exists(payload), "Payload should not be in cache initially"
        )

        # Make first request

        response1 = make_request(payload)
        self.assertIsNotNone(response1, "First request should succeed")

        # Now should be in cache
        self.assertTrue(
            check_key_exists(payload), "Payload should be cached after first request"
        )

        # Make second request
        response2 = make_request(payload)
        self.assertIsNotNone(response2, "Second request should succeed")

    def test_lru(self):
        payloads = [
            create_payload("Access Test 1: Name a color"),
            create_payload("Access Test 2: Name an animal"),
            create_payload("Access Test 3: Name a fruit"),
            create_payload("Access Test 4: Name a country"),
        ]

        # Fill cache with first 3 items
        for i in range(3):
            response = make_request(payloads[i])
            self.assertIsNotNone(response, f"Initial request {i+1} should succeed")
            time.sleep(0.3)

        # Access first item to refresh its position
        response_refresh = make_request(payloads[0])
        self.assertIsNotNone(response_refresh, "Refresh request should succeed")

        # Add 4th item - should evict 2nd item
        response4 = make_request(payloads[3])
        self.assertIsNotNone(response4, "4th request should succeed")

        # Check final state
        self.assertTrue(
            check_key_exists(payloads[0]),
            "First payload should remain (was refreshed)",
        )
        self.assertFalse(
            check_key_exists(payloads[1]), "Second payload should be evicted"
        )
        self.assertTrue(check_key_exists(payloads[2]), "Third payload should remain")
        self.assertTrue(
            check_key_exists(payloads[3]), "Fourth payload should be cached"
        )

    def test_cache_size_limit(self):
        payloads = [create_payload(f"Size test {i}") for i in range(5)]

        # Add items one by one and check cache size
        for i, payload in enumerate(payloads):
            make_request(payload)
            expected_size = min(i + 1, 3)  # Max size is 3
            actual_size = get_cache_size()
            self.assertEqual(
                actual_size,
                expected_size,
                f"Cache size should be {expected_size} after {i+1} requests",
            )


if __name__ == "__main__":
    if(settings.cache_max_size !=3):
        print(f"Cache max size is not 3, please change it in config.yaml and run again")
        exit(0)
    print(f"Running LRU Cache Tests")
    unittest.main(verbosity=2)
