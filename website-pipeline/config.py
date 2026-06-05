"""
QuantEA Labs Website Pipeline — Configuration
==============================================
Carmen's auto-blogging pipeline for the QuantEA Labs Astro website.
Website path: /Users/kimssa/Documents/Quant-Labs/
Deploy: Netlify (auto-deploy on git push)
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
WEBSITE_ROOT = Path("/Users/kimssa/Documents/Quant-Labs")
CONTENT_DIR = WEBSITE_ROOT / "src" / "content" / "blog"
IMAGES_DIR = WEBSITE_ROOT / "public" / "images" / "blog"
PUBLIC_DIR = WEBSITE_ROOT / "public"

# Pipeline workspace
PIPELINE_DIR = Path("/Users/kimssa/.openclaw/workspace/website-pipeline")
TEMPLATES_DIR = PIPELINE_DIR / "templates"

# Patreon DB (for data-driven articles)
PATREON_DB = Path("/Users/kimssa/.openclaw/workspace/patreon-db")

# ── Site Config ────────────────────────────────────────
SITE_URL = "https://quantealabs.com"
SITE_NAME = "QuantEA Labs"
AUTHOR = "Kim Ssa"
AUTHOR_BIO = (
    "Quantitative trader and researcher specializing in the intersection of "
    "Vedic astrology and algorithmic trading. Passionate about developing "
    "data-driven insights for the XAUUSD market."
)
DEFAULT_DESCRIPTION = "Where Vedic Astrology Meets Quantitative Trading"

# ── Article Categories ────────────────────────────────
CATEGORIES = [
    "Trading Strategy",
    "Market Analysis",
    "EA Development",
    "Astrology Fundamentals",
    "Risk Management",
]

# ── SEO Defaults ───────────────────────────────────────
DEFAULT_OG_IMAGE = "/images/og-default.png"
KEYWORDS_BASE = [
    "XAUUSD", "gold trading", "forex", "algorithmic trading",
    "Vedic astrology trading", "Gann theory", "EA trading",
    "quantitative trading", "gold analysis",
]

# ── Git Config ─────────────────────────────────────────
GIT_REMOTE = "origin"
GIT_BRANCH = "main"
AUTO_COMMIT = True  # Carmen auto-commits & pushes after publishing
COMMIT_MESSAGE_TEMPLATE = "publish: {title}"

# ── Article Templates ─────────────────────────────────
ARTICLE_TEMPLATE = """---
title: "{title}"
description: "{description}"
pubDate: {pub_date}
author: "{author}"
tags: {tags}
category: "{category}"
featuredImage: "{featured_image}"
featuredImageAlt: "{featured_image_alt}"
slug: "{slug}"
readingTime: {reading_time}
draft: false
seo:
  keywords: {seo_keywords}
  ogType: "article"
schema:
  "@type": "Article"
---

{content}
"""

# ── Content Quality Rules ─────────────────────────────
MIN_WORD_COUNT = 1200  # Minimum words per article
MAX_WORD_COUNT = 3500
TARGET_WORD_COUNT = 1800

# Required sections in every article
REQUIRED_SECTIONS = [
    "## Key Takeaways",
    "## The Setup",
    "## The Analysis",
    "## Risk Management",
    "## Conclusion",
]

# ── Image Generation ──────────────────────────────────
# Chart settings for mplfinance (if auto-generating)
CHART_WIDTH = 1200
CHART_HEIGHT = 675  # 16:9 aspect ratio
CHART_DPI = 150
