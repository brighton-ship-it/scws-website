#!/usr/bin/env python3
"""
Fix systematic issues in city service pages:
1. Fix "services services" duplication in IDs and hrefs
2. Map correct hero images based on service type
3. Update alt text to match service type
"""

import re
import os
from pathlib import Path
from typing import Dict, Tuple

# Service type to image mapping
SERVICE_IMAGE_MAP = {
    'pressure-tank': '/assets/images/blog-images/pressure-tank-1.png',
    'well-pump-repair': '/assets/images/blog-images/submersible-pump.png',
    'well-drilling': '/assets/images/blog-images/well-drilling-1.png',
    'water-treatment': '/assets/images/blog-images/water-softener.png',
    'booster-pump': '/assets/images/blog-images/booster-pump-1.png',
    'well-inspection': '/assets/images/blog-images/well-inspection.png',
    'well-chlorination': '/assets/images/blog-images/bacteria-contamination.png',
    'emergency-well-repair': '/assets/images/blog-images/emergency-well-repair-1.png',
    'rusty-water': '/assets/images/blog-images/iron-bacteria.png',
    'sandy-water': '/assets/images/blog-images/sand-in-water.png',
    'cloudy-water': '/assets/images/blog-images/sediment-filter.png',
    'brown-water': '/assets/images/blog-images/sediment-filter.png',
    'low-water-pressure': '/assets/images/blog-images/low-water-pressure.png',
    'low-flow': '/assets/images/blog-images/low-water-pressure.png',
    'dry-well': '/assets/images/blog-images/drought.png',
    'well-video-inspection': '/assets/images/blog-images/well-inspection.png',
    'agricultural-well': '/assets/images/article-categories/agricultural.png',
    'ranch-well': '/assets/images/article-categories/agricultural.png',
    'avocado': '/assets/images/article-categories/agricultural.png',
    'citrus': '/assets/images/article-categories/agricultural.png',
    'equestrian': '/assets/images/article-categories/agricultural.png',
    'hydrofracturing': '/assets/images/blog-images/well-drilling-1.png',
    'well-rehabilitation': '/assets/images/blog-images/well-casing.png',
    'well-abandonment': '/assets/images/blog-images/well-cap.png',
    'well-decommissioning': '/assets/images/blog-images/well-cap.png',
    'well-permit': '/assets/images/article-categories/drilling.png',
    'pump-wont-start': '/assets/images/blog-images/pump-control-box-1.png',
    'pump-wont-stop': '/assets/images/blog-images/pump-control-box-1.png',
    'constant-pressure': '/assets/images/blog-images/pressure-tank-2.png',
}

# Service type to readable name mapping for alt text
SERVICE_NAME_MAP = {
    'pressure-tank': 'Pressure tank',
    'well-pump-repair': 'Well pump repair',
    'well-drilling': 'Well drilling',
    'water-treatment': 'Water treatment',
    'booster-pump': 'Booster pump',
    'well-inspection': 'Well inspection',
    'well-chlorination': 'Well chlorination',
    'emergency-well-repair': 'Emergency well repair',
    'rusty-water': 'Rusty water treatment',
    'sandy-water': 'Sandy water treatment',
    'cloudy-water': 'Cloudy water treatment',
    'brown-water': 'Brown water treatment',
    'low-water-pressure': 'Low water pressure repair',
    'low-flow': 'Low flow repair',
    'dry-well': 'Dry well service',
    'well-video-inspection': 'Well video inspection',
    'agricultural-well': 'Agricultural well service',
    'ranch-well': 'Ranch well service',
    'avocado': 'Avocado grove well service',
    'citrus': 'Citrus grove well service',
    'equestrian': 'Equestrian well service',
    'hydrofracturing': 'Hydrofracturing',
    'well-rehabilitation': 'Well rehabilitation',
    'well-abandonment': 'Well abandonment',
    'well-decommissioning': 'Well decommissioning',
    'well-permit': 'Well permit assistance',
    'pump-wont-start': 'Pump repair',
    'pump-wont-stop': 'Pump repair',
    'constant-pressure': 'Constant pressure system',
}

def determine_service_type(filename: str) -> str:
    """Determine service type from filename."""
    # Check specific patterns in order (most specific first)
    for service_type in SERVICE_IMAGE_MAP.keys():
        if filename.startswith(service_type + '-'):
            return service_type
    
    # Default to well-service if no match
    return 'well-service'

def get_city_name(filename: str) -> str:
    """Extract city name from filename for alt text."""
    # Remove service type prefix and .html suffix
    service_type = determine_service_type(filename)
    
    if service_type == 'well-service':
        # For well-service files, the pattern is well-service-{city}.html
        city_part = filename.replace('well-service-', '').replace('.html', '')
    else:
        # For other services, the pattern is {service-type}-{city}.html
        city_part = filename.replace(service_type + '-', '').replace('.html', '')
    
    # Remove any remaining "well-" prefix that might be in compound names
    city_part = re.sub(r'^well-', '', city_part)
    
    # Convert hyphens to spaces and title case
    city_name = city_part.replace('-', ' ').title()
    return city_name

def fix_html_file(filepath: Path) -> bool:
    """Fix a single HTML file. Returns True if changes were made."""
    filename = filepath.name
    
    # Skip if it's a well-service file (they're fine)
    if filename.startswith('well-service-'):
        return False
    
    service_type = determine_service_type(filename)
    
    # Get correct image path
    if service_type == 'well-service':
        # Keep well-service images as is
        return False
    
    correct_image = SERVICE_IMAGE_MAP.get(service_type, '/assets/images/blog-images/well-service-1.png')
    service_name = SERVICE_NAME_MAP.get(service_type, 'Well service')
    city_name = get_city_name(filename)
    
    # Read file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    original_content = content
    changes_made = False
    
    # Fix 1: Replace hero image src
    # Find the hero image tag and replace its src
    hero_pattern = r'(<figure class="blog-hero-image">[\s\S]*?<img[^>]*?)src="[^"]*"([^>]*?>)'
    
    def replace_hero_image(match):
        nonlocal changes_made
        before = match.group(1)
        after = match.group(2)
        changes_made = True
        return f'{before}src="{correct_image}"{after}'
    
    content = re.sub(hero_pattern, replace_hero_image, content)
    
    # Fix 2: Update alt text on hero image
    new_alt = f"{service_name} in {city_name}"
    hero_alt_pattern = r'(<figure class="blog-hero-image">[\s\S]*?<img[^>]*?)alt="[^"]*"([^>]*?>)'
    
    def replace_alt_text(match):
        nonlocal changes_made
        before = match.group(1)
        after = match.group(2)
        changes_made = True
        return f'{before}alt="{new_alt}"{after}'
    
    content = re.sub(hero_alt_pattern, replace_alt_text, content)
    
    # Fix 3: Fix "services-services" in IDs
    id_pattern = r'id="([^"]*?)-services-services-'
    if re.search(id_pattern, content):
        content = re.sub(id_pattern, r'id="\1-services-', content)
        changes_made = True
    
    # Fix 4: Fix "services-services" in hrefs
    href_pattern = r'href="#([^"]*?)-services-services-'
    if re.search(href_pattern, content):
        content = re.sub(href_pattern, r'href="#\1-services-', content)
        changes_made = True
    
    # Fix 5: Fix any remaining "services services" text (though body should be fixed)
    text_pattern = r'\bservices\s+services\b'
    if re.search(text_pattern, content, re.IGNORECASE):
        content = re.sub(text_pattern, 'services', content, flags=re.IGNORECASE)
        changes_made = True
    
    # Write back if changes were made
    if changes_made:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    
    return False

def main():
    blog_dir = Path('/Users/jarvis/clawd/scws-website/blog')
    
    if not blog_dir.exists():
        print(f"Error: {blog_dir} does not exist")
        return
    
    html_files = list(blog_dir.glob('*.html'))
    print(f"Found {len(html_files)} HTML files")
    
    files_changed = 0
    
    for filepath in html_files:
        if fix_html_file(filepath):
            files_changed += 1
            if files_changed % 100 == 0:
                print(f"Processed {files_changed} files...")
    
    print(f"\n✅ Complete! Fixed {files_changed} files")

if __name__ == '__main__':
    main()
