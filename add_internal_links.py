#!/usr/bin/env python3
"""
Add internal links to blog pages with few or no internal links.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple

# Topic keyword mappings
TOPIC_CATEGORIES = {
    'pump_repair': {
        'keywords': ['pump', 'repair', 'troubleshoot', 'fix', 'replacement', 'labor', 'breaker', 'trip', 'air lock', 'stuck', 'retrieval', 'lifespan', 'expectancy'],
        'articles': [
            ('well-pump-lifespan-expectancy.html', 'Well Pump Lifespan & Replacement Timeline'),
            ('well-pump-replacement-labor-cost.html', 'Well Pump Replacement Labor Costs'),
            ('breaker-trips-when-pump-starts.html', 'Why Your Breaker Trips When Pump Starts'),
            ('air-lock-well-pump-fix.html', 'How to Fix an Air Lock in Well Pump'),
            ('pump-stuck-in-well-retrieval.html', 'Stuck Pump Retrieval Guide'),
        ]
    },
    'pressure_tank': {
        'keywords': ['pressure', 'tank', 'sizing', 'bladder', 'waterlogged', 'low pressure', 'vfd', 'controller', 'constant pressure'],
        'articles': [
            ('pressure-tank-sizing-guide.html', 'Pressure Tank Sizing Guide'),
            ('pressure-tank-lifespan-replacement.html', 'Pressure Tank Lifespan & Replacement'),
            ('low-water-pressure-well.html', 'Low Water Pressure Troubleshooting'),
            ('vfd-vs-standard-pump-controller.html', 'VFD vs Standard Pump Controller'),
        ]
    },
    'water_quality': {
        'keywords': ['water quality', 'hardness', 'tds', 'dissolved solids', 'coliform', 'bacteria', 'lead', 'testing', 'iron bacteria', 'contamination'],
        'articles': [
            ('hardness-testing-well-water.html', 'How to Test Water Hardness'),
            ('tds-total-dissolved-solids-well.html', 'TDS: Total Dissolved Solids Explained'),
            ('coliform-bacteria-test-well-water.html', 'Coliform Bacteria Testing Guide'),
            ('lead-testing-well-water-california.html', 'Lead Testing for Well Water in California'),
            ('iron-bacteria-in-well.html', 'Iron Bacteria in Well Water'),
        ]
    },
    'water_treatment': {
        'keywords': ['stain', 'discolor', 'blue', 'green', 'black specks', 'sediment', 'gritty', 'orange', 'tint', 'treatment', 'filter'],
        'articles': [
            ('blue-green-stains-well-water.html', 'Blue-Green Stains from Well Water'),
            ('black-specks-well-water.html', 'Black Specks in Well Water: Causes & Fixes'),
            ('gritty-sediment-well-water.html', 'Gritty Sediment in Well Water'),
            ('well-water-orange-tint.html', 'Why Is My Well Water Orange?'),
        ]
    },
    'maintenance': {
        'keywords': ['maintenance', 'checklist', 'inspection', 'spring', 'annual', 'preventive', 'log', 'flow meter', 'monitoring'],
        'articles': [
            ('spring-well-maintenance-checklist.html', 'Spring Well Maintenance Checklist'),
            ('well-maintenance-log-keeping.html', 'How to Keep a Well Maintenance Log'),
            ('preventive-maintenance-extends-well-life.html', 'How Preventive Maintenance Extends Well Life'),
            ('well-flow-meter-guide.html', 'Well Flow Meter Installation & Benefits'),
        ]
    },
    'drilling_cost': {
        'keywords': ['drill', 'drilling', 'cost', 'price', 'per foot', 'san diego', 'inspection', 'permit', 'anywhere'],
        'articles': [
            ('drilling-cost-per-foot-san-diego.html', 'Well Drilling Cost Per Foot in San Diego'),
            ('can-you-drill-well-anywhere.html', 'Can You Drill a Well Anywhere?'),
            ('well-inspection-cost-california.html', 'Well Inspection Costs in California'),
        ]
    },
    'general': {
        'keywords': ['foot valve', 'drop pipe', 'cold water', 'neighbor', 'interference', 'rights', 'guide'],
        'articles': [
            ('foot-valve-well-pump-guide.html', 'Foot Valve Guide for Well Pumps'),
            ('drop-pipe-selection-guide.html', 'Drop Pipe Selection Guide'),
            ('why-well-water-so-cold.html', 'Why Is Well Water So Cold?'),
            ('neighbor-well-interference-rights.html', 'Neighbor Well Interference & Water Rights'),
        ]
    }
}

def count_internal_blog_links(soup: BeautifulSoup) -> int:
    """Count internal blog links in the body content (between </header> and <footer>)."""
    # Find the main content area
    header = soup.find('header')
    footer = soup.find('footer')
    
    if not header or not footer:
        # Fallback: count in <main> or <article>
        main = soup.find('main') or soup.find('article')
        if not main:
            return 0
        content_area = main
    else:
        # Get all siblings between header and footer
        content_area = BeautifulSoup(str(soup), 'html.parser')
    
    # Find all links in the content area
    links = content_area.find_all('a', href=True)
    
    # Count internal blog links (relative links to .html files, excluding #anchors)
    count = 0
    for link in links:
        href = link.get('href', '')
        # Skip anchors, external links, and non-blog links
        if href.startswith('#'):
            continue
        if href.startswith('http'):
            continue
        if href.startswith('../') and not href.startswith('../blog/'):
            continue
        if href.endswith('.html') and 'blog' in href:
            # Make sure it's in the body, not header/footer
            parent = link.find_parent(['header', 'footer'])
            if not parent:
                count += 1
    
    return count

def has_related_articles_section(soup: BeautifulSoup) -> bool:
    """Check if page already has a related articles section."""
    sections = soup.find_all('section', class_='related-articles')
    if sections:
        return True
    
    # Also check for other variations
    for heading in soup.find_all(['h2', 'h3']):
        text = heading.get_text().lower()
        if 'related article' in text or 'related resource' in text:
            return True
    
    return False

def extract_page_topic(soup: BeautifulSoup, filename: str) -> str:
    """Extract the page topic from title/h1."""
    # Try to get title
    title_tag = soup.find('title')
    h1_tag = soup.find('h1')
    
    topic_text = ''
    if h1_tag:
        topic_text = h1_tag.get_text().lower()
    elif title_tag:
        topic_text = title_tag.get_text().lower()
    else:
        topic_text = filename.replace('-', ' ').replace('.html', '').lower()
    
    return topic_text

def get_article_title(filepath: Path) -> str:
    """Extract article title from HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            h1 = soup.find('h1')
            if h1:
                return h1.get_text().strip()
            title = soup.find('title')
            if title:
                # Strip site name
                title_text = title.get_text().strip()
                if '|' in title_text:
                    return title_text.split('|')[0].strip()
                if ':' in title_text:
                    return title_text.split(':')[0].strip()
                return title_text
    except:
        pass
    
    # Fallback: convert filename to title
    name = filepath.stem.replace('-', ' ').title()
    return name

def find_related_articles(topic_text: str, current_file: str, blog_dir: Path, num_articles: int = 5) -> List[Tuple[str, str]]:
    """Find related articles based on topic keywords."""
    related = []
    
    # Score each category
    category_scores = {}
    for category, data in TOPIC_CATEGORIES.items():
        score = 0
        for keyword in data['keywords']:
            if keyword in topic_text:
                score += 1
        if score > 0:
            category_scores[category] = score
    
    # Get articles from top matching categories
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    
    for category, score in sorted_categories:
        for article_file, article_title in TOPIC_CATEGORIES[category]['articles']:
            if article_file != current_file and article_file not in [r[0] for r in related]:
                # Verify file exists
                if (blog_dir / article_file).exists():
                    # Get actual title from file
                    actual_title = get_article_title(blog_dir / article_file)
                    related.append((article_file, actual_title))
                    if len(related) >= num_articles:
                        break
        if len(related) >= num_articles:
            break
    
    # If we don't have enough, add from other categories
    if len(related) < 4:
        for category, data in TOPIC_CATEGORIES.items():
            if category not in [c[0] for c in sorted_categories]:
                for article_file, article_title in data['articles']:
                    if article_file != current_file and article_file not in [r[0] for r in related]:
                        if (blog_dir / article_file).exists():
                            actual_title = get_article_title(blog_dir / article_file)
                            related.append((article_file, actual_title))
                            if len(related) >= 4:
                                break
            if len(related) >= 4:
                break
    
    return related[:6]  # Return max 6

def create_related_articles_html(related_articles: List[Tuple[str, str]]) -> str:
    """Create the related articles section HTML."""
    html = '''
<section class="related-articles my-8 p-6 bg-gray-50 rounded-xl border border-gray-200">
    <h3 class="font-bold text-primary text-lg mb-3">📚 Related Articles</h3>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
'''
    
    for filename, title in related_articles:
        html += f'        <a href="{filename}" class="text-accent hover:text-green-700 hover:underline font-medium">→ {title}</a>\n'
    
    html += '''    </div>
</section>
'''
    
    return html

def insert_related_articles(html_content: str, related_html: str) -> str:
    """Insert related articles section before </article> or <footer>."""
    # Try to insert before </article>
    if '</article>' in html_content:
        return html_content.replace('</article>', f'{related_html}</article>', 1)
    
    # Otherwise, insert before <footer>
    if '<footer>' in html_content:
        return html_content.replace('<footer>', f'{related_html}\n<footer>', 1)
    
    # Fallback: insert before </main>
    if '</main>' in html_content:
        return html_content.replace('</main>', f'{related_html}</main>', 1)
    
    # Last resort: insert before </body>
    if '</body>' in html_content:
        return html_content.replace('</body>', f'{related_html}\n</body>', 1)
    
    return html_content

def process_blog_files(blog_dir: Path) -> Dict[str, any]:
    """Process all blog HTML files."""
    stats = {
        'total': 0,
        'processed': 0,
        'skipped_has_links': 0,
        'skipped_has_section': 0,
        'skipped_index': 0,
        'modified': []
    }
    
    html_files = sorted(blog_dir.glob('*.html'))
    
    for filepath in html_files:
        stats['total'] += 1
        filename = filepath.name
        
        # Skip index.html
        if filename == 'index.html':
            stats['skipped_index'] += 1
            print(f"⏭️  Skipping {filename} (index page)")
            continue
        
        print(f"\n📄 Processing {filename}...")
        
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check if already has related articles section
        if has_related_articles_section(soup):
            stats['skipped_has_section'] += 1
            print(f"   ✓ Already has related articles section")
            continue
        
        # Count internal blog links
        link_count = count_internal_blog_links(soup)
        print(f"   Found {link_count} internal blog links")
        
        if link_count >= 3:
            stats['skipped_has_links'] += 1
            print(f"   ✓ Has enough internal links")
            continue
        
        # Extract topic
        topic = extract_page_topic(soup, filename)
        print(f"   Topic: {topic[:60]}...")
        
        # Find related articles
        related = find_related_articles(topic, filename, blog_dir)
        
        if not related:
            print(f"   ⚠️  No related articles found")
            continue
        
        print(f"   Adding {len(related)} related articles:")
        for article_file, title in related:
            print(f"      → {title}")
        
        # Create related articles HTML
        related_html = create_related_articles_html(related)
        
        # Insert into page
        modified_html = insert_related_articles(html_content, related_html)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_html)
        
        stats['processed'] += 1
        stats['modified'].append(filename)
        print(f"   ✅ Added related articles section")
    
    return stats

def main():
    """Main function."""
    blog_dir = Path('/Users/jarvis/clawd/scws-website/blog')
    
    if not blog_dir.exists():
        print(f"❌ Blog directory not found: {blog_dir}")
        return
    
    print("🚀 Starting internal link addition process...")
    print(f"📂 Blog directory: {blog_dir}\n")
    
    stats = process_blog_files(blog_dir)
    
    print("\n" + "="*60)
    print("📊 Summary:")
    print(f"   Total files: {stats['total']}")
    print(f"   Modified: {stats['processed']}")
    print(f"   Skipped (index): {stats['skipped_index']}")
    print(f"   Skipped (has links): {stats['skipped_has_links']}")
    print(f"   Skipped (has section): {stats['skipped_has_section']}")
    print("="*60)
    
    if stats['modified']:
        print(f"\n✅ Modified {len(stats['modified'])} files")
        print("\nReady to commit changes!")
    else:
        print("\n✨ No files needed modification")

if __name__ == '__main__':
    main()
