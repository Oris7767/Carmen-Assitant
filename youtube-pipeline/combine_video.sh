#!/bin/bash
# Combine background image + audio narration → YouTube Short 1080x1920
# Usage: ./combine_video.sh <bg_image> <audio_file> <output_mp4>

BG="${1:-bg.jpg}"
AUDIO="${2:-narration.mp3}"
OUTPUT="${3:-output_003.mp4}"
DURATION=30  # seconds
FPS=15
W=1080
H=1920

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🎬 Creating video..."
echo "   BG: $BG"
echo "   Audio: $AUDIO"
echo "   Output: $OUTPUT"
echo "   Duration: ${DURATION}s"

# If audio exists, get its actual duration
if [ -f "$AUDIO" ]; then
    AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO" 2>/dev/null)
    if [ -n "$AUDIO_DUR" ]; then
        DURATION=$(echo "$AUDIO_DUR + 0.5" | bc)
        DURATION=${DURATION%.*}
        echo "   Audio duration: ${AUDIO_DUR}s → Video: ${DURATION}s"
    fi
fi

TOTAL_FRAMES=$((DURATION * FPS))

# Simple approach: static image + audio
ffmpeg -y \
    -loop 1 -i "$BG" \
    -i "$AUDIO" \
    -c:v libx264 \
    -preset ultrafast \
    -crf 23 \
    -t "$DURATION" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
    -c:a aac -b:a 128k \
    -shortest \
    -movflags +faststart \
    "$OUTPUT"

echo "✅ Video: $OUTPUT ($(du -h "$OUTPUT" | cut -f1))"
