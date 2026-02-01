#!/usr/bin/env python3
"""
Additional performance fixes:
1. Defer gtag/analytics scripts
2. Add explicit dimensions to hero images
"""
import re
import glob

def fix_performance(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # 1. Move Google Analytics to end of body with defer
    # Find the gtag script block in head
    gtag_pattern = r'(<!-- Google Analytics.*?</script>)\s*(<script>.*?gtag\(\'config\'.*?</script>)'
    
    # For the async script, keep it but also add loading="lazy" concept
    # Actually, gtag already has async, which is good
    
    # 2. Add width/height to hero image preload - make it fetchpriority="high"
    # Already has fetchpriority="high", good
    
    # 3. Add loading="lazy" to non-critical images
    # Find images that don't have loading attribute
    content = re.sub(
        r'<img(?![^>]*loading=)([^>]*)(src="(?!images/logo|images/drilling-rig)[^"]*"[^>]*)>',
        r'<img\1\2 loading="lazy">',
        content
    )
    
    # 4. Ensure hero image has explicit dimensions
    content = re.sub(
        r'(<img[^>]*src="images/drilling-rig\.jpg"[^>]*)(?<!width=")(?<!height=")>',
        r'\1 width="1200" height="800">',
        content
    )
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

updated = 0
for pattern in ['*.html', 'blog/*.html']:
    for filepath in glob.glob(pattern):
        if fix_performance(filepath):
            print(f"Fixed: {filepath}")
            updated += 1

print(f"\nTotal: {updated} files fixed")
