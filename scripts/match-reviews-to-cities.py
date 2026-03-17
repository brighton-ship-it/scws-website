#!/usr/bin/env python3
"""Match Google reviews to Jobber clients to get cities."""
import json, requests, time, sys

with open('/Users/jarvis/clawd/jobber_credentials.json') as f:
    creds = json.load(f)

TOKEN = creds['access_token']
API = 'https://api.getjobber.com/api/graphql'
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'X-JOBBER-GRAPHQL-VERSION': '2025-01-20'
}

def search_client(name):
    query = '{clients(searchTerm: "%s", first: 5) { nodes { firstName lastName billingAddress { city } properties { address { city } } } } }' % name.replace('"', '\\"')
    r = requests.post(API, json={'query': query}, headers=HEADERS, timeout=15)
    if r.status_code == 200:
        data = r.json().get('data', {})
        return data.get('clients', {}).get('nodes', []) if data else []
    return []

# Load reviews
with open('/Users/jarvis/clawd/scws-gmb/reviews.json') as f:
    data = json.load(f)

five_star = []
for loc in data:
    for r in loc.get('reviews', []):
        if r.get('starRating') == 'FIVE' and r.get('comment'):
            five_star.append({
                'name': r.get('reviewer', {}).get('displayName', ''),
                'text': r.get('comment', ''),
                'date': r.get('createTime', '')[:10],
            })

print(f"Processing {len(five_star)} 5-star reviews with comments...", flush=True)

SKIP = {'Phoenix', 'Bob Nunya', 'Ricardo', 'Maggie', 'Nancy', 'fromelkriver',
        'Sand to Sea Videos', 'Capital & Influence Inc', 'Birdsong Retreat',
        "Ledezma #6", "George's Perez", "Nadia S", "Maria M", "Sabrina N", 
        "Jarrod P", "sister haero"}

matched = {}
unmatched = []

for i, review in enumerate(five_star):
    name = review['name']
    if name in SKIP:
        print(f"  [{i+1}] SKIP {name}", flush=True)
        unmatched.append(review)
        continue
    
    search_name = name.split('(')[0].strip()
    search_name = search_name.replace("Keep n' up with ", "")
    
    clients = search_client(search_name)
    time.sleep(0.25)
    
    city = None
    if clients:
        c = clients[0]
        props = c.get('properties', [])
        if props and props[0].get('address', {}).get('city'):
            city = props[0]['address']['city']
        elif c.get('billingAddress', {}).get('city'):
            city = c['billingAddress']['city']
    
    if city:
        city = city.strip().title()
        matched.setdefault(city, []).append({
            'name': review['name'],
            'text': review['text'],
            'date': review['date']
        })
        print(f"  [{i+1}] ✅ {name} → {city}", flush=True)
    else:
        unmatched.append(review)
        print(f"  [{i+1}] ❌ {name}", flush=True)

output_path = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json'
with open(output_path, 'w') as f:
    json.dump(matched, f, indent=2)

print(f"\n{'='*50}", flush=True)
print(f"Matched: {sum(len(v) for v in matched.values())} reviews", flush=True)
print(f"Unmatched: {len(unmatched)} reviews", flush=True)
print(f"Cities: {len(matched)}", flush=True)
print(f"\nCities with testimonials:", flush=True)
for city, reviews in sorted(matched.items(), key=lambda x: -len(x[1])):
    print(f"  {city}: {len(reviews)} reviews", flush=True)
