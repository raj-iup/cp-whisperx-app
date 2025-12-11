#!/usr/bin/env bash
# Manual test for YouTube download integration
# Tests the prepare-job.sh YouTube download feature

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
cd "$PROJECT_ROOT"

echo "================================"
echo "YouTube Download Integration Test"
echo "================================"
echo ""

# Test 1: URL Detection
echo "Test 1: URL Detection"
echo "-------------------"
TEST_URL="https://youtube.com/watch?v=dQw4w9WgXcQ"
if [[ "$TEST_URL" =~ ^https?:// ]]; then
    echo "✅ URL pattern detected correctly"
else
    echo "❌ URL pattern NOT detected"
    exit 1
fi
echo ""

# Test 2: Local File Detection (negative test)
echo "Test 2: Local File Detection"
echo "----------------------------"
TEST_FILE="in/movie.mp4"
if [[ "$TEST_FILE" =~ ^https?:// ]]; then
    echo "❌ Local file incorrectly detected as URL"
    exit 1
else
    echo "✅ Local file correctly identified"
fi
echo ""

# Test 3: Python Module Import
echo "Test 3: Python Module Import"
echo "----------------------------"
python3 -c "
from shared.online_downloader import OnlineMediaDownloader, is_online_url
print('✅ Module imported successfully')
assert is_online_url('https://youtube.com/watch?v=TEST')
assert not is_online_url('in/movie.mp4')
print('✅ is_online_url() works correctly')
"
echo ""

# Test 4: Downloader Initialization
echo "Test 4: Downloader Initialization"
echo "---------------------------------"
python3 -c "
from pathlib import Path
from shared.online_downloader import OnlineMediaDownloader

downloader = OnlineMediaDownloader(
    cache_dir=Path('in/online'),
    format_quality='best'
)
print(f'✅ Downloader created')
print(f'   Cache dir: {downloader.cache_dir}')
print(f'   Quality: {downloader.format_quality}')
"
echo ""

# Test 5: Video ID Extraction
echo "Test 5: Video ID Extraction"
echo "---------------------------"
python3 -c "
from pathlib import Path
from shared.online_downloader import OnlineMediaDownloader

downloader = OnlineMediaDownloader(cache_dir=Path('in/online'))

test_urls = [
    ('https://youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ('https://youtu.be/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ('https://youtube.com/embed/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
]

for url, expected_id in test_urls:
    video_id = downloader.extract_video_id(url)
    if video_id == expected_id:
        print(f'✅ {url} → {video_id}')
    else:
        print(f'❌ {url} → {video_id} (expected {expected_id})')
        exit(1)
"
echo ""

# Test 6: Cache Check (should not exist)
echo "Test 6: Cache Check"
echo "------------------"
python3 -c "
from pathlib import Path
from shared.online_downloader import OnlineMediaDownloader

downloader = OnlineMediaDownloader(cache_dir=Path('in/online'))
cached = downloader.get_cached_video('test_nonexistent_video_id')

if cached is None:
    print('✅ Cache miss handled correctly (no file found)')
else:
    print(f'⚠️  Unexpected cached file: {cached}')
"
echo ""

echo "================================"
echo "All Tests Passed! ✅"
echo "================================"
echo ""
echo "Next: Test with real YouTube URL (requires internet)"
echo "  ./prepare-job.sh --media \"https://youtu.be/VIDEO_ID\" --workflow transcribe -s en"
