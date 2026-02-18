#!/usr/bin/env python3
"""
Add AI-generated images to all blog posts based on content keywords.
"""
import os
import re
from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")
IMAGE_DIR = Path("/Users/jarvis/clawd/scws-website/assets/images/blog-images")

# Map keywords to images
SERVICE_IMAGES = {
    'pump-repair': ['pump repair', 'pump replacement', 'pump service', 'broken pump', 'pump fix'],
    'pump-installation': ['pump install', 'new pump', 'pump upgrade'],
    'well-drilling': ['well drill', 'drilling', 'new well', 'dig well'],
    'well-rehabilitation': ['rehabilitation', 'well rehab', 'restore well', 'clean well'],
    'water-testing': ['water test', 'water quality test', 'testing', 'lab test'],
    'well-service': ['well service', 'well maintenance', 'annual service'],
    'emergency-well-repair': ['emergency', 'no water', 'urgent', '24/7', 'immediate'],
    'booster-pump': ['booster pump', 'pressure boost', 'low pressure'],
    'submersible-pump': ['submersible', 'deep well pump'],
    'jet-pump': ['jet pump', 'shallow well pump'],
}

# Content topic images
TOPIC_IMAGES = {
    'bacteria-contamination': ['bacteria', 'coliform', 'e.coli', 'contamination'],
    'hard-water': ['hard water', 'mineral', 'scale', 'calcium'],
    'drought': ['drought', 'dry', 'water shortage'],
    'arsenic': ['arsenic', 'heavy metal'],
    'iron': ['iron', 'rust', 'orange water', 'red water'],
    'sulfur': ['sulfur', 'rotten egg', 'smell'],
    'nitrate': ['nitrate', 'nitrogen'],
    'sediment': ['sediment', 'sand', 'silt', 'dirty water'],
    'air-in-lines': ['air in line', 'sputter', 'spit'],
    'low-pressure': ['low pressure', 'weak flow', 'pressure drop'],
    'aquifer': ['aquifer', 'groundwater', 'water table'],
    'permits': ['permit', 'regulation', 'county', 'compliance'],
    'diy-maintenance': ['diy', 'homeowner', 'yourself', 'maintenance tip'],
    'seasonal': ['winter', 'summer', 'season', 'freeze', 'frost'],
    'frozen-pipes': ['frozen', 'freeze', 'ice', 'winter'],
    'gpm-flow-rate': ['gpm', 'gallons per minute', 'flow rate'],
    'hand-pump': ['hand pump', 'manual pump'],
}

def get_available_images():
    """Get list of available images."""
    images = {}
    for img in IMAGE_DIR.glob("*.png"):
        base = img.stem.rsplit('-', 1)[0] if img.stem[-1].isdigit() else img.stem
        if base not in images:
            images[base] = []
        images[base].append(img.name)
    return images

def match_image(title, content, available_images):
    """Match a blog post to an appropriate image."""
    text = (title + " " + content).lower()
    
    # Check service images first (higher priority)
    for base, keywords in SERVICE_IMAGES.items():
        for kw in keywords:
            if kw in text:
                if base in available_images:
                    # Rotate through numbered variants
                    variants = sorted(available_images[base])
                    idx = hash(title) % len(variants)
                    return variants[idx]
    
    # Check topic images
    for base, keywords in TOPIC_IMAGES.items():
        for kw in keywords:
            if kw in text:
                if base in available_images:
                    variants = sorted(available_images[base])
                    idx = hash(title) % len(variants)
                    return variants[idx]
    
    # Default to well-service image
    if 'well-service' in available_images:
        variants = sorted(available_images['well-service'])
        idx = hash(title) % len(variants)
        return variants[idx]
    
    return None

def add_image_to_html(filepath, image_name):
    """Add image to blog post HTML after the h1 tag."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has a blog image
    if 'blog-images/' in content or 'class="blog-hero-image"' in content:
        return False
    
    # Extract title for alt text
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
    alt_text = title_match.group(1) if title_match else "Well service illustration"
    
    # Create image HTML
    image_html = f'''
            <figure class="blog-hero-image">
                <img src="/assets/images/blog-images/{image_name}" alt="{alt_text}" loading="lazy" width="800" height="450">
            </figure>
'''
    
    # Insert after </h1> and before <p class="lead">
    pattern = r'(</h1>\s*\n)'
    replacement = r'\1' + image_html
    
    new_content = re.sub(pattern, replacement, content, count=1)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    available_images = get_available_images()
    print(f"Found {sum(len(v) for v in available_images.values())} images in {len(available_images)} categories")
    
    blog_files = list(BLOG_DIR.glob("*.html"))
    print(f"Processing {len(blog_files)} blog posts...")
    
    updated = 0
    skipped = 0
    no_match = 0
    
    for filepath in sorted(blog_files):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get title
        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else filepath.stem
        
        image_name = match_image(title, content[:2000], available_images)
        
        if not image_name:
            no_match += 1
            # Use a default
            image_name = 'well-service-1.png'
        
        if add_image_to_html(filepath, image_name):
            updated += 1
            if updated <= 10 or updated % 100 == 0:
                print(f"  ✓ {filepath.name} → {image_name}")
        else:
            skipped += 1
    
    print(f"\n=== Complete ===")
    print(f"Updated: {updated}")
    print(f"Skipped (already has image): {skipped}")
    print(f"No match (used default): {no_match}")

if __name__ == '__main__':
    main()
