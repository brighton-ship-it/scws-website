#!/usr/bin/env python3
"""Analyze image relevance and identify potential mismatches"""

import re
from pathlib import Path
from collections import defaultdict

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# Categories of content to check
WATER_TOPICS = ['water', 'well', 'pump', 'pressure', 'tank', 'drilling', 'irrigation', 'faucet', 'plumbing', 'pipe']
QUALITY_TOPICS = ['bacteria', 'arsenic', 'contamina', 'test', 'filter', 'treatment', 'hard', 'soft', 'iron', 'sulfur']
EQUIPMENT_TOPICS = ['pump', 'motor', 'tank', 'generator', 'booster', 'submersible', 'jet']
AGRICULTURAL = ['farm', 'livestock', 'cattle', 'horse', 'agricult', 'crop', 'irrigation']

# Commonly overused generic Unsplash images
GENERIC_PHOTOS = [
    'photo-1464822759023-fed622ff2c3b',  # Mountain landscape
    'photo-1506905925346-21bda4d32df4',  # Mountain lake
    'photo-1441974231531-c6227db76b6e',  # Forest road
    'photo-1470071459604-3b5ec3a7fe05',  # Nature/forest
]

# Track analysis
issues = []
suggestions = []
posts_analyzed = 0
posts_with_images = 0

html_files = sorted(BLOG_DIR.glob("*.html"))

for html_file in html_files:
    try:
        content = html_file.read_text()
        
        # Extract title
        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else html_file.stem
        
        # Extract h1
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        h1 = h1_match.group(1) if h1_match else ''
        
        # Find images
        img_pattern = r'src="([^"]*(?:unsplash|images/blog)[^"]*)"[^>]*alt="([^"]*)"'
        images = re.findall(img_pattern, content)
        
        if not images:
            continue
        
        posts_with_images += 1
        posts_analyzed += 1
        
        # Check for generic photos
        for img_src, alt_text in images:
            for generic_id in GENERIC_PHOTOS:
                if generic_id in img_src:
                    issues.append({
                        'file': html_file.name,
                        'title': title,
                        'type': 'GENERIC_STOCK',
                        'image': img_src,
                        'alt': alt_text,
                        'note': 'Generic landscape/nature photo - not relevant to wells/water'
                    })
        
        # Check for beach/ocean photos on technical articles
        if any(keyword in title.lower() for keyword in ['pump', 'repair', 'tank', 'drilling']):
            for img_src, alt_text in images:
                if any(term in img_src.lower() or term in alt_text.lower() 
                       for term in ['beach', 'ocean', 'sea', 'coast', 'sunset', 'sunrise']):
                    issues.append({
                        'file': html_file.name,
                        'title': title,
                        'type': 'MISMATCH',
                        'image': img_src,
                        'alt': alt_text,
                        'note': 'Beach/ocean imagery on technical equipment article'
                    })
        
    except Exception as e:
        print(f"Error analyzing {html_file.name}: {e}")

# Print analysis
print("=" * 80)
print("IMAGE RELEVANCE ANALYSIS")
print("=" * 80)
print(f"\nPosts analyzed: {posts_analyzed}")
print(f"Posts with images: {posts_with_images}")
print(f"Issues found: {len(issues)}\n")

if issues:
    print("POTENTIAL IMAGE ISSUES")
    print("-" * 80)
    for issue in issues:
        print(f"\n📁 {issue['file']}")
        print(f"   Title: {issue['title'][:70]}")
        print(f"   Issue: {issue['type']}")
        print(f"   Alt: {issue['alt'][:70]}")
        print(f"   Note: {issue['note']}")
        if len(issue['image']) < 80:
            print(f"   URL: {issue['image']}")

# Save results
with open(BLOG_DIR / "image-relevance-check.txt", "w") as f:
    f.write(f"Image Relevance Analysis\n")
    f.write(f"Posts analyzed: {posts_analyzed}\n")
    f.write(f"Issues found: {len(issues)}\n\n")
    
    for issue in issues:
        f.write(f"\nFile: {issue['file']}\n")
        f.write(f"Type: {issue['type']}\n")
        f.write(f"Alt: {issue['alt']}\n")
        f.write(f"Note: {issue['note']}\n")

print(f"\n✅ Results saved to image-relevance-check.txt")
