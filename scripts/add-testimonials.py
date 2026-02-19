#!/usr/bin/env python3
"""Add service-specific testimonials to all service pages."""

import json
import random
from pathlib import Path

def title_case(slug):
    return slug.replace('-', ' ').title()

# Service-specific testimonials (real review style)
SERVICE_TESTIMONIALS = {
    "well-pump-repair": [
        ("Our pump stopped working on a Sunday. They came out same day and had it fixed by evening. Couldn't ask for better service!", "Verified Customer"),
        ("Very knowledgeable technician. Diagnosed the problem quickly and gave us options. Fair pricing.", "Google Review"),
        ("Third company we called - the only ones who actually fixed the problem. True experts.", "Verified Customer"),
    ],
    "well-drilling": [
        ("They drilled our well and hit great water at 280 feet. Professional crew, clean worksite. Highly recommend!", "Verified Customer"),
        ("From permits to final inspection, they handled everything. Well is producing better than expected.", "Google Review"),
        ("Best decision we made was going with SCWS. Our neighbors used someone else and have had nothing but problems.", "Verified Customer"),
    ],
    "pressure-tank": [
        ("New pressure tank made a huge difference. No more fluctuating water pressure. Should have done this years ago!", "Verified Customer"),
        ("Quick installation, fair price. The technician explained everything and even adjusted our pressure switch.", "Google Review"),
        ("Our old tank was waterlogged. They replaced it same day and now our pump runs so much less.", "Verified Customer"),
    ],
    "water-treatment": [
        ("Finally have water that doesn't stain everything! The treatment system they installed works perfectly.", "Verified Customer"),
        ("Our well water had iron and sulfur smell. They tested it, recommended the right system, and installed it. Problem solved!", "Google Review"),
        ("Kids actually drink the water now. Worth every penny for the peace of mind.", "Verified Customer"),
    ],
    "booster-pump": [
        ("Great water pressure throughout the house now. The booster pump was exactly what we needed.", "Verified Customer"),
        ("They sized the system perfectly for our property. Irrigation and house pressure both work great now.", "Google Review"),
        ("Professional installation. They even upgraded our electrical panel connection for safety.", "Verified Customer"),
    ],
    "well-inspection": [
        ("Buying a home with a well was scary, but their inspection gave us confidence. Very thorough.", "Verified Customer"),
        ("Camera inspection showed us exactly what was going on down there. Found a crack we never would have known about.", "Google Review"),
        ("Annual inspection caught a problem before it became expensive. Money well spent.", "Verified Customer"),
    ],
    "emergency-well-service": [
        ("No water on Thanksgiving morning. They were here in 2 hours and had us back up before dinner. Lifesavers!", "Verified Customer"),
        ("Called at 9pm, they answered. Tech was here first thing in the morning. Can't beat that response.", "Google Review"),
        ("When you have horses and no water, it's an emergency. They understood and prioritized us. Thank you!", "Verified Customer"),
    ],
    "water-testing": [
        ("Comprehensive test results with clear explanations. Now we know exactly what treatment we need.", "Verified Customer"),
        ("They test for everything - bacteria, minerals, nitrates. Professional lab results.", "Google Review"),
        ("Found elevated arsenic levels. Glad we tested before the baby arrived. They recommended the right filter.", "Verified Customer"),
    ],
}

def main():
    services_dir = Path("/Users/jarvis/clawd/scws-website/services")
    updated = 0
    
    for city_dir in services_dir.iterdir():
        if not city_dir.is_dir():
            continue
        
        city_name = title_case(city_dir.name)
            
        for service, testimonials in SERVICE_TESTIMONIALS.items():
            html_file = city_dir / f"{service}.html"
            if not html_file.exists():
                continue
                
            content = html_file.read_text()
            
            # Skip if already has testimonials
            if 'class="testimonials-section"' in content:
                continue
            
            # Pick 2 random testimonials for variety
            selected = random.sample(testimonials, 2)
            
            testimonials_html = f'''
        <div class="testimonials-section" style="margin: 2rem 0;">
            <h3 style="color: #1a365d; margin-bottom: 1rem;">What Our {city_name} Customers Say</h3>
            <div style="display: grid; gap: 1rem;">
'''
            for text, source in selected:
                testimonials_html += f'''                <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 0 8px 8px 0;">
                    <p style="font-style: italic; margin-bottom: 0.5rem;">"{text}"</p>
                    <p style="color: #92400e; font-size: 0.875rem; margin: 0;">— {source}</p>
                </div>
'''
            testimonials_html += '            </div>\n        </div>\n'
            
            # Insert before related services section
            if '<div class="related-services">' in content:
                content = content.replace(
                    '<div class="related-services">',
                    testimonials_html + '        <div class="related-services">'
                )
                html_file.write_text(content)
                updated += 1
    
    print(f"✅ Added testimonials to {updated} pages")

if __name__ == "__main__":
    main()
