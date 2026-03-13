#!/usr/bin/env python3
"""Comprehensive blog page audit for SCWS website."""

import glob, re, os, json
from collections import defaultdict

BLOG_DIR = '/Users/jarvis/clawd/scws-website/blog'
IMAGE_DIR = '/Users/jarvis/clawd/scws-website'

files = sorted(glob.glob(f'{BLOG_DIR}/*.html'))
print(f"Auditing {len(files)} blog pages...\n")

issues = defaultdict(list)
stats = defaultdict(int)

for f in files:
    fname = os.path.basename(f)
    size = os.path.getsize(f)
    
    with open(f) as fh:
        c = fh.read()
    
    page_issues = []
    
    # === CONTENT QUALITY ===
    if size < 5000:
        page_issues.append(('CRITICAL', 'content', f'Extremely thin page ({size} bytes)'))
    elif size < 8000:
        page_issues.append(('HIGH', 'content', f'Thin page ({size} bytes)'))
    
    # === SEO ===
    # Title
    title_match = re.search(r'<title>(.*?)</title>', c, re.DOTALL)
    if not title_match:
        page_issues.append(('CRITICAL', 'seo', 'Missing <title> tag'))
    elif len(title_match.group(1).strip()) < 10:
        page_issues.append(('HIGH', 'seo', f'Title too short: "{title_match.group(1).strip()}"'))
    elif len(title_match.group(1).strip()) > 70:
        page_issues.append(('LOW', 'seo', f'Title too long ({len(title_match.group(1).strip())} chars)'))
    
    # Meta description
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', c, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']', c, re.IGNORECASE)
    if not desc_match:
        page_issues.append(('HIGH', 'seo', 'Missing meta description'))
    elif len(desc_match.group(1).strip()) < 50:
        page_issues.append(('MEDIUM', 'seo', f'Meta description too short ({len(desc_match.group(1).strip())} chars)'))
    elif len(desc_match.group(1).strip()) > 160:
        page_issues.append(('LOW', 'seo', f'Meta description too long ({len(desc_match.group(1).strip())} chars)'))
    
    # H1
    h1_match = re.findall(r'<h1[^>]*>(.*?)</h1>', c, re.DOTALL)
    if not h1_match:
        page_issues.append(('HIGH', 'seo', 'Missing H1 tag'))
    elif len(h1_match) > 1:
        page_issues.append(('MEDIUM', 'seo', f'Multiple H1 tags ({len(h1_match)})'))
    
    # Canonical
    if 'rel="canonical"' not in c and "rel='canonical'" not in c:
        page_issues.append(('MEDIUM', 'seo', 'Missing canonical URL'))
    
    # Schema
    if 'application/ld+json' not in c:
        page_issues.append(('MEDIUM', 'seo', 'Missing schema markup (ld+json)'))
    
    # og:image
    if 'og:image' not in c:
        page_issues.append(('LOW', 'seo', 'Missing og:image'))
    
    # === IMAGES ===
    img_tags = re.findall(r'<img\s+([^>]*)>', c, re.IGNORECASE)
    for img_attr in img_tags:
        # Missing alt
        if 'alt=' not in img_attr:
            page_issues.append(('HIGH', 'images', 'Image missing alt text'))
            break  # Just flag once per page
        # Empty alt (not decorative)
        alt_match = re.search(r'alt=["\'](["\'])', img_attr)
        
        # Check src exists
        src_match = re.search(r'src=["\'](.*?)["\']', img_attr)
        if src_match:
            src = src_match.group(1)
            if not src.startswith('http') and not src.startswith('data:'):
                # Resolve relative path
                if src.startswith('/'):
                    full_path = os.path.join(IMAGE_DIR, src.lstrip('/'))
                elif src.startswith('../'):
                    full_path = os.path.normpath(os.path.join(BLOG_DIR, src))
                else:
                    full_path = os.path.join(BLOG_DIR, src)
                if not os.path.exists(full_path):
                    page_issues.append(('HIGH', 'images', f'Broken image: {src}'))
    
    # === TEMPLATE / LAYOUT ===
    if 'mobile-menu-btn' not in c:
        page_issues.append(('HIGH', 'template', 'Missing mobile hamburger menu'))
    
    if '<header' not in c:
        page_issues.append(('CRITICAL', 'template', 'No header at all'))
    
    if 'styles.css' not in c:
        page_issues.append(('CRITICAL', 'template', 'Missing CSS stylesheet'))
    
    if 'max-w-4xl' not in c and 'max-w-3xl' not in c and 'max-w-5xl' not in c and 'max-w-7xl' not in c:
        page_issues.append(('HIGH', 'template', 'No content container (edge-to-edge text)'))
    
    if 'viewport' not in c:
        page_issues.append(('CRITICAL', 'template', 'Missing viewport meta'))
    
    if 'favicon' not in c and 'rel="icon"' not in c:
        page_issues.append(('MEDIUM', 'template', 'Missing favicon'))
    
    # === INTERNAL LINKS ===
    # Count internal blog links in body (exclude nav/header/footer)
    body_match = re.search(r'</header>(.*?)<footer', c, re.DOTALL)
    if body_match:
        body = body_match.group(1)
        internal_links = re.findall(r'href=["\'][^"\']*\.html["\']', body)
        # Subtract nav links that might be in the body
        if len(internal_links) < 2:
            page_issues.append(('MEDIUM', 'links', f'Few/no internal links in body ({len(internal_links)})'))
    
    # === PHONE NUMBER ===
    if '463-0493' in c or '4630493' in c:
        page_issues.append(('HIGH', 'phone', 'Uses tracking number (760) 463-0493 instead of main'))
    
    if '440-8520' not in c and '4408520' not in c:
        page_issues.append(('MEDIUM', 'phone', 'Main phone number (760) 440-8520 not found'))
    
    # === GA4 ===
    if 'G-5LL1YRWT5T' not in c:
        page_issues.append(('MEDIUM', 'analytics', 'Missing GA4 tracking'))
    
    # Record issues
    for severity, category, desc in page_issues:
        issues[f'{severity}:{category}'].append((fname, desc))
        stats[severity] += 1
    
    if not page_issues:
        stats['CLEAN'] += 1

# === REPORT ===
print("=" * 70)
print("SCWS BLOG AUDIT REPORT")
print("=" * 70)
print(f"\nTotal pages: {len(files)}")
print(f"Clean pages (no issues): {stats['CLEAN']}")
print(f"Pages with issues: {len(files) - stats['CLEAN']}")
print(f"\nIssues by severity:")
print(f"  CRITICAL: {stats['CRITICAL']}")
print(f"  HIGH:     {stats['HIGH']}")
print(f"  MEDIUM:   {stats['MEDIUM']}")
print(f"  LOW:      {stats['LOW']}")

print(f"\n{'=' * 70}")
print("ISSUES BY CATEGORY")
print("=" * 70)

# Group and summarize
categories = defaultdict(lambda: defaultdict(list))
for key, items in issues.items():
    severity, category = key.split(':', 1)
    categories[category][severity].extend(items)

for cat in ['template', 'content', 'seo', 'images', 'links', 'phone', 'analytics']:
    if cat not in categories:
        continue
    print(f"\n--- {cat.upper()} ---")
    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if sev not in categories[cat]:
            continue
        items = categories[cat][sev]
        # Group by description
        desc_groups = defaultdict(list)
        for fname, desc in items:
            desc_groups[desc].append(fname)
        for desc, fnames in desc_groups.items():
            print(f"  [{sev}] {desc}: {len(fnames)} pages")
            if len(fnames) <= 5:
                for fn in fnames:
                    print(f"    - {fn}")

# Save detailed report as JSON
report = {}
for key, items in issues.items():
    report[key] = [(fname, desc) for fname, desc in items]

with open('/Users/jarvis/clawd/scws-website/audit-report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n\nDetailed report saved: audit-report.json")
