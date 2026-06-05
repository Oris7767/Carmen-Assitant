import sys, os
sys.path.insert(0, '/root/horoscope-bot')
from engine.pdf_generator import save_pdf

with open('/root/horoscope-bot/data/pdfs/reading_20260602_input.txt', 'r') as f:
    full_text = f.read()

chart_data = {
    'name': 'Khách hàng (10:05 22/04/2000 - Hà Tĩnh)',
    'metadata': {
        'date': '22/04/2000',
        'time': '10:05',
        'location': 'Hà Tĩnh',
    }
}

print(f'Input text: {len(full_text):,} chars')
pdf_path = save_pdf(full_text, chart_data)
print(f'PDF: {pdf_path} ({os.path.getsize(pdf_path):,} bytes)')
print(f'Filename: {os.path.basename(pdf_path)}')
