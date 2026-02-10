#!/usr/bin/env python3
"""Fix broken Unsplash URLs in blog posts"""

from pathlib import Path

BLOG_DIR = Path("/Users/jarvis/clawd/scws-website/blog")

# Image replacements with appropriate Unsplash photo IDs
# These are manually selected for relevance to well/water/plumbing content

fixes = {
    'air-in-well-water-lines.html': [
        {
            'old': 'src="https://images.unsplash.com/?w=1200&h=600&fit=crop"',
            'new': 'src="https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=1200&h=600&fit=crop"',
            'note': 'Hero: Water running from faucet (water droplet/faucet theme)'
        },
        {
            'old': 'src="https://images.unsplash.com/?w=800&h=500&fit=crop"',
            'new': 'src="https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=800&h=500&fit=crop"',
            'note': 'Inline: Industrial pipes/plumbing system'
        },
        {
            'old': 'src="https://images.unsplash.com/?w=400&h=200&fit=crop" alt="Signs of pump failure"',
            'new': 'src="https://images.unsplash.com/photo-1621905252507-b35492cc74b4?w=400&h=200&fit=crop" alt="Signs of pump failure"',
            'note': 'Related: Industrial pump/machinery'
        },
        {
            'old': 'src="https://images.unsplash.com/?w=400&h=200&fit=crop" alt="Pressure tank issues"',
            'new': 'src="https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=400&h=200&fit=crop" alt="Pressure tank issues"',
            'note': 'Related: Pressure tank/pipes'
        },
        {
            'old': 'src="https://images.unsplash.com/?w=400&h=200&fit=crop" alt="Low water pressure"',
            'new': 'src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=200&fit=crop" alt="Low water pressure"',
            'note': 'Related: Water/faucet pressure'
        }
    ],
    'new-construction-well-drilling.html': [
        {
            'old': 'src="https://images.unsplash.com/?w=1200&q=80"',
            'new': 'src="https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=1200&q=80"',
            'note': 'Property site planning: Construction/blueprints'
        }
    ],
    'well-pump-repair-hemet.html': [
        {
            'old': 'src="https://images.unsplash.com/?auto=format&fit=crop&w=1200&q=80"',
            'new': 'src="https://images.unsplash.com/photo-1621905252507-b35492cc74b4?auto=format&fit=crop&w=1200&q=80"',
            'note': 'Well pump control box: Industrial pump equipment'
        }
    ]
}

# Apply fixes
print("Applying image fixes...\n")
fixed_count = 0

for filename, replacements in fixes.items():
    file_path = BLOG_DIR / filename
    
    if not file_path.exists():
        print(f"❌ File not found: {filename}")
        continue
    
    content = file_path.read_text()
    original_content = content
    
    for fix in replacements:
        if fix['old'] in content:
            content = content.replace(fix['old'], fix['new'])
            fixed_count += 1
            print(f"✅ {filename}")
            print(f"   {fix['note']}")
            print(f"   {fix['old'][:60]}...")
            print(f"   → {fix['new'][:60]}...")
            print()
        else:
            print(f"⚠️  Pattern not found in {filename}:")
            print(f"   {fix['old'][:60]}...")
            print()
    
    if content != original_content:
        file_path.write_text(content)
        print(f"💾 Saved {filename}\n")

print(f"\n{'='*80}")
print(f"FIXES APPLIED: {fixed_count} broken URLs fixed across {len(fixes)} files")
print(f"{'='*80}")
