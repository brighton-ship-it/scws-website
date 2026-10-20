#!/usr/bin/env python3
"""Build the SCWS job map ("check-in" pins) from recent-work/projects.json.

Writes:
  recent-work/job-map.json      town-level pins (no names, no street addresses)
  recent-work/map/index.html    map page (static ItemList JSON-LD + crawlable list)
  services/ramona|anza/index.html  refreshes ONLY the block between
                                <!-- JOB_MAP_HUB_START --> and <!-- JOB_MAP_HUB_END -->

--geocode looks up towns missing from recent-work/city-coords.json (Nominatim, town centroid,
rounded to 2 decimals). Safe to re-run; output is deterministic.
"""
import hashlib, html, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
FIX = {'desert hot sprongs': 'Desert Hot Springs', 'desert hot springs': 'Desert Hot Springs', 'delzura': 'Dulzura',
       'hamul': 'Jamul', 'idyllwild-pine cove': 'Idyllwild'}
SKIP = {'southern california', 'san diego county', 'riverside county', 'owonga', 'marietta'}
SITE = 'https://scwellservice.com'


def norm(s):
    s = re.sub(r'\s*\(.*\)', '', s or '').strip()
    k = s.lower()
    if not k or k in SKIP:
        return None
    return FIX.get(k, s.title() if s.islower() else s)


def jitter(key):
    h = hashlib.sha1(key.encode()).digest()
    return ((h[0] / 255) - 0.5) * 0.024, ((h[1] / 255) - 0.5) * 0.024  # about +/-1.3 km, stays town-level


def geocode(name):
    q = urllib.parse.urlencode({'q': f'{name}, California, USA', 'format': 'json', 'limit': 1, 'countrycodes': 'us'})
    r = urllib.request.Request('https://nominatim.openstreetmap.org/search?' + q,
                               headers={'User-Agent': 'scwellservice-jobmap/1.0 (scwellservice.com)'})
    d = json.load(urllib.request.urlopen(r, timeout=20))
    time.sleep(1.1)
    if not d:
        return None
    lat, lng = round(float(d[0]['lat']), 2), round(float(d[0]['lon']), 2)
    if not (32.5 < lat < 35.6 and -118.6 < lng < -114.3):  # SoCal service region sanity box
        return None
    return [lat, lng]


def paperwork():
    s = set()
    for line in open(P('recent-work', 'paperwork-photos.txt')):
        line = line.strip()
        if line and not line.startswith('#'):
            s.add(line)
    return s


def build_pins(do_geo):
    projects = json.load(open(P('recent-work', 'projects.json')))['projects']
    cpath = P('recent-work', 'city-coords.json')
    cc = json.load(open(cpath))
    towns = cc['towns']
    bad = paperwork()
    missing = sorted({t for p in projects if (t := norm(p['location'])) and t not in towns})
    if missing and do_geo:
        for t in missing:
            try:
                g = geocode(t)
            except Exception as e:  # network hiccup: skip, try next run
                print('geocode error', t, e, file=sys.stderr)
                g = None
            if g:
                towns[t] = g
        cc['towns'] = dict(sorted(towns.items()))
        json.dump(cc, open(cpath, 'w'), indent=1, ensure_ascii=False)
        missing = [t for t in missing if t not in towns]
    pins = []
    for p in projects:
        t = norm(p['location'])
        if not t or t not in towns or not os.path.exists(P('recent-work', p['slug'] + '.html')):
            continue
        dy, dx = jitter(p['id'])
        photo = next((ph['file'] for ph in p.get('photos') or [] if ph['file'] not in bad
                      and os.path.exists(P('images', 'recent-work', ph['file']))), None)
        pins.append({'id': p['id'], 'slug': p['slug'], 'title': p['title'], 'town': t,
                     'lat': round(towns[t][0] + dy, 3), 'lng': round(towns[t][1] + dx, 3),
                     'date': p['date'], 'dateLabel': p['dateLabel'], 'category': p['categoryLabel'],
                     'photo': photo})
    pins.sort(key=lambda x: (x['date'], x['id']), reverse=True)
    if missing:
        print('towns without coords (not pinned):', ', '.join(missing), file=sys.stderr)
    return pins


HEAD_TMPL = P('recent-work', 'areas', 'ramona.html')


def page(pins):
    src = open(HEAD_TMPL).read()
    head_scripts = src[src.index('<head>') + 6:src.index('<meta charset')]
    body_top = src[src.index('<body'):src.index('<div class="bg-white border-b">')]
    footer = src[src.index('<footer class="bg-gray-900'):src.index('<script>\n    function openLightbox')]
    n, towns = len(pins), len({p['town'] for p in pins})
    title = 'Well Job Map: Completed Well Jobs Across SoCal | SCWS'
    desc = (f'{n} completed well pump, tank, and well jobs from Southern California Well Service, pinned by town. '
            'Field photos from Ramona, Anza, Julian, Aguanga, and the backcountry.')
    latest = pins[:60]
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'SCWS well job map',
          'url': SITE + '/recent-work/map/', 'description': desc,
          'isPartOf': {'@type': 'WebSite', 'url': SITE + '/'},
          'about': {'@type': 'LocalBusiness', '@id': SITE + '/#business', 'name': 'Southern California Well Service',
                    'url': SITE + '/', 'telephone': '+1-760-440-8520'},
          'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(latest), 'itemListElement': [
              {'@type': 'ListItem', 'position': i + 1, 'url': f"{SITE}/recent-work/{p['slug']}.html",
               'name': f"{p['title']} in {p['town']}"} for i, p in enumerate(latest)]}}
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Recent Work', 'item': SITE + '/recent-work/'},
        {'@type': 'ListItem', 'position': 3, 'name': 'Job map', 'item': SITE + '/recent-work/map/'}]}
    e = html.escape
    items = '\n'.join(f'<li><a href="/recent-work/{e(p["slug"])}.html">{e(p["title"])}</a> · {e(p["town"])} · {e(p["dateLabel"])}</li>' for p in latest)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>{head_scripts}<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0, viewport-fit=cover" name="viewport"/>
<title>{e(title)}</title>
<meta content="{e(desc)}" name="description"/>
<link href="{SITE}/recent-work/map/" rel="canonical"/>
<meta content="website" property="og:type"/>
<meta content="{SITE}/recent-work/map/" property="og:url"/>
<meta content="{e(title)}" property="og:title"/>
<meta content="{e(desc)}" property="og:description"/>
<link href="/css/styles.css" rel="stylesheet"/>
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumbs)}</script>
<style>
.jm-wrap{{max-width:1100px;margin:0 auto;padding:24px 16px 96px}}
.jm-wrap h1{{font-size:1.9rem;font-weight:700;color:#1a365d;margin:0 0 8px}}
.scws-job-map{{height:70vh;min-height:420px;border-radius:10px;border:1px solid #e2e8f0;z-index:0}}
.jm-list{{columns:1;margin-top:18px;padding-left:18px}} @media(min-width:768px){{.jm-list{{columns:2}}}}
.jm-list li{{margin:4px 0;break-inside:avoid}}
</style>
</head>
{body_top}<div class="bg-white border-b">
<div class="max-w-7xl mx-auto px-4 py-3 text-sm text-gray-500">
<a class="hover:text-accent" href="/">Home</a> · <a class="hover:text-accent" href="/recent-work/">Recent Work</a> · <span class="text-gray-700">Job map</span>
</div>
</div>
<main class="jm-wrap">
<h1>Well job map</h1>
<p>Every red dot is a finished SCWS job: pump pulls, pressure tanks, switches, boosters, and diagnostics across {towns} towns. Pins are placed by town, never at a customer's house. Tap a pin for the field photo and write-up.</p>
<p class="scws-job-map-count" style="font-weight:600">{n} completed jobs on the map</p>
<div class="scws-job-map" data-center="33.25,-116.85" data-zoom="9"></div>
<p style="margin-top:14px">Shops: <a href="/services/ramona/">Ramona well pump repair</a> · <a href="/services/anza/">Anza well pump repair</a> · <a href="/recent-work/">All recent work</a></p>
<h2 style="font-size:1.3rem;font-weight:700;margin-top:28px">Latest jobs</h2>
<ul class="jm-list">
{items}
</ul>
</main>
{footer}<script src="/js/job-map.js" defer></script>
</body>
</html>
'''


HUBS = {
    'ramona': dict(center='33.04,-116.87', radius=40, zoom=10, shop='Ramona', label='Ramona',
                   towns=[('julian', 'Julian'), ('santa-ysabel', 'Santa Ysabel'), ('ranchita', 'Ranchita'),
                          ('poway', 'Poway'), ('escondido', 'Escondido'), ('valley-center', 'Valley Center'),
                          ('lakeside', 'Lakeside'), ('el-cajon', 'El Cajon'), ('alpine', 'Alpine'),
                          ('santee', 'Santee'), ('jamul', 'Jamul'), ('pine-valley', 'Pine Valley')]),
    'anza': dict(center='33.56,-116.67', radius=45, zoom=10, shop='Anza', label='Anza',
                 towns=[('aguanga', 'Aguanga'), ('mountain-center', 'Mountain Center'), ('idyllwild', 'Idyllwild'),
                        ('warner-springs', 'Warner Springs'), ('hemet', 'Hemet'), ('san-jacinto', 'San Jacinto'),
                        ('winchester', 'Winchester'), ('temecula', 'Temecula'), ('murrieta', 'Murrieta'),
                        ('menifee', 'Menifee')]),
}


def money(x):
    return '${:,.0f}'.format(round(x / 100) * 100)


def hub_block(key, pins):
    h = HUBS[key]
    st = json.load(open(P('data', 'pump-replacement-price-stats.json')))
    c = [float(v) for v in h['center'].split(',')]
    import math
    near = sum(1 for p in pins if math.dist((p['lat'], p['lng'] * math.cos(math.radians(c[0]))),
                                            (c[0], c[1] * math.cos(math.radians(c[0])))) * 111 <= h['radius'])
    if key == 'ramona':
        r = st['ramona']
        local = (f"<li>Ramona itself: our last {r['n']} pump replacement invoices ran {money(r['min'])} to {money(r['max'])}.</li>")
    else:
        r = st['anza_area']
        local = (f"<li>Anza-shop side (Aguanga, Winchester, Hemet, Temecula valley): {r['n']} invoices, middle half "
                 f"{money(r['p25'])} to {money(r['p75'])}. Deeper settings and bigger pumps push this side higher.</li>")
    links = '\n'.join(f'<li><a href="/services/{s}/">Well pump repair in {t}</a></li>' for s, t in h['towns'])
    return f'''<!-- JOB_MAP_HUB_START -->
<section class="hub-job-map" id="job-map" style="max-width:1100px;margin:32px auto;padding:0 16px">
<h2>{h['label']}-area jobs on the map</h2>
<p>Each pin is a finished job out of the {h['shop']} shop, placed by town (never a customer's address). Tap a pin for the field photo and what we fixed.</p>
<p class="scws-job-map-count" style="font-weight:600">{near} completed jobs on the map</p>
<div class="scws-job-map" data-center="{h['center']}" data-radius-km="{h['radius']}" data-zoom="{h['zoom']}" style="height:420px;border-radius:10px;border:1px solid #e2e8f0;z-index:0"></div>
<p><a href="/recent-work/map/">Open the full job map →</a></p>
</section>
<section class="hub-pump-prices" id="pump-replacement-prices" style="max-width:1100px;margin:32px auto;padding:0 16px">
<h2>What a well pump replacement really costs ({h['label']} area)</h2>
<p>These are our own numbers: {st['n']} submersible pump and motor replacement invoices from {st['first'][:7].replace('-', '/')} to {st['last'][:7].replace('-', '/')}, tax included. Warranty jobs and partial invoices under $1,500 are left out.</p>
<ul>
<li>Typical job (middle half): {money(st['p25'])} to {money(st['p75'])}. Median about {money(st['median'])}.</li>
<li>Most jobs (8 in 10): {money(st['p10'])} to {money(st['p90'])}.</li>
{local}
<li>Jobs over $10,000 in this set included a variable-speed (VFD) controller and a larger 3 HP, 45 GPM pump.</li>
</ul>
<p>What moves the price: pump depth and horsepower, whether the wire and drop pipe are reusable, and the control box. We quote before we replace anything. <a href="/cost-calculator.html">Get a free estimate</a> or call <a href="tel:+17604408520">(760) 440-8520</a>.</p>
<p>Not sure it is the pump? If water fades in late summer or the pump runs but delivers less, read <a href="/blog/well-running-dry.html">well running dry: causes, signs, and fixes</a> before you replace anything.</p>
</section>
<section class="hub-nearby-towns" id="nearby-towns" style="max-width:1100px;margin:32px auto;padding:0 16px">
<h2>Towns served from the {h['shop']} shop</h2>
<ul style="columns:2">
{links}
</ul>
</section>
<!-- JOB_MAP_HUB_END -->
'''


def patch_hub(key, pins):
    path = P('services', key, 'index.html')
    s = open(path).read()
    block = hub_block(key, pins)
    if '<!-- JOB_MAP_HUB_START -->' in s:
        s2 = re.sub(r'<!-- JOB_MAP_HUB_START -->.*?<!-- JOB_MAP_HUB_END -->\n', lambda m: block, s, flags=re.S)
    else:
        m = '<!-- MONEY_PAGE_RECENT_WORK_END -->\n'
        i = s.index(m) + len(m)
        s2 = s[:i] + block + s[i:]
    if '/js/job-map.js' not in s2:
        j = s2.rindex('</body>')
        s2 = s2[:j] + '<script src="/js/job-map.js" defer></script>\n' + s2[j:]
    if s2 != s:
        open(path, 'w').write(s2)


def main():
    pins = build_pins('--geocode' in sys.argv)
    json.dump({'generated': time.strftime('%Y-%m-%d'), 'note': 'Town-level pins only. No customer names or addresses.',
               'pins': pins}, open(P('recent-work', 'job-map.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
    os.makedirs(P('recent-work', 'map'), exist_ok=True)
    open(P('recent-work', 'map', 'index.html'), 'w').write(page(pins))
    for k in HUBS:
        patch_hub(k, pins)
    print(f'{len(pins)} pins, {len({p["town"] for p in pins})} towns')


if __name__ == '__main__':
    main()
