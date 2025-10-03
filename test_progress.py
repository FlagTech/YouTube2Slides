#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify progress update functionality
"""
import requests
import time
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

API_BASE = "http://localhost:8000"

def test_progress():
    """Test the complete progress update flow"""

    print("=" * 60)
    print("Testing Progress Update Flow")
    print("=" * 60)

    # Step 1: Check backend health
    print("\n1. Checking backend health...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"   ✓ Backend is healthy: {response.json()}")
    except Exception as e:
        print(f"   ✗ Backend error: {e}")
        return

    # Step 2: Get video info (lightweight test)
    print("\n2. Testing video info endpoint...")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Short test video

    try:
        response = requests.post(
            f"{API_BASE}/api/video/info",
            json={"url": test_url},
            timeout=30
        )
        if response.status_code == 200:
            info = response.json()
            print(f"   ✓ Video info received:")
            print(f"     - Title: {info.get('title', 'N/A')[:50]}...")
            print(f"     - Duration: {info.get('duration', 'N/A')} seconds")
            print(f"     - Available subtitles: {len(info.get('available_subtitles', []))}")
        else:
            print(f"   ✗ Error: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ✗ Error getting video info: {e}")
        return

    # Step 3: Start video processing
    print("\n3. Starting video processing...")
    try:
        response = requests.post(
            f"{API_BASE}/api/video/process",
            json={
                "url": test_url,
                "quality": "360",  # Use lowest quality for faster testing
                "subtitle_languages": ["en"],
                "translate_to": None,
                "screenshot_position": "middle",
                "screenshot_offset": 0.0
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            print(f"   ✓ Job created: {job_id}")
        else:
            print(f"   ✗ Error: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ✗ Error starting processing: {e}")
        return

    # Step 4: Poll job status
    print("\n4. Polling job status...")
    print("   (Press Ctrl+C to stop)")

    try:
        last_progress = -1
        last_step = None

        while True:
            try:
                response = requests.get(f"{API_BASE}/api/jobs/{job_id}")

                if response.status_code == 200:
                    status = response.json()
                    progress = status.get('progress', 0)
                    current_step = status.get('current_step', 'unknown')
                    message = status.get('message', '')
                    job_status = status.get('status', 'unknown')

                    # Only print when progress changes
                    if progress != last_progress or current_step != last_step:
                        print(f"\n   [{job_status.upper()}] {progress}% - {current_step}")
                        print(f"   Message: {message}")
                        last_progress = progress
                        last_step = current_step

                    # Check if completed or failed
                    if job_status == 'completed':
                        print("\n   ✓ Job completed successfully!")
                        result = status.get('result', {})
                        print(f"   Total frames: {result.get('total_frames', 0)}")
                        break
                    elif job_status == 'failed':
                        error = status.get('error', 'Unknown error')
                        print(f"\n   ✗ Job failed: {error}")
                        break

                else:
                    print(f"   ✗ Error polling status: {response.status_code}")
                    break

            except requests.exceptions.RequestException as e:
                print(f"   ✗ Request error: {e}")
                break

            time.sleep(0.5)  # Poll every 500ms

    except KeyboardInterrupt:
        print("\n\n   Polling stopped by user")

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_progress()
