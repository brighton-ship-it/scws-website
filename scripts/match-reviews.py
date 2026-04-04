#!/usr/bin/env python3
import json, urllib.request, time, sys

with open('/Users/jarvis/clawd/jobber_credentials.json') as f:
    creds = json.load(f)
token = creds["access_token"]

def jobber(query, variables=None):
    payload = json.dumps({"query": query, "variables": variables or {}})
    req = urllib.request.Request("https://api.getjobber.com/api/graphql",
        data=payload.encode('utf-8'),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "X-JOBBER-GRAPHQL-VERSION": "2026-03-10"
        })
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())

with open('/tmp/five_star_reviews.json') as f:
    reviews = json.load(f)

query = """query($s: String!) {
    clients(searchTerm: $s, first: 5) {
        nodes {
            firstName lastName
            billingAddress { city }
            properties { address { city } }
        }
    }
}"""

matched = {}
unmatched = []

for rev in reviews:
    name = rev['name']
    parts = name.split()
    if len(parts) < 2:
        unmatched.append(name)
        continue

    try:
        r = jobber(query, {"s": name})
        clients = r.get('data', {}).get('clients', {}).get('nodes', [])

        found = False
        for c in clients:
            full = (c.get('firstName', '') + ' ' + c.get('lastName', '')).lower()
            if parts[-1].lower() in full:
                city = None
                props = c.get('properties', []) or []
                if props:
                    city = (props[0].get('address') or {}).get('city', '')
                if not city:
                    city = (c.get('billingAddress') or {}).get('city', '')
                if city:
                    city = city.strip().title()
                    matched.setdefault(city, []).append({
                        'name': rev['name'],
                        'text': rev['text'],
                        'date': rev['date']
                    })
                    found = True
                    print("OK " + name + " -> " + city, flush=True)
                else:
                    print("NO_CITY " + name, flush=True)
                    unmatched.append(name)
                    found = True
                break
        if not found:
            unmatched.append(name)
            print("MISS " + name, flush=True)
        time.sleep(0.3)
    except Exception as e:
        print("ERR " + name + ": " + str(e), flush=True)
        unmatched.append(name)

with open('/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json', 'w') as f:
    json.dump(matched, f, indent=2)

print("\n" + "=" * 50)
total = sum(len(v) for v in matched.values())
print("MATCHED: %d reviews across %d cities" % (total, len(matched)))
print("UNMATCHED: %d" % len(unmatched))
print("\nCities with testimonials:")
for city, revs in sorted(matched.items(), key=lambda x: -len(x[1])):
    print("  %s: %d reviews" % (city, len(revs)))
