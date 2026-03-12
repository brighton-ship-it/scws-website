#!/usr/bin/env python3
"""
Fix missing width/height attributes on all <img> tags in HTML files.
This improves CLS (Cumulative Layout Shift) for Core Web Vitals.
"""

import os
import re
from pathlib import Path
from PIL import Image
from urllib.parse import urlparse, unquote
import sys

# Directory setup
WEBSITE_ROOT = Path(__file__).parent.resolve()
os.chdir(WEBSITE_ROOT)

# Stats tracking
stats = {
    'html_files_processed': 0,
    'html_files_modified': 0,
    'images_fixed': 0,
    'images_skipped_already_have_dims': 0,
    'local_images_measured': 0,
    'external_images_defaulted': 0,
    'errors': []
}

# Cache for image dimensions
image_dimension_cache = {}

def get_image_dimensions(img_path_relative, html_file_path):
    """
    Get dimensions for an image. Returns (width, height) or None.
    
    Args:
        img_path_relative: The src attribute value from the HTML
        html_file_path: Path to the HTML file (for resolving relative paths)
    """
    # Remove query strings like ?v=2
    img_path_clean = img_path_relative.split('?')[0].split('#')[0]
    
    # Check if external URL
    if img_path_clean.startswith('http://') or img_path_clean.startswith('https://'):
        # External image - use defaults
        # Most Unsplash images are landscape 800x533, but let's be generic
        if 'unsplash.com' in img_path_clean:
            return (800, 533)
        return (800, 600)  # Generic default
    
    # Local image - resolve path
    if img_path_clean in image_dimension_cache:
        return image_dimension_cache[img_path_clean]
    
    # Resolve relative path based on HTML file location
    html_dir = Path(html_file_path).parent
    
    # Handle absolute paths (starting with /)
    if img_path_clean.startswith('/'):
        img_full_path = WEBSITE_ROOT / img_path_clean.lstrip('/')
    else:
        # Relative path
        img_full_path = (html_dir / img_path_clean).resolve()
    
    # Check if file exists
    if not img_full_path.exists():
        # Try without leading ../
        alt_path = WEBSITE_ROOT / img_path_clean.lstrip('./')
        if alt_path.exists():
            img_full_path = alt_path
        else:
            stats['errors'].append(f"Image not found: {img_path_clean} (from {html_file_path})")
            return None
    
    # Try to read dimensions
    try:
        with Image.open(img_full_path) as img:
            width, height = img.size
            image_dimension_cache[img_path_clean] = (width, height)
            stats['local_images_measured'] += 1
            return (width, height)
    except Exception as e:
        stats['errors'].append(f"Error reading {img_full_path}: {e}")
        return None

def fix_img_tag(match, html_file_path):
    """
    Fix a single <img> tag by adding width/height if missing.
    """
    full_tag = match.group(0)
    
    # Check if width AND height already exist
    has_width = re.search(r'\bwidth\s*=', full_tag, re.IGNORECASE)
    has_height = re.search(r'\bheight\s*=', full_tag, re.IGNORECASE)
    
    if has_width and has_height:
        stats['images_skipped_already_have_dims'] += 1
        return full_tag  # Already has both
    
    # Extract src attribute
    src_match = re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']', full_tag, re.IGNORECASE)
    if not src_match:
        return full_tag  # No src, can't determine dimensions
    
    src = src_match.group(1)
    
    # Get dimensions
    dimensions = get_image_dimensions(src, html_file_path)
    if not dimensions:
        return full_tag  # Couldn't determine dimensions
    
    width, height = dimensions
    
    # Build new attributes
    new_attrs = []
    if not has_width:
        new_attrs.append(f'width="{width}"')
    if not has_height:
        new_attrs.append(f'height="{height}"')
    
    # Insert attributes after <img (before other attributes)
    # Find the position right after '<img' and any whitespace
    img_start = re.match(r'<img\s*', full_tag, re.IGNORECASE)
    if img_start:
        insert_pos = img_start.end()
        new_tag = full_tag[:insert_pos] + ' '.join(new_attrs) + ' ' + full_tag[insert_pos:]
        stats['images_fixed'] += 1
        
        # Track if it was external
        if src.startswith('http'):
            stats['external_images_defaulted'] += 1
        
        return new_tag
    
    return full_tag

def process_html_file(html_path):
    """
    Process a single HTML file, fixing all <img> tags missing width/height.
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Find all <img> tags (including self-closing and not)
        # Pattern matches: <img ...> or <img .../>
        img_pattern = re.compile(
            r'<img\b[^>]*>',
            re.IGNORECASE | re.DOTALL
        )
        
        # Replace all img tags
        content = img_pattern.sub(
            lambda m: fix_img_tag(m, html_path),
            content
        )
        
        # Write back if modified
        if content != original_content:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            stats['html_files_modified'] += 1
            return True
        
        return False
        
    except Exception as e:
        stats['errors'].append(f"Error processing {html_path}: {e}")
        return False

def main():
    print("🔍 Scanning for HTML files...")
    
    # Find all HTML files
    html_files = list(WEBSITE_ROOT.rglob('*.html'))
    print(f"Found {len(html_files)} HTML files")
    
    print("\n📐 Building image dimension cache...")
    # Pre-cache common images to speed up processing
    common_image_paths = [
        'images/logo-text-only-3x.png',
        'assets/images/blog-images',
        'assets/images/article-categories'
    ]
    
    print(f"\n🔧 Processing HTML files...")
    for i, html_file in enumerate(html_files, 1):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(html_files)} files processed...")
        
        process_html_file(html_file)
        stats['html_files_processed'] += 1
    
    # Print results
    print("\n" + "="*60)
    print("✅ COMPLETION REPORT")
    print("="*60)
    print(f"HTML files processed: {stats['html_files_processed']}")
    print(f"HTML files modified: {stats['html_files_modified']}")
    print(f"Images fixed (width/height added): {stats['images_fixed']}")
    print(f"Images skipped (already had dims): {stats['images_skipped_already_have_dims']}")
    print(f"Local images measured: {stats['local_images_measured']}")
    print(f"External images (defaults used): {stats['external_images_defaulted']}")
    
    if stats['errors']:
        print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
        # Show first 10 errors
        for error in stats['errors'][:10]:
            print(f"  - {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")
    
    print("\n" + "="*60)
    
    return stats['images_fixed']

if __name__ == '__main__':
    images_fixed = main()
    sys.exit(0)
