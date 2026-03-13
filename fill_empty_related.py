#!/usr/bin/env python3
"""Fill empty related-articles sections."""

import re
from pathlib import Path
from add_related_articles import classify_page, get_related_articles, generate_card_html

def fill_empty_section(filepath: Path) -> bool:
    """Fill an empty related-articles section. Returns True if modified."""
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Check if has empty related section (various patterns)
        has_related_articles = '<section class="related-articles">' in content
        has_related = '<section class="related">' in content
        # Also check for plain <section> near end of article (before footer/main)
        has_plain_section = bool(re.search(r'</section>\s*<section>\s*</section>\s*</(?:div|main|article)>', content))
        
        if not has_related_articles and not has_related and not has_plain_section:
            return False
        
        # Check if already filled (has h2)
        if 'Related Articles</h2>' in content:
            return False
        
        # Generate the content
        filename = filepath.name
        topic = classify_page(filename)
        articles = get_related_articles(filename, topic)
        
        cards_html = '\n                '.join([
            generate_card_html(href, img, color, label, title, desc)
            for href, img, color, label, title, desc in articles
        ])
        
        related_content = f'''
                <div class="max-w-4xl mx-auto px-4">
                    <div class="text-center mb-10">
                        <h2 id="related-articles" class="text-3xl font-bold text-primary mb-2">Related Articles</h2>
                        <p class="text-gray-600">Continue learning about well maintenance and troubleshooting</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-6">
                        {cards_html}
                    </div>
                </div>
            '''
        
        # Replace empty section with filled one
        # Try all patterns
        pattern1 = r'<section class="related-articles">\s*</section>'
        pattern2 = r'<section class="related">\s*</section>'
        pattern3 = r'(</section>\s*)<section>\s*</section>(\s*</(?:div|main|article)>)'
        
        if re.search(pattern1, content):
            replacement = f'<section class="related-articles py-16 bg-gray-50">{related_content}\n            </section>'
            new_content = re.sub(pattern1, replacement, content)
        elif re.search(pattern2, content):
            replacement = f'<section class="py-16 bg-gray-50">{related_content}\n</section>'
            new_content = re.sub(pattern2, replacement, content)
        elif re.search(pattern3, content):
            # Use capture groups to preserve the closing tag
            replacement = r'\1<section class="py-16 bg-gray-50">' + related_content + '\n</section>' + r'\2'
            new_content = re.sub(pattern3, replacement, content)
        else:
            return False
        
        if new_content != content:
            filepath.write_text(new_content, encoding='utf-8')
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error processing {filepath.name}: {e}")
        return False

def main():
    """Main processing loop."""
    blog_dir = Path('blog')
    
    # Find all HTML files
    all_files = list(blog_dir.glob('*.html'))
    
    print("🔍 Finding files with empty related-articles sections...")
    empty_files = []
    
    for filepath in all_files:
        try:
            content = filepath.read_text(encoding='utf-8')
            has_section = ('<section class="related-articles">' in content or 
                          '<section class="related">' in content or
                          bool(re.search(r'</section>\s*<section>\s*</section>\s*</(?:div|main|article)>', content)))
            if has_section and 'Related Articles</h2>' not in content:
                empty_files.append(filepath)
        except Exception as e:
            print(f"⚠️  Error reading {filepath.name}: {e}")
    
    print(f"📊 Found {len(empty_files)} files with empty sections")
    
    if len(empty_files) == 0:
        print("✅ No empty sections found!")
        return
    
    # Process all files
    modified = 0
    for filepath in empty_files:
        if fill_empty_section(filepath):
            modified += 1
            if modified % 10 == 0:
                print(f"  ✅ Processed {modified}/{len(empty_files)}...")
    
    print(f"\n🎉 Complete! Filled {modified} empty sections.")

if __name__ == '__main__':
    main()
