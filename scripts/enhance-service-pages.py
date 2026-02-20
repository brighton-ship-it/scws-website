#!/usr/bin/env python3
"""
Enhance service pages with hyper-local content:
1. Housing stock info tied to well system age
2. Specific neighborhoods served
3. Google Maps directions embed
4. Local facts and common issues
"""

import json
import os
import re
from pathlib import Path

# Load hyper-local data
with open('city-hyperlocal-data.json', 'r') as f:
    city_data = json.load(f)

# Remove meta entry
city_data.pop('_meta', None)

# Office addresses for Google Maps
RAMONA_OFFICE = "1077 Main St, Ramona, CA 92065"
ANZA_OFFICE = "57174 US Highway 79, Anza, CA 92539"

def get_maps_embed(city_name, nearest_office):
    """Generate Google Maps embed for directions"""
    office_address = RAMONA_OFFICE if nearest_office == "ramona" else ANZA_OFFICE
    # URL encode the addresses
    origin = city_name.replace(' ', '+') + ",+CA"
    destination = office_address.replace(' ', '+').replace(',', '%2C')
    
    return f'''
        <div class="directions-map" style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; margin: 2rem 0;">
            <h3 style="color: #1a365d; margin-bottom: 1rem;">📍 Directions from {city_name}</h3>
            <p style="margin-bottom: 1rem; color: #4a5568;">Our nearest office is in {"Ramona" if nearest_office == "ramona" else "Anza"} — {city_data.get(city_name.lower().replace(' ', '-'), {}).get('drive_time', 'a short drive away')}.</p>
            <iframe 
                width="100%" 
                height="300" 
                frameborder="0" 
                style="border:0; border-radius: 8px;" 
                referrerpolicy="no-referrer-when-downgrade"
                src="https://www.google.com/maps/embed/v1/directions?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&origin={origin}&destination={destination}&mode=driving"
                allowfullscreen>
            </iframe>
        </div>
'''

def get_housing_section(data, city_name):
    """Generate housing stock section"""
    housing = data.get('housing', {})
    
    return f'''
        <div class="housing-info" style="background: #fef3c7; padding: 1.5rem; border-radius: 8px; margin: 2rem 0; border-left: 4px solid #f59e0b;">
            <h3 style="color: #92400e; margin-bottom: 1rem;">🏠 {city_name} Housing & Well Systems</h3>
            <p><strong>Typical homes:</strong> {housing.get('era_description', 'Various styles and ages')}</p>
            <p><strong>Common home styles:</strong> {', '.join(housing.get('common_styles', ['Single-family homes']))}</p>
            <p><strong>Average lot size:</strong> {housing.get('typical_lot_size', 'Varies')}</p>
            <p style="margin-top: 1rem; color: #92400e;"><strong>What this means for your well:</strong> {housing.get('well_system_age', 'Many wells in this area may be due for inspection or upgrade.')}</p>
        </div>
'''

def get_neighborhoods_section(data, city_name):
    """Generate neighborhoods section"""
    neighborhoods = data.get('neighborhoods', [])
    if not neighborhoods:
        return ''
    
    # Create two columns of neighborhoods
    mid = len(neighborhoods) // 2 + len(neighborhoods) % 2
    col1 = neighborhoods[:mid]
    col2 = neighborhoods[mid:]
    
    col1_html = ''.join([f'<li style="padding: 0.25rem 0;">✓ {n}</li>' for n in col1])
    col2_html = ''.join([f'<li style="padding: 0.25rem 0;">✓ {n}</li>' for n in col2])
    
    return f'''
        <div class="neighborhoods-section" style="background: #ecfdf5; padding: 1.5rem; border-radius: 8px; margin: 2rem 0; border-left: 4px solid #10b981;">
            <h3 style="color: #065f46; margin-bottom: 1rem;">🏘️ Neighborhoods We Serve in {city_name}</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <ul style="list-style: none; margin: 0; padding: 0;">{col1_html}</ul>
                <ul style="list-style: none; margin: 0; padding: 0;">{col2_html}</ul>
            </div>
            <p style="margin-top: 1rem; font-size: 0.9rem; color: #047857;">Don't see your neighborhood? We serve all of {city_name} and surrounding areas!</p>
        </div>
'''

def get_local_issues_section(data, city_name):
    """Generate local issues/facts section"""
    issues = data.get('common_issues', [])
    facts = data.get('local_facts', [])
    
    if not issues and not facts:
        return ''
    
    issues_html = ''.join([f'<li style="padding: 0.25rem 0;">{issue}</li>' for issue in issues])
    facts_html = ''.join([f'<li style="padding: 0.25rem 0;">{fact}</li>' for fact in facts])
    
    return f'''
        <div class="local-expertise" style="background: #eff6ff; padding: 1.5rem; border-radius: 8px; margin: 2rem 0; border-left: 4px solid #3b82f6;">
            <h3 style="color: #1e40af; margin-bottom: 1rem;">🔧 Common Well Issues in {city_name}</h3>
            <ul style="list-style: disc; margin-left: 1.5rem; margin-bottom: 1rem;">{issues_html}</ul>
            {f'<h4 style="color: #1e40af; margin: 1rem 0 0.5rem;">Local Facts:</h4><ul style="list-style: disc; margin-left: 1.5rem;">{facts_html}</ul>' if facts else ''}
        </div>
'''

def enhance_page(filepath, city_slug, city_info):
    """Enhance a single service page with hyper-local content"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already enhanced
    if 'neighborhoods-section' in content or 'housing-info' in content:
        return False
    
    city_name = city_info.get('full_name', city_slug.replace('-', ' ').title())
    nearest_office = city_info.get('nearest_office', 'ramona')
    
    # Build new sections
    housing_section = get_housing_section(city_info, city_name)
    neighborhoods_section = get_neighborhoods_section(city_info, city_name)
    local_issues_section = get_local_issues_section(city_info, city_name)
    maps_section = get_maps_embed(city_name, nearest_office)
    
    # Find insertion point - after the local-info div or after price-box
    # Try to insert before the "Why Choose" section
    
    insertion_content = housing_section + neighborhoods_section + local_issues_section + maps_section
    
    # Try to insert before "Why Choose SCWS" section
    if '<div class="why-us">' in content:
        content = content.replace(
            '<div class="why-us">',
            insertion_content + '\n        <div class="why-us">'
        )
    # Or before the related-services section
    elif '<div class="related-services">' in content:
        content = content.replace(
            '<div class="related-services">',
            insertion_content + '\n        <div class="related-services">'
        )
    # Or before the CTA section
    elif '<section class="cta-section">' in content:
        content = content.replace(
            '<section class="cta-section">',
            insertion_content + '\n    </div>\n    <section class="cta-section">'
        )
    else:
        # Fallback - insert before closing </body>
        content = content.replace(
            '</body>',
            insertion_content + '\n</body>'
        )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    services_dir = Path('../services')
    
    enhanced_count = 0
    skipped_count = 0
    no_data_count = 0
    
    # Get all city directories
    for city_dir in services_dir.iterdir():
        if not city_dir.is_dir():
            continue
        
        city_slug = city_dir.name
        
        # Skip special directories
        if city_slug in ['agricultural', 'commercial', 'residential', 'hoa', 'vineyard']:
            continue
        
        # Check if we have data for this city
        if city_slug not in city_data:
            print(f"⚠️  No data for {city_slug}")
            no_data_count += 1
            continue
        
        city_info = city_data[city_slug]
        
        # Process each HTML file in the city directory
        for html_file in city_dir.glob('*.html'):
            result = enhance_page(html_file, city_slug, city_info)
            if result:
                enhanced_count += 1
            else:
                skipped_count += 1
    
    print(f"\n✅ Enhanced: {enhanced_count} pages")
    print(f"⏭️  Skipped (already done): {skipped_count} pages")
    print(f"⚠️  No data: {no_data_count} cities")

if __name__ == '__main__':
    main()
