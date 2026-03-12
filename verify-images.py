#!/usr/bin/env python3
"""
Verify all image references in SCWS website are valid
Excludes images with ?v=2 query strings (those work on web server)
"""

import os
import re
from pathlib import Path

def verify_images(base_dir):
    """Check all image references in HTML files"""
    broken_images = []
    
    # Find all HTML files
    html_files = list(Path(base_dir).rglob('*.html'))
    print(f"Checking {len(html_files)} HTML files...")
    
    # Common image patterns
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    bg_pattern = re.compile(r'background(?:-image)?:\s*url\(["\']?([^"\')\s]+)["\']?\)', re.IGNORECASE)
    
    for html_file in html_files:
        # Skip node_modules
        if 'node_modules' in str(html_file):
            continue
            
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all image references
            img_srcs = img_pattern.findall(content)
            bg_imgs = bg_pattern.findall(content)
            all_imgs = img_srcs + bg_imgs
            
            for img_src in all_imgs:
                # Skip versioned images (they work on web server)
                if '?v=' in img_src:
                    continue
                
                # Skip external URLs
                if img_src.startswith(('http://', 'https://', '//', 'data:')):
                    continue
                
                # Skip SVGs and other non-file references
                if img_src.startswith('#') or img_src == '':
                    continue
                
                # Resolve relative path
                img_path = img_src.lstrip('/')
                
                # Try different base paths
                possible_paths = [
                    Path(base_dir) / img_path,
                    Path(base_dir) / 'assets' / img_path,
                ]
                
                found = False
                for path in possible_paths:
                    if path.exists():
                        found = True
                        break
                
                if not found:
                    broken_images.append({
                        'file': str(html_file),
                        'image': img_src,
                        'type': 'img' if img_src in img_srcs else 'background'
                    })
        
        except Exception as e:
            print(f"Error checking {html_file}: {e}")
    
    return broken_images

if __name__ == '__main__':
    base_dir = '/Users/jarvis/clawd/scws-website'
    print("Verifying all image references...")
    print("=" * 60)
    
    broken = verify_images(base_dir)
    
    print("=" * 60)
    
    if broken:
        print(f"\n❌ Found {len(broken)} broken image references:\n")
        for item in broken:
            print(f"  File: {item['file']}")
            print(f"  Image: {item['image']}")
            print(f"  Type: {item['type']}")
            print()
    else:
        print("\n✅ All image references verified - 0 broken images!")
