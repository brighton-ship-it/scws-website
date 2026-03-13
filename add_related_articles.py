#!/usr/bin/env python3
"""
Add Related Articles sections to blog pages missing them.
Processes in batches of 500 with git commits.
"""

import re
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict

# Category definitions with image, color, and label
CATEGORIES = {
    'emergency': {'image': 'emergency.png', 'color': 'red-600', 'label': 'Emergency'},
    'troubleshooting': {'image': 'troubleshooting.png', 'color': 'accent', 'label': 'Troubleshooting'},
    'maintenance': {'image': 'maintenance.png', 'color': 'accent', 'label': 'Maintenance'},
    'equipment': {'image': 'equipment.png', 'color': 'blue-600', 'label': 'Equipment'},
    'water-quality': {'image': 'water-quality.png', 'color': 'blue-600', 'label': 'Water Quality'},
    'drilling': {'image': 'drilling.png', 'color': 'accent', 'label': 'Drilling'},
    'cost-guide': {'image': 'cost-guide.png', 'color': 'amber-600', 'label': 'Cost Guide'},
    'pressure-issues': {'image': 'pressure-issues.png', 'color': 'orange-600', 'label': 'Pressure Issues'},
    'treatment': {'image': 'treatment.png', 'color': 'blue-600', 'label': 'Treatment'},
    'urgent': {'image': 'urgent.png', 'color': 'orange-600', 'label': 'Urgent'},
    'warning-signs': {'image': 'warning-signs.png', 'color': 'red-600', 'label': 'Warning Signs'},
    'agricultural': {'image': 'agricultural.png', 'color': 'accent', 'label': 'Agricultural'},
}

# High-value hub pages by topic
HUB_PAGES = {
    'emergency': [
        ('no-water-from-well.html', 'No Water From Well? Emergency Troubleshooting Guide', 'Step-by-step guide to diagnose and fix no water emergencies'),
        ('emergency-well-no-water.html', 'Emergency Well No Water Checklist', 'Quick checklist for when your well stops producing water'),
        ('no-water-emergency-checklist.html', 'No Water Emergency: What to Check First', 'Essential first steps when facing a water emergency'),
    ],
    'pump-repair': [
        ('signs-well-pump-failing.html', '10 Warning Signs Your Well Pump Is Failing', 'Recognize the early warning signs before complete failure'),
        ('well-pump-repair.html', 'Well Pump Repair Guide: Common Issues & Solutions', 'Complete guide to diagnosing and repairing well pumps'),
        ('well-pump-replacement.html', 'Well Pump Replacement: Process, Cost & Timeline', 'Everything you need to know about pump replacement'),
        ('well-pump-troubleshooting.html', 'Well Pump Troubleshooting: Complete Diagnostic Guide', 'Systematic approach to identifying pump problems'),
    ],
    'pump-wont-start': [
        ('well-pump-wont-turn-on.html', 'Well Pump Won\'t Turn On: Troubleshooting Steps', 'Diagnose why your pump won\'t start'),
        ('pump-hums-but-wont-start.html', 'Pump Hums But Won\'t Start: Causes & Fixes', 'Why your pump hums but fails to run'),
        ('well-pump-breaker-keeps-tripping.html', 'Well Pump Breaker Keeps Tripping: Diagnosis Guide', 'Find and fix breaker tripping issues'),
    ],
    'pump-runs-constantly': [
        ('well-pump-runs-constantly.html', 'Well Pump Runs Constantly: Causes & Solutions', 'Why your pump won\'t shut off and how to fix it'),
        ('well-pump-short-cycling-causes.html', 'Well Pump Short Cycling: 7 Common Causes', 'Understanding and fixing rapid on/off cycling'),
    ],
    'pressure': [
        ('low-water-pressure-well.html', 'Low Water Pressure From Well: Complete Fix Guide', 'Diagnose and solve low pressure problems'),
        ('well-pressure-switch-guide.html', 'Well Pressure Switch: Settings, Adjustment & Replacement', 'Everything about pressure switches'),
        ('pressure-tank-maintenance-guide.html', 'Pressure Tank Maintenance: Complete Guide', 'Keep your pressure tank working properly'),
    ],
    'water-quality': [
        ('well-water-testing.html', 'Well Water Testing: What, When & How Often', 'Complete guide to testing your well water'),
        ('well-water-filtration-systems.html', 'Well Water Filtration Systems: Complete Buyer\'s Guide', 'Choose the right filtration system'),
        ('hard-water-solutions.html', 'Hard Water Solutions for Well Owners', 'Fix hard water problems effectively'),
        ('sulfur-smell-well-water.html', 'Sulfur Smell in Well Water: Causes & Solutions', 'Eliminate rotten egg odor from your water'),
    ],
    'drilling': [
        ('well-drilling-cost-calculator.html', 'Well Drilling Cost Calculator: Get Accurate Estimates', 'Calculate your well drilling costs'),
        ('san-diego-county-well-permit-process.html', 'San Diego County Well Permit Process Guide', 'Navigate the permit process successfully'),
        ('well-drilling-timeline.html', 'Well Drilling Timeline: What to Expect', 'Understand the drilling process and timeframe'),
    ],
    'maintenance': [
        ('spring-well-maintenance-checklist.html', 'Spring Well Maintenance Checklist', 'Essential spring maintenance tasks'),
        ('well-maintenance-schedule.html', 'Well Maintenance Schedule: Year-Round Guide', 'Complete maintenance calendar for well owners'),
        ('well-pump-lifespan-expectancy.html', 'Well Pump Lifespan: How Long Do They Last?', 'Expected lifespan and factors that affect it'),
    ],
    'cost': [
        ('well-pump-replacement-cost.html', 'Well Pump Replacement Cost: 2024 Price Guide', 'Detailed breakdown of replacement costs'),
        ('well-drilling-cost-per-foot.html', 'Well Drilling Cost Per Foot: Regional Price Guide', 'What to expect for drilling costs'),
        ('water-well-cost.html', 'Water Well Cost: Complete Installation Price Guide', 'Total cost of new well installation'),
    ],
    'rusty-sediment': [
        ('rusty-well-water.html', 'Rusty Well Water: Causes, Risks & Solutions', 'Fix rust and iron in your well water'),
        ('sediment-in-well-water.html', 'Sediment in Well Water: Causes & Filtration', 'Clear up sediment and particulates'),
        ('well-water-filtration-systems.html', 'Well Water Filtration Systems: Complete Buyer\'s Guide', 'Choose the right filtration system'),
    ],
    'treatment': [
        ('water-softener-well-cost.html', 'Water Softener for Well: Cost & Installation Guide', 'Everything about well water softeners'),
        ('reverse-osmosis-well-water.html', 'Reverse Osmosis for Well Water: Complete Guide', 'RO systems for well water'),
        ('uv-water-treatment-wells.html', 'UV Water Treatment for Wells: Buyer\'s Guide', 'UV sterilization for well water'),
    ],
    'agricultural': [
        ('ranch-water-well-systems.html', 'Ranch Water Well Systems: Complete Guide', 'Well systems for ranches and farms'),
        ('agricultural-water-rights-california.html', 'Agricultural Water Rights in California', 'Understand your water rights'),
        ('vineyard-well-drilling.html', 'Vineyard Well Drilling: Requirements & Costs', 'Wells for vineyards and wineries'),
    ],
    'abandonment': [
        ('well-abandonment-guide.html', 'Well Abandonment Guide: Process & Requirements', 'How to properly abandon a well'),
        ('well-abandonment-cost-california.html', 'Well Abandonment Cost in California', 'What you\'ll pay to abandon a well'),
        ('well-abandonment-california-guide.html', 'California Well Abandonment: Complete Guide', 'State requirements for well closure'),
    ],
    'inspection': [
        ('well-inspection-checklist.html', 'Well Inspection Checklist: What to Look For', 'Complete inspection guide'),
        ('well-inspection-before-buying-home.html', 'Well Inspection Before Buying a Home', 'Critical inspection points for home buyers'),
        ('well-inspection-cost.html', 'Well Inspection Cost: What to Expect', 'Pricing for professional inspections'),
    ],
    'permits': [
        ('well-permits-california.html', 'Well Permits in California: Complete Guide', 'Navigate California well permitting'),
        ('well-drilling-permits-california.html', 'Well Drilling Permits California: Requirements', 'Permit requirements for new wells'),
        ('well-permit-guide-san-diego.html', 'San Diego Well Permit Guide', 'Local permit process for San Diego'),
    ],
    'rehab': [
        ('well-rehabilitation-cost.html', 'Well Rehabilitation Cost: What to Expect', 'Cost of rehabilitating an old well'),
        ('well-rehabilitation-techniques.html', 'Well Rehabilitation Techniques & Methods', 'How wells are rehabilitated'),
        ('well-deepening-vs-new-well.html', 'Well Deepening vs New Well: Which Is Better?', 'Compare your options for low-yield wells'),
    ],
}

def classify_page(filename: str) -> str:
    """Classify a page by its filename to determine topic category."""
    basename = filename.lower().replace('.html', '')
    
    # City-specific patterns (for routing to service type)
    cities = ['ramona', 'alpine', 'escondido', 'poway', 'valley-center', 'julian', 
              'lakeside', 'santee', 'el-cajon', 'la-mesa', 'spring-valley']
    
    # Check keywords in order of specificity
    if any(word in basename for word in ['no-water', 'emergency', 'well-stopped', 'suddenly-stopped']):
        return 'emergency'
    elif 'wont-turn-on' in basename or 'wont-start' in basename or 'hums-but' in basename or 'breaker-trip' in basename:
        return 'pump-wont-start'
    elif 'runs-constantly' in basename or 'short-cycling' in basename or 'wont-shut-off' in basename:
        return 'pump-runs-constantly'
    elif any(word in basename for word in ['pump-repair', 'pump-failing', 'pump-replacement', 'pump-troubleshoot', 'pump-noise', 'pump-vibrat']):
        return 'pump-repair'
    elif any(word in basename for word in ['pressure', 'psi']):
        return 'pressure'
    elif any(word in basename for word in ['rusty', 'sediment', 'cloudy', 'particles']):
        return 'rusty-sediment'
    elif any(word in basename for word in ['sulfur', 'smell', 'odor', 'taste', 'discolor', 'contaminat', 'bacteria', 'testing', 'water-quality']):
        return 'water-quality'
    elif any(word in basename for word in ['softener', 'reverse-osmosis', 'uv-treatment', 'filtration', 'treatment']):
        return 'treatment'
    elif any(word in basename for word in ['drilling', 'new-well', 'drill']):
        return 'drilling'
    elif any(word in basename for word in ['cost', 'price', 'pricing']):
        return 'cost'
    elif any(word in basename for word in ['abandon', 'decommission', 'closure']):
        return 'abandonment'
    elif any(word in basename for word in ['inspection', 'inspect']):
        return 'inspection'
    elif any(word in basename for word in ['permit', 'permitting']):
        return 'permits'
    elif any(word in basename for word in ['rehab', 'deepening', 'redevelop']):
        return 'rehab'
    elif any(word in basename for word in ['ranch', 'agricultural', 'farm', 'vineyard']):
        return 'agricultural'
    elif any(word in basename for word in ['maintenance', 'checklist', 'schedule', 'lifespan']):
        return 'maintenance'
    else:
        # Default to maintenance for general topics
        return 'maintenance'

def get_related_articles(filename: str, topic: str) -> List[Tuple[str, str, str, str, str, str]]:
    """
    Get 3 related articles for a page.
    Returns list of tuples: (href, category_image, color, label, title, description)
    """
    basename = filename.replace('.html', '')
    
    # For city-specific pages, pick 2 service-type articles + 1 general
    cities = ['ramona', 'alpine', 'escondido', 'poway', 'valley-center', 'julian',
              'lakeside', 'santee', 'el-cajon', 'la-mesa', 'spring-valley']
    
    is_city_page = any(city in basename.lower() for city in cities)
    
    articles = []
    
    if is_city_page:
        # For city pages: 2 from service type + 1 general maintenance/cost
        service_articles = HUB_PAGES.get(topic, HUB_PAGES['maintenance'])[:2]
        general_articles = HUB_PAGES['maintenance'][:1]
        
        for href, title, desc in service_articles:
            if href != filename:
                cat = get_category_for_topic(topic)
                articles.append((href, cat['image'], cat['color'], cat['label'], title, desc))
        
        for href, title, desc in general_articles:
            if href != filename:
                cat = CATEGORIES['maintenance']
                articles.append((href, cat['image'], cat['color'], cat['label'], title, desc))
    else:
        # Regular pages: 3 from topic category, or mix if needed
        topic_articles = HUB_PAGES.get(topic, [])
        
        # Filter out self-references
        topic_articles = [(h, t, d) for h, t, d in topic_articles if h != filename]
        
        # Take up to 3 from topic
        for href, title, desc in topic_articles[:3]:
            cat = get_category_for_topic(topic)
            articles.append((href, cat['image'], cat['color'], cat['label'], title, desc))
        
        # If we need more, add from maintenance
        if len(articles) < 3:
            for href, title, desc in HUB_PAGES['maintenance']:
                if href != filename and not any(a[0] == href for a in articles):
                    cat = CATEGORIES['maintenance']
                    articles.append((href, cat['image'], cat['color'], cat['label'], title, desc))
                    if len(articles) >= 3:
                        break
    
    return articles[:3]

def get_category_for_topic(topic: str) -> Dict[str, str]:
    """Map topic to category definition."""
    topic_to_category = {
        'emergency': 'emergency',
        'pump-repair': 'troubleshooting',
        'pump-wont-start': 'troubleshooting',
        'pump-runs-constantly': 'troubleshooting',
        'pressure': 'pressure-issues',
        'water-quality': 'water-quality',
        'drilling': 'drilling',
        'maintenance': 'maintenance',
        'cost': 'cost-guide',
        'rusty-sediment': 'water-quality',
        'treatment': 'treatment',
        'agricultural': 'agricultural',
        'abandonment': 'maintenance',
        'inspection': 'maintenance',
        'permits': 'drilling',
        'rehab': 'maintenance',
    }
    
    category_key = topic_to_category.get(topic, 'maintenance')
    return CATEGORIES.get(category_key, CATEGORIES['maintenance'])

def generate_card_html(href: str, image: str, color: str, label: str, title: str, desc: str) -> str:
    """Generate HTML for a single article card."""
    # Escape quotes in title for alt text
    alt_text = title.replace('"', '&quot;')
    
    return f'''<a href="{href}" class="group bg-white rounded-xl shadow-md hover:shadow-xl transition overflow-hidden">
                    <div class="h-40 overflow-hidden">
                        <img width="800" height="600" loading="lazy" src="/assets/images/article-categories/{image}" alt="{alt_text}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                    </div>
                    <div class="p-5">
                        <span class="text-xs font-semibold text-{color} uppercase tracking-wide">{label}</span>
                        <h3 class="font-bold text-lg text-primary mt-1 mb-2 group-hover:text-accent transition">{title}</h3>
                        <p class="text-gray-600 text-sm">{desc}</p>
                    </div>
                </a>'''

def generate_related_section(filename: str, topic: str) -> str:
    """Generate the complete Related Articles section."""
    articles = get_related_articles(filename, topic)
    
    cards_html = '\n                '.join([
        generate_card_html(href, img, color, label, title, desc)
        for href, img, color, label, title, desc in articles
    ])
    
    return f'''
<!-- Related Articles -->
<section class="py-16 bg-gray-50">
    <div class="max-w-4xl mx-auto px-4">
        <div class="text-center mb-10">
            <h2 id="related-articles" class="text-3xl font-bold text-primary mb-2">Related Articles</h2>
            <p class="text-gray-600">Continue learning about well maintenance and troubleshooting</p>
        </div>
        <div class="grid md:grid-cols-3 gap-6">
            {cards_html}
        </div>
    </div>
</section>
'''

def process_file(filepath: Path) -> bool:
    """Process a single HTML file. Returns True if modified."""
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Skip if already has Related Articles
        if 'Related Articles</h2>' in content:
            return False
        
        # Classify and generate section
        filename = filepath.name
        topic = classify_page(filename)
        section = generate_related_section(filename, topic)
        
        # Find insertion point (before </article> or <footer>)
        article_match = re.search(r'</article>', content)
        footer_match = re.search(r'<footer', content)
        
        if article_match:
            insert_pos = article_match.start()
        elif footer_match:
            insert_pos = footer_match.start()
        else:
            print(f"⚠️  No insertion point found in {filename}")
            return False
        
        # Insert the section
        new_content = content[:insert_pos] + section + content[insert_pos:]
        
        filepath.write_text(new_content, encoding='utf-8')
        return True
        
    except Exception as e:
        print(f"❌ Error processing {filepath.name}: {e}")
        return False

def main():
    """Main processing loop."""
    blog_dir = Path('blog')
    
    # Find all files missing Related Articles
    all_files = list(blog_dir.glob('*.html'))
    missing_files = []
    
    print("🔍 Finding files missing Related Articles...")
    for filepath in all_files:
        try:
            content = filepath.read_text(encoding='utf-8')
            if 'Related Articles</h2>' not in content:
                missing_files.append(filepath)
        except Exception as e:
            print(f"⚠️  Error reading {filepath.name}: {e}")
    
    print(f"📊 Found {len(missing_files)} files to process")
    
    # Process in batches of 500
    batch_size = 500
    total_processed = 0
    
    for batch_num in range(0, len(missing_files), batch_size):
        batch = missing_files[batch_num:batch_num + batch_size]
        batch_number = (batch_num // batch_size) + 1
        
        print(f"\n📦 Processing batch {batch_number} ({len(batch)} files)...")
        
        modified = 0
        for filepath in batch:
            if process_file(filepath):
                modified += 1
                if modified % 100 == 0:
                    print(f"  ✅ Processed {modified}/{len(batch)}...")
        
        total_processed += modified
        print(f"  ✅ Batch {batch_number} complete: {modified} files modified")
        
        # Git commit and push
        if modified > 0:
            try:
                print(f"  📤 Committing batch {batch_number}...")
                subprocess.run(['git', 'add', '-A'], check=True)
                subprocess.run(['git', 'commit', '-m', f'Add related articles cards (batch {batch_number})'], check=True)
                subprocess.run(['git', 'push'], check=True)
                print(f"  ✅ Batch {batch_number} pushed to git")
            except subprocess.CalledProcessError as e:
                print(f"  ⚠️  Git error: {e}")
    
    print(f"\n🎉 Complete! Processed {total_processed} files total.")

if __name__ == '__main__':
    main()
