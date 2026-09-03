#!/usr/bin/env python3
"""Enrich all 68 city service pages with unique local content."""

import os
import json
import re
from pathlib import Path

# Regional data for Southern California areas
REGIONS = {
    "san_diego_coast": {
        "cities": ["carlsbad", "encinitas", "oceanside", "la-mesa", "el-cajon", "santee", "spring-valley"],
        "water_table": "50-150 feet",
        "soil_type": "decomposed granite and sandy loam",
        "common_issues": "saltwater intrusion near coast, iron and manganese in groundwater",
        "aquifer": "San Diego Formation aquifer",
        "rainfall": "10-12 inches annually"
    },
    "san_diego_inland": {
        "cities": ["ramona", "poway", "escondido", "valley-center", "san-marcos", "vista", "fallbrook", "bonsall", "pauma-valley", "rainbow", "de-luz"],
        "water_table": "100-300 feet",
        "soil_type": "fractured granite bedrock with decomposed granite overlay",
        "common_issues": "low yield wells due to fractured rock, seasonal water table fluctuation",
        "aquifer": "fractured crystalline rock aquifer",
        "rainfall": "12-18 inches annually"
    },
    "san_diego_mountain": {
        "cities": ["julian", "santa-ysabel", "warner-springs", "ranchita", "borrego-springs", "cuyamaca", "descanso", "pine-valley", "alpine", "jamul", "campo", "jacumba", "boulevard", "lakeside"],
        "water_table": "150-400 feet",
        "soil_type": "granite bedrock with thin topsoil",
        "common_issues": "hard rock drilling, low-yield wells, seasonal springs",
        "aquifer": "mountain fractured rock system",
        "rainfall": "15-25 inches annually"
    },
    "rancho_santa_fe": {
        "cities": ["rancho-santa-fe"],
        "water_table": "100-200 feet",
        "soil_type": "decomposed granite with clay layers",
        "common_issues": "high-demand estates requiring high-capacity systems, water quality for landscaping",
        "aquifer": "San Dieguito watershed",
        "rainfall": "12-14 inches annually"
    },
    "temecula_valley": {
        "cities": ["temecula", "murrieta", "menifee", "wildomar", "lake-elsinore", "winchester", "sun-city", "perris"],
        "water_table": "80-200 feet", 
        "soil_type": "alluvial deposits with clay and sand layers",
        "common_issues": "high mineral content, hard water, vineyard irrigation demands",
        "aquifer": "Temecula Valley groundwater basin",
        "rainfall": "12-15 inches annually"
    },
    "hemet_san_jacinto": {
        "cities": ["hemet", "san-jacinto", "anza", "aguanga", "idyllwild"],
        "water_table": "100-300 feet",
        "soil_type": "alluvial fan deposits transitioning to granite in foothills",
        "common_issues": "agricultural well competition, seasonal water table drops, arsenic in some areas",
        "aquifer": "San Jacinto groundwater basin",
        "rainfall": "10-20 inches (varies by elevation)"
    },
    "coachella_valley": {
        "cities": ["palm-desert", "palm-springs", "rancho-mirage", "la-quinta", "indio", "cathedral-city"],
        "water_table": "100-250 feet",
        "soil_type": "desert alluvium with sand and gravel",
        "common_issues": "high mineral content, water softening needs, extreme heat affecting equipment",
        "aquifer": "Coachella Valley groundwater basin",
        "rainfall": "3-6 inches annually"
    },
    "morongo_basin": {
        "cities": ["morongo-valley", "yucca-valley", "joshua-tree", "landers"],
        "water_table": "200-500 feet",
        "soil_type": "desert alluvium over granite bedrock",
        "common_issues": "deep drilling required, low yield, high mineral content",
        "aquifer": "Morongo groundwater basin",
        "rainfall": "4-8 inches annually"
    },
    "high_desert": {
        "cities": ["apple-valley", "hesperia", "victorville", "oak-hills", "lucerne-valley", "wrightwood"],
        "water_table": "200-400 feet",
        "soil_type": "alluvial deposits with caliche layers",
        "common_issues": "deep wells required, fluoride in some areas, hard water",
        "aquifer": "Mojave River groundwater basin",
        "rainfall": "5-10 inches annually"
    },
    "mountain_communities": {
        "cities": ["big-bear-lake", "lake-arrowhead", "crestline", "yucaipa"],
        "water_table": "100-300 feet",
        "soil_type": "granite bedrock with forest soil overlay",
        "common_issues": "hard rock drilling, winterization needed, seasonal access challenges",
        "aquifer": "mountain fractured rock aquifer",
        "rainfall": "20-40 inches annually (including snow)"
    },
    "banning_beaumont": {
        "cities": ["banning", "beaumont"],
        "water_table": "150-300 feet",
        "soil_type": "alluvial fan deposits from San Gorgonio Pass",
        "common_issues": "high water demand from growth, groundwater level monitoring required",
        "aquifer": "San Gorgonio Pass groundwater basin",
        "rainfall": "12-18 inches annually"
    }
}

# Service types we need to enrich
SERVICES = [
    "well-pump-repair",
    "well-drilling", 
    "pressure-tank",
    "water-treatment",
    "booster-pump",
    "well-inspection",
    "emergency-well-service",
    "water-testing"
]

def get_region_for_city(city):
    """Find which region a city belongs to."""
    for region_name, data in REGIONS.items():
        if city in data["cities"]:
            return region_name, data
    return None, None

def title_case(slug):
    """Convert slug to title case."""
    return slug.replace('-', ' ').title()

def generate_local_content(city, region_data, service):
    """Generate unique local content for a city+service combination."""
    city_name = title_case(city)
    
    # Base local info section
    local_info = f"""
        <div class="local-info" style="background: #f0f9ff; padding: 1.5rem; border-radius: 8px; margin: 2rem 0; border-left: 4px solid #0ea5e9;">
            <h3 style="color: #0369a1; margin-bottom: 1rem;">Well Conditions in {city_name}</h3>
            <p>In {city_name}, wells typically reach depths of <strong>{region_data['water_table']}</strong> to access the {region_data['aquifer']}. The local geology consists of {region_data['soil_type']}, which affects drilling methods and well performance.</p>
            <p><strong>Common issues we see in {city_name}:</strong> {region_data['common_issues']}. With {region_data['rainfall']} rainfall, proper well maintenance is essential for reliable water supply.</p>
        </div>
"""
    
    # Service-specific local content
    service_content = {
        "well-pump-repair": f"""
            <p>Our {city_name} well pump repair team understands the unique demands of the {region_data['aquifer']}. Wells in this area often require pumps rated for depths of {region_data['water_table']}, and we stock common replacement parts locally for faster service.</p>
""",
        "well-drilling": f"""
            <p>Drilling in {city_name} requires specialized knowledge of local geology. The {region_data['soil_type']} presents specific challenges, and we use the right drilling techniques to ensure a productive well. Our experience with the {region_data['aquifer']} helps us site wells for optimal yield.</p>
""",
        "pressure-tank": f"""
            <p>Homes in {city_name} often benefit from properly sized pressure tanks to handle the {region_data['water_table']} well depths common in this area. We recommend tanks that accommodate the specific flow rates typical of {region_data['aquifer']} wells.</p>
""",
        "water-treatment": f"""
            <p>{city_name} well water often requires treatment for {region_data['common_issues'].split(',')[0]}. We design treatment systems specifically for the water chemistry found in the {region_data['aquifer']}, ensuring clean, safe water for your home.</p>
""",
        "booster-pump": f"""
            <p>Properties in {city_name} with longer distances from well to home, or multi-story buildings, benefit from booster pump systems. We size systems appropriately for the typical well yields in the {region_data['aquifer']}.</p>
""",
        "well-inspection": f"""
            <p>Well inspections in {city_name} focus on the specific conditions of the {region_data['aquifer']}. We check for issues common to this area including {region_data['common_issues']}, ensuring your well is performing optimally.</p>
""",
        "emergency-well-service": f"""
            <p>When {city_name} residents lose water, we respond quickly. Our technicians are familiar with the {region_data['aquifer']} and common failure points in wells of {region_data['water_table']} depth. We carry parts for the most common repairs in this area.</p>
""",
        "water-testing": f"""
            <p>Water testing in {city_name} focuses on contaminants common to the {region_data['aquifer']}, including {region_data['common_issues'].split(',')[0]}. We recommend annual testing to monitor for changes in water quality.</p>
"""
    }
    
    return local_info + service_content.get(service, "")

def enrich_page(city, service, services_dir):
    """Add local content to a service page."""
    page_path = services_dir / city / f"{service}.html"
    
    if not page_path.exists():
        return False, f"Page not found: {page_path}"
    
    region_name, region_data = get_region_for_city(city)
    if not region_data:
        return False, f"No region data for {city}"
    
    content = page_path.read_text()
    
    # Check if already enriched
    if 'class="local-info"' in content:
        return False, "Already enriched"
    
    # Generate local content
    local_content = generate_local_content(city, region_data, service)
    
    # Insert after the price box
    if '<div class="price-box">' in content:
        content = content.replace(
            '</div>\n        \n        <h2>Our',
            '</div>\n' + local_content + '\n        <h2>Our',
            1
        )
    
    page_path.write_text(content)
    return True, "Enriched"

def main():
    services_dir = Path("/Users/jarvis/clawd/scws-website/services")
    
    # Get all cities
    cities = [d.name for d in services_dir.iterdir() if d.is_dir() and d.name != "index.html"]
    
    enriched = 0
    skipped = 0
    errors = 0
    
    for city in sorted(cities):
        region_name, region_data = get_region_for_city(city)
        if not region_data:
            print(f"⚠️  {city}: No region data - skipping")
            skipped += 1
            continue
            
        for service in SERVICES:
            success, msg = enrich_page(city, service, services_dir)
            if success:
                enriched += 1
            elif "Already" in msg:
                skipped += 1
            else:
                errors += 1
                print(f"❌ {city}/{service}: {msg}")
    
    print(f"\n{'='*50}")
    print(f"✅ Enriched: {enriched} pages")
    print(f"⏭️  Skipped: {skipped} pages")
    print(f"❌ Errors: {errors} pages")
    print(f"{'='*50}")

if __name__ == "__main__":
    raise SystemExit(
        "Disabled: do not generate or enrich new city×topic factory pages."
    )
    main()
