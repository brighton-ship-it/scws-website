#!/usr/bin/env python3
"""Add internal links to blog posts based on keyword matching"""
import os
import re
from collections import defaultdict

blog_dir = "blog"

# Define link categories with keywords and target URLs
link_categories = {
    "pump repair": [
        ("well pump repair", "well-pump-repair-san-diego.html"),
        ("pump replacement", "well-pump-replacement-cost.html"),
        ("pump problems", "signs-well-pump-failing.html"),
    ],
    "well drilling": [
        ("well drilling", "well-drilling-cost-san-diego.html"),
        ("drill a well", "well-drilling-cost-san-diego.html"),
        ("new well", "new-construction-well-drilling.html"),
    ],
    "pressure tank": [
        ("pressure tank", "pressure-tank-problems.html"),
        ("water pressure", "low-water-pressure-well.html"),
    ],
    "maintenance": [
        ("maintenance", "well-water-maintenance-guide.html"),
        ("annual service", "well-water-maintenance-guide.html"),
    ],
    "water quality": [
        ("water quality", "well-water-testing-guide.html"),
        ("water test", "well-water-testing-guide.html"),
        ("smells bad", "well-water-smells-bad.html"),
    ],
    "cost": [
        ("cost", "well-drilling-cost-san-diego.html"),
        ("price", "well-pump-replacement-cost.html"),
    ],
}

# City pages to link to
city_pages = {
    "ramona": "well-service-ramona.html",
    "escondido": "well-service-escondido.html",
    "valley center": "well-service-valley-center.html",
    "poway": "well-service-poway.html",
    "fallbrook": "well-service-fallbrook.html",
    "julian": "well-service-julian.html",
    "temecula": "well-service-temecula.html",
    "hemet": "well-pump-repair-hemet.html",
    "murrieta": "well-service-murrieta.html",
}

def get_related_posts(filename, content):
    """Find related posts based on content keywords"""
    related = set()
    content_lower = content.lower()
    
    # Match based on keywords
    if "pump" in content_lower:
        related.add(("Well Pump Repair Guide", "well-pump-repair-san-diego.html"))
        related.add(("Signs Your Well Pump is Failing", "signs-well-pump-failing.html"))
    if "pressure" in content_lower:
        related.add(("Low Water Pressure Solutions", "low-water-pressure-well.html"))
        related.add(("Pressure Tank Guide", "pressure-tank-problems.html"))
    if "drill" in content_lower or "new well" in content_lower:
        related.add(("Well Drilling Costs", "well-drilling-cost-san-diego.html"))
        related.add(("Well Permits in San Diego", "well-permit-san-diego.html"))
    if "maintenance" in content_lower or "service" in content_lower:
        related.add(("Well Maintenance Guide", "well-water-maintenance-guide.html"))
    if "cost" in content_lower or "price" in content_lower:
        related.add(("Well Drilling Costs", "well-drilling-cost-san-diego.html"))
        related.add(("Pump Replacement Costs", "well-pump-replacement-cost.html"))
    
    # Don't link to self
    related = {(title, url) for title, url in related if url != filename}
    
    return list(related)[:4]  # Max 4 related links

def add_related_section(content, related_posts):
    """Add related articles section before the closing </article> or </main>"""
    if not related_posts:
        return content
    
    related_html = '''
    <section class="related-articles" style="margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 8px;">
      <h3 style="margin-bottom: 1rem;">Related Articles</h3>
      <ul style="list-style: none; padding: 0;">
'''
    for title, url in related_posts:
        related_html += f'        <li style="margin-bottom: 0.5rem;"><a href="/blog/{url}">{title}</a></li>\n'
    related_html += '''      </ul>
    </section>
'''
    
    # Insert before </article> or </main>
    if '</article>' in content:
        content = content.replace('</article>', related_html + '</article>')
    elif '</main>' in content:
        content = content.replace('</main>', related_html + '</main>')
    
    return content

# Process files
processed = 0
for filename in os.listdir(blog_dir):
    if not filename.endswith('.html') or filename == 'index.html':
        continue
    
    filepath = os.path.join(blog_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has related articles
    if 'related-articles' in content:
        continue
    
    related = get_related_posts(filename, content)
    if related:
        new_content = add_related_section(content, related)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        processed += 1

print(f"Added internal links to {processed} posts")
