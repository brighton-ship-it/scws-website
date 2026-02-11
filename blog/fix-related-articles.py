#!/usr/bin/env python3
"""
Fix Related Articles sections across all SCWS blog pages:
1. Remove old bullet-list style Related Articles sections
2. Add nice card-style Related Articles section if missing
"""

import os
import re
import glob

# The nice card-style Related Articles section
NICE_RELATED_ARTICLES = '''
    <!-- Related Articles -->
    <section class="py-16 bg-gray-50">
        <div class="max-w-4xl mx-auto px-4">
            <div class="text-center mb-10">
                <h2 class="text-3xl font-bold text-primary mb-2">Related Articles</h2>
                <p class="text-gray-600">Continue learning about well maintenance and troubleshooting</p>
            </div>
            <div class="grid md:grid-cols-3 gap-6">
                <a href="signs-well-pump-failing.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                    <div class="h-40 overflow-hidden">
                        <img src="https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=200&fit=crop" alt="Well pump warning signs" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                    </div>
                    <div class="p-5">
                        <span class="text-xs font-semibold text-accent uppercase tracking-wide">Troubleshooting</span>
                        <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Signs Your Well Pump Is Failing</h3>
                        <p class="text-gray-600 text-sm">Catch pump problems early before you lose water completely.</p>
                    </div>
                </a>
                <a href="low-water-pressure-well.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                    <div class="h-40 overflow-hidden">
                        <img src="https://images.unsplash.com/photo-1562016600-ece13e8ba570?w=400&h=200&fit=crop" alt="Low water pressure from faucet" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                    </div>
                    <div class="p-5">
                        <span class="text-xs font-semibold text-accent uppercase tracking-wide">Pressure Issues</span>
                        <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Low Water Pressure From Well</h3>
                        <p class="text-gray-600 text-sm">Diagnose and fix pressure problems before they get worse.</p>
                    </div>
                </a>
                <a href="water-well-maintenance-guide.html" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                    <div class="h-40 overflow-hidden">
                        <img src="https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=400&h=200&fit=crop" alt="Well maintenance and care" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                    </div>
                    <div class="p-5">
                        <span class="text-xs font-semibold text-accent uppercase tracking-wide">Maintenance</span>
                        <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">Well Maintenance Guide</h3>
                        <p class="text-gray-600 text-sm">Keep your well running smoothly with regular maintenance.</p>
                    </div>
                </a>
            </div>
        </div>
    </section>
'''

def fix_related_articles(filepath):
    """Fix Related Articles section in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # 1. Remove old-style <section class="related-articles"...>...</section>
    # Pattern handles inline styles and multi-line content
    pattern1 = re.compile(
        r'<section\s+class="related-articles"[^>]*>.*?</section>',
        re.DOTALL | re.IGNORECASE
    )
    if pattern1.search(content):
        content = pattern1.sub('', content)
        changes_made.append('removed section.related-articles')
    
    # 2. Remove old-style <div class="related-articles">...</div>
    pattern2 = re.compile(
        r'<div\s+class="related-articles"[^>]*>.*?</div>\s*(?=\n)',
        re.DOTALL | re.IGNORECASE
    )
    if pattern2.search(content):
        content = pattern2.sub('', content)
        changes_made.append('removed div.related-articles')
    
    # 3. Check if nice card-style already exists
    has_nice_cards = 'py-16 bg-gray-50' in content
    
    # 4. If no nice card section, add it
    if not has_nice_cards:
        # Try different insertion points (in order of preference)
        
        # Option A: Before <!-- Footer -->
        if '<!-- Footer -->' in content:
            content = content.replace('<!-- Footer -->', NICE_RELATED_ARTICLES + '\n    <!-- Footer -->')
            changes_made.append('added card-style before footer comment')
        
        # Option B: Before <footer
        elif '<footer' in content:
            content = re.sub(
                r'(\s*)(<footer)',
                r'\1' + NICE_RELATED_ARTICLES + r'\n\1\2',
                content,
                count=1
            )
            changes_made.append('added card-style before footer tag')
        
        # Option C: Before <!-- Blog Post CTA -->
        elif '<!-- Blog Post CTA -->' in content:
            content = content.replace('<!-- Blog Post CTA -->', NICE_RELATED_ARTICLES + '\n    <!-- Blog Post CTA -->')
            changes_made.append('added card-style before CTA')
        
        # Option D: Before </main>
        elif '</main>' in content:
            content = content.replace('</main>', NICE_RELATED_ARTICLES + '\n</main>')
            changes_made.append('added card-style before </main>')
        
        # Option E: Before closing style tag (for simpler pages)
        elif '</style>' in content and '</body>' in content:
            content = content.replace('</body>', NICE_RELATED_ARTICLES + '\n</body>')
            changes_made.append('added card-style before </body>')
    
    # Clean up extra blank lines that may have been created
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made
    
    return []

def main():
    blog_dir = '/Users/jarvis/clawd/scws-website/blog'
    html_files = glob.glob(os.path.join(blog_dir, '*.html'))
    
    # Skip non-blog files
    skip_files = ['index.html']
    
    total_modified = 0
    stats = {
        'removed_old': 0,
        'added_new': 0,
        'no_change': 0
    }
    
    for filepath in sorted(html_files):
        filename = os.path.basename(filepath)
        if filename in skip_files:
            continue
        
        changes = fix_related_articles(filepath)
        
        if changes:
            total_modified += 1
            print(f"✓ {filename}: {', '.join(changes)}")
            if any('removed' in c for c in changes):
                stats['removed_old'] += 1
            if any('added' in c for c in changes):
                stats['added_new'] += 1
        else:
            stats['no_change'] += 1
    
    print(f"\n{'='*50}")
    print(f"SUMMARY:")
    print(f"  Files modified: {total_modified}")
    print(f"  Old sections removed: {stats['removed_old']}")
    print(f"  New card sections added: {stats['added_new']}")
    print(f"  Already correct: {stats['no_change']}")

if __name__ == '__main__':
    main()
