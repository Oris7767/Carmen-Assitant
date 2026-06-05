#!/usr/bin/env python3
"""
manual_reading.py — Manual Full Reading Injector
================================================
Dùng khi bot lỗi / lag, cần tạo PDF và inject vào hệ thống thủ công.

Cách dùng:
  1. Tôi luận giải xong 7 section
  2. Chạy script này trên VPS để:
     - Tạo PDF đúng template
     - Inject vào task store để khách tải qua /reading/pdf/{task_id}
     - Update Supabase order status
     - Gửi Telegram notification cho admin

Usage:
  python3 manual_reading.py --order VEDIC2XXXXXX --name "Nguyễn Văn A" \\
    --dob "22/04/2000" --tob "10:05" --pob "Hà Tĩnh" \\
    --input reading_text.txt
"""

import os
import sys
import json
import uuid
import argparse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "horoscope-bot"
sys.path.insert(0, str(BASE_DIR))

def main():
    parser = argparse.ArgumentParser(description="Manual Reading Injector")
    parser.add_argument("--order", required=True, help="Order ID (VEDIC2XXXXXX)")
    parser.add_argument("--name", default="Không xác định", help="Tên khách hàng")
    parser.add_argument("--dob", default="?", help="Ngày sinh")
    parser.add_argument("--tob", default="?", help="Giờ sinh")
    parser.add_argument("--pob", default="?", help="Nơi sinh")
    parser.add_argument("--input", required=True, help="File txt chứa nội dung 7 section")
    parser.add_argument("--task-id", help="Override task ID (optional)")
    args = parser.parse_args()

    # 1. Đọc nội dung reading
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)
    
    with open(args.input, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
    total_chars = len(full_text)
    print(f"📖 Reading text: {total_chars:,} chars")
    
    # 2. Build chart_data dict (minimal for PDF metadata)
    chart_data = {
        "name": args.name,
        "metadata": {
            "date": args.dob,
            "time": args.tob,
            "location": args.pob,
        }
    }
    
    # 3. Generate PDF
    from engine.pdf_generator import save_pdf
    print("📄 Generating PDF...")
    pdf_path = save_pdf(full_text, chart_data)
    print(f"✅ PDF: {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")
    
    # 4. Inject into task store
    task_id = args.task_id or str(uuid.uuid4())[:8]
    task_store_path = BASE_DIR / "task_store.json"
    
    tasks = {}
    if task_store_path.exists():
        with open(task_store_path) as f:
            tasks = json.load(f)
    
    tasks[task_id] = {
        "status": "done",
        "pdf_path": str(pdf_path),
        "chars": total_chars,
        "sections": 7,
        "injected": True,
    }
    
    with open(task_store_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    print(f"✅ Task store updated: {task_id}")
    
    # 5. Update Supabase (nếu có)
    try:
        from engine.supabase_client import update_order_status
        bp = os.path.basename(pdf_path)
        update_order_status(args.order, "done", 
            pdf_url=f"/reading/pdf/{task_id}",
            notes=f"Manual | PDF: {bp}, chars: {total_chars}, sections: 7")
        print(f"✅ Supabase updated for order {args.order}")
    except Exception as e:
        print(f"⚠️ Supabase update failed: {e}")
    
    # 6. Telegram notification
    try:
        from api.main import send_notification
        send_notification(args.order, task_id, str(pdf_path), chart_data)
        print("✅ Telegram notification sent")
    except Exception as e:
        print(f"⚠️ Telegram notification failed: {e}")
    
    print(f"\n🎉 ALL DONE — Khách tải PDF tại:")
    print(f"   https://horoscope.vedicvn.sbs/reading/pdf/{task_id}")
    print(f"   Hoặc gửi file: {pdf_path}")
    
    return task_id, pdf_path

if __name__ == "__main__":
    main()
