#!/usr/bin/env python3
"""Create San Bernardino County city pages served by Anza office."""

import os
from pathlib import Path

services_dir = Path("/Users/jarvis/clawd/scws-website/services")

# San Bernardino cities to add (served from Anza office)
new_cities = {
    "san-bernardino": {"name": "San Bernardino", "county": "San Bernardino"},
    "redlands": {"name": "Redlands", "county": "San Bernardino"},
    "highland": {"name": "Highland", "county": "San Bernardino"},
    "fontana": {"name": "Fontana", "county": "San Bernardino"},
    "rancho-cucamonga": {"name": "Rancho Cucamonga", "county": "San Bernardino"},
    "ontario": {"name": "Ontario", "county": "San Bernardino"},
    "adelanto": {"name": "Adelanto", "county": "San Bernardino"},
    "barstow": {"name": "Barstow", "county": "San Bernardino"},
    "running-springs": {"name": "Running Springs", "county": "San Bernardino"},
    "rialto": {"name": "Rialto", "county": "San Bernardino"},
    "upland": {"name": "Upland", "county": "San Bernardino"},
    "colton": {"name": "Colton", "county": "San Bernardino"},
    "loma-linda": {"name": "Loma Linda", "county": "San Bernardino"},
    "twentynine-palms": {"name": "Twentynine Palms", "county": "San Bernardino"},
    "joshua-tree": {"name": "Joshua Tree", "county": "San Bernardino"},
    "yucca-valley": {"name": "Yucca Valley", "county": "San Bernardino"},
}

services = [
    ("well-pump-repair", "Well Pump Repair"),
    ("well-drilling", "Well Drilling"),
    ("water-testing", "Water Testing"),
    ("water-treatment", "Water Treatment"),
    ("pressure-tank", "Pressure Tank Service"),
    ("well-inspection", "Well Inspection"),
    ("emergency-well-service", "Emergency Well Service"),
    ("booster-pump", "Booster Pump Service"),
]

def create_city_index(city_slug, city_info):
    city_name = city_info["name"]
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Well Service {city_name} CA | Pump Repair & Drilling | SCWS</title>
    <meta name="description" content="Professional well services in {city_name}, CA. Well pump repair, drilling, water testing & treatment. Served by our Anza office. Call (760) 463-0493.">
    <link rel="canonical" href="https://scwellservice.com/services/{city_slug}/">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-MBHM6GR0XS"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","G-MBHM6GR0XS");</script>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-blue-900 text-white py-4">
        <div class="max-w-6xl mx-auto px-4 flex justify-between items-center">
            <a href="/" class="text-2xl font-bold">SC Well Service</a>
            <a href="tel:7604630493" class="bg-red-600 px-4 py-2 rounded font-semibold hover:bg-red-700">(760) 463-0493</a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-12">
        <h1 class="text-4xl font-bold text-blue-900 mb-6">Well Services in {city_name}, California</h1>
        
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <p class="text-lg text-gray-700 mb-4">
                Southern California Well Service provides comprehensive well services to {city_name} and surrounding {city_info["county"]} County areas. 
                Our <strong>Anza office</strong> serves this region with fast response times and local expertise.
            </p>
            <p class="text-gray-600 mb-4">
                With 4.9★ Google rating and decades of experience, we're the trusted choice for residential and commercial well owners in {city_name}.
            </p>
            <div class="bg-blue-50 border-l-4 border-blue-600 p-4">
                <p class="font-semibold text-blue-900">📍 Served by: Anza Office</p>
                <p class="text-gray-600">57174 US Highway 79, Anza, CA 92539</p>
            </div>
        </div>

        <h2 class="text-2xl font-bold text-gray-800 mb-4">Our Services in {city_name}</h2>
        <div class="grid md:grid-cols-2 gap-4 mb-8">
            <a href="well-pump-repair.html" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition">
                <h3 class="font-bold text-blue-900">Well Pump Repair</h3>
                <p class="text-gray-600 text-sm">Diagnose and fix pump problems fast</p>
            </a>
            <a href="well-drilling.html" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition">
                <h3 class="font-bold text-blue-900">Well Drilling</h3>
                <p class="text-gray-600 text-sm">New wells for homes and businesses</p>
            </a>
            <a href="water-testing.html" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition">
                <h3 class="font-bold text-blue-900">Water Testing</h3>
                <p class="text-gray-600 text-sm">Comprehensive water quality analysis</p>
            </a>
            <a href="water-treatment.html" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition">
                <h3 class="font-bold text-blue-900">Water Treatment</h3>
                <p class="text-gray-600 text-sm">Filtration and softening systems</p>
            </a>
            <a href="pressure-tank.html" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition">
                <h3 class="font-bold text-blue-900">Pressure Tank Service</h3>
                <p class="text-gray-600 text-sm">Repair and replacement</p>
            </a>
            <a href="emergency-well-service.html" class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition">
                <h3 class="font-bold text-blue-900">Emergency Service</h3>
                <p class="text-gray-600 text-sm">24/7 urgent well repairs</p>
            </a>
        </div>

        <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h3 class="text-xl font-bold text-red-800 mb-2">Need Well Service in {city_name}?</h3>
            <p class="text-gray-700 mb-4">Call now for fast, professional service from our Anza team.</p>
            <a href="tel:7604630493" class="inline-block bg-red-600 text-white font-bold py-3 px-8 rounded-lg hover:bg-red-700 transition">
                📞 (760) 463-0493
            </a>
        </div>
    </main>

    <footer class="bg-gray-800 text-white py-8 mt-12">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <p>&copy; 2026 Southern California Well Service. Licensed C-57 Contractor.</p>
        </div>
    </footer>
</body>
</html>'''

def create_service_page(city_slug, city_info, service_slug, service_name):
    city_name = city_info["name"]
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{service_name} {city_name} CA | Licensed Pros | SCWS</title>
    <meta name="description" content="{service_name} in {city_name}, CA. Fast, reliable service from our Anza office. Licensed C-57, 4.9★ rated. Call (760) 463-0493.">
    <link rel="canonical" href="https://scwellservice.com/services/{city_slug}/{service_slug}.html">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-MBHM6GR0XS"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","G-MBHM6GR0XS");</script>
</head>
<body class="bg-gray-50">
    <header class="bg-blue-900 text-white py-4">
        <div class="max-w-6xl mx-auto px-4 flex justify-between items-center">
            <a href="/" class="text-2xl font-bold">SC Well Service</a>
            <a href="tel:7604630493" class="bg-red-600 px-4 py-2 rounded font-semibold hover:bg-red-700">(760) 463-0493</a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-12">
        <nav class="text-sm text-gray-500 mb-4">
            <a href="/services/{city_slug}/" class="hover:text-blue-600">{city_name}</a> &raquo; {service_name}
        </nav>
        
        <h1 class="text-4xl font-bold text-blue-900 mb-6">{service_name} in {city_name}, CA</h1>
        
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <p class="text-lg text-gray-700 mb-4">
                Need {service_name.lower()} in {city_name}? Southern California Well Service provides expert well services 
                throughout {city_info["county"]} County from our <strong>Anza office</strong>.
            </p>
            
            <div class="bg-green-50 border-l-4 border-green-600 p-4 mb-4">
                <p class="font-semibold text-green-800">✓ Licensed C-57 Water Well Contractor</p>
                <p class="font-semibold text-green-800">✓ 4.9★ Google Rating</p>
                <p class="font-semibold text-green-800">✓ Fast Response from Anza Office</p>
            </div>

            <div class="bg-blue-50 border-l-4 border-blue-600 p-4">
                <p class="font-semibold text-blue-900">📍 Served by: Anza Office</p>
                <p class="text-gray-600">57174 US Highway 79, Anza, CA 92539</p>
            </div>
        </div>

        <h2 class="text-2xl font-bold text-gray-800 mb-4">Why Choose SCWS for {service_name}?</h2>
        <ul class="list-disc list-inside text-gray-700 mb-8 space-y-2">
            <li>Decades of experience in {city_info["county"]} County</li>
            <li>Fully licensed and insured</li>
            <li>Transparent pricing - no surprises</li>
            <li>Local team that knows the area</li>
            <li>Emergency service available</li>
        </ul>

        <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h3 class="text-xl font-bold text-red-800 mb-2">Get {service_name} in {city_name}</h3>
            <p class="text-gray-700 mb-4">Call now for a free estimate.</p>
            <a href="tel:7604630493" class="inline-block bg-red-600 text-white font-bold py-3 px-8 rounded-lg hover:bg-red-700 transition">
                📞 (760) 463-0493
            </a>
        </div>
        
        <div class="mt-8">
            <a href="/services/{city_slug}/" class="text-blue-600 hover:underline">← All {city_name} Well Services</a>
        </div>
    </main>

    <footer class="bg-gray-800 text-white py-8 mt-12">
        <div class="max-w-4xl mx-auto px-4 text-center">
            <p>&copy; 2026 Southern California Well Service. Licensed C-57 Contractor.</p>
        </div>
    </footer>
</body>
</html>'''

# Create pages
created = 0
for city_slug, city_info in new_cities.items():
    city_dir = services_dir / city_slug
    
    if city_dir.exists():
        print(f"⏭️  Skipping {city_info['name']} (already exists)")
        continue
    
    city_dir.mkdir(parents=True)
    
    # Create index
    with open(city_dir / "index.html", "w") as f:
        f.write(create_city_index(city_slug, city_info))
    
    # Create service pages
    for service_slug, service_name in services:
        with open(city_dir / f"{service_slug}.html", "w") as f:
            f.write(create_service_page(city_slug, city_info, service_slug, service_name))
    
    print(f"✅ Created {city_info['name']} ({len(services) + 1} pages)")
    created += 1

print(f"\n✅ Created {created} new city directories with {created * (len(services) + 1)} total pages")
