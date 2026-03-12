#!/usr/bin/env python3
"""
Fix all broken image references in SCWS website
Maps broken references to existing images
"""

import os
import re
from pathlib import Path

# Mapping of broken references to existing images
ARTICLE_CATEGORY_MAPPINGS = {
    'buying-property.png': 'cost-guide.png',
    'costs.png': 'cost-guide.png',
    'filtration.png': 'treatment.png',
    'home-buying.png': 'cost-guide.png',
    'inspection.png': 'maintenance.png',
    'pump-repair.png': 'troubleshooting.png',
    'real-estate.png': 'cost-guide.png',
    'repair.png': 'troubleshooting.png',
    'solar-pumps.png': 'equipment.png',
    'storage-tanks.png': 'equipment.png',
    'testing.png': 'water-quality.png',
    'water-treatment.png': 'treatment.png',
}

BLOG_CATEGORY_MAPPINGS = {
    'blog-categories/costs.png': 'article-categories/cost-guide.png',
    'blog-categories/repair.png': 'article-categories/troubleshooting.png',
    'blog-categories/testing.png': 'article-categories/water-quality.png',
}

BLOG_IMAGE_MAPPINGS = {
    'drought-well.png': 'drought.png',
    'emergency-well.png': 'emergency-well-repair-1.png',
    'hydrofracturing.png': 'well-drilling-1.png',
    'insurance-coverage.png': 'well-service-1.png',
    'irrigation-well.png': 'well-service-2.png',
    'livestock-well.png': 'well-service-3.png',
    'pool-well-water.png': 'water-test.png',
    'selling-home-well.png': 'well-inspection.png',
    'shared-well.png': 'well-service-4.png',
    'solar-well-pump.png': 'solar-pump.png',
    'water-quality-1.png': 'sulfur-water.png',
    'water-storage-tank.png': 'pressure-tank-1.png',
    'well-abandonment.png': 'well-casing.png',
    'well-log.png': 'well-inspection.png',
    'well-mortgage.png': 'well-service-5.png',
    'well-property-value.png': 'well-service-1.png',
    'well-water-safety.png': 'water-test.png',
}

HERO_IMAGE_MAPPINGS = {
    'hero-mountains.jpg': 'hero-mountain-landscape.jpg',
    'hero-ranch.jpg': 'hero-rural.jpg',
    'hero-rancho-penasquitos-hills.jpg': 'hero-poway-hills.jpg',
    'rancho-penasquitos-estate-property.jpg': 'hero-poway-hills.jpg',
}

def fix_image_references(base_dir):
    """Find and fix all broken image references in HTML files"""
    fixed_count = 0
    files_modified = set()
    
    # Find all HTML files
    html_files = list(Path(base_dir).rglob('*.html'))
    print(f"Found {len(html_files)} HTML files to process")
    
    for html_file in html_files:
        # Skip node_modules
        if 'node_modules' in str(html_file):
            continue
            
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix article category images
            for broken, fixed in ARTICLE_CATEGORY_MAPPINGS.items():
                # Match various path patterns
                patterns = [
                    f'article-categories/{broken}',
                    f'/article-categories/{broken}',
                    f'assets/images/article-categories/{broken}',
                    f'/assets/images/article-categories/{broken}',
                ]
                for pattern in patterns:
                    if pattern in content:
                        replacement = pattern.replace(broken, fixed)
                        content = content.replace(pattern, replacement)
                        fixed_count += 1
                        files_modified.add(str(html_file))
                        print(f"  Fixed: {pattern} → {replacement}")
            
            # Fix blog category images (redirect to article-categories)
            for broken, fixed in BLOG_CATEGORY_MAPPINGS.items():
                patterns = [
                    f'{broken}',
                    f'/{broken}',
                    f'assets/images/{broken}',
                    f'/assets/images/{broken}',
                ]
                for pattern in patterns:
                    if pattern in content:
                        # Replace with article-categories path
                        if pattern.startswith('/'):
                            replacement = f'/assets/images/{fixed}'
                        elif pattern.startswith('assets'):
                            replacement = f'assets/images/{fixed}'
                        else:
                            replacement = f'assets/images/{fixed}'
                        content = content.replace(pattern, replacement)
                        fixed_count += 1
                        files_modified.add(str(html_file))
                        print(f"  Fixed: {pattern} → {replacement}")
            
            # Fix blog images
            for broken, fixed in BLOG_IMAGE_MAPPINGS.items():
                patterns = [
                    f'blog-images/{broken}',
                    f'/blog-images/{broken}',
                    f'assets/images/blog-images/{broken}',
                    f'/assets/images/blog-images/{broken}',
                ]
                for pattern in patterns:
                    if pattern in content:
                        replacement = pattern.replace(broken, fixed)
                        content = content.replace(pattern, replacement)
                        fixed_count += 1
                        files_modified.add(str(html_file))
                        print(f"  Fixed: {pattern} → {replacement}")
            
            # Fix hero images
            for broken, fixed in HERO_IMAGE_MAPPINGS.items():
                # Hero images are typically in /images/ or images/
                patterns = [
                    f'images/{broken}',
                    f'/images/{broken}',
                ]
                for pattern in patterns:
                    if pattern in content:
                        replacement = pattern.replace(broken, fixed)
                        content = content.replace(pattern, replacement)
                        fixed_count += 1
                        files_modified.add(str(html_file))
                        print(f"  Fixed: {pattern} → {replacement}")
            
            # Write back if changed
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Modified: {html_file}")
                
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    return fixed_count, len(files_modified)

if __name__ == '__main__':
    base_dir = '/Users/jarvis/clawd/scws-website'
    print("Starting image reference fixes...")
    print("=" * 60)
    
    fixed, files = fix_image_references(base_dir)
    
    print("=" * 60)
    print(f"\n✓ Fixed {fixed} broken references in {files} files")
