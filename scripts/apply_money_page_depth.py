#!/usr/bin/env python3
"""Add unique shop-voice depth + CTA/H1 fixes on high-intent money pages.

Bodies are written per page (not a city-name template). Facts only:
founded 2020, family heritage, CSLB #1086994, two shops, real phones.
No 4.9★, no invented years-in-business, no Heritage-since-1960s claims.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPTH_MARKERS = ("<!-- MONEY_PAGE_DEPTH_START -->", "<!-- MONEY_PAGE_DEPTH_END -->")

CTA = """<p class="shop-local-ctas">
<a class="shop-lead-call" href="tel:+17604408520">Call (760) 440-8520</a>
<a class="shop-lead-text" href="sms:7602195877">Text (760) 219-5877</a>
<a class="shop-lead-est" href="/contact.html">Get estimate</a>
</p>
<p class="shop-local-license">CSLB #1086994 (C-57). Voice (760) 440-8520. Text (760) 219-5877. Founded 2020. Shops in Ramona and Anza.</p>"""


def note(title: str, paragraphs: list[str], proof: str) -> str:
    body = "\n".join(f"<p>{p}</p>" for p in paragraphs)
    start, end = DEPTH_MARKERS
    return (
        f"{start}\n"
        f'<section class="shop-local-note" id="shop-local-note">\n'
        f"<h2>{title}</h2>\n"
        f"{body}\n"
        f"<p>{proof}</p>\n"
        f"{CTA}\n"
        f"</section>\n"
        f"{end}\n"
    )


# Unique 200–400 word shop notes. Do not copy-swap city names.
DEPTH_HTML = {
    "services/ramona/index.html": note(
        "From the Ramona shop on Main Street",
        [
            "The Ramona shop is at 1077 Main Street, Unit B — same town as San Diego Country Estates, Dye Road, and the Mussey Grade properties we pull pumps on most weeks. SCWS started in 2020. The crew still works these granite and Santiago Peak wells the old way: show up, test the system, and tell you what actually failed before anyone talks about a new pump.",
            "A lot of Ramona calls start the same way. Pressure switch chatters. Tank short-cycles. No water after a power blink. Country Estates houses from the 80s and 90s still run original controls next to a 300-foot setting. We keep contactors, 40/60 switches, and common drop-pipe fittings on the truck because the drive back to town wastes the afternoon when a family is already on bottled water.",
            "Iron and manganese stain fixtures here. That is not a sales pitch for a filter package — it is why we look at the pressure tank bladder and the control box before we assume the submersible died. If the well is tired in late summer, we say so. If it is a melted switch, we replace the switch.",
            "Need us today? Call the voice line or text the text-only number. Ask for the Ramona shop. We will tell you if we can roll same-day or if Anza has to cover.",
        ],
        'Proof is on the site — <a href="/recent-work/">Recent Work</a> has the Ramona jobs with field photos, not stock pictures.',
    ),
    "services/anza/index.html": note(
        "Anza shop on CA-371",
        [
            "The Anza shop sits at 57174 CA-371 (US Hwy 79). That is the high-desert yard — Terwilliger, Cahuilla, Thomas Mountain, and the Aguanga wells that are closer to us than to Ramona. Founded 2020. Same C-57 license as the Main Street shop. Different dirt.",
            "Anza wells are often shallower than Ramona granite holes and still beat up equipment. Dust, hard water, storage tanks on hillsides, float switches that stick after a windy week. We pull and inspect a lot of pumps here because “no water” on a ranch is usually a control or a hole in the drop pipe, not a brand-new drill.",
            "If you are in Anza proper and the house is dry, call or text. Do not wait for a weekday office hour if the stock is out of water — we answer the phone after 5. Tell us whether you have a storage tank and a booster. That changes what we load.",
            "We are not inventing an old Anza drilling company. SCWS is the 2020 shop that bought the local routes and still runs trucks from this highway.",
        ],
        'See the Anza and Aguanga cards on <a href="/recent-work/">Recent Work</a> — those are jobs we already finished.',
    ),
    "services/valley-center/index.html": note(
        "Valley Center wells — groves and houses",
        [
            "Brighton lives in Valley Center. That is why this page is not a copied city template with the name swapped. Avocado and citrus places out here run irrigation pumps that work all summer, then a house well that nobody thinks about until the kitchen is dry. We treat those as two systems even when they share a parcel.",
            "Valley Center sits between the Escondido grade and Pauma. Alluvial floor, granite on the hills. Some domestic wells are easy 180-foot settings. Grove wells go deeper and harder. When a VFD faults or a motor lead burns, we want the model and the last time anyone opened the control box — not a story about a company that has always been here. We have not. SCWS started in 2020. We still run these roads every week.",
            "If the grove is out and the house still has water, say that on the phone. We will not pull the domestic pump to chase an irrigation breaker. Text photos of the panel if you can. The text line is (760) 219-5877.",
        ],
        'Real Valley Center jobs live on <a href="/recent-work/">Recent Work</a> — overcurrent faults, pump replacements, and electrical diagnostics, not brochure copy.',
    ),
    "services/aguanga/index.html": note(
        "Aguanga is Anza-shop country",
        [
            "Aguanga is closer to the Anza yard than to Main Street. Low-yield holes, melted pressure switches, and pumps that sand up after a dry year are the usual calls. We already have a stack of Aguanga cards on Recent Work — pump installs, pull-and-inspect, tanks — because that is the route, not a marketing city we added to a map.",
            "Highway 79 and the back roads off it are slow when a tanker is in the way. If you have no water, tell us whether you can run a garden hose from a neighbor or a tank. We will say if we can be there today from Anza or if Ramona has to send a second truck.",
            "SCWS was founded in 2020. Family heritage in well work is real; a fake “serving Aguanga since 1960” line is not. Licensed C-57, CSLB #1086994. Call or text and give us the gate code the first time so we are not sitting on the county road.",
        ],
        'Start with <a href="/recent-work/">Recent Work</a> if you want to see the Aguanga jobs before you call.',
    ),
    "services/temecula/index.html": note(
        "Temecula and Wine Country wells",
        [
            "Temecula wells are a mix: De Luz hills, estate tanks, and the occasional 30-horse pump that is doing agricultural work next to a tasting room. We pull those. We also replace transducers and pressure tanks when the house side of the system is the part that died.",
            "This is Riverside County work out of both shops. Anza is closer to some De Luz gates than Ramona is. If you are on the valley floor, say so — response is different than a locked ranch off a dirt road. We do not pretend we have a Temecula storefront. We have Ramona and Anza, and we already run Temecula jobs every week.",
            "No water on a weekend in Wine Country still gets the same two numbers: voice (760) 440-8520, text (760) 219-5877. Founded 2020. C-57 #1086994. We will not quote a new well on the phone from a guess. We will tell you if it sounds like a control, a pump, or a well that is done.",
        ],
        'Temecula pull-and-replace and diagnostic jobs are listed on <a href="/recent-work/">Recent Work</a>.',
    ),
    "services/escondido/index.html": note(
        "Escondido and the North County grade",
        [
            "Escondido wells sit on the edge of city water. Some streets are municipal. The properties we see are the ones that never got a meter — hidden tanks, old jet pumps, and submersibles in granite on the way toward Valley Center and Hidden Meadows.",
            "A lot of “Escondido well guys” are plumbers. We are a C-57 well shop. If the pump is in the hole, we pull it. If the well needs a camera or a production test, we say that before we sell a motor. SCWS started in 2020. We did not inherit a mid-century Escondido drill company.",
            "If you are between Escondido and Valley Center, tell us the nearest cross street. That is how we decide which truck. Call or text. We will not invent a star-rating speech on the phone. We will ask what the pressure gauge is doing and whether the tank is in a shed or under the house.",
        ],
        'Escondido jobs with photos are on <a href="/recent-work/">Recent Work</a>.',
    ),
    "services/julian/index.html": note(
        "Julian mountain wells — freeze and granite",
        [
            "Julian is 4,200 feet. Pipes freeze. Fracture wells make 2–8 GPM on a good day. People run storage because the hole will not keep up with guests on a holiday weekend. We already service Julian, Wynola, Santa Ysabel, and Pine Hills from the Ramona shop — Highway 78, about a half hour when the snow is not on the grade.",
            "Uranium and hardness show up in this granite. That is a water-quality conversation after you have water. First job is usually a pump, a pressure switch that iced, or a tank that lost air. We do not sell a new mountain well over a text. We will tell you if the existing hole is worth spending money on.",
            "SCWS founded 2020. Licensed C-57 #1086994. If the cabin is vacant and the neighbor called you, text us the gate combo and whether heat is on at the well house. That is the difference between a simple switch and a split pipe.",
        ],
        'Julian and Santa Ysabel cards are on <a href="/recent-work/">Recent Work</a>.',
    ),
    "pages/services/pump-repair.html": note(
        "How we actually repair well pumps",
        [
            "Pump repair here is pull, inspect, and decide — not a parts-cannon from the driveway. We work San Diego and Riverside backcountry wells: Ramona granite, Anza desert tanks, Temecula boosters, Valley Center grove motors. Same two shops. Same C-57.",
            "The first question is whether the motor is dead, the controls are dead, or the well is done. A melted 40/60 switch looks like a failed pump if nobody opens the tank tee. A bad contactor looks like a shorted motor. We test before we order a Goulds or a Franklin.",
            "Founded 2020. Family heritage in the trade, not a fake 40-year company age. If you have no water, call or text. Tell us the last time the pump was pulled and whether sand is in the toilets. That is enough to know if we bring a hoist or a control kit. Ramona and Anza both stock common switches so a lot of these calls end the same day.",
        ],
        'Field photos of real pump jobs are on <a href="/recent-work/">Recent Work</a> and in the cards below.',
    ),
    "pages/services/well-drilling.html": note(
        "New wells vs. the hole you already have",
        [
            "Most calls we get labeled “drilling” are not a new well. They are a pump that will not make water, a well that sanded, or a second house on a parcel that already has a tired hole. We still drill. We also tell you when deepening or a new site is the honest answer.",
            "San Diego and Riverside granite is slow, abrasive work. Ramona and Julian settings are often hundreds of feet. Anza can be shallower and still a fight. Permits are county-specific. We will not quote a per-foot number in a hero banner and call it a contract.",
            "SCWS is a 2020 C-57 shop (#1086994), Ramona and Anza. Family heritage is the crew background — not a claim that this LLC has always drilled the county. If you want a new well, call. If you want to know whether the existing well is worth another pump, that is a production test, and those jobs are already on Recent Work.",
        ],
        'See production tests, bail-and-brush, and deep-set pulls on <a href="/recent-work/">Recent Work</a>.',
    ),
    "pages/services/emergency-well-service.html": note(
        "No-water calls in San Diego and Riverside Counties",
        [
            "Emergency well service on this site means the house or the stock is dry. We answer 24/7 on the voice line. Text if you cannot talk. We do not have a call center reading a script from another state. You get the shop.",
            "After-hours we ask the same things: is the breaker tripped, is the pressure gauge at zero, do you hear the pump, is there a storage tank. A lot of “emergencies” are a pressure switch or a tank bladder. Some are a dead motor at 400 feet. We would rather spend ten minutes on the phone than roll a hoist for a switch.",
            "Primary coverage is Ramona, Anza, Valley Center, Aguanga, Temecula, and the towns between. Founded 2020. CSLB #1086994. We will tell you an honest ETA. We will not promise a 20-minute arrival from Ramona to the far side of Riverside.",
        ],
        'Diagnostic jobs we already ran are on <a href="/recent-work/">Recent Work</a> and in the cards on this page.',
    ),
    "services/ramona/well-pump-repair.html": note(
        "Ramona pump pulls — Country Estates to Dye Road",
        [
            "Ramona pump repair is the Main Street shop’s daily work. Deep-set submersibles, boosters on hillside tanks, and control panels that cook in a pump house with no shade. We see iron staining and summer yield drop on the same properties year after year.",
            "If your pump short-cycles, start with the tank and the switch. If you have sand, we talk about the well before we sell a new motor that will eat itself. Same-day from town is normal when we are not already in a hole. Anza covers if both Ramona trucks are out.",
            "Call (760) 440-8520 or text (760) 219-5877. Licensed C-57 #1086994. Founded 2020. Ask for Ramona pump repair and give us the neighborhood — SDCE, Woodson, Barona — so we know the typical setting depth. Mussey Grade and the back side of the Estates are the same shop, just a longer dirt driveway.",
        ],
        'Ramona pump cards are below and on <a href="/recent-work/">Recent Work</a>.',
    ),
    "services/ramona/well-drilling.html": note(
        "Drilling and well work from the Ramona shop",
        [
            "A Ramona “drilling” page should be honest: new holes happen, but most of what we do on existing wells is evaluate, clean, or reset a pump in fractured granite. Two-well systems on larger parcels are common. One well for the house, one that was drilled for a pasture and then forgotten.",
            "We will not tell you this LLC has always drilled Ramona. The company is 2020. The geology notes on this page are from the wells we actually work — 250 to 450 feet is typical, not a statewide average pasted in.",
            "If you need a new well, we talk permits and access before a rig date. If you need to know what the current well can still do, that is a production test. Those jobs are already published with photos. San Diego County well permits are not a form we fill in for you on this page — we will tell you what the county wants when we walk the site.",
        ],
        'Well evaluation and related jobs: <a href="/recent-work/">Recent Work</a>.',
    ),
    "services/ramona/emergency-well-service.html": note(
        "Ramona no-water — we are already in town",
        [
            "If you are in Ramona and the house is dry, you are calling the shop that is on Main Street, not a dispatch board in another county. After hours we still answer. Tell us if the neighbors have water. That is the fastest way to know if it is the well or SDG&amp;E.",
            "Power blinks kill contactors and VFDs on this grid. We carry those parts because we replace them here constantly. Country Estates and Dye Road houses lose a switch or a tank bladder more often than they lose a motor — we would rather say that on the phone than sell a pull you do not need.",
            "If it is a pull, we schedule the hoist and tell you whether you need a tank of water overnight. Same two numbers every time. Voice (760) 440-8520. Text (760) 219-5877. CSLB #1086994. Founded 2020.",
        ],
        'Ramona diagnostic jobs are in the cards below and on <a href="/recent-work/">Recent Work</a>.',
    ),
    "services/anza/well-pump-repair.html": note(
        "Anza and high-desert pump work",
        [
            "Anza pump repair is pull-and-inspect more often than a driveway capacitor swap. High-desert wells chew up motors. Storage tanks and boosters hide the real problem until the house is already dry. We open the control box and the tank before we commit to a pull.",
            "Aguanga jobs run on the same truck. If you are between the two, we still come from CA-371. Ramona only rolls this way when Anza is already in a hole or you need a second crew. Terwilliger and Cahuilla are the same route — say the community so we do not guess the gate.",
            "Founded 2020. C-57 #1086994. Call or text. Mention Anza pump repair and whether you have a storage tank. That is the load-out. If the tank is on a hill and the house booster is screaming, tell us that too.",
        ],
        'Anza pump photos: <a href="/recent-work/">Recent Work</a>.',
    ),
    "services/anza/well-drilling.html": note(
        "Anza well work — not a desert brochure",
        [
            "New wells in Anza and Terwilliger are their own permit and geology problem. A lot of landowners call this page because production fell off, not because they want a second hole. We would rather test the well you have than sell a drill date you do not need.",
            "Low-yield diagnostics and bail-and-brush jobs from this shop are already on Recent Work. That is the honest “drilling adjacent” work we publish. SCWS did not inherit a mid-century high-desert drill company. We are the 2020 shop on Highway 79.",
            "Call or text for a site look. Bring the well log if you have one. If you do not, we work from the pump setting and what comes out of the hose. Riverside County paperwork is not San Diego County paperwork — we will say which stack you are in before anyone talks about a rig.",
        ],
        'Well jobs near Anza: <a href="/recent-work/">Recent Work</a>.',
    ),
    "services/anza/emergency-well-service.html": note(
        "Anza after-hours — ranch and house",
        [
            "No water in Anza at 9 p.m. is usually stock, a house on a tank, or both. Tell us which. A dry storage tank is a different call than a pump that will not start. We answer the same two numbers as Ramona.",
            "Dirt roads and locked gates waste time. Put the combo in the first text. If you can hear the pump and the tank is empty, say that — we will talk about a leak or a float before we wake a second tech.",
            "If the cows are out of water and the house still has a trickle, we load for the tank first. CSLB #1086994. Founded 2020. Anza shop on CA-371. Voice (760) 440-8520. Text (760) 219-5877.",
        ],
        'Anza no-water jobs: <a href="/recent-work/">Recent Work</a>.',
    ),
    "pages/locations/cities/ramona.html": note(
        "Ramona is the Main Street shop",
        [
            "This location page is the same company as /services/ramona/ — Southern California Well Service, 1077 Main Street, Unit B, Ramona, CA 92065. Founded 2020. Not a second contractor. Not a 20-year franchise.",
            "If you found this URL from a search, use it to call or text and then look at Recent Work. The job photos are the local proof. Geology and neighborhoods — Country Estates, Woodson, Barona, Dye Road — are on the city service hub. We are not going to paste a fake review count here.",
            "Need a pump, a well look, or a dry-house call? Voice (760) 440-8520. Text (760) 219-5877. CSLB #1086994. If you are standing in a dry kitchen in Ramona, start with the voice line. If you can send a photo of the tank gauge, use the text line.",
        ],
        'Ramona field jobs: <a href="/recent-work/">Recent Work</a> and <a href="/services/ramona/">the Ramona hub</a>.',
    ),
    "pages/locations/cities/valley-center.html": note(
        "Valley Center from the Ramona shop — not since 2006",
        [
            "SCWS was founded in 2020. We do not have a Valley Center storefront and we do not claim a made-up avocado-country start year. Brighton lives here. The trucks come from Ramona, and Anza covers when that is the closer yard.",
            "Grove irrigation and house wells fail differently. Tell us which one is dry. If you are buying a property, ask for a production test before you trust an old well log. We publish those jobs with photos instead of a star rating.",
            "Pauma and Hidden Meadows get the same crew. Call or text. CSLB #1086994. For the longer city page see <a href=\"/services/valley-center/\">Valley Center well services</a>. If the grove pump is down in July, say that first — we will not treat it like a kitchen-sink call.",
        ],
        'Valley Center jobs: <a href="/recent-work/">Recent Work</a>.',
    ),
    "pages/locations/cities/temecula.html": note(
        "Temecula service from Ramona and Anza",
        [
            "There is no SCWS shop in Temecula. The work still happens — pump pulls, tanks, diagnostics — from the two shops we do have. If you are in De Luz or on a locked ranch, say that up front so we do not quote a valley-floor ETA.",
            "Founded 2020. C-57 #1086994. We will not put a fake decades-in-business line on this page to look older than the LLC. Wine Country estates and agricultural pumps are different tickets; tell us which side of the property is dry.",
            "Call (760) 440-8520 or text (760) 219-5877. The city hub with more local notes is <a href=\"/services/temecula/\">Temecula well services</a>. Recent Work has the Temecula pull jobs if you want to see the truck work before you call.",
        ],
        'Temecula jobs: <a href="/recent-work/">Recent Work</a>.',
    ),
    "pages/locations/cities/anza.html": note(
        "Anza is the second shop, not a pin on a map",
        [
            "57174 CA-371 (US Hwy 79), Anza, CA 92539 is a real yard. If you searched “well service Anza” and landed here, that is the address to put in the truck GPS. Ramona is the other shop. Same license, same phones.",
            "High-desert wells, tanks, and after-hours ranch calls are why this location exists. Founded 2020. Family heritage in the trade. No invented company-age story. Terwilliger and Aguanga are on the same radio.",
            "Voice (760) 440-8520. Text (760) 219-5877. CSLB #1086994. Longer Anza page: <a href=\"/services/anza/\">well services in Anza</a>. If you need a pump pull and you already have a tank on the hill, say so — that is most of the Anza tickets we publish.",
        ],
        'Anza jobs: <a href="/recent-work/">Recent Work</a>.',
    ),
}

H1_FIXES = [
    (
        ROOT / "pages/services/pump-repair.html",
        "                    Well Pump Repair & Replacement\n",
        "                    Well Pump Repair in San Diego &amp; Riverside Counties\n",
    ),
    (
        ROOT / "pages/services/well-drilling.html",
        "Professional Water Well Drilling",
        "Well Drilling in San Diego &amp; Riverside Counties",
    ),
    (
        ROOT / "pages/services/emergency-well-service.html",
        "Emergency Well Service — 24/7 Response",
        "Emergency Well Service in San Diego &amp; Riverside Counties",
    ),
    (
        ROOT / "pages/locations/cities/valley-center.html",
        "Serving Avocado Country Since 2006",
        "Avocado-country wells in Valley Center — SCWS, founded 2020",
    ),
    (
        ROOT / "pages/locations/cities/ramona.html",
        "We're based right here in Ramona — your founded in 2020",
        "Based at 1077 Main Street, Unit B — founded 2020",
    ),
]


def insert_depth(text: str, block: str) -> str:
    start, end = DEPTH_MARKERS
    if start in text and end in text:
        return re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            lambda _: block.rstrip() + "\n",
            text,
            count=1,
            flags=re.S,
        )
    money = "<!-- MONEY_PAGE_RECENT_WORK_START -->"
    if money in text:
        return text.replace(money, block + money, 1)
    jobs = re.search(r'<section\b[^>]*id=["\']recent-jobs["\']', text, re.I)
    if jobs:
        return text[: jobs.start()] + block + text[jobs.start() :]
    foot = re.search(r"<footer\b", text, re.I)
    if foot:
        return text[: foot.start()] + block + text[foot.start() :]
    return text + block


def apply_h1_fixes() -> list[Path]:
    changed: list[Path] = []
    for path, old, new in H1_FIXES:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if old in text:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            changed.append(path)
    return changed


def apply_depth() -> list[Path]:
    changed: list[Path] = []
    for rel, block in DEPTH_HTML.items():
        path = ROOT / rel
        if not path.is_file():
            continue
        original = path.read_text(encoding="utf-8")
        updated = insert_depth(original, block)
        if "/css/shop-chrome.css" not in updated and re.search(r"</head>", updated, re.I):
            updated = re.sub(
                r"</head>",
                '<link rel="stylesheet" href="/css/shop-chrome.css"/>\n</head>',
                updated,
                count=1,
                flags=re.I,
            )
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    h1 = apply_h1_fixes()
    depth = apply_depth()
    for path in h1:
        print(f"h1 {path.relative_to(ROOT)}")
    for path in depth:
        print(f"depth {path.relative_to(ROOT)}")
    print(f"h1 fixes: {len(h1)}; depth pages: {len(depth)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
