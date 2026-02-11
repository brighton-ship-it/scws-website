#!/usr/bin/env python3
"""Add internal links from top-performing pages to unindexed pages."""

import os
import re

# Pages to link TO (currently not indexed)
TARGET_PAGES = {
    'jamul': {
        'url': 'well-service-jamul.html',
        'anchor': 'Jamul well service',
        'context_keywords': ['San Diego', 'service area', 'South County', 'backcountry', 'emergency']
    },
    'lakeside': {
        'url': 'well-service-lakeside.html', 
        'anchor': 'Lakeside well service',
        'context_keywords': ['San Diego', 'East County', 'service area', 'emergency']
    },
    'signs_pump': {
        'url': 'signs-you-need-new-well-pump.html',
        'anchor': 'signs you need a new well pump',
        'context_keywords': ['failing', 'replacement', 'old pump', 'worn', 'lifespan']
    }
}

# Top-performing pages to add links FROM
SOURCE_PAGES = [
    'well-pump-noise-problems.html',
    'well-pump-keeps-tripping-breaker.html',
    'well-pump-short-cycling.html',
    'well-pump-sizing-guide.html',
    'loud-noise-from-well-pump.html',
]

BLOG_DIR = '/Users/jarvis/clawd/scws-website/blog'

def add_service_area_link(html_content, filename):
    """Add Jamul/Lakeside links in the footer service area mention."""
    
    # Check if link already exists
    if 'well-service-jamul.html' in html_content and 'well-service-lakeside.html' in html_content:
        print(f"  {filename}: Links already exist, skipping")
        return html_content
    
    # Replace plain "Jamul" with linked version in footer service areas
    if 'well-service-jamul.html' not in html_content:
        html_content = re.sub(
            r'(Service Areas</h3>\s*<p class="text-gray-300">.*?)Jamul([^<]*</p>)',
            r'\1<a href="well-service-jamul.html" class="hover:text-accent">Jamul</a>\2',
            html_content,
            flags=re.DOTALL
        )
    
    return html_content

def add_pump_replacement_link(html_content, filename):
    """Add link to signs-you-need-new-well-pump.html where contextually appropriate."""
    
    target_url = 'signs-you-need-new-well-pump.html'
    
    # Skip if link already exists
    if target_url in html_content:
        print(f"  {filename}: Pump replacement link already exists")
        return html_content
    
    # Look for mentions of pump failure/replacement without existing link
    patterns = [
        # Pattern 1: "pump is nearing the end of its life" without link
        (
            r'(pump is nearing the end of its life)',
            r'\1—review <a href="signs-you-need-new-well-pump.html" class="text-accent hover:underline">signs you need a new pump</a>'
        ),
        # Pattern 2: "replacement" mention
        (
            r'(whether repair or replacement makes sense)',
            r'\1. See our guide on <a href="signs-you-need-new-well-pump.html" class="text-accent hover:underline">when to replace your well pump</a>'
        ),
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, html_content) and target_url not in html_content:
            html_content = re.sub(pattern, replacement, html_content, count=1)
            print(f"  {filename}: Added pump replacement link")
            break
    
    return html_content

def process_file(filepath):
    """Process a single HTML file to add internal links."""
    filename = os.path.basename(filepath)
    print(f"Processing: {filename}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Add various internal links
    content = add_service_area_link(content, filename)
    content = add_pump_replacement_link(content, filename)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated {filename}")
        return True
    else:
        print(f"  - No changes needed for {filename}")
        return False

def main():
    updated = 0
    for page in SOURCE_PAGES:
        filepath = os.path.join(BLOG_DIR, page)
        if os.path.exists(filepath):
            if process_file(filepath):
                updated += 1
        else:
            print(f"  ⚠ File not found: {page}")
    
    print(f"\nUpdated {updated} files")

if __name__ == '__main__':
    main()
