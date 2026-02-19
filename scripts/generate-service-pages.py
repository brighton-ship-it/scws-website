#!/usr/bin/env python3
"""Generate service pages for each city with proper commercial structure."""

import os
import json
from pathlib import Path

# Cities we serve
CITIES = [
    "aguanga", "alpine", "anza", "apple-valley", "banning", "beaumont", 
    "big-bear-lake", "bonsall", "borrego-springs", "boulevard", "campo", 
    "carlsbad", "crestline", "cuyamaca", "de-luz", "descanso", "el-cajon", 
    "encinitas", "escondido", "fallbrook", "hemet", "hesperia", "idyllwild", 
    "jacumba", "jamul", "joshua-tree", "julian", "la-mesa", "lake-arrowhead", 
    "lake-elsinore", "lakeside", "landers", "lucerne-valley", "menifee", 
    "morongo-valley", "murrieta", "oak-hills", "oceanside", "pauma-valley", 
    "perris", "pine-valley", "poway", "rainbow", "ramona", "rancho-mirage", 
    "rancho-santa-fe", "ranchita", "san-jacinto", "san-marcos", "santa-ysabel", 
    "santee", "spring-valley", "sun-city", "temecula", "valley-center", 
    "victorville", "vista", "warner-springs", "wildomar", "winchester", 
    "wrightwood", "yucaipa", "yucca-valley", "palm-desert", "palm-springs",
    "indio", "la-quinta", "cathedral-city"
]

# Services with details
SERVICES = {
    "well-pump-repair": {
        "title": "Well Pump Repair",
        "description": "Expert well pump repair services",
        "price_range": "$200 - $2,500",
        "keywords": ["well pump repair", "submersible pump repair", "pump replacement", "pump service"],
        "intro": "Is your well pump failing? We diagnose and repair all types of well pumps including submersible, jet, and booster pumps.",
        "services_list": [
            "Submersible pump repair & replacement",
            "Jet pump service",
            "Pump motor replacement",
            "Control box repair",
            "Pressure switch adjustment",
            "Pump wiring repair"
        ]
    },
    "well-drilling": {
        "title": "Well Drilling",
        "description": "Professional water well drilling services",
        "price_range": "$15,000 - $50,000+",
        "keywords": ["well drilling", "water well drilling", "drill a well", "new well"],
        "intro": "Need a new water well? Our experienced drilling team has drilled thousands of wells across Southern California.",
        "services_list": [
            "Residential well drilling",
            "Agricultural well drilling", 
            "Test hole drilling",
            "Well permit assistance",
            "Site evaluation",
            "Hydrogeological assessment"
        ]
    },
    "pressure-tank": {
        "title": "Pressure Tank Service",
        "description": "Pressure tank repair and replacement",
        "price_range": "$300 - $2,000",
        "keywords": ["pressure tank", "well pressure tank", "bladder tank", "water pressure"],
        "intro": "Experiencing water pressure problems? We service, repair, and replace all types of pressure tanks.",
        "services_list": [
            "Pressure tank replacement",
            "Bladder tank service",
            "Air charge adjustment",
            "Pressure switch calibration",
            "Tank sizing consultation",
            "System pressure optimization"
        ]
    },
    "water-treatment": {
        "title": "Water Treatment",
        "description": "Well water treatment and filtration systems",
        "price_range": "$500 - $5,000",
        "keywords": ["water treatment", "water filtration", "water softener", "iron filter"],
        "intro": "Concerned about your water quality? We install and service water treatment systems for well water.",
        "services_list": [
            "Water testing",
            "Filtration system installation",
            "Water softener service",
            "Iron & manganese removal",
            "UV disinfection systems",
            "Reverse osmosis installation"
        ]
    },
    "booster-pump": {
        "title": "Booster Pump Service",
        "description": "Booster pump installation and repair",
        "price_range": "$800 - $3,500",
        "keywords": ["booster pump", "water pressure booster", "pump installation"],
        "intro": "Need more water pressure? We install and service booster pumps for homes, farms, and commercial properties.",
        "services_list": [
            "Booster pump installation",
            "Pump repair & service",
            "Variable speed drives (VFD)",
            "System design",
            "Pressure optimization",
            "Multi-pump systems"
        ]
    },
    "well-inspection": {
        "title": "Well Inspection",
        "description": "Professional well inspection services",
        "price_range": "$250 - $500",
        "keywords": ["well inspection", "well camera inspection", "well evaluation"],
        "intro": "Buying a property with a well? Concerned about your well's condition? We provide comprehensive well inspections.",
        "services_list": [
            "Video camera inspection",
            "Flow rate testing",
            "Water quality testing",
            "Equipment evaluation",
            "Real estate inspections",
            "Annual well checkups"
        ]
    },
    "emergency-well-service": {
        "title": "Emergency Well Service",
        "description": "24/7 emergency well repair",
        "price_range": "$300+ (emergency rates)",
        "keywords": ["emergency well service", "no water", "well emergency", "24 hour well service"],
        "intro": "No water? We offer emergency well service to get your water back on fast. Call now for immediate assistance.",
        "services_list": [
            "Same-day emergency response",
            "After-hours service available",
            "Rapid pump replacement",
            "Emergency diagnostics",
            "Temporary water solutions",
            "Priority scheduling"
        ]
    },
    "water-testing": {
        "title": "Water Testing",
        "description": "Comprehensive well water testing",
        "price_range": "$50 - $400",
        "keywords": ["water testing", "well water test", "water quality test"],
        "intro": "Know what's in your water. We offer comprehensive water testing for bacteria, minerals, and contaminants.",
        "services_list": [
            "Bacteria testing (coliform, E. coli)",
            "Mineral analysis",
            "Nitrate testing",
            "Heavy metal screening",
            "Full panel testing",
            "Annual testing programs"
        ]
    }
}

def title_case(slug):
    """Convert slug to title case."""
    return slug.replace('-', ' ').title()

def generate_page(city, service_slug, service_data, output_dir):
    """Generate a single service page."""
    city_name = title_case(city)
    service_name = service_data['title']
    
    # Create city directory
    city_dir = output_dir / city
    city_dir.mkdir(parents=True, exist_ok=True)
    
    page_title = f"{service_name} {city_name} | Licensed Well Contractor"
    meta_desc = f"{service_data['description']} in {city_name}, CA. Licensed C-57 contractor. {service_data['price_range']}. Call (760) 440-8520."
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KR42LY3LF7"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-KR42LY3LF7');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_desc}">
    <title>{page_title}</title>
    <link rel="canonical" href="https://scwellservice.com/services/{city}/{service_slug}.html">
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "{service_name} in {city_name}",
        "description": "{service_data['description']} in {city_name}, California",
        "provider": {{
            "@type": "LocalBusiness",
            "name": "Southern California Well Service",
            "telephone": "(760) 440-8520",
            "address": {{
                "@type": "PostalAddress",
                "streetAddress": "1077 Main St",
                "addressLocality": "Ramona",
                "addressRegion": "CA",
                "postalCode": "92065"
            }},
            "priceRange": "{service_data['price_range']}"
        }},
        "areaServed": {{
            "@type": "City",
            "name": "{city_name}",
            "containedInPlace": {{
                "@type": "State",
                "name": "California"
            }}
        }}
    }}
    </script>
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #1a365d; color: white; padding: 1rem; }}
        .header-content {{ max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ color: white; text-decoration: none; font-size: 1.25rem; font-weight: bold; }}
        .phone {{ background: #ed8936; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .phone:hover {{ background: #dd6b20; }}
        .hero {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 3rem 1rem; text-align: center; }}
        .hero h1 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
        .hero p {{ font-size: 1.25rem; opacity: 0.9; max-width: 600px; margin: 0 auto 2rem; }}
        .cta-button {{ background: #ed8936; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 5px; font-size: 1.25rem; font-weight: bold; display: inline-block; }}
        .cta-button:hover {{ background: #dd6b20; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        .services-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin: 2rem 0; }}
        .service-card {{ background: #f7fafc; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ed8936; }}
        .service-card h3 {{ color: #1a365d; margin-bottom: 0.5rem; }}
        .price-box {{ background: #1a365d; color: white; padding: 2rem; border-radius: 8px; text-align: center; margin: 2rem 0; }}
        .price-box h2 {{ margin-bottom: 0.5rem; }}
        .price-range {{ font-size: 2rem; font-weight: bold; color: #ed8936; }}
        .why-us {{ background: #f7fafc; padding: 2rem; border-radius: 8px; margin: 2rem 0; }}
        .why-us h2 {{ color: #1a365d; margin-bottom: 1rem; }}
        .why-us ul {{ list-style: none; }}
        .why-us li {{ padding: 0.5rem 0; padding-left: 1.5rem; position: relative; }}
        .why-us li:before {{ content: "✓"; color: #38a169; position: absolute; left: 0; font-weight: bold; }}
        .cta-section {{ background: #ed8936; color: white; padding: 3rem 1rem; text-align: center; margin-top: 2rem; }}
        .cta-section h2 {{ margin-bottom: 1rem; }}
        .cta-section .phone-big {{ font-size: 2rem; color: white; text-decoration: none; font-weight: bold; }}
        .footer {{ background: #1a365d; color: white; padding: 2rem 1rem; text-align: center; }}
        .footer a {{ color: #ed8936; }}
        .breadcrumb {{ padding: 1rem; background: #edf2f7; }}
        .breadcrumb a {{ color: #2c5282; text-decoration: none; }}
        .breadcrumb span {{ color: #718096; }}
        .related-services {{ margin: 2rem 0; }}
        .related-services h3 {{ color: #1a365d; margin-bottom: 1rem; }}
        .related-links {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
        .related-links a {{ background: #edf2f7; padding: 0.5rem 1rem; border-radius: 5px; text-decoration: none; color: #2c5282; }}
        .related-links a:hover {{ background: #e2e8f0; }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">Southern California Well Service</a>
            <a href="tel:+17604408520" class="phone">📞 (760) 440-8520</a>
        </div>
    </header>
    
    <nav class="breadcrumb">
        <div class="container" style="padding: 0;">
            <a href="/">Home</a> <span>›</span>
            <a href="/services/">Services</a> <span>›</span>
            <a href="/services/{city}/">{city_name}</a> <span>›</span>
            <span>{service_name}</span>
        </div>
    </nav>
    
    <section class="hero">
        <h1>{service_name} in {city_name}</h1>
        <p>{service_data['intro']}</p>
        <a href="tel:+17604408520" class="cta-button">Call Now: (760) 440-8520</a>
    </section>
    
    <div class="container">
        <div class="price-box">
            <h2>Typical Price Range</h2>
            <div class="price-range">{service_data['price_range']}</div>
            <p>Free estimates • No trip charge in {city_name}</p>
        </div>
        
        <h2>Our {service_name} Services in {city_name}</h2>
        <div class="services-grid">
'''
    
    for svc in service_data['services_list']:
        html += f'''            <div class="service-card">
                <h3>{svc}</h3>
            </div>
'''
    
    html += f'''        </div>
        
        <div class="why-us">
            <h2>Why Choose SCWS for {service_name} in {city_name}?</h2>
            <ul>
                <li>Licensed C-57 Well Contractor</li>
                <li>4.9★ Google Rating (120+ reviews)</li>
                <li>Family-owned, serving {city_name} since 1987</li>
                <li>Same-day service available</li>
                <li>Transparent pricing, no hidden fees</li>
                <li>Local team based in Ramona & Anza</li>
            </ul>
        </div>
        
        <div class="related-services">
            <h3>Other Well Services in {city_name}</h3>
            <div class="related-links">
'''
    
    for other_slug, other_data in SERVICES.items():
        if other_slug != service_slug:
            html += f'                <a href="/services/{city}/{other_slug}.html">{other_data["title"]}</a>\n'
    
    html += f'''            </div>
        </div>
    </div>
    
    <section class="cta-section">
        <h2>Ready to Get Started?</h2>
        <p>Call us now for a free estimate on {service_name.lower()} in {city_name}</p>
        <a href="tel:+17604408520" class="phone-big">(760) 440-8520</a>
    </section>
    
    <footer class="footer">
        <p>© 2026 Southern California Well Service | Licensed C-57 Contractor #1098473</p>
        <p><a href="/">Home</a> | <a href="/services/">Services</a> | <a href="/blog/">Resources</a> | <a href="/contact.html">Contact</a></p>
    </footer>
</body>
</html>'''
    
    output_path = city_dir / f"{service_slug}.html"
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path

def generate_city_index(city, output_dir):
    """Generate index page for a city listing all services."""
    city_name = title_case(city)
    city_dir = output_dir / city
    city_dir.mkdir(parents=True, exist_ok=True)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KR42LY3LF7"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-KR42LY3LF7');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Well services in {city_name}, CA. Well pump repair, drilling, water testing & more. Licensed C-57 contractor. Call (760) 440-8520.">
    <title>Well Services in {city_name}, CA | Southern California Well Service</title>
    <link rel="canonical" href="https://scwellservice.com/services/{city}/">
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "Southern California Well Service - {city_name}",
        "telephone": "(760) 440-8520",
        "areaServed": "{city_name}, CA"
    }}
    </script>
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #1a365d; color: white; padding: 1rem; }}
        .header-content {{ max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ color: white; text-decoration: none; font-size: 1.25rem; font-weight: bold; }}
        .phone {{ background: #ed8936; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .hero {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 3rem 1rem; text-align: center; }}
        .hero h1 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        .services-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin: 2rem 0; }}
        .service-card {{ background: white; border: 1px solid #e2e8f0; padding: 1.5rem; border-radius: 8px; text-decoration: none; color: #333; transition: box-shadow 0.2s; }}
        .service-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .service-card h2 {{ color: #1a365d; margin-bottom: 0.5rem; font-size: 1.25rem; }}
        .service-card .price {{ color: #ed8936; font-weight: bold; }}
        .cta-section {{ background: #ed8936; color: white; padding: 3rem 1rem; text-align: center; margin-top: 2rem; }}
        .cta-section .phone-big {{ font-size: 2rem; color: white; text-decoration: none; font-weight: bold; }}
        .footer {{ background: #1a365d; color: white; padding: 2rem 1rem; text-align: center; }}
        .footer a {{ color: #ed8936; }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">Southern California Well Service</a>
            <a href="tel:+17604408520" class="phone">📞 (760) 440-8520</a>
        </div>
    </header>
    
    <section class="hero">
        <h1>Well Services in {city_name}, CA</h1>
        <p>Licensed C-57 well contractor serving {city_name} and surrounding areas</p>
    </section>
    
    <div class="container">
        <div class="services-grid">
'''
    
    for slug, data in SERVICES.items():
        html += f'''            <a href="/services/{city}/{slug}.html" class="service-card">
                <h2>{data['title']}</h2>
                <p>{data['description']}</p>
                <p class="price">{data['price_range']}</p>
            </a>
'''
    
    html += f'''        </div>
    </div>
    
    <section class="cta-section">
        <h2>Need Well Service in {city_name}?</h2>
        <p>Call us now for a free estimate</p>
        <a href="tel:+17604408520" class="phone-big">(760) 440-8520</a>
    </section>
    
    <footer class="footer">
        <p>© 2026 Southern California Well Service | Licensed C-57 Contractor #1098473</p>
    </footer>
</body>
</html>'''
    
    output_path = city_dir / "index.html"
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path

def main():
    output_dir = Path("/Users/jarvis/clawd/scws-website/services")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_pages = 0
    
    for city in CITIES:
        # Generate city index
        generate_city_index(city, output_dir)
        total_pages += 1
        
        # Generate service pages
        for service_slug, service_data in SERVICES.items():
            generate_page(city, service_slug, service_data, output_dir)
            total_pages += 1
    
    print(f"Generated {total_pages} pages in {output_dir}")
    print(f"- {len(CITIES)} city index pages")
    print(f"- {len(CITIES) * len(SERVICES)} service pages")

if __name__ == "__main__":
    main()
