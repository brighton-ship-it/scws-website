#!/usr/bin/env python3
"""Update blog posts to use unique category images instead of Unsplash."""

import os
import re
from pathlib import Path

blog_dir = Path("/Users/jarvis/clawd/scws-website/blog")
image_base = "/assets/images/article-categories"

# Map category text to image files
category_to_image = {
    "troubleshooting": f"{image_base}/troubleshooting.png",
    "pressure issues": f"{image_base}/pressure-issues.png",
    "pressure": f"{image_base}/pressure-issues.png",
    "maintenance": f"{image_base}/maintenance.png",
    "emergency": f"{image_base}/emergency.png",
    "water quality": f"{image_base}/water-quality.png",
    "cost guide": f"{image_base}/cost-guide.png",
    "cost": f"{image_base}/cost-guide.png",
    "equipment": f"{image_base}/equipment.png",
    "warning signs": f"{image_base}/warning-signs.png",
    "warning": f"{image_base}/warning-signs.png",
    "treatment": f"{image_base}/treatment.png",
    "urgent": f"{image_base}/urgent.png",
    "availability": f"{image_base}/equipment.png",  # fallback
}

def get_image_for_category(category_text):
    """Get the appropriate image path for a category."""
    cat_lower = category_text.lower().strip()
    for key, img in category_to_image.items():
        if key in cat_lower:
            return img
    return f"{image_base}/maintenance.png"  # default fallback

def update_related_articles(content):
    """Update Related Articles section images based on category spans."""
    # Pattern to find article cards with category and image
    # Looking for the pattern: <img src="...unsplash..."> followed by <span>Category</span>
    
    # Find all Related Articles sections
    pattern = r'(<a href="[^"]*" class="group[^>]*>.*?<img src=")([^"]+)(" alt="[^"]*"[^>]*>.*?<span class="[^"]*uppercase[^"]*">)([^<]+)(</span>)'
    
    def replacer(match):
        prefix = match.group(1)
        old_src = match.group(2)
        middle = match.group(3)
        category = match.group(4)
        suffix = match.group(5)
        
        # Only replace Unsplash URLs
        if 'unsplash.com' in old_src:
            new_src = get_image_for_category(category)
            return f'{prefix}{new_src}{middle}{category}{suffix}'
        return match.group(0)
    
    # Use DOTALL to match across lines
    updated = re.sub(pattern, replacer, content, flags=re.DOTALL)
    return updated

def update_blog_file(filepath):
    """Update a single blog file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if has unsplash images in related articles
    if 'unsplash.com' not in content:
        return False
    
    updated = update_related_articles(content)
    
    if updated != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        return True
    return False

# Process all blog files
updated_count = 0
for html_file in blog_dir.glob("*.html"):
    if update_blog_file(html_file):
        updated_count += 1
        print(f"✅ Updated {html_file.name}")

print(f"\n✅ Updated {updated_count} blog files with unique category images")
