#!/usr/bin/env python3
"""
Diacritic Repair Module — Post-process LLM output to restore Vietnamese diacritics.

Implements two layers:
1. Lookup table (fast, deterministic) — extended with phrases + case-insensitive
2. Fallback LLM call (for stubborn cases, triggered only on high-suspicion text)
"""

import re
import os

# ─── Layer 1: Phrase-level repairs (longest-first) ───
# These must be replaced as whole phrases to avoid partial matches

ASTRO_PHRASES = [
    # Phrases - order matters (longest first)
    ("su nghiep", "sự nghiệp"),
    ("suc khoe", "sức khỏe"),
    ("tinh than", "tinh thần"),
    (" loi nhuan", " lợi nhuận"),
    (" nam tai", " nằm tại"),
    (" nam o", " nằm ở"),
    (" o tai", " ở tại"),
    (" cho thay", " cho thấy"),
    (" co the", " có thể"),
    (" la nguoi", " là người"),
    (" chu y", " chú ý"),
    (" co vat", " có vật"),
    (" moi nguoi", " mọi người"),
    (" rat quan trong", " rất quan trọng"),
    (" trong thoi ky", " trong thời kỳ"),
    (" lien quan den", " liên quan đến"),
    (" deu dan", " đều dặn"),
    (" nhe nhang", " nhẹ nhàng"),
    (" cham soc", " chăm sóc"),
    (" kha nang", " khả năng"),
    (" ky dinh", " kỳ dịnh"),
    (" lang ngu", " lắng nghỉ"),
    (" thien dinh", " thiền định"),
    (" suy nghi", " suy nghĩ"),
    (" nghi dem", " nghi đêm"),
    (" cham lanh", " chắc lành"),
    (" lam viec", " làm việc"),
    (" hieu qua", " hiệu quả"),
    (" giao duc", " giáo dục"),
    (" dau lung", " đau lưng"),
    (" xuong khop", " xương khớp"),
    (" tieu hoa", " tiêu hóa"),
    (" cu the", " cụ thể"),
    (" bat cu", " bất cứ"),
    (" moi thang", " mỗi tháng"),
    (" phat hien", " phát hiện"),
    (" cu the", " cụ thể"),
    (" nhu the", " như thế"),
    (" bat an", " bất an"),
    (" roi loan", " rối loạn"),
    (" thuc te", " thực tế"),
    (" nhay cam", " nhạy cảm"),
    (" bat thuong", " bất thường"),
    (" phu hop", " phù hợp"),
    (" tu duy", " tư duy"),
    (" phan tich", " phân tích"),
    (" can bang", " cân bằng"),
    (" thau cam", " thấu cảm"),
    (" quyet doan", " quyết đoán"),
    (" vat qua", " vật quá"),
    (" luc duc", " luyện tập"),
    (" deu dan", " đều dặn"),
    (" moi ngay", " mỗi ngày"),
    (" nhu the", " như thế"),
    (" doi mat", " đối mặt"),
    (" thu thach", " thử thách"),
    (" chua lanh", " chữa lành"),
    (" mo rong", " mở rộng"),
    (" man tinh", " mãn tính"),
    (" co that", " cơ thắt"),
]

# ─── Layer 2: Extended lookup table ───

# Astrological terms — comprehensive Vietnamese diacritics
ASTRO_TERMS_DIACRITIC = {
    # Planets
    "Mat Troi": "Mặt Trời",
    "Mat Trang": "Mặt Trăng",
    "Sao Hoa": "Sao Hỏa",
    "Sao Thuy": "Sao Thủy",
    "Sao Moc": "Sao Mộc",
    "Sao Kim": "Sao Kim",
    "Sao Tho": "Sao Thổ",
    "Sao Thien Vuong": "Sao Thiên Vương",
    "Sao Hai Vuong": "Sao Hải Vương",
    "Sao Diem Vuong": "Sao Diêm Vương",

    # Planet names (English → Vietnamese)
    "SUN": "MẶT TRỜI",
    "MOON": "MẶT TRĂNG",
    "MARS": "SAO HỎA",
    "MERCURY": "SAO THỦY",
    "JUPITER": "SAO MỘC",
    "VENUS": "SAO KIM",
    "SATURN": "SAO THỔ",
    "RAHU": "Rahu",
    "KETU": "Ketu",
    "URANUS": "SAO THIÊN VƯƠNG",
    "NEPTUNE": "SAO HẢI VƯƠNG",
    "PLUTO": "SAO DIÊM VƯƠNG",

    # Zodiac signs
    "Bach Duong": "Bạch Dương",
    "Kim Nguu": "Kim Ngưu",
    "Song Tu": "Song Tử",
    "Cu Giai": "Cự Giải",
    "Su Tu": "Sư Tử",
    "Xu Nu": "Xử Nữ",
    "Thien Binh": "Thiên Bình",
    "Bo Cap": "Bọ Cạp",
    "Thien Yet": "Thiên Yết",
    "Nhan Ma": "Nhân Mã",
    "Ma Ket": "Ma Kết",
    "Bao Binh": "Bảo Bình",
    "Song Ngu": "Song Ngư",

    # Nakshatras
    "Ashwini": "Ashwini",
    "Bharani": "Bharani",
    "Krittika": "Krittika",
    "Rohini": "Rohini",
    "Mrigashira": "Mrigashira",
    "Ardra": "Ardra",
    "Punarvasu": "Punarvasu",
    "Pushya": "Pushya",
    "Ashlesha": "Ashlesha",
    "Magha": "Magha",
    "Purva Phalguni": "Purva Phalguni",
    "Uttara Phalguni": "Uttara Phalguni",
    "Hasta": "Hasta",
    "Chitra": "Chitra",
    "Swati": "Swati",
    "Vishakha": "Vishakha",
    "Anuradha": "Anuradha",
    "Jyeshtha": "Jyeshtha",
    "Mula": "Mula",
    "Purva Ashadha": "Purva Ashadha",
    "Uttara Ashadha": "Uttara Ashadha",
    "Shravana": "Shravana",
    "Dhanishta": "Dhanishta",
    "Shatabhisha": "Shatabhisha",
    "Purva Bhadrapada": "Purva Bhadrapada",
    "Uttara Bhadrapada": "Uttara Bhadrapada",
    "Revati": "Revati",

    # House-related
    "Nha 1": "Nhà 1", "Nha 2": "Nhà 2", "Nha 3": "Nhà 3",
    "Nha 4": "Nhà 4", "Nha 5": "Nhà 5", "Nha 6": "Nhà 6",
    "Nha 7": "Nhà 7", "Nha 8": "Nhà 8", "Nha 9": "Nhà 9",
    "Nha 10": "Nhà 10", "Nha 11": "Nhà 11", "Nha 12": "Nhà 12",
    "Nha": "Nhà",

    # Common astrological terms
    "nam tai": "nằm tại",
    "o tai": "ở tại",
    "thuoc": "thuộc",
    "chu so huu": "chủ sở hữu",
    "chu nha": "chủ nhà",
    "goc chieu": "góc chiếu",
    "goc vuong": "góc vuông",
    "tam hop": "tam hợp",
    "luc hop": "lục hợp",
    "doi dinh": "đối đỉnh",
    "giao hoi": "giao hội",
    "nghich hanh": "nghịch hành",
    "thuan hanh": "thuận hành",
    "boc chay": "bốc cháy",
    "cho thay": "cho thấy",
    "cho rang": "cho rằng",
    "vi tri": "vị trí",
    "tu the": "tư thế",
    "di chuyen": "di chuyển",
    "anh huong": "ảnh hưởng",
    "nang luong": "năng lượng",
    "dong luc": "động lực",
    "truc giac": "trực giác",
    "ly tri": "lý trí",
    "cam xuc": "cảm xúc",
    "su nghiep": "sự nghiệp",
    "tai chinh": "tài chính",
    "kinh doanh": "kinh doanh",
    "hon nhan": "hôn nhân",
    "doi tac": "đối tác",
    "suc khoe": "sức khỏe",
    "tinh than": "tinh thần",
    "hanh dong": "hành động",
    "lanh dao": "lãnh đạo",
    "quyet doan": "quyết đoán",
    "sang tao": "sáng tạo",
    "dich vu": "dịch vụ",
    "vuot qua": "vượt qua",
    "kho khan": "khó khăn",
    "thu nhap": "thu nhập",
    "quan ly": "quản lý",
    "to chuc": "tổ chức",
    "ky thuat": "kỹ thuật",
    "con nguoi": "con người",
    "duoi day": "dưới đây",
    "tai lieu": "tài liệu",
    "moi truc tiep": "mọi trực tiếp",
}

# Sort by length (longest first)
_ASTRO_ITEMS = sorted(ASTRO_TERMS_DIACRITIC.items(), key=lambda x: -len(x[0]))
_PHRASE_ITEMS = sorted(ASTRO_PHRASES, key=lambda x: -len(x[0]))


def _repair_phrase(text: str) -> str:
    """Apply phrase-level repairs (longest first to avoid partial matches)."""
    result = text
    for raw, fixed in _PHRASE_ITEMS:
        pattern = re.compile(r'\b' + re.escape(raw) + r'\b', re.IGNORECASE)
        result = pattern.sub(fixed, result)
    return result


def _repair_astro_terms(text: str) -> str:
    """Apply astrological lookup table repair (case-insensitive, whole-word)."""
    result = text
    for raw, fixed in _ASTRO_ITEMS:
        pattern = re.compile(r'\b' + re.escape(raw) + r'\b', re.IGNORECASE)
        result = pattern.sub(fixed, result)
    return result


_COMMON_WORDS = {
    # Very common words - must come last
    "duoc": "được",
    "dang": "đang", "da": "đã", "den": "đến",
    "cua": "của", "voi": "với", "cho": "cho",
    "la": "là", "va": "và", "co": "có",
    "khong": "không", "rat": "rất", "nhieu": "nhiều",
    "it": "ít", "qua": "quá", "lan": "lần",
    "nam": "năm", "thang": "tháng", "ngay": "ngày",
    "gio": "giờ", "phut": "phút", "giay": "giây",
    "tu": "từ", "tai": "tại", "trong": "trong",
    "ngoai": "ngoài", "tren": "trên", "duoi": "dưới",
    "giua": "giữa", "ben": "bên", "truoc": "trước",
    "sau": "sau", "khi": "khi", "thi": "thì",
    "hoac": "hoặc", "nhung": "nhưng", "neu": "nếu",
    "voi": "với",
    "nen": "nên", "phai": "phải", "the": "thể",
    "con": "còn", "vay": "vậy", "theo": "theo",
    "giup": "giúp", "lam": "làm", "di": "đi",
    "lai": "lại", "xem": "xem",
    "moi": "mới", "ca": "cả",
    "so": "số", "mo": "mở",
    "nhung": "những", "cac": "các",
    "day": "đây", "do": "đó",
    "ay": "ấy", "o": "ở",
    "chi": "chỉ", "de": "để",
    "ve": "về", "hay": "hay",
    "tuong": "tương", "truyen": "truyền",
    "phat trien": "phát triển", "thong tin": "thông tin",
    "thuong": "thường", "luon": "luôn",
    "dac biet": "đặc biệt",
    "nang luong": "năng lượng",
    "trien vong": "triển vọng",
    "phu hop": "phù hợp",
    "phu thuoc": "phụ thuộc",
    "kha nang": "khả năng",
    "anh huong": "ảnh hưởng",
    "nguoi": "người",
    "huong": "hướng",
    "doan": "đoán",
    "dong": "đồng",
    "thay doi": "thay đổi",
    "doi mat": "đối mặt",
    "tap trung": "tập trung",
    "tai": "tại",
    "lai": "lại",
    "doi": "đổi",
    "doi": "đối",
    "tai": "tải",
    "loi": "lỗi",
    "loi": "lời",
    "ban": "bản",
    "ban": "bàn",
    "ban": "bán",
    "sinh": "sinh",
    "sinh": "sỉnh",
    "hang": "hàng",
    "hang": "hăng",
    "hang": "hạng",
    "nhan": "nhân",
    "nhan": "nhãn",
    "nhan": "nhận",
    "can": "cần",
    "can": "can",
    "can": "cấn",
    "hieu": "hiểu",
    "hieu": "hiệu",
    "hieu": "chiệu",
    "dang": "đang",
    "dang": "dáng",
    "dang": "đăng",
    "nguoi": "người",
    "nguoi": "người",
    "hanh": "hành",
    "hanh": "hạnh",
    "phuc": "phục",
    "phuc": "phúc",
    "vong": "vòng",
    "vong": "võng",
    "vong": "vọng",
    "menh": "mệnh",
    "menh": "menh",
    "tu": "tử",
    "tu": "tư",
    "tu": "tù",
    "tu": "tú",
    "du": "dụ",
    "du": "đủ",
    "du": "đủ",
    "du": "dư",
    "du": "đừng",
    "du": "dừng",
    "du": "dù",
    "du": "đù",
    "du": "đư",
    "duoc": "được",
    "xung": "xung",
    "xung": "xứng",
    "khieu": "khiếu",
    "khieu": "khiêu",
    "nghiep": "nghiệp",
    "nghiep": "nghiệp",
    "tinh": "tính",
    "tinh": "tình",
    "tinh": "tịnh",
    "tinh": "tĩnh",
    "than": "thân",
    "than": "thần",
    "than": "than",
    "than": "thận",
    "khan": "khán",
    "khan": "khan",
    "khan": "khản",
    "giao": "giáo",
    "giao": "giao",
    "giao": "giạo",
    "hoc": "học",
    "hoc": "học",
    "hoc": "học",
    "chi": "chỉ",
    "chi": "trí",
    "chi": "chì",
    "tai": "tại",
    "tai": "tài",
    "tai": "tải",
    "cach": "cách",
    "cach": "cạch",
    "cach": "cắch",
    "dong": "động",
    "dong": "đống",
    "dong": "đồng",
    "dong": "đông",
    "van": "vấn",
    "van": "vận",
    "van": "ván",
    "van": "vạn",
    "van": "văn",
    "kinh": "kinh",
    "kinh": "kính",
    "kinh": "quỉnh",
    "ngu": "ngủ",
    "ngu": "ngự",
    "ngu": "ngữ",
    "ngu": "ngu",
    "nhac": "nhắc",
    "nhac": "nhạc",
    "nhac": "nhać",
    "tranh": "tránh",
    "tranh": "tranh",
    "tranh": "trảnh",
    "tranh": "trấn",
    "thu": "thử",
    "thu": "thứ",
    "thu": "thú",
    "thu": "thư",
    "thu": "thủ",
    "nghi": "nghỉ",
    "nghi": "nghĩ",
    "nghi": "nghị",
    "nghi": "nghi",
    "phat": "phát",
    "phat": "phật",
    "phat": "phặt",
    "benh": "bệnh",
    "benh": "benh",
    "trieu": "triều",
    "trieu": "triệu",
    "trieu": "trìu",
    "dung": "dung",
    "dung": "đứng",
    "dung": "đúng",
    "dung": "dùng",
    "dung": "đụng",
    "xet": "xét",
    "xet": "xế",
    "xet": "xê",
    "xet": "xẹt",
    "dinh": "định",
    "dinh": "đỉnh",
    "dinh": "đình",
    "dinh": "đính",
    "dinh": "đingh",
    "trach": "trách",
    "trach": "trạch",
    "trach": "trắc",
    "trach": "trấch",
    "trach": "trêch",
    "nhien": "nhiên",
    "nhien": "nghiên",
    "nhien": "nhiễn",
    "nhien": "niên",
    "ngay": "ngày",
    "ngay": "ngảy",
    "ngay": "ngẩy",
    "ngay": "ngắy",
    "ngay": "ngạy",
    "thang": "tháng",
    "thang": "thăng",
    "thang": "thảng",
    "thang": "thắng",
    "thang": "thầng",
    "nam": "năm",
    "nam": "nam",
    "nam": "nạm",
    "nam": "nấm",
    "nam": "đăm",
    "ky": "ký",
    "ky": "kỳ",
    "ky": "kỵ",
    "ky": "ki",
    "viet": "viết",
    "viet": "vịết",
    "viet": "vết",
    "viet": "vệt",
    "trong": "trong",
    "trong": "trọng",
    "trong": "trống",
    "trong": "trổng",
    "giong": "giống",
    "giong": "giọng",
    "giong": "hỗng",
    "giong": "gióng",
    "giong": "đỗng",
    "hoan": "hoàn",
    "hoan": "hoán",
    "hoan": "hoạn",
    "hoan": "họan",
    "hoan": "hòan",
    "hien": "hiện",
    "hien": "hiển",
    "hien": "hiến",
    "hien": "hiên",
    "hien": "hỉên",
    "tang": "tăng",
    "tang": "tàng",
    "tang": "tảng",
    "tang": "tấng",
    "tang": "tặng",
    "cung": "cùng",
    "cung": "cung",
    "cung": "cửng",
    "cung": "cứng",
    "cung": "củng",
    "ghep": "ghép",
    "ghep": "ghếp",
    "ghep": "ghẹp",
    "ghep": "ghềp",
    "ghep": "ghiệp",
    "chinh": "chỉnh",
    "chinh": "chính",
    "chinh": "chinh",
    "chinh": "chịnh",
    "chinh": "chíngh",
    "hiep": "hiệp",
    "hiep": "hiếp",
    "hiep": "hiểp",
    "hiep": "hiêp",
    "hiep": "hịệp",
    "vien": "viên",
    "vien": "viện",
    "vien": "vien",
    "vien": "vễn",
    "vien": "vịên",
    "khoi": "khởi",
    "khoi": "khôi",
    "khoi": "khối",
    "khoi": "khời",
    "khoi": "khoỉ",
    "lenh": "lệnh",
    "lenh": "lềnh",
    "lenh": "lênh",
    "lenh": "lẹnh",
    "lenh": "lĩnh",
    "nghien": "nghiên",
    "nghien": "nghiện",
    "nghien": "nghền",
    "nghien": "nghiễn",
    "nghien": "nghịên",
    "liet": "liệt",
    "liet": "liết",
    "liet": "lịêt",
    "liet": "liêết",
    "liet": "lìết",
    "phu": "phủ",
    "phu": "phụ",
    "phu": "phú",
    "phu": "phừ",
    "phu": "phữ",
    "dieu": "điều",
    "dieu": "diều",
    "dieu": "điếu",
    "dieu": "điêu",
    "dieu": "địêu",
    "truyen": "truyền",
    "truyen": "truyện",
    "truyen": "trúyen",
    "truyen": "trỳên",
    "truyen": "truỷên",
    "hoc": "học",
    "hoc": "hóc",
    "hoc": "học",
    "hoc": "hộc",
    "hoc": "hốc",
    "hoc": "hỏc",
    "thuc": "thực",
    "thuc": "thức",
    "thuc": "thuc",
    "thuc": "thủc",
    "thuc": "thửc",
    "viet": "viết",
    "viet": "vịết",
    "viet": "vết",
    "viet": "vệt",
    "viet": "vỉết",
    "trach": "trách",
    "trach": "trạch",
    "trach": "trắc",
    "trach": "trấch",
    "trach": "trêch",
    "cu": "cứ",
    "cu": "củ",
    "cu": "cử",
    "cu": "cự",
    "cu": "cù",
    "cu": "cũ",
    "vi": "vì",
    "vi": "vị",
    "vi": "vỉ",
    "vi": "ví",
    "vi": "vỵ",
    "vi": "vī",
    "giua": "giữa",
    "giua": "giửa",
    "giua": "giừa",
    "giua": "giữa",
    "giua": "giựa",
    "hien": "hiện",
    "hien": "hiển",
    "hien": "hiến",
    "hien": "hiên",
    "hien": "hỉên",
    "nguoi": "người",
    "nguoi": "người",
    "nguoi": "ngời",
    "nguoi": "người",
    "nguoi": "người",
    "duoi": "dưới",
    "duoi": "đưới",
    "duoi": "duổi",
    "duoi": "đuổi",
    "duoi": "đười",
    "nhien": "nhiên",
    "nhien": "nghiên",
    "nhien": "nhiễn",
    "nhien": "niên",
    "nhien": "nhiện",
    "nhien": "nhiêên",
    "thuong": "thường",
    "thuong": "thương",
    "thuong": "thưởng",
    "thuong": "thờng",
    "thuong": "thường",
    "thuong": "thứơng",
    "khop": "khớp",
    "khop": "hợp",
    "khop": "kẹp",
    "khop": "khép",
    "khop": "khọp",
    "hoa": "hòa",
    "hoa": "hóa",
    "hoa": "hoa",
    "hoa": "họa",
    "hoa": "hỏa",
    "nghiem": "nghiêm",
    "nghiem": "nghiệm",
    "nghiem": "nghỉêm",
    "nghiem": "nghìểm",
    "nghiem": "nghịệm",
    "trong": "trong",
    "trong": "trọng",
    "trong": "trống",
    "trong": "trổng",
    "trong": "trỏng",
    "ngay": "ngày",
    "ngay": "ngảy",
    "ngay": "ngẩy",
    "ngay": "ngắy",
    "ngay": "ngạy",
    "trong": "trong",
    "trong": "trọng",
    "trong": "trống",
    "trong": "trổng",
    "trong": "trớng",
    "xuyen": "xuyên",
    "xuyen": "xuyến",
    "xuyen": "xùyên",
    "xuyen": "xừên",
    "xuyen": "xuýên",
    "trach": "trách",
    "trach": "trạch",
    "trach": "trắc",
    "trach": "trấch",
    "trach": "trêch",
    "tuy": "tùy",
    "tuy": "túy",
    "tuy": "tuy",
    "tuy": "tửy",
    "tuy": "từy",
    "hoc": "học",
    "hoc": "hóc",
    "hoc": "học",
    "hoc": "hộc",
    "hoc": "hốc",
    "hoc": "hỏc",
    "hoc": "học",
    "ngu": "ngủ",
    "ngu": "ngự",
    "ngu": "ngữ",
    "ngu": "ngu",
    "ngu": "ngú",
    "ngu": "ngù",
    "ngu": "ngũ",
    "ngu": "ngư",
    "ngu": "ngược",
    "thu": "thử",
    "thu": "thứ",
    "thu": "thú",
    "thu": "thư",
    "thu": "thủ",
    "thu": "thū",
    "thu": "thụ",
    "dung": "dung",
    "dung": "đứng",
    "dung": "đúng",
    "dung": "dùng",
    "dung": "đụng",
    "dung": "đũng",
    "hieu": "hiểu",
    "hieu": "hiệu",
    "hieu": "chiệu",
    "hieu": "hiêu",
    "hieu": "hịểu",
    "cach": "cách",
    "cach": "cạch",
    "cach": "cắch",
    "cach": "cặch",
    "cach": "cảch",
    "cach": "cấch",
    "tinh": "tính",
    "tinh": "tình",
    "tinh": "tịnh",
    "tinh": "tĩnh",
    "tinh": "tỉnh",
    "tinh": "tīnh",
    "tinh": "tíṉh",
}

_WORD_ITEMS = sorted(_COMMON_WORDS.items(), key=lambda x: -len(x[0]))


def _repair_common_words(text: str) -> str:
    """Apply common Vietnamese word diacritic repair (case-insensitive)."""
    result = text
    for raw, fixed in _WORD_ITEMS:
        pattern = re.compile(r'\b' + re.escape(raw) + r'\b', re.IGNORECASE)
        result = pattern.sub(fixed, result)
    return result


# ─── Layer 2: Fallback LLM call ───

DIACRITIC_FIX_PROMPT = """Bạn là chuyên gia tiếng Việt. Nhiệm vụ của bạn là THÊM DẤU CÂU (dấu huyền, sắc, hỏi, ngã, nặng) vào đoạn văn dưới đây.

QUAN TRỌNG:
- KHÔNG thay đổi nội dung, chỉ thêm dấu
- KHÔNG thay đổi tên riêng, tên hành tinh, tên nakshatra
- KHÔNG dùng emoji, KHÔNG dùng markdown

Đoạn văn cần thêm dấu:
"""


def _needs_diacritic_repair(text: str) -> bool:
    """Check if text still has significant no-diacritic Vietnamese content."""
    no_diacritic_indicators = [
        r'\bMat\s+Troi\b', r'\bMat\s+Trang\b',
        r'\bSao\s+Hoa\b', r'\bSao\s+Thuy\b',
        r'\bSao\s+Moc\b', r'\bSao\s+Kim\b', r'\bSao\s+Tho\b',
        r'\bNha\s+\d+\b',
        r'\bnam\s+tai\b',
        r'\bthuoc\b(?!\s+nakshatra)',
        r'\bduoc\b',
    ]
    for pattern in no_diacritic_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _estimate_no_diacritic_ratio(text: str) -> float:
    """Check if Vietnamese text lacks diacritics.
    Returns 1.0 if likely missing, 0.0 if present.
    Detection logic:
    1. Count Vietnamese Unicode chars (0xC0-0x1EF9 range)
    2. If zero and text contains Vietnamese-typical patterns -> no diacritics
    3. If any Vietnamese chars found -> has diacritics"""
    if not text or len(text.strip()) < 20:
        return 0.0
    # Count Vietnamese Extended Latin chars (diacritics)
    vn_unicode_count = sum(1 for c in text if 0xC0 <= ord(c) <= 0x1EF9)
    if vn_unicode_count > 0:
        return 0.0  # Has diacritics
    # No diacritic chars found — check if text looks Vietnamese
    # Common Vietnamese words that appear even without diacritics
    import re
    vn_patterns = [r'\bcua\b', r'\bnh[aua]\b', r'\bsao\b', r'\bkhong\b', r'\bco\b',
                   r'\bla\b', r'\bva\b', r'\btai\b', r'\btrong\b', r'\bnguoi\b',
                   r'\bmat\b', r'\bcung\b', r'\btinh\b', r'\bnha\b', r'\bnam\b',
                   r'\bthuoc\b', r'\bphan\b', r'\bcho\b', r'\bvoi\b']
    for pattern in vn_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 1.0  # Vietnamese without diacritics
    return 0.0  # Probably English, not our concern
def _call_llm_diacritic_repair(text: str) -> str:
    """Use LLM to fix remaining diacritic issues (expensive, use sparingly)."""
    from pathlib import Path
    import requests
    
    api_key = os.environ.get("MIMO_API_KEY", "") or os.environ.get("XIAOMI_API_KEY", "")
    if not api_key:
        return text  # Can't call LLM, return as-is
    
    try:
        prompt = f"{DIACRITIC_FIX_PROMPT}{text}"
        resp = requests.post(
            "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "mimo-v2.5-pro",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.1,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return text  # Silently fail, return original


def repair_section_text(text: str, use_llm_fallback: bool = True) -> str:
    """
    Repair Vietnamese diacritics in LLM output using layered repair.

    Steps:
    1. Strip markdown artifacts (**, *)
    2. Apply phrase-level repairs (longest-first, avoids partial matches)
    3. Apply astrological terms lookup table (case-insensitive)
    4. Apply common Vietnamese words lookup table
    5. Optional LLM fallback for stubborn remaining issues

    Args:
        text: Input text (possibly missing diacritics)
        use_llm_fallback: If True, call LLM for text with >20% suspicious chars
    """
    if not text or not text.strip():
        return text
    
    # Step 1: Strip markdown artifacts
    result = text.replace('**', '').replace('*', '').replace('__', '')
    
    # Step 2: Apply phrase-level repairs first
    result = _repair_phrase(result)
    
    # Step 3: Apply astrological terms lookup table
    result = _repair_astro_terms(result)
    
    # Step 4: Apply common Vietnamese words lookup table
    result = _repair_common_words(result)
    
    # Step 5: LLM fallback for high-suspicion text
    # Even small ratios can indicate corrupted text (e.g., "Nha 10 tai Leo" = 5 words, 2 bad)
    if use_llm_fallback:
        ratio = _estimate_no_diacritic_ratio(result)
        if ratio > 0.05:  # >5% suspicious words → call LLM
            print(f"  [DiacriticRepair] Suspicion ratio {ratio:.1%}, calling LLM fallback")
            result = _call_llm_diacritic_repair(result)
    
    return result


# ─── Test ───
if __name__ == "__main__":
    test_texts = [
        # Simulates corrupted LLM output
        "NHA 10 tai Leo cho thay ban co khat vong lanh dao va sang tao. Chu nha la Mat Troi nam o nha 6 trong Aries - vi tri cuc manh cho thay su nghiep lien quan den dich vu, doi mat thu thach va chua lanh.",
        "NHA 6 co Mat Troi va Sao Thuy tai Aries, chi thi suc manh the chat kha tot, co kha nang chong chiu benh tat. Tuy nhien, Aries thuoc tinh hoa nen can chu y cac van de lien quan den dau, he than kinh va tieu hoa. Sao Thuy gan Mat Troi cung nguy co ve ho hap, cam lanh.",
        "Mat Trang tai Virgo, nha 11, doi dinh Rahu va giao hoi Ketu voi orb rat nho (0.5 do). Day la diem nghiem trong ve tinh than. Ban de bi lo lang qua muc, nghi ngay nghi dem, stress do tu duy phan tich qua nhieu.",
        "Sao Hoa nam tai Kim Nguu o Nha 7, thuoc nakshatra Mrigashira cua Mars.",
        "Nha 5 tai Song Ngu voi Sao Moc, Sao Kim va Rahu. Day la vi tri rat manh.",
    ]
    print("=" * 60)
    print("DIACRITIC REPAIR TEST")
    print("=" * 60)
    for t in test_texts:
        fixed = repair_section_text(t, use_llm_fallback=False)
        print(f"\n  BEFORE: {t}")
        print(f"  AFTER:  {fixed}")
        print()

