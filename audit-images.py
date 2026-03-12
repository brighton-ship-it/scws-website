#!/usr/bin/env python3
"""
SCWS Website Image Audit Script
Audits all HTML files for image-related issues
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from urllib.parse import urlparse
from html.parser import HTMLParser

class ImageAuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.og_image = None
        self.schema_images = []
        self.in_script = False
        self.script_content = ''
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'img':
            self.images.append({
                'tag': 'img',
                'src': attrs_dict.get('src', ''),
                'alt': attrs_dict.get('alt', ''),
                'width': attrs_dict.get('width', ''),
                'height': attrs_dict.get('height', ''),
                'loading': attrs_dict.get('loading', ''),
            })
        
        elif tag == 'meta':
            prop = attrs_dict.get('property', '')
            name = attrs_dict.get('name', '')
            content = attrs_dict.get('content', '')
            
            if prop == 'og:image':
                self.og_image = content
            elif name == 'twitter:image':
                if not self.og_image:
                    self.og_image = content
        
        elif tag == 'script':
            self.in_script = True
            self.script_content = ''
    
    def handle_data(self, data):
        if self.in_script:
            self.script_content += data
    
    def handle_endtag(self, tag):
        if tag == 'script' and self.in_script:
            self.in_script = False
            # Look for schema.org image references
            if 'schema.org' in self.script_content or '"@type"' in self.script_content:
                # Find image URLs in JSON-LD
                image_pattern = r'"image"\s*:\s*"([^"]+)"'
                matches = re.findall(image_pattern, self.script_content)
                self.schema_images.extend(matches)

def audit_website(root_dir):
    """Main audit function"""
    
    root_path = Path(root_dir)
    
    # Find all HTML files
    html_files = list(root_path.rglob('*.html'))
    
    # Statistics
    stats = {
        'total_pages': 0,
        'total_images': 0,
        'pages_with_no_images': [],
        'missing_src': [],
        'empty_src': [],
        'broken_relative_paths': [],
        'external_urls': [],
        'missing_alt': [],
        'missing_dimensions': [],
        'non_optimized_formats': [],
        'pages_missing_og_image': [],
        'schema_image_issues': [],
        'image_usage_count': Counter(),
        'image_format_count': Counter(),
    }
    
    print(f"🔍 Scanning {len(html_files)} HTML files...")
    
    for idx, html_file in enumerate(html_files):
        if idx % 500 == 0:
            print(f"  Progress: {idx}/{len(html_files)} pages...")
        
        stats['total_pages'] += 1
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse HTML
            parser = ImageAuditParser()
            parser.feed(content)
            
            relative_path = str(html_file.relative_to(root_path))
            
            # Check for pages with no images
            if not parser.images:
                stats['pages_with_no_images'].append(relative_path)
            
            # Check for missing og:image
            if not parser.og_image:
                stats['pages_missing_og_image'].append(relative_path)
            elif parser.og_image:
                # Check if og:image exists
                if parser.og_image.startswith('/'):
                    og_path = root_path / parser.og_image.lstrip('/')
                    if not og_path.exists():
                        stats['schema_image_issues'].append({
                            'file': relative_path,
                            'issue': 'broken_og_image',
                            'image': parser.og_image
                        })
            
            # Process each image
            for img in parser.images:
                stats['total_images'] += 1
                src = img['src'].strip()
                
                # Missing or empty src
                if not src:
                    stats['empty_src'].append({
                        'file': relative_path,
                        'alt': img.get('alt', '')
                    })
                    continue
                
                # Count image usage
                stats['image_usage_count'][src] += 1
                
                # Check format
                ext = Path(src).suffix.lower()
                if ext:
                    stats['image_format_count'][ext] += 1
                
                # Non-optimized formats
                if ext in ['.bmp', '.tiff', '.tif']:
                    stats['non_optimized_formats'].append({
                        'file': relative_path,
                        'image': src,
                        'format': ext
                    })
                
                # External URLs
                if src.startswith('http://') or src.startswith('https://'):
                    parsed = urlparse(src)
                    if 'scwellservice.com' not in parsed.netloc:
                        stats['external_urls'].append({
                            'file': relative_path,
                            'url': src
                        })
                else:
                    # Check if relative path exists
                    if src.startswith('/'):
                        img_path = root_path / src.lstrip('/')
                    else:
                        img_path = html_file.parent / src
                    
                    # Normalize path
                    try:
                        img_path = img_path.resolve()
                        if not img_path.exists():
                            stats['broken_relative_paths'].append({
                                'file': relative_path,
                                'image': src
                            })
                    except:
                        stats['broken_relative_paths'].append({
                            'file': relative_path,
                            'image': src
                        })
                
                # Missing alt text
                if not img.get('alt'):
                    stats['missing_alt'].append({
                        'file': relative_path,
                        'image': src
                    })
                
                # Missing dimensions (width/height)
                if not img.get('width') or not img.get('height'):
                    stats['missing_dimensions'].append({
                        'file': relative_path,
                        'image': src
                    })
        
        except Exception as e:
            print(f"  ⚠️  Error processing {relative_path}: {e}")
    
    print(f"✅ Scan complete: {stats['total_pages']} pages, {stats['total_images']} images")
    
    return stats

def generate_report(stats, output_file):
    """Generate markdown report"""
    
    report = []
    report.append("# SCWS Website Image Audit Report")
    report.append(f"**Date:** 2026-03-12")
    report.append("")
    
    # Summary
    report.append("## 📊 Summary")
    report.append("")
    report.append(f"- **Total Pages Scanned:** {stats['total_pages']:,}")
    report.append(f"- **Total Images Found:** {stats['total_images']:,}")
    report.append(f"- **Pages with No Images:** {len(stats['pages_with_no_images']):,}")
    report.append(f"- **Pages Missing og:image:** {len(stats['pages_missing_og_image']):,}")
    report.append("")
    
    # Critical Issues
    report.append("## 🚨 Critical Issues")
    report.append("")
    
    report.append(f"### Broken/Missing Images")
    report.append(f"- **Empty src attributes:** {len(stats['empty_src'])}")
    report.append(f"- **Broken relative paths:** {len(stats['broken_relative_paths'])}")
    report.append("")
    
    if stats['empty_src']:
        report.append("#### Empty src attributes:")
        for item in stats['empty_src'][:20]:  # Limit to first 20
            report.append(f"- `{item['file']}`")
        if len(stats['empty_src']) > 20:
            report.append(f"- ... and {len(stats['empty_src']) - 20} more")
        report.append("")
    
    if stats['broken_relative_paths']:
        report.append("#### Broken relative paths:")
        for item in stats['broken_relative_paths'][:20]:
            report.append(f"- `{item['file']}` → `{item['image']}`")
        if len(stats['broken_relative_paths']) > 20:
            report.append(f"- ... and {len(stats['broken_relative_paths']) - 20} more")
        report.append("")
    
    # SEO Issues
    report.append("## 🔍 SEO & Accessibility Issues")
    report.append("")
    
    report.append(f"### Missing Alt Text")
    report.append(f"- **Total:** {len(stats['missing_alt']):,} images")
    report.append(f"- **Impact:** Hurts SEO and accessibility")
    report.append("")
    
    report.append(f"### Missing og:image Tags")
    report.append(f"- **Total:** {len(stats['pages_missing_og_image']):,} pages")
    report.append(f"- **Impact:** Poor social sharing CTR")
    report.append("")
    
    if stats['pages_missing_og_image'][:10]:
        report.append("#### Sample pages missing og:image:")
        for page in stats['pages_missing_og_image'][:10]:
            report.append(f"- `{page}`")
        if len(stats['pages_missing_og_image']) > 10:
            report.append(f"- ... and {len(stats['pages_missing_og_image']) - 10} more")
        report.append("")
    
    # Performance Issues
    report.append("## ⚡ Performance Issues (Core Web Vitals)")
    report.append("")
    
    report.append(f"### Missing Width/Height Attributes")
    report.append(f"- **Total:** {len(stats['missing_dimensions']):,} images")
    report.append(f"- **Impact:** Causes Cumulative Layout Shift (CLS), hurts Core Web Vitals")
    report.append("")
    
    report.append(f"### Non-Optimized Image Formats")
    report.append(f"- **Total:** {len(stats['non_optimized_formats'])}")
    if stats['non_optimized_formats']:
        report.append("#### Files:")
        for item in stats['non_optimized_formats'][:10]:
            report.append(f"- `{item['file']}` → `{item['image']}` ({item['format']})")
        report.append("")
    
    # External Images
    report.append("## 🌐 External Images")
    report.append(f"- **Total:** {len(stats['external_urls'])}")
    report.append(f"- **Impact:** Slower load times, dependency on external services")
    report.append("")
    
    if stats['external_urls']:
        report.append("#### Sample external images:")
        unique_domains = {}
        for item in stats['external_urls']:
            domain = urlparse(item['url']).netloc
            if domain not in unique_domains:
                unique_domains[domain] = 0
            unique_domains[domain] += 1
        
        for domain, count in sorted(unique_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"- `{domain}` ({count} images)")
        report.append("")
    
    # Most Used Images
    report.append("## 🖼️ Most Commonly Used Images")
    report.append(f"*Detecting placeholder/stock image overuse*")
    report.append("")
    
    most_common = stats['image_usage_count'].most_common(20)
    for src, count in most_common:
        if count > 5:  # Only show images used more than 5 times
            report.append(f"- `{src}` — used **{count:,} times**")
    report.append("")
    
    # Image Format Distribution
    report.append("## 📈 Image Format Distribution")
    report.append("")
    for ext, count in stats['image_format_count'].most_common():
        report.append(f"- `{ext or '(no extension)'}` — {count:,} images")
    report.append("")
    
    # Pages with No Images
    report.append("## 📄 Pages with No Images")
    report.append(f"- **Total:** {len(stats['pages_with_no_images']):,}")
    report.append(f"- **Impact:** Missed engagement opportunity")
    report.append("")
    
    if stats['pages_with_no_images']:
        report.append("#### Sample pages:")
        for page in stats['pages_with_no_images'][:15]:
            report.append(f"- `{page}`")
        if len(stats['pages_with_no_images']) > 15:
            report.append(f"- ... and {len(stats['pages_with_no_images']) - 15} more")
        report.append("")
    
    # Recommendations
    report.append("## ✅ Recommendations")
    report.append("")
    
    report.append("### 🚨 High Priority")
    report.append("")
    
    if stats['broken_relative_paths']:
        report.append(f"1. **Fix {len(stats['broken_relative_paths'])} broken image paths** — These images won't load")
    
    if len(stats['missing_alt']) > 100:
        report.append(f"2. **Add alt text to {len(stats['missing_alt']):,} images** — Critical for SEO and accessibility")
    
    if len(stats['pages_missing_og_image']) > 100:
        report.append(f"3. **Add og:image tags to {len(stats['pages_missing_og_image']):,} pages** — Improves social sharing CTR")
    
    report.append("")
    report.append("### ⚡ Performance")
    report.append("")
    
    if len(stats['missing_dimensions']) > 100:
        report.append(f"4. **Add width/height to {len(stats['missing_dimensions']):,} images** — Prevents layout shift (CLS)")
    
    if stats['non_optimized_formats']:
        report.append(f"5. **Convert {len(stats['non_optimized_formats'])} images to WebP/JPEG** — Reduce file sizes")
    
    if stats['external_urls']:
        report.append(f"6. **Consider hosting {len(stats['external_urls'])} external images locally** — Better performance & control")
    
    report.append("")
    report.append("### 📸 Content")
    report.append("")
    
    if len(stats['pages_with_no_images']) > 10:
        report.append(f"7. **Add images to {len(stats['pages_with_no_images']):,} pages** — Visual content improves engagement")
    
    # Check for overused stock images
    overused = [src for src, count in stats['image_usage_count'].most_common(10) if count > 50]
    if overused:
        report.append(f"8. **Replace overused stock images** — {len(overused)} images appear on 50+ pages")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("*Generated by SCWS Image Audit Script*")
    
    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"\n✅ Report saved to: {output_file}")

if __name__ == '__main__':
    root_dir = '/Users/jarvis/clawd/scws-website'
    output_file = '/Users/jarvis/clawd/scws-website/IMAGE-AUDIT-2026-03-12.md'
    
    print("🚀 Starting SCWS Website Image Audit...")
    print("")
    
    stats = audit_website(root_dir)
    generate_report(stats, output_file)
    
    print("")
    print("📊 Quick Stats:")
    print(f"  • {stats['total_pages']:,} pages scanned")
    print(f"  • {stats['total_images']:,} images found")
    print(f"  • {len(stats['broken_relative_paths'])} broken paths")
    print(f"  • {len(stats['missing_alt']):,} missing alt text")
    print(f"  • {len(stats['missing_dimensions']):,} missing dimensions")
    print(f"  • {len(stats['pages_missing_og_image']):,} pages missing og:image")
    print("")
