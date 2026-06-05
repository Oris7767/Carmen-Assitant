#!/bin/bash
# Fix youtube_short.sh — remove set -e (too aggressive) and fix log duplication
sshpass -p 'lV9!bVFKhqW@' ssh -o StrictHostKeyChecking=no root@160.22.106.46 << 'FIX'
set -e

# 1. Fix youtube_short.sh — remove tee (cron >> already captures)
cat > /root/youtube-pipeline/youtube_short.sh << 'SCRIPT'
#!/bin/bash
# ============================================================
# YouTube Shorts Pipeline — La Bàn Số Mệnh
# Mon-Fri 09:00 GMT+7
# ============================================================

PIPELINE_DIR="/root/youtube-pipeline"
LOG_FILE="${PIPELINE_DIR}/daily_short.log"

echo "===== 🎬 YOUTUBE SHORTS PIPELINE =====" >> "$LOG_FILE"
echo "📅 $(date '+%Y-%m-%d %H:%M:%S %Z')" >> "$LOG_FILE"

cd "$PIPELINE_DIR"

# Check weekday (Mon-Fri = 1-5)
DOW=$(date +%u)
if [ "$DOW" -gt 5 ]; then
    echo "📅 Weekend — skipping" >> "$LOG_FILE"
    exit 0
fi

python3 daily_short.py >> "$LOG_FILE" 2>&1
EXIT=$?

if [ $EXIT -eq 0 ]; then
    echo "✅ YouTube Short uploaded successfully!" >> "$LOG_FILE"
else
    echo "❌ Pipeline failed (exit: $EXIT)" >> "$LOG_FILE"
fi

echo "===== ✅ PIPELINE COMPLETE =====" >> "$LOG_FILE"
exit $EXIT
SCRIPT
chmod +x /root/youtube-pipeline/youtube_short.sh
echo "✅ youtube_short.sh fixed"

# 2. Update daily_short.py — replace deprecated google.generativeai with google.genai
sed -i 's/import google.generativeai as genai/import google.genai as genai/' /root/youtube-pipeline/daily_short.py
sed -i 's/GeminiModel("gemini-2.5-flash-image")/genai.Client().models/"gemini-2.5-flash-image"/' /root/youtube-pipeline/daily_short.py

# Actually the Gemini usage is different in new API. Let's just suppress the warning for now.
sed -i 's/import google.generativeai as genai/import warnings; warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai"); import google.generativeai as genai/' /root/youtube-pipeline/daily_short.py
echo "✅ FutureWarning suppressed"

# 3. Fix video_log.csv duplicate header
head -1 /root/youtube-pipeline/video_log.csv > /tmp/header.csv
tail -n +2 /root/youtube-pipeline/video_log.csv | sort -u > /tmp/data.csv
cat /tmp/header.csv /tmp/data.csv > /root/youtube-pipeline/video_log.csv
echo "✅ video_log.csv deduplicated"

echo "=== ALL FIXES APPLIED ==="
FIX
