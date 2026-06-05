"""
error_sanitizer.py — Sanitize internal errors for user-facing API responses.
Prevents leaking API keys, quota details, model names, internal architecture.
"""

import re
import sys

# Patterns that indicate sensitive internal info
_SENSITIVE_PATTERNS = [
    r'api[_-]?key[=:]\s*\S+',
    r'AIza\w+',
    r'sk-\w+',
    r'quotaMetric.*',
    r'quotaId.*',
    r'quotaDimensions.*',
    r'generativelanguage\.googleapis\.com',
    r'generate_content_free_tier.*',
    r'GenerateRequestsPer.*',
    r'generateContent.*',
    r'@type.*googleapis\.com.*',
    r'retryDelay.*',
    r'RetryInfo.*',
    r'links.*ai\.google\.dev.*',
    r'QuotaFailure.*',
    r'violations.*',
]

_ERROR_CATEGORIES = {
    '429': 'Hệ thống AI đang quá tải, vui lòng thử lại sau vài phút.',
    'RESOURCE_EXHAUSTED': 'Hệ thống AI đã đạt giới hạn truy vấn, vui lòng thử lại sau.',
    'quota': 'API đã đạt giới hạn sử dụng. Đội ngũ kỹ thuật sẽ kiểm tra.',
    'timeout': 'Kết nối đến dịch vụ phân tích bị timeout. Vui lòng thử lại.',
    'ConnectionError': 'Không thể kết nối đến dịch vụ dữ liệu. Kiểm tra kết nối mạng.',
    'HTTPError': 'Dịch vụ dữ liệu gặp sự cố. Đội ngũ kỹ thuật đã được thông báo.',
    'RateLimitError': 'Hệ thống đang xử lý quá nhiều yêu cầu. Vui lòng đợi.',
}


def _categorize_error(error_text: str) -> str:
    """Map raw error text to a user-friendly Vietnamese message."""
    lower = error_text.lower()
    if '429' in error_text or 'resource_exhausted' in lower:
        return _ERROR_CATEGORIES['429']
    if 'quota' in lower:
        return _ERROR_CATEGORIES['quota']
    if 'timeout' in lower or 'timed out' in lower:
        return _ERROR_CATEGORIES['timeout']
    if 'connection' in lower:
        return _ERROR_CATEGORIES['ConnectionError']
    if 'http' in lower and ('500' in error_text or '503' in error_text):
        return _ERROR_CATEGORIES['HTTPError']
    if 'rate' in lower and 'limit' in lower:
        return _ERROR_CATEGORIES['RateLimitError']
    return 'Hệ thống gặp sự cố kỹ thuật tạm thời. Vui lòng thử lại sau.'


def sanitize_error_text(raw_text: str, context: str = "") -> str:
    """
    Convert raw error text into a safe, user-friendly message.
    Logs the full error to stderr for debugging.
    """
    print(f"🔴 ERROR [{context}]: {raw_text[:300]}", file=sys.stderr)
    return _categorize_error(raw_text)


def sanitize_exception(e: Exception, context: str = "") -> str:
    """Sanitize an exception for user-facing output."""
    return sanitize_error_text(str(e), context)
