#!/usr/bin/env python3
"""
Download all Wikimedia Commons images used in posts.json to a local /images/ folder.
Run this locally to self-host images instead of hotlinking from Wikimedia.

Usage:
    python3 download_images.py

After running, update posts.json URLs from:
    https://upload.wikimedia.org/wikipedia/commons/thumb/.../800px-Filename.jpg
To:
    /images/Filename.jpg
"""

import json
import os
import re
import hashlib
import urllib.request
import time

IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')
POSTS_FILE = os.path.join(os.path.dirname(__file__), 'posts.json')

USER_AGENT = 'Mozilla/5.0 (404MemoryFound Blog; https://404memoryfound.com) Python/3.x'


def extract_wikimedia_urls(data):
    """Extract all unique Wikimedia URLs from posts.json."""
    urls = set()
    for post in data['posts']:
        if 'wikimedia' in post.get('image', ''):
            urls.add(post['image'])
        for match in re.finditer(r'src="(https://upload\.wikimedia\.org/[^"]+)"', post['body']):
            urls.add(match.group(1))
    return urls


def filename_from_url(url):
    """Extract the original Wikimedia filename from a thumb URL."""
    # URL format: .../thumb/a/ab/Filename.jpg/800px-Filename.jpg
    parts = url.split('/')
    # The original filename is the second-to-last part
    for i, part in enumerate(parts):
        if part == 'thumb':
            return parts[i + 3]  # skip hash1/hash2/Filename
    # Fallback: last component without width prefix
    last = parts[-1]
    if last.startswith(('800px-', '600px-', '400px-', '1024px-')):
        return last.split('-', 1)[1]
    return last


def download_image(url, filepath):
    """Download a single image with retry."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                with open(filepath, 'wb') as f:
                    f.write(data)
                return len(data)
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                raise


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    with open(POSTS_FILE) as f:
        data = json.load(f)

    urls = extract_wikimedia_urls(data)
    print(f"Found {len(urls)} unique Wikimedia URLs")

    downloaded = 0
    skipped = 0
    failed = 0

    for url in sorted(urls):
        filename = filename_from_url(url)
        filepath = os.path.join(IMAGES_DIR, filename)

        if os.path.exists(filepath):
            print(f"  SKIP (exists): {filename}")
            skipped += 1
            continue

        try:
            size = download_image(url, filepath)
            print(f"  ✓ Downloaded: {filename} ({size:,} bytes)")
            downloaded += 1
            time.sleep(0.5)  # Be polite to Wikimedia servers
        except Exception as e:
            print(f"  ✗ FAILED: {filename} - {e}")
            failed += 1

    print(f"\nDone! Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}")

    if downloaded > 0:
        print("\nTo switch to self-hosted images, run:")
        print("  python3 convert_to_local_images.py")


if __name__ == '__main__':
    main()
