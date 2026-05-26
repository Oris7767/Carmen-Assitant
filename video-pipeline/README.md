# 🎬 Video Pipeline

Auto video generator từ prompt đơn giản. Chỉ cần Gemini API key.

## Flow

```
User Prompt → Gemini 2.5 Pro (kịch bản JSON)
  → Gemini Imagen (tạo ảnh stick figure từng cảnh)
  → gTTS (đọc thoại tiếng Việt/Anh)
  → ffmpeg (ghép ảnh + audio thành video clip)
  → ffmpeg concat → Final MP4
```

## Cài đặt

```bash
cd video-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Cấu hình

Tạo file `.env`:

```bash
GEMINI_API_KEY=your_gemini_api_key
```

Lấy key tại: https://aistudio.google.com/apikey

## Chạy

```bash
source venv/bin/activate
python pipeline.py "tạo video người que, triết lý Elon Musk, 10 phân cảnh"
```

Kết quả trong `outputs/<timestamp>/<title>.mp4`

## Output Structure

```
outputs/20260523_203000_a1b2c3d4/
├── script.json              # Full script with all prompts
├── scene_01_image.png       # Image per scene
├── scene_01_audio.mp3       # Voiceover per scene
├── scene_01.mp4             # Video clip per scene
├── ...
└── Final_Video_Title.mp4    # Concatenated final video
```

## Tuỳ chọn

```bash
# Tiếng Anh
python pipeline.py "make a stickman video about stoicism, 8 scenes" --lang en

# Force tiếng Việt
python pipeline.py "vẽ video người que về thiền định" --lang vi
```
