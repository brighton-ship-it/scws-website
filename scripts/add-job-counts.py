#!/usr/bin/env python3
"""Add real job counts to service pages."""

import json
from pathlib import Path

def title_case(slug):
    return slug.replace('-', ' ').title()

def main():
    services_dir = Path("/Users/jarvis/clawd/scws-website/services")
    
    # Load job counts
    with open("/Users/jarvis/clawd/scws-website/scripts/city-job-counts.json") as f:
        job_counts = json.load(f)
    
    updated = 0
    skipped = 0
    
    for city_dir in services_dir.iterdir():
        if not city_dir.is_dir():
            continue
            
        city = city_dir.name
        count = job_counts.get(city, 0)
        
        if count == 0:
            skipped += 1
            continue
            
        city_name = title_case(city)
        
        # Create the badge HTML
        badge = f'''
        <div class="job-count-badge" style="background: #f0fdf4; border: 2px solid #22c55e; padding: 1rem; border-radius: 8px; text-align: center; margin: 1.5rem 0;">
            <span style="font-size: 2rem; font-weight: bold; color: #16a34a;">{count:,}</span><br>
            <span style="color: #166534;">customers served in {city_name}</span>
        </div>
'''
        
        for html_file in city_dir.glob("*.html"):
            if html_file.name == "index.html":
                continue
                
            content = html_file.read_text()
            
            # Skip if already has job count
            if 'job-count-badge' in content:
                continue
            
            # Insert before <h2>Our
            if '<h2>Our' in content:
                content = content.replace(
                    '<h2>Our',
                    badge + '<h2>Our',
                    1
                )
                html_file.write_text(content)
                updated += 1
    
    print(f"✅ Updated {updated} pages with job counts")
    print(f"⏭️  Skipped {skipped} cities (no job data)")

if __name__ == "__main__":
    main()
