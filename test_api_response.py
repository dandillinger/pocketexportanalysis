#!/usr/bin/env python3
"""
Test script to examine Pocket API response structure
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_api_response():
    """Test the Pocket API response structure"""

    consumer_key = os.getenv("POCKET_CONSUMER_KEY")
    access_token = os.getenv("POCKET_ACCESS_TOKEN")

    if not consumer_key or not access_token:
        print("❌ Missing credentials in .env file")
        return

    # Test with a small batch
    payload = {
        "consumer_key": consumer_key,
        "access_token": access_token,
        "detailType": "complete",
        "state": "all",
        "count": 5,
        "offset": 0,
    }

    print("🔍 Testing Pocket API response structure...")
    print(f"📤 Request payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            "https://getpocket.com/v3/get",
            json=payload,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "X-Accept": "application/json",
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response status: {response.status_code}")
            print(f"📊 Articles in response: {len(data.get('list', {}))}")
            print(f"🔍 Response keys: {list(data.keys())}")

            # Check for 'complete' field
            complete = data.get("complete", "NOT_FOUND")
            print(f"🎯 'complete' field value: {complete} (type: {type(complete)})")

            # Show first article structure
            articles = data.get("list", {})
            if articles:
                first_article_id = list(articles.keys())[0]
                first_article = articles[first_article_id]
                print(f"📄 First article ID: {first_article_id}")
                print(f"📄 First article keys: {list(first_article.keys())}")

            # Test with offset to see if pagination works
            print("\n🔍 Testing pagination with offset=5...")
            payload["offset"] = 5
            response2 = requests.post(
                "https://getpocket.com/v3/get",
                json=payload,
                headers={
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Accept": "application/json",
                },
                timeout=30,
            )

            if response2.status_code == 200:
                data2 = response2.json()
                print(f"📊 Articles in offset=5 response: {len(data2.get('list', {}))}")
                complete2 = data2.get("complete", "NOT_FOUND")
                print(f"🎯 'complete' field value (offset=5): {complete2}")

                # Check if we got different articles
                articles2 = data2.get("list", {})
                if articles2:
                    first_article_id2 = list(articles2.keys())[0]
                    print(f"📄 First article ID (offset=5): {first_article_id2}")
                    print(
                        f"🔍 Same as first batch? {first_article_id == first_article_id2}"
                    )

        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_api_response()
