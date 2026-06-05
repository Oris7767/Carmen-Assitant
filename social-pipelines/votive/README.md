# 🪐 Votive Academy — Social Pipeline

> Brand: **Votive Academy** — Chiêm tinh Vệ Đà
> Website: https://votive.vedicvn.com
> Không dùng "bot", "AI", "La Bàn Số Mệnh" — dùng "trợ lý số Votive"

## Post lên Facebook + Instagram

```bash
cd social-pipelines/votive/scripts

# Facebook (có ảnh)
python3 meta_post.py fb "nội dung..." "/path/to/image.jpg"

# Facebook (text only)
python3 meta_post.py fb "nội dung..."

# Instagram (cần ảnh)
python3 meta_post.py ig-photo "/path/to/image.jpg" "caption..."
```

## Post lên X (Twitter)

```bash
cd social-pipelines/votive/scripts

# Browser automation (có session login)
node x_poster.js \
  --content ../posts/x-post.md \
  --image /path/to/image.jpg

# Nếu cần login lại
node x_poster.js \
  --content ../posts/x-post.md \
  --image /path/to/image.jpg \
  --visible
```

## Post content mẫu

| File | Dùng cho |
|------|----------|
| `posts/fb-post.md` | Facebook |
| `posts/ig-caption.md` | Instagram caption |
| `posts/x-post.md` | X (Twitter) |

## Token

- **Meta token:** lưu ở `scripts/.token` (vĩnh viễn)
- **X session:** lưu ở `scripts/x-session/` (Playwright persistent context)
