#!/usr/bin/env python3
import re
import glob

def remove_tailwind_config(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Remove the tailwind.config script block more aggressively
    # Pattern: <script> followed by tailwind.config, ending with </script>
    pattern = r'<script>\s*\n?\s*tailwind\.config\s*=\s*\{[\s\S]*?\}\s*\n?\s*</script>'
    content = re.sub(pattern, '', content)
    
    # Clean up any double newlines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

updated = 0
for pattern in ['*.html', 'blog/*.html']:
    for filepath in glob.glob(pattern):
        if remove_tailwind_config(filepath):
            print(f"Fixed: {filepath}")
            updated += 1

print(f"\nTotal: {updated} files fixed")
