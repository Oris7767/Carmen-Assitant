from docx import Document
import sys

def read_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        print('\n'.join(full_text))
    except Exception as e:
        print(f"Error reading docx: {e}")

if __name__ == "__main__":
    file_path = "/Users/kimssa/.openclaw/media/inbound/Ta_i_lie_u_chie_m_tinh_trading---b422153b-ad5a-4e18-a91e-4994407403f7.docx"
    read_docx(file_path)
