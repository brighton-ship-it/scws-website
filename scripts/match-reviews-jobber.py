#!/usr/bin/env python3
import json, urllib.request, time, sys, re

# Load Jobber credentials
with open('/Users/jarvis/clawd/jobber_credentials.json') as f:
    creds = json.load(f)
token = creds['access_token']

# Load all reviews
with open('/Users/jarvis/clawd/scws-gmb/reviews-all.json') as f:
    data = json.load(f)

# Extract 5-star reviews with text
reviews = []
for loc in data:
    gmb = loc.get('address', {}).get('locality', 'Unknown')
    for r in loc.get('reviews', []):
        if r.get('starRating') == 'FIVE' and r.get('comment'):
            reviews.append({
                'name': r['reviewer']['displayName'],
                'text': r['comment'],
                'date': r.get('createTime', '')[:10],
                'gmb_location': gmb
            })

print(f"Total 5-star reviews with text: {len(reviews)}")

# All known cities
ALL_CITIES = [
    'Ramona', 'Julian', 'Alpine', 'Escondido', 'Valley Center', 'Poway',
    'Lakeside', 'El Cajon', 'Santee', 'Jamul', 'Descanso', 'Pine Valley',
    'Boulevard', 'Campo', 'Potrero', 'Mount Laguna', 'Wynola', 'Santa Ysabel',
    'Warner Springs', 'Borrego Springs', 'Fallbrook', 'Bonsall', 'Pauma Valley',
    'San Diego', 'Oceanside', 'Vista', 'Carlsbad', 'Encinitas', 'La Mesa',
    'Anza', 'Aguanga', 'Temecula', 'Murrieta', 'Hemet', 'San Jacinto',
    'Idyllwild', 'Mountain Center', 'Palm Desert', 'Menifee', 'Wildomar',
    'Lake Elsinore', 'Winchester', 'French Valley', 'Sage', 'Garner Valley',
    'Pinyon Pines', 'Cahuilla', 'De Luz', 'Riverside', 'Corona', 'Perris',
    'Sun City', 'Beaumont', 'Banning', 'Nuevo', 'Homeland', 'Romoland',
    'Idyllwild-Pine Cove', 'Spring Valley', 'Lemon Grove', 'Bonita',
    'Rancho Bernardo', 'San Marcos', 'Rancho Santa Fe', 'Del Mar',
    'Solana Beach', 'Pala', 'Tecate'
]

def extract_city_from_text(text):
    if not text:
        return None
    lower = text.lower()
    for city in ALL_CITIES:
        if city.lower() in lower:
            return city
    return None

def extract_city_from_address(street1, city_field):
    """Extract city from Jobber address fields. City is sometimes embedded in street1."""
    if city_field and city_field.strip():
        return city_field.strip()
    if not street1:
        return None
    # Try to parse "123 Main St, City, State ZIP" pattern
    parts = street1.split(',')
    if len(parts) >= 2:
        # Check each part for a known city
        for part in parts[1:]:
            clean = part.strip()
            # Remove state/zip
            clean = re.sub(r'\b(California|CA)\b', '', clean, flags=re.IGNORECASE).strip()
            clean = re.sub(r'\b\d{5}(-\d{4})?\b', '', clean).strip()
            if clean:
                # Check against known cities
                for known in ALL_CITIES:
                    if clean.lower() == known.lower():
                        return known
                # Return as-is if looks like a city name
                if len(clean) > 2 and not clean.isdigit():
                    return clean
    return None

def query_jobber(name):
    clean = name.split('(')[0].strip()
    # Remove special chars, #, numbers
    clean = re.sub(r'[#\d]', '', clean).strip()
    if len(clean) < 2:
        return None

    query = """query SearchClients($search: String!) {
      clients(searchTerm: $search, first: 3) {
        nodes {
          firstName
          lastName
          billingAddress {
            city
            street1
          }
        }
      }
    }"""

    payload = json.dumps({
        'query': query,
        'variables': {'search': clean}
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.getjobber.com/api/graphql',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-JOBBER-GRAPHQL-VERSION': '2026-03-10'
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            nodes = result.get('data', {}).get('clients', {}).get('nodes', [])
            if not nodes:
                return None
            # Try to match name more closely
            name_lower = clean.lower().split()
            for client in nodes:
                fn = (client.get('firstName') or '').lower()
                ln = (client.get('lastName') or '').lower()
                # Check if first or last name matches
                if any(n in [fn, ln] for n in name_lower) or fn in clean.lower():
                    addr = client.get('billingAddress', {})
                    city = extract_city_from_address(
                        addr.get('street1', ''),
                        addr.get('city', '')
                    )
                    if city:
                        return city
            # Fallback: just use first result if we got one
            if nodes:
                addr = nodes[0].get('billingAddress', {})
                city = extract_city_from_address(
                    addr.get('street1', ''),
                    addr.get('city', '')
                )
                return city
            return None
    except Exception as e:
        print(f"  API error for {name}: {e}", file=sys.stderr)
        return None

# Process all reviews
results = {}
stats = {'total': 0, 'matched': 0, 'text_match': 0, 'jobber_match': 0, 'gmb_fallback': 0}

for i, rev in enumerate(reviews):
    stats['total'] += 1
    city = None
    match_type = None

    # 1. Check text for city mention
    city = extract_city_from_text(rev['text'])
    if city:
        match_type = 'text'
        stats['text_match'] += 1

    # 2. Query Jobber
    if not city:
        time.sleep(0.2)
        city = query_jobber(rev['name'])
        if city:
            match_type = 'jobber'
            stats['jobber_match'] += 1

    # 3. GMB fallback
    if not city:
        gmb = rev['gmb_location'].lower()
        if 'anza' in gmb:
            city = 'Anza'
        elif 'ramona' in gmb:
            city = 'Ramona'
        if city:
            match_type = 'gmb'
            stats['gmb_fallback'] += 1

    if city:
        stats['matched'] += 1
        if city not in results:
            results[city] = []
        results[city].append({
            'name': rev['name'],
            'text': rev['text'],
            'date': rev['date']
        })
        print(f"  [{match_type:6s}] {rev['name']:30s} -> {city}")
    else:
        print(f"  [MISS  ] {rev['name']:30s} -> ???")

# Sort by review count
sorted_results = dict(sorted(results.items(), key=lambda x: -len(x[1])))

# Save
output_path = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json'
with open(output_path, 'w') as f:
    json.dump(sorted_results, f, indent=2)

print(f"\n{'='*50}")
print(f"RESULTS:")
print(f"  Total 5-star reviews with text: {stats['total']}")
print(f"  Matched to a city: {stats['matched']}")
print(f"    - By text mention: {stats['text_match']}")
print(f"    - By Jobber client lookup: {stats['jobber_match']}")
print(f"    - By GMB location fallback: {stats['gmb_fallback']}")
print(f"\nCities with testimonials ({len(sorted_results)} cities):")
for city, revs in sorted_results.items():
    print(f"  {city}: {len(revs)} reviews")
print(f"\nSaved to: {output_path}")
