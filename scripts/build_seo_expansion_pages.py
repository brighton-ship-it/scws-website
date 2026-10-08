#!/usr/bin/env python3
"""Write the Oct 2026 service pages and Anza-shop city hubs.

Copy is facts from the service brief only: founded 2020, CSLB C-57 #1086994,
two phones, two shop addresses. No prices, ratings, or invoice counts.

Re-running overwrites the five HTML files. Afterward run apply_depth() and
apply_money_page_recent_work() so shop notes and Recent Work cards come back.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hub_schema_lib import schema_script

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://scwellservice.com"

TRACKING = """<script src="/js/ga4-filter.js"></script>
<script src="/js/cookie-consent.js"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-5LL1YRWT5T"></script>
<script src="/js/scws-tracking.js"></script>
<script src="/js/call-tracking.js"></script>"""

HEADER = """<body class="shop-page" style="padding-bottom:80px">
<div class="bg-gradient-to-r from-red-600 to-red-700 text-white py-2.5">
<div class="max-w-7xl mx-auto px-4 text-center flex items-center justify-center gap-2 flex-wrap">
<span class="font-bold tracking-wide">No water?</span>
<span class="hidden sm:inline">Call or text the shop.</span>
<a class="bg-white text-red-600 font-bold px-4 py-2.5 rounded-full text-sm hover:bg-red-100 transition ml-1" style="min-height:44px;display:inline-flex;align-items:center;" href="tel:+17604408520">Call Now</a>
</div>
</div>
<header class="bg-primary text-white sticky top-0 z-50 shadow-lg">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
<div class="flex justify-between items-center py-4">
<a class="flex items-center space-x-3 shrink-0" href="/">
<img width="840" height="150" alt="Southern California Well Service" class="h-10 lg:h-12 w-auto" loading="lazy" src="/images/logo-text-only-3x.png"/>
</a>
<nav class="hidden lg:flex space-x-4 items-center">
<a class="text-white hover:text-accent transition whitespace-nowrap" href="/pages/services/">Services</a>
<a class="text-white hover:text-accent transition whitespace-nowrap" href="/pages/service-area.html">Service Areas</a>
<a class="text-white hover:text-accent transition whitespace-nowrap" href="/recent-work/">Recent Work</a>
<a class="text-white hover:text-accent transition whitespace-nowrap" href="/contact.html">Contact</a>
<a class="text-white hover:text-accent transition whitespace-nowrap" href="/pages/about.html">About</a>
</nav>
<div class="flex items-center gap-2">
<button type="button" id="mobile-menu-btn" class="shop-menu-btn" aria-label="Open menu">☰</button>
<a class="site-phone-cta bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition" href="tel:+17604408520">(760) 440-8520</a>
</div>
</div>
</div>
<div id="mobile-menu" class="hidden shop-mobile-nav bg-primary/95 border-t border-white/10 px-4 py-3">
<a href="/">Home</a>
<a href="/pages/services/">Services</a>
<a href="/recent-work/">Recent Work</a>
<a href="/contact.html">Contact</a>
<a href="/pages/about.html">About</a>
</div>
</header>
<script>
(function(){var b=document.getElementById('mobile-menu-btn');var m=document.getElementById('mobile-menu');if(b&&m){b.addEventListener('click',function(){m.classList.toggle('hidden');});}})();
</script>"""

TAIL = """<footer class="footer shop-footer-nap" style="background:#0f172a;color:#94a3b8;padding:2rem 1rem;">
<p><strong style="color:#fff;">Southern California Well Service</strong></p>
<p>Voice <a href="tel:+17604408520">(760) 440-8520</a> · Text <a href="sms:7602195877">(760) 219-5877</a></p>
<p>1077 Main St Unit B, Ramona, CA 92065 · 57174 CA-371 (US Hwy 79), Anza, CA 92539</p>
<p>Founded 2020 · CSLB License #1086994 (C-57)</p>
</footer>
<div id="sticky-cta">
<a class="cta-call" href="tel:+17604408520">Call</a>
<a class="cta-text" href="sms:7602195877">Text</a>
<a class="cta-est" href="/contact.html">Estimate</a>
</div>
</body>
</html>
"""

TAILWIND = """<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = { theme: { extend: { colors: { primary: '#1f3b4d', accent: '#4e9271' } } } }
</script>
<link rel="stylesheet" href="/css/shop-chrome.css"/>"""


def _json_script(obj: dict) -> str:
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(obj, indent=2, ensure_ascii=False)
        + "\n</script>"
    )


def _breadcrumb(crumbs: list[tuple[str, str | None]]) -> dict:
    items = []
    for i, (name, url) in enumerate(crumbs, start=1):
        item = {"@type": "ListItem", "position": i, "name": name}
        if url:
            item["item"] = url
        items.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def _faq(pairs: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in pairs
        ],
    }


def _service_schema(name: str, service_type: str, url: str, description: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "serviceType": service_type,
        "url": url,
        "description": description,
        "provider": {
            "@type": "LocalBusiness",
            "name": "Southern California Well Service",
            "telephone": "(760) 440-8520",
            "url": SITE,
            "address": [
                {
                    "@type": "PostalAddress",
                    "streetAddress": "1077 Main St Unit B",
                    "addressLocality": "Ramona",
                    "addressRegion": "CA",
                    "postalCode": "92065",
                    "addressCountry": "US",
                },
                {
                    "@type": "PostalAddress",
                    "streetAddress": "57174 CA-371 (US Hwy 79)",
                    "addressLocality": "Anza",
                    "addressRegion": "CA",
                    "postalCode": "92539",
                    "addressCountry": "US",
                },
            ],
        },
        "areaServed": [
            {"@type": "AdministrativeArea", "name": "San Diego County"},
            {"@type": "AdministrativeArea", "name": "Riverside County"},
        ],
    }


def _shell(title: str, description: str, canonical: str, scripts: str, body: str) -> str:
    if len(title) > 60:
        raise ValueError(f"title over 60 chars ({len(title)}): {title}")
    title_html = html.escape(title, quote=True)
    description_html = html.escape(description, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title_html}</title>
<meta name="description" content="{description_html}"/>
<link href="{canonical}" rel="canonical"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{title_html}"/>
<meta property="og:description" content="{description_html}"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:image" content="https://scwellservice.com/images/logo-text-only-3x.png"/>
{TRACKING}
{TAILWIND}
{scripts}
</head>
{HEADER}
{body}
{TAIL}
"""


def _faq_html(pairs: list[tuple[str, str]]) -> str:
    blocks = []
    for q, a in pairs:
        blocks.append(
            f'<div class="border border-gray-200 rounded-lg p-6 mb-4">'
            f'<h3 class="font-semibold text-primary mb-2">{q}</h3>'
            f'<p class="text-gray-700">{a}</p></div>'
        )
    return "\n".join(blocks)


def _service_page(
    filename: str,
    title: str,
    description: str,
    h1: str,
    lede: str,
    service_type: str,
    body: str,
    faqs: list[tuple[str, str]],
) -> None:
    url = f"{SITE}/pages/services/{filename}"
    scripts = "\n".join(
        [
            _json_script(_service_schema(h1, service_type, url, description)),
            _json_script(
                _breadcrumb(
                    [
                        ("Home", f"{SITE}/"),
                        ("Services", f"{SITE}/pages/services/"),
                        (h1, None),
                    ]
                )
            ),
            _json_script(_faq(faqs)),
        ]
    )
    crumb = (
        '<p class="text-sm text-gray-500 mb-4">'
        '<a href="/">Home</a> · <a href="/pages/services/">Services</a> · '
        f"{h1}</p>"
    )
    hero = f"""<main class="service-page">
<section class="hero">
<div class="max-w-3xl mx-auto">
{crumb}
<h1>{h1}</h1>
<p class="text-lg">{lede}</p>
<p class="shop-local-ctas" style="justify-content:center;">
<a class="shop-lead-call" href="tel:+17604408520">Call (760) 440-8520</a>
<a class="shop-lead-text" href="sms:7602195877">Text (760) 219-5877</a>
<a class="shop-lead-est" href="/contact.html">Get estimate</a>
</p>
</div>
</section>
<section class="content">
{body}
<h2>Questions we hear</h2>
{_faq_html(faqs)}
</section>
</main>
"""
    path = ROOT / "pages" / "services" / filename
    path.write_text(
        _shell(title, description, url, scripts, hero),
        encoding="utf-8",
    )
    print(f"wrote {path.relative_to(ROOT)}")


def write_service_pages() -> None:
    tank_faqs = [
        (
            "Why does my well pump keep running?",
            "On a storage-tank system, a stuck pump-down float or a float weight that fell off is the usual reason. The pump is doing what the float is telling it to do. We check the float before we pull the pump.",
        ),
        (
            "Why will the storage tank not fill?",
            "A pump-up float that fails, a float that cannot drop, or a well pump that is not starting. The tank stays empty and the house goes dry if there is no other supply.",
        ),
        (
            "Do you replace the tank, or only the float?",
            "Both. We replace pump-up and pump-down float switches, float weights, and ball floats. We also deliver and remove tanks, including 3,000 gallon PVC tanks and 5,000 and 10,000 gallon tanks, and we reset bulkhead fittings when the new tank goes in.",
        ),
    ]
    _service_page(
        "water-storage-tanks.html",
        "Water Storage Tanks & Float Switches | SCWS",
        "Float switches, tank pads, and storage tank replacement for San Diego and Riverside wells. Pump-up and pump-down floats. Call (760) 440-8520.",
        "Water storage tanks and float switches",
        "Most storage-tank calls are a float, not a new well. A pump-up float that sticks means the well pump does not fill the tank. A pump-down float that sticks means the pump keeps running after the tank is full.",
        "Water storage tank service",
        """
<h2>What fails</h2>
<p>The common line on these jobs is a pump-up or pump-down float switch. Float weights and ball floats fail the same way: the pump either never starts or never stops. After that we see tank pads, gravel rings, bulkhead fittings, and tanks that need to come out or go in. A booster-and-tank system that is acting up gets diagnosed as a pair before anyone sells a pump.</p>
<h2>Symptoms</h2>
<ul>
<li>The well pump will not shut off and the tank is already full.</li>
<li>The tank never fills and the house pressure dies.</li>
<li>The float hangs, or the weight is gone.</li>
<li>A fitting weeps at the bulkhead.</li>
</ul>
<h2>What we do</h2>
<p>We replace pump-up and pump-down float switches, float weights, and ball floats. We set tank pads — the 24x24x3 pads we actually use — plus gravel rings, bulkhead fittings, and epoxy where a fitting weeps. We deliver and remove tanks, including 3,000 gallon PVC tanks and 5,000 and 10,000 gallon tanks.</p>
<h2>When to call</h2>
<p>Call or text when the pump runs on and the tank is full, or the tank is empty and the pump will not start. Say whether a booster sits between the tank and the house. That changes what we load. Southern California Well Service was founded in 2020. CSLB C-57 #1086994. Ramona shop: 1077 Main St Unit B, Ramona, CA 92065. Anza shop: 57174 CA-371 (US Hwy 79), Anza, CA 92539.</p>
<h2>Related pages</h2>
<ul>
<li><a href="/blog/water-storage-tank-guide.html">Water storage tank guide</a></li>
<li><a href="/pages/services/booster-pumps.html">Booster pump repair and replacement</a></li>
<li><a href="/pages/services/pressure-tanks.html">Pressure tanks and pressure switches</a></li>
<li><a href="/pages/services/pump-repair.html">Well pump repair</a></li>
<li><a href="/services/anza/">Anza shop</a> and <a href="/services/ramona/">Ramona shop</a></li>
</ul>
<h2>More tank jobs</h2>
<ul>
<li><a href="/recent-work/fallbrook-tank-float-inspection.html">Tank float inspection in Fallbrook</a></li>
<li><a href="/recent-work/aguanga-float-and-pressure-switch-replacement.html">Float and pressure switch replacement in Aguanga</a></li>
</ul>
""",
        tank_faqs,
    )

    booster_faqs = [
        (
            "The storage tank is full but the house has no water. Where do we start?",
            "That is usually the booster, not the well pump. Tell us the tank has water so we load for the booster instead of a pull.",
        ),
        (
            "Which booster brands do you work on?",
            "The brands already listed on our brands page, including Franklin Electric, Grundfos, Goulds, and Pentair. We do not guess a model number from the driveway.",
        ),
        (
            "What is a constant-pressure booster package?",
            "A booster with a drive and a transducer that holds house pressure instead of a simple on-off switch. When it faults, we diagnose the package before we replace the pump.",
        ),
    ]
    _service_page(
        "booster-pumps.html",
        "Booster Pump Repair & Replacement | SCWS",
        "Booster pump and motor replacement, seal work, and constant-pressure packages. Ramona and Anza shops. Call (760) 440-8520.",
        "Booster pump repair and replacement",
        "A booster sits between a storage tank and the house, or between a weak well and the pressure the fixtures need. A locked booster looks like no water even when the tank is full.",
        "Booster pump repair",
        """
<h2>What fails</h2>
<p>Motors lock up. Mechanical seals weep. Constant-pressure packages fault on a transducer or a drive. We replace booster pumps and booster motors, including three-phase motors, run diagnostics and evaluations, and replace mechanical seals.</p>
<h2>Symptoms</h2>
<ul>
<li>The storage tank is full and the house is dry.</li>
<li>The booster hums and will not turn.</li>
<li>A seal leak at the booster.</li>
<li>Pressure swings on a constant-pressure package.</li>
</ul>
<h2>What we do</h2>
<p>Replacement, motor replacement, diagnostics, mechanical seals, and constant-pressure booster packages. Brands we already service are on the <a href="/pages/brands-we-service.html">brands page</a>: Franklin Electric, Grundfos, Goulds, Pentair, and the others listed there. No model numbers from a phone description.</p>
<h2>When to call</h2>
<p>Tell us whether the storage tank has water. That decides if we load a booster or a well pump. Voice (760) 440-8520. Text (760) 219-5877. Founded 2020. CSLB C-57 #1086994. Ramona: 1077 Main St Unit B, Ramona, CA 92065. Anza: 57174 CA-371 (US Hwy 79), Anza, CA 92539.</p>
<h2>Related pages</h2>
<ul>
<li><a href="/pages/services/pump-repair.html">Well pump repair</a></li>
<li><a href="/pages/services/pressure-tanks.html">Pressure tanks and pressure switches</a></li>
<li><a href="/pages/services/water-storage-tanks.html">Water storage tanks and float switches</a></li>
<li><a href="/pages/services/controls.html">Pump controls</a></li>
<li><a href="/pages/brands-we-service.html">Brands we service</a></li>
</ul>
<h2>More booster jobs</h2>
<ul>
<li><a href="/recent-work/ramona-locked-booster-pump-replacement.html">Locked booster pump replacement in Ramona</a></li>
<li><a href="/recent-work/winchester-booster-pump-replacement.html">Booster pump replacement in Winchester</a></li>
</ul>
""",
        booster_faqs,
    )

    pressure_faqs = [
        (
            "Why does the pump short-cycle?",
            "A waterlogged pressure tank is the usual cause. The bladder is gone or the air charge is wrong, so the pump starts and stops every few seconds. We look at the tank before we blame the pump.",
        ),
        (
            "The pressure dies a few minutes after the pump stops. What failed?",
            "Often a pressure tank that will not hold, a check valve, or a switch that is set wrong. On a constant-pressure system it can be the transducer and the tank together.",
        ),
        (
            "Do you only replace the tank?",
            "No. We replace tanks, replace or adjust pressure switches, repair pressure-tank plumbing, and replace the transducer and tank on constant-pressure systems. If the complaint is lost pressure, we diagnose before we sell a pump.",
        ),
    ]
    _service_page(
        "pressure-tanks.html",
        "Pressure Tanks & Pressure Switches | SCWS",
        "Pressure tank replacement, switch replacement, and pressure-loss diagnostics for San Diego and Riverside wells. Call (760) 440-8520.",
        "Pressure tanks and pressure switches",
        "A waterlogged pressure tank short-cycles the pump. A pressure switch that sticks or is set wrong leaves you with no water or a switch that chatters.",
        "Pressure tank service",
        """
<h2>What fails</h2>
<p>Pressure tanks lose their air charge or the bladder. Pressure switches burn, stick, or get set where the pump cannot start. Plumbing at the tank tee leaks. On a constant-pressure system, a failed transducer and a failed tank show up on the same call.</p>
<h2>Symptoms</h2>
<ul>
<li>The pump short-cycles.</li>
<li>No pressure at the house.</li>
<li>The switch chatters or will not click in.</li>
<li>Pressure dies a few minutes after the pump stops.</li>
</ul>
<h2>What we do</h2>
<p>Pressure tank replacement, pressure switch replacement or adjustment, pressure-tank plumbing repair, transducer and tank replacement on constant-pressure systems, and pressure-loss diagnostics.</p>
<h2>When to call</h2>
<p>If the pump is clicking on and off every few seconds, or the gauge sits at zero and the switch will not start the pump, call or text. Voice (760) 440-8520. Text (760) 219-5877. Founded 2020. CSLB C-57 #1086994.</p>
<h2>Related pages</h2>
<ul>
<li><a href="/blog/how-to-check-pressure-tank.html">How to check a pressure tank</a></li>
<li><a href="/blog/bladder-tank-vs-pressure-tank.html">Bladder tank vs pressure tank</a></li>
<li><a href="/pages/services/water-storage-tanks.html">Water storage tanks and float switches</a></li>
<li><a href="/pages/services/pump-repair.html">Well pump repair</a></li>
<li><a href="/pages/services/controls.html">Pump controls</a></li>
</ul>
<h2>More pressure jobs</h2>
<ul>
<li><a href="/recent-work/corona-pressure-tank-and-switch-adjustment.html">Pressure tank and switch adjustment in Corona</a></li>
<li><a href="/recent-work/thermal-pressure-switch-replacement.html">Pressure switch replacement in Thermal</a></li>
</ul>
""",
        pressure_faqs,
    )


def _city_page(slug: str, title: str, description: str, h1: str, lede: str, body: str) -> None:
    url = f"{SITE}/services/{slug}/"
    scripts = "\n".join(
        [
            schema_script(slug),
            _json_script(
                _breadcrumb(
                    [
                        ("Home", f"{SITE}/"),
                        ("Service areas", f"{SITE}/services/"),
                        (h1, None),
                    ]
                )
            ),
        ]
    )
    html_body = f"""<main class="city-landing">
<section class="hero">
<p class="text-sm"><a href="/">Home</a> · <a href="/services/">Service areas</a> · <a href="/services/anza/">Anza shop</a></p>
<h1>{h1}</h1>
<p>{lede}</p>
<p class="shop-local-ctas" style="justify-content:center;">
<a class="shop-lead-call" href="tel:+17604408520">Call (760) 440-8520</a>
<a class="shop-lead-text" href="sms:7602195877">Text (760) 219-5877</a>
<a class="shop-lead-est" href="/contact.html">Get estimate</a>
</p>
</section>
{body}
</main>
"""
    path = ROOT / "services" / slug / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_shell(title, description, url, scripts, html_body), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def write_city_hubs() -> None:
    _city_page(
        "desert-hot-springs",
        "Desert Hot Springs Well Service | Anza Shop",
        "Well service in Desert Hot Springs from the Anza shop. Pumps, pressure tanks, wire, and diagnostics, plus nearby Coachella Valley towns we have already worked. Call (760) 440-8520.",
        "Desert Hot Springs well service from the Anza shop",
        "Desert Hot Springs is Anza-shop country. There is no SCWS storefront in the Coachella Valley. The trucks come from 57174 CA-371 (US Hwy 79), Anza, CA 92539.",
        """
<section>
<h2>The work we actually do here</h2>
<p>Calls are mostly service and diagnostics. The rest is wire, drop pipe, check valves, and well seals; pump and motor replacement; pressure tank and pressure switch replacement; and a little drilling. If the house is dry, say whether you hear the pump and whether a storage tank is in the yard. That is the difference between a control ticket and a pull.</p>
<p>Southern California Well Service was founded in 2020. CSLB C-57 #1086994. Voice (760) 440-8520. Text (760) 219-5877. The other shop is Ramona, at 1077 Main St Unit B, Ramona, CA 92065. Desert Hot Springs rolls from Anza.</p>
</section>
<section>
<h2>Nearby Coachella Valley towns we have worked</h2>
<p>Same twelve-month stretch, same Anza trucks. We are not opening town pages for these. The proof is the Recent Work area pages:</p>
<ul>
<li><a href="/recent-work/areas/desert-hot-springs.html">Desert Hot Springs recent work</a></li>
<li><a href="/recent-work/areas/rancho-mirage.html">Rancho Mirage recent work</a></li>
<li><a href="/recent-work/areas/palm-desert.html">Palm Desert recent work</a></li>
<li><a href="/recent-work/areas/la-quinta.html">La Quinta recent work</a></li>
<li><a href="/recent-work/areas/thousand-palms.html">Thousand Palms recent work</a></li>
<li><a href="/recent-work/areas/thermal.html">Thermal recent work</a></li>
<li><a href="/recent-work/thermal-pressure-switch-replacement.html">Pressure switch replacement in Thermal</a></li>
</ul>
</section>
<section>
<h2>Service pages</h2>
<ul>
<li><a href="/pages/services/pump-repair.html">Well pump repair</a></li>
<li><a href="/pages/services/pressure-tanks.html">Pressure tanks and pressure switches</a></li>
<li><a href="/pages/services/water-storage-tanks.html">Water storage tanks and float switches</a></li>
<li><a href="/pages/services/booster-pumps.html">Booster pumps</a></li>
<li><a href="/pages/services/well-drilling.html">Well drilling</a></li>
<li><a href="/services/anza/">Anza shop hub</a></li>
</ul>
</section>
""",
    )
    _city_page(
        "mountain-center",
        "Mountain Center Well Service | Anza Shop",
        "Mountain Center well service from the Anza shop. Service calls, pressure tanks, pumps, and controls, next door to Idyllwild. Call (760) 440-8520.",
        "Mountain Center wells, served from Anza",
        "Mountain Center sits on the San Jacinto grade between Hemet and Idyllwild. The shop that runs it is Anza, not a cabin-town storefront.",
        """
<section>
<h2>The work we actually do here</h2>
<p>Service calls, pressure tank and pressure switch replacement, pump and motor replacement, and controls. Idyllwild and Pine Cove are the same Anza route. If the cabin is vacant, text the gate combo and whether the well house has heat. A frozen switch and a dead motor are different loads.</p>
<p>Founded 2020. CSLB C-57 #1086994. Voice (760) 440-8520. Text (760) 219-5877. Anza shop: 57174 CA-371 (US Hwy 79), Anza, CA 92539. Ramona shop: 1077 Main St Unit B, Ramona, CA 92065.</p>
</section>
<section>
<h2>Idyllwild and Pine Cove</h2>
<p>Cross the ridge and you are in Idyllwild. That hub is <a href="/services/idyllwild/">Idyllwild well service</a>, also out of Anza. Recent Work for this stretch of the mountain:</p>
<ul>
<li><a href="/recent-work/areas/mountain-center.html">Mountain Center recent work</a></li>
<li><a href="/recent-work/areas/idyllwild.html">Idyllwild recent work</a></li>
<li><a href="/recent-work/areas/idyllwild-pine-cove.html">Idyllwild-Pine Cove recent work</a></li>
</ul>
</section>
<section>
<h2>Service pages</h2>
<ul>
<li><a href="/pages/services/pressure-tanks.html">Pressure tanks and pressure switches</a></li>
<li><a href="/pages/services/pump-repair.html">Well pump repair</a></li>
<li><a href="/pages/services/controls.html">Pump controls</a></li>
<li><a href="/pages/services/water-storage-tanks.html">Water storage tanks</a></li>
<li><a href="/services/anza/">Anza shop hub</a></li>
</ul>
</section>
""",
    )


def main() -> int:
    write_service_pages()
    write_city_hubs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
