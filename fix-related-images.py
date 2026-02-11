#!/usr/bin/env python3
"""Fix Related Articles section to use varied images"""

import re
from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# Different images for each related article position
IMAGES = {
    # First related article - pump/equipment
    1: "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=200&fit=crop",  # water pressure gauge
    # Second related article - water flow
    2: "https://images.unsplash.com/photo-1562016600-ece13e8ba570?w=400&h=200&fit=crop",  # water faucet
    # Third related article - maintenance  
    3: "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=400&h=200&fit=crop",  # water testing
}

# The repeated image URL to find
OLD_IMAGE = "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400&h=200&fit=crop"

updated = 0

for filepath in BLOG_DIR.glob("*.html"):
    if filepath.name == "index.html":
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if OLD_IMAGE not in content:
        continue
    
    # Find all occurrences and replace them with different images
    # Count how many times the old image appears
    count = content.count(OLD_IMAGE)
    
    if count >= 3:
        # Replace first occurrence with image 1
        content = content.replace(OLD_IMAGE, IMAGES[1], 1)
        # Replace second occurrence with image 2
        content = content.replace(OLD_IMAGE, IMAGES[2], 1)
        # Replace third occurrence with image 3
        content = content.replace(OLD_IMAGE, IMAGES[3], 1)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated += 1

print(f"✓ Fixed related article images in {updated} blog posts")
