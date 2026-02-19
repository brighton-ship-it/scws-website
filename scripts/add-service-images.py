#!/usr/bin/env python3
"""Add service images to all service pages."""

from pathlib import Path

# Map services to existing images
SERVICE_IMAGES = {
    "well-pump-repair": "/images/well-pump-service.jpg",
    "well-drilling": "/images/drilling-rig.jpg",
    "pressure-tank": "/images/water-tanks.jpg",
    "water-treatment": "/images/estate-well-system.jpg",
    "booster-pump": "/images/well-pump-motor.jpg",
    "well-inspection": "/images/maintenance.jpg",
    "emergency-well-service": "/images/service-truck.jpg",
    "water-testing": "/images/water-testing.jpg"
}

def main():
    services_dir = Path("/Users/jarvis/clawd/scws-website/services")
    updated = 0
    
    for city_dir in services_dir.iterdir():
        if not city_dir.is_dir():
            continue
            
        for service, image_path in SERVICE_IMAGES.items():
            html_file = city_dir / f"{service}.html"
            if not html_file.exists():
                continue
                
            content = html_file.read_text()
            
            # Skip if already has service image
            if 'class="service-hero-image"' in content:
                continue
            
            # Create image HTML
            image_html = f'''
        <div class="service-hero-image" style="margin: 2rem 0; border-radius: 8px; overflow: hidden;">
            <img src="{image_path}" alt="{service.replace('-', ' ').title()}" style="width: 100%; height: 300px; object-fit: cover;">
        </div>
'''
            
            # Insert after the hero section closing tag
            if '</section>\n    \n    <div class="container">' in content:
                content = content.replace(
                    '</section>\n    \n    <div class="container">',
                    '</section>\n    \n    <div class="container">' + image_html
                )
                html_file.write_text(content)
                updated += 1
    
    print(f"✅ Added images to {updated} pages")

if __name__ == "__main__":
    main()
