#!/usr/bin/env python3
"""
QuantEA Labs — Article Generator
=================================
Writes SEO-optimized Markdown articles into the QuantEA Labs Astro website.
Run: python3 generate_article.py
Or import: from generate_article import publish_article
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import date, datetime
from typing import Optional

# Add pipeline dir to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    WEBSITE_ROOT, CONTENT_DIR, IMAGES_DIR, SITE_URL, AUTHOR,
    ARTICLE_TEMPLATE, KEYWORDS_BASE, MIN_WORD_COUNT, REQUIRED_SECTIONS,
    GIT_REMOTE, GIT_BRANCH, AUTO_COMMIT, COMMIT_MESSAGE_TEMPLATE,
)


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80]  # Max 80 chars


def count_words(text: str) -> int:
    """Count words in markdown text (excluding frontmatter)."""
    # Remove frontmatter
    body = re.sub(r'^---.*?---', '', text, flags=re.DOTALL)
    # Count words
    words = re.findall(r'\b\w+\b', body)
    return len(words)


def estimate_reading_time(word_count: int) -> int:
    """Estimate reading time in minutes (200 WPM)."""
    return max(1, round(word_count / 200))


def validate_article(content: str, title: str) -> list[str]:
    """Validate article quality. Returns list of warnings."""
    warnings = []
    word_count = count_words(content)

    if word_count < MIN_WORD_COUNT:
        warnings.append(f"⚠️ Word count {word_count} < {MIN_WORD_COUNT} minimum")

    for section in REQUIRED_SECTIONS:
        if section.lower() not in content.lower():
            warnings.append(f"⚠️ Missing section: {section}")

    # Check for empty headings
    empty_headings = re.findall(r'^#{1,3}\s*$', content, re.MULTILINE)
    if empty_headings:
        warnings.append(f"⚠️ Found {len(empty_headings)} empty heading(s)")

    # Check for broken image references
    broken_imgs = re.findall(r'!\[.*?\]\((?!https?://)(.*?)\)', content)
    for img in broken_imgs:
        img_path = IMAGES_DIR / Path(img).name
        if not img_path.exists():
            warnings.append(f"⚠️ Referenced image not found: {img}")

    return warnings


def build_frontmatter(
    title: str,
    description: str,
    tags: list[str],
    category: str,
    slug: str,
    content: str,
    featured_image: Optional[str] = None,
    featured_image_alt: Optional[str] = None,
    pub_date: Optional[str] = None,
    keywords: Optional[list[str]] = None,
) -> str:
    """Build YAML frontmatter string."""

    if pub_date is None:
        pub_date = date.today().isoformat()

    word_count = count_words(content)
    reading_time = estimate_reading_time(word_count)

    if featured_image is None:
        featured_image = f"/images/blog/{pub_date}-chart.png"

    if featured_image_alt is None:
        featured_image_alt = f"Chart analysis for: {title}"

    if keywords is None:
        keywords = list(set(KEYWORDS_BASE + tags))

    # Python-safe list formatting for YAML
    tags_str = json.dumps(tags)
    kw_str = json.dumps(keywords)

    return ARTICLE_TEMPLATE.format(
        title=title,
        description=description,
        pub_date=pub_date,
        author=AUTHOR,
        tags=tags_str,
        category=category,
        featured_image=featured_image,
        featured_image_alt=featured_image_alt,
        slug=slug,
        reading_time=reading_time,
        seo_keywords=kw_str,
        content=content.strip(),
    )


def publish_article(
    title: str,
    description: str,
    content: str,
    tags: list[str],
    category: str,
    slug: Optional[str] = None,
    featured_image: Optional[str] = None,
    featured_image_alt: Optional[str] = None,
    pub_date: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    dry_run: bool = False,
) -> dict:
    """
    Publish an article to the QuantEA Labs website.

    Args:
        title: Article title (H1)
        description: Meta description (150-160 chars ideal)
        content: Markdown body (min 1200 words)
        tags: 3-5 tags e.g. ["XAUUSD", "Gann", "Mars Retrograde"]
        category: One of Trading Strategy, Market Analysis, EA Development,
                  Astrology Fundamentals, Risk Management
        slug: URL slug (auto-generated from title if not provided)
        featured_image: Path relative to /public/ e.g. "/images/blog/2026-05-27-chart.png"
        featured_image_alt: Alt text for featured image
        pub_date: ISO date YYYY-MM-DD (defaults to today)
        keywords: SEO keywords list
        dry_run: If True, prints article but doesn't save

    Returns:
        dict with status, path, warnings
    """
    # Generate slug
    if slug is None:
        slug = slugify(title)

    # Generate pub_date
    if pub_date is None:
        pub_date = date.today().isoformat()

    # Validate
    warnings = validate_article(content, title)

    # Build full markdown with frontmatter
    full_md = build_frontmatter(
        title=title,
        description=description,
        tags=tags,
        category=category,
        slug=slug,
        content=content,
        featured_image=featured_image,
        featured_image_alt=featured_image_alt,
        pub_date=pub_date,
        keywords=keywords,
    )

    # Determine filename
    filename = f"{pub_date}-{slug}.md"
    filepath = CONTENT_DIR / filename

    result = {
        "status": "ok",
        "filename": filename,
        "filepath": str(filepath),
        "slug": slug,
        "word_count": count_words(content),
        "reading_time": estimate_reading_time(count_words(content)),
        "warnings": warnings,
    }

    if dry_run:
        print("=" * 70)
        print("DRY RUN — Article Preview")
        print("=" * 70)
        print(f"Title: {title}")
        print(f"Slug: {slug}")
        print(f"Date: {pub_date}")
        print(f"Category: {category}")
        print(f"Tags: {tags}")
        print(f"Word Count: {result['word_count']}")
        print(f"Reading Time: {result['reading_time']} min")
        if warnings:
            print(f"\n⚠️ Warnings:")
            for w in warnings:
                print(f"  {w}")
        print(f"\nFile would be: {filepath}")
        print("=" * 70)
        return result

    # Ensure directories exist
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Write article
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"✅ Article published: {filepath}")
    print(f"   Words: {result['word_count']} | Read: {result['reading_time']} min")

    if warnings:
        print(f"   ⚠️ {len(warnings)} warning(s):")
        for w in warnings:
            print(f"      {w}")

    # Auto-commit & push if enabled
    if AUTO_COMMIT:
        print(f"\n🚀 Auto-pushing to {GIT_REMOTE}/{GIT_BRANCH}...")
        success = git_commit_and_push(title)
        result["deployed"] = success
        if success:
            print(f"   ✅ Deployed! Check: {SITE_URL}/blog/{slug}")

    return result


def git_commit_and_push(article_title: str) -> bool:
    """Commit and push the new article to trigger Netlify deploy."""
    try:
        # Stage content + images
        subprocess.run(
            ["git", "add", "src/content/blog/", "public/images/blog/"],
            cwd=WEBSITE_ROOT,
            check=True,
            capture_output=True,
        )

        # Check if there's anything to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=WEBSITE_ROOT,
            capture_output=True,
        )
        if result.returncode == 0:
            print("📝 Nothing new to commit")
            return True

        # Commit
        msg = COMMIT_MESSAGE_TEMPLATE.format(title=article_title)
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=WEBSITE_ROOT,
            check=True,
            capture_output=True,
        )

        # Push
        subprocess.run(
            ["git", "push", GIT_REMOTE, GIT_BRANCH],
            cwd=WEBSITE_ROOT,
            check=True,
            capture_output=True,
        )

        print(f"🚀 Pushed to {GIT_REMOTE}/{GIT_BRANCH} — Netlify deploying...")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e.stderr.decode() if e.stderr else str(e)}")
        return False


def check_site_health() -> dict:
    """Check if the website structure is ready for publishing."""
    issues = []

    if not WEBSITE_ROOT.exists():
        issues.append("❌ Website root not found")
    if not CONTENT_DIR.exists():
        issues.append("❌ Content directory not found: src/content/blog/")
    if not IMAGES_DIR.exists():
        issues.append("⚠️ Images directory doesn't exist yet: public/images/blog/")

    # Check if astro can build
    try:
        result = subprocess.run(
            ["npx", "astro", "check"],
            cwd=WEBSITE_ROOT,
            capture_output=True,
            timeout=30,
        )
        astro_ok = result.returncode == 0
    except Exception:
        astro_ok = False

    return {
        "site_root": str(WEBSITE_ROOT),
        "content_dir": str(CONTENT_DIR),
        "images_dir": str(IMAGES_DIR),
        "content_exists": CONTENT_DIR.exists(),
        "images_exist": IMAGES_DIR.exists(),
        "astro_check": astro_ok,
        "issues": issues,
    }


# ── CLI ───────────────────────────────────────────────────
if __name__ == "__main__":
    # Health check
    print("🔍 Checking site health...")
    health = check_site_health()
    for issue in health["issues"]:
        print(f"  {issue}")

    if not health["content_exists"]:
        print("\n❌ Content directory missing. Create src/content/blog/ first.")
        sys.exit(1)

    print(f"\n✅ Site root: {health['site_root']}")
    print(f"✅ Content dir: {health['content_dir']}")
    print(f"✅ Astro check: {'PASS' if health['astro_check'] else 'FAIL'}")
    print("\nPipeline ready. Use publish_article() to generate content.")
    print("Or run: python3 -c \"from generate_article import publish_article; ...\"")
