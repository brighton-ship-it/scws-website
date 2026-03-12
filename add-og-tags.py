#!/usr/bin/env python3
"""
Add og:image, og:title, and og:description meta tags to HTML files missing them.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import json

SITE_URL = "https://www.scwellservice.com"
LOGO_FALLBACK = f"{SITE_URL}/images/logo-text-only-3x.png"

def find_all_html_files(root_dir):
    """Find all HTML files in the directory."""
    html_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    return html_files

def extract_first_image(soup):
    """Extract the first meaningful image from the page."""
    # Look for hero images first
    hero_selectors = [
        'img.hero-image',
        'img[class*="hero"]',
        '.hero img',
        'article img',
        '.content img',
        'main img'
    ]
    
    for selector in hero_selectors:
        imgs = soup.select(selector)
        if imgs:
            src = imgs[0].get('src', '')
            if src and not src.startswith('data:'):
                return src
    
    # Fallback to first img tag
    imgs = soup.find_all('img')
    for img in imgs:
        src = img.get('src', '')
        # Skip data URIs, icons, logos in nav
        if src and not src.startswith('data:') and 'icon' not in src.lower():
            # Skip navigation/header logos
            parent_classes = []
            for parent in img.parents:
                if parent.get('class'):
                    parent_classes.extend(parent.get('class'))
            
            if not any(x in parent_classes for x in ['nav', 'header', 'footer']):
                return src
    
    return None

def make_absolute_url(url, file_path, root_dir):
    """Convert relative URL to absolute URL."""
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    # Calculate relative depth
    rel_path = os.path.relpath(file_path, root_dir)
    depth = len(Path(rel_path).parts) - 1
    
    # Remove leading ../ or ./
    url = url.lstrip('./')
    
    # Remove any ../ prefixes from the URL
    while url.startswith('../'):
        url = url[3:]
        depth -= 1
    
    # Build absolute URL
    return f"{SITE_URL}/{url}"

def has_og_tag(soup, property_name):
    """Check if a specific og: tag exists."""
    return soup.find('meta', property=property_name) is not None

def process_html_file(file_path, root_dir):
    """Process a single HTML file and add missing og: tags."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        head = soup.find('head')
        
        if not head:
            return False, "No <head> found"
        
        # Check what's missing
        needs_og_image = not has_og_tag(soup, 'og:image')
        needs_og_title = not has_og_tag(soup, 'og:title')
        needs_og_desc = not has_og_tag(soup, 'og:description')
        
        if not (needs_og_image or needs_og_title or needs_og_desc):
            return False, "Already has all og: tags"
        
        changes = []
        
        # Add og:image if missing
        if needs_og_image:
            # Find appropriate image
            page_image = extract_first_image(soup)
            
            if page_image:
                og_image_url = make_absolute_url(page_image, file_path, root_dir)
            else:
                og_image_url = LOGO_FALLBACK
            
            # Create og:image tag
            og_image = soup.new_tag('meta', property='og:image', content=og_image_url)
            og_width = soup.new_tag('meta', property='og:image:width', content='1200')
            og_height = soup.new_tag('meta', property='og:image:height', content='630')
            
            # Find insertion point (after other meta tags or at start of head)
            last_meta = head.find_all('meta')
            if last_meta:
                last_meta[-1].insert_after(og_height)
                last_meta[-1].insert_after(og_width)
                last_meta[-1].insert_after(og_image)
            else:
                head.insert(0, og_height)
                head.insert(0, og_width)
                head.insert(0, og_image)
            
            changes.append(f"og:image → {og_image_url}")
        
        # Add og:title if missing
        if needs_og_title:
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                og_title = soup.new_tag('meta', property='og:title', content=title_tag.string.strip())
                last_meta = head.find_all('meta')
                if last_meta:
                    last_meta[-1].insert_after(og_title)
                else:
                    head.insert(0, og_title)
                changes.append("og:title")
        
        # Add og:description if missing
        if needs_og_desc:
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag and desc_tag.get('content'):
                og_desc = soup.new_tag('meta', property='og:description', content=desc_tag['content'])
                last_meta = head.find_all('meta')
                if last_meta:
                    last_meta[-1].insert_after(og_desc)
                else:
                    head.insert(0, og_desc)
                changes.append("og:description")
        
        if not changes:
            return False, "No changes needed"
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        return True, ", ".join(changes)
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    root_dir = '/Users/jarvis/clawd/scws-website'
    
    print("🔍 Finding all HTML files...")
    html_files = find_all_html_files(root_dir)
    print(f"Found {len(html_files)} HTML files")
    
    print("\n🏷️  Processing files...")
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    updated_files = []
    
    for i, file_path in enumerate(html_files, 1):
        if i % 100 == 0:
            print(f"Progress: {i}/{len(html_files)} ({updated_count} updated)")
        
        rel_path = os.path.relpath(file_path, root_dir)
        updated, reason = process_html_file(file_path, root_dir)
        
        if updated:
            updated_count += 1
            updated_files.append(rel_path)
            if updated_count <= 10:  # Show first 10
                print(f"✅ {rel_path}: {reason}")
        elif "Error" in reason:
            error_count += 1
            if error_count <= 5:  # Show first 5 errors
                print(f"❌ {rel_path}: {reason}")
        else:
            skipped_count += 1
    
    print(f"\n" + "="*60)
    print(f"✅ Updated: {updated_count} files")
    print(f"⏭️  Skipped: {skipped_count} files (already have og: tags)")
    print(f"❌ Errors: {error_count} files")
    print(f"📊 Total: {len(html_files)} files")
    print("="*60)
    
    # Save report
    report = {
        'total_files': len(html_files),
        'updated': updated_count,
        'skipped': skipped_count,
        'errors': error_count,
        'updated_files': updated_files
    }
    
    with open('og-tags-report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to og-tags-report.json")
    
    return updated_count

if __name__ == '__main__':
    updated = main()
    print(f"\n🎉 Complete! {updated} pages updated with og:image tags.")
