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
    "services/hemet/index.html": note(
        "Hemet runs out of the Anza yard",
        [
            "Hemet does not have an SCWS storefront. The shop is 57174 CA-371 (US Hwy 79), Anza, CA 92539. Florida Avenue, East Hemet, Diamond Valley, and the Sage side of the valley are calls we already run: service calls, pressure tanks and switches, controls, and some drilling. If you searched for a Hemet well company and landed here, you found the Anza crew.",
            "A Hemet pressure problem is often the tank or the switch, not a dead pump. We have already done pressure-tank plumbing, a pressure switch and filter, and a deepen-the-setting job when the pump was not deep enough. Those are on Recent Work with field photos. Storage-tank floats are the same trucks. See <a href=\"/pages/services/pressure-tanks.html\">pressure tanks and switches</a> and <a href=\"/pages/services/water-storage-tanks.html\">storage tanks and float switches</a>.",
            "Founded 2020. CSLB C-57 #1086994. Tell us whether the house is dry or the pump will not shut off. That is enough to load the truck from Anza. The Anza hub is <a href=\"/services/anza/\">here</a>. Area proof: <a href=\"/recent-work/areas/hemet.html\">Hemet recent work</a>.",
        ],
        "Hemet field photos are in the cards below.",
    ),
    "services/el-cajon/index.html": note(
        "El Cajon wells from the Ramona shop",
        [
            "El Cajon is Ramona-shop work. The address is 1077 Main St Unit B, Ramona, CA 92065, not a yard in El Cajon. The calls we publish are service calls, controls and contactors, wire and check valves, and pressure tanks. A contactor that welds shut looks like a pump that will not stop. A check valve that fails looks like the pump is weak.",
            "We already have an El Cajon check-valve job, a contactor replacement, and a control diagnostic on Recent Work. Start there if you want to see the truck work before you call. Pressure-tank work on this route is the same crew: <a href=\"/pages/services/pressure-tanks.html\">pressure tanks and switches</a>. Controls live on <a href=\"/pages/services/controls.html\">the controls page</a>.",
            "Founded 2020. CSLB C-57 #1086994. Voice (760) 440-8520. Text (760) 219-5877. If you are between El Cajon and Alpine or Lakeside, say the cross street. Area page: <a href=\"/recent-work/areas/el-cajon.html\">El Cajon recent work</a>. Ramona hub: <a href=\"/services/ramona/\">Ramona shop</a>.",
        ],
        "El Cajon cards below are real jobs, not a city-name swap.",
    ),
    "services/menifee/index.html": note(
        "Menifee tank floats and pumps, from Anza",
        [
            "Menifee is closer to the Anza shop on CA-371 than to Main Street. The work is service calls, pressure tanks, and pump or motor replacement. Two jobs we already published are a pump-down float and a tank float. Those are storage-tank failures: the pump will not start, or it will not stop. That is not a Menifee storefront. It is the Anza truck.",
            "If the float is the problem, read <a href=\"/pages/services/water-storage-tanks.html\">water storage tanks and float switches</a> before you assume the submersible died. Pressure tanks are the other half of a short-cycling house: <a href=\"/pages/services/pressure-tanks.html\">pressure tanks and switches</a>. Pump pulls are <a href=\"/pages/services/pump-repair.html\">pump repair</a>.",
            "Founded 2020. CSLB C-57 #1086994. Anza shop: 57174 CA-371 (US Hwy 79), Anza, CA 92539. Tell us if you have a storage tank on the pad. Area page: <a href=\"/recent-work/areas/menifee.html\">Menifee recent work</a>.",
        ],
        "Menifee float and pump cards are below.",
    ),
    "services/warner-springs/index.html": note(
        "Warner Springs, from the Ramona shop",
        [
            "Warner Springs is Ramona-shop country along Highway 79, not an Anza ticket. The calls are service, controls, flow tests, and some drilling. A booster and a storage tank on the same parcel is a normal Warner Springs diagnostic. Lost pressure is often the switch or the tank, which we would rather say on the phone than sell a pull.",
            "Recent Work already has a booster-and-tank diagnostic, a pressure-loss diagnostic, and a pressure-switch job. Those photos are the local proof. Related pages: <a href=\"/pages/services/booster-pumps.html\">booster pumps</a> and <a href=\"/pages/services/pressure-tanks.html\">pressure tanks and switches</a>.",
            "The Ramona shop is 1077 Main St Unit B, Ramona, CA 92065. Founded 2020. CSLB C-57 #1086994. If the ranch gate is locked, put the combo in the first text. Area page: <a href=\"/recent-work/areas/warner-springs.html\">Warner Springs recent work</a>.",
        ],
        "Warner Springs cards below are jobs we already finished.",
    ),
    "services/rancho-santa-fe/index.html": note(
        "Rancho Santa Fe pumps and panels, from Ramona",
        [
            "Rancho Santa Fe does not get a fake local shop. The crew comes from 1077 Main St Unit B, Ramona, CA 92065. The work is service calls, controls, boosters, and pump or motor replacement. We have published an electrical panel job, a high-amp diagnostic, and a pull of the well pump and motor. High amp draw is a reason to stop and test, not a reason to order a motor over the phone.",
            "Boosters on estate tanks are a separate ticket from the submersible in the hole. Say which one is dead. <a href=\"/pages/services/booster-pumps.html\">Booster pump repair</a> and <a href=\"/pages/services/pump-repair.html\">well pump repair</a> are the two pages. Controls: <a href=\"/pages/services/controls.html\">pump controls</a>.",
            "Founded 2020. CSLB C-57 #1086994. Voice (760) 440-8520. Text (760) 219-5877. Area page: <a href=\"/recent-work/areas/rancho-santa-fe.html\">Rancho Santa Fe recent work</a>.",
        ],
        "Rancho Santa Fe cards below are the published jobs.",
    ),
    "services/santa-ysabel/index.html": note(
        "Santa Ysabel pump and switch work",
        [
            "Santa Ysabel is on the Ramona shop route with Julian, up Highway 78. The calls are service, pump and motor replacement, and controls. We have published a pressure switch and filter job and a bail-and-brush on the well. A switch that iced or burned is a different morning than a pump that has to come out of the hole.",
            "If the complaint is no pressure, start with <a href=\"/pages/services/pressure-tanks.html\">pressure tanks and switches</a>. If the pump has to be pulled, that is <a href=\"/pages/services/pump-repair.html\">pump repair</a>. The Ramona shop is 1077 Main St Unit B, Ramona, CA 92065. Anza does not normally roll this grade.",
            "Founded 2020. CSLB C-57 #1086994. Text the gate code if the place is vacant. Area page: <a href=\"/recent-work/areas/santa-ysabel.html\">Santa Ysabel recent work</a>. Julian hub, same shop: <a href=\"/services/julian/\">Julian well service</a>.",
        ],
        "Santa Ysabel cards below are real jobs.",
    ),
    "services/desert-hot-springs/index.html": note(
        "Desert Hot Springs is an Anza route",
        [
            "There is no shop in Desert Hot Springs. The yard is 57174 CA-371 (US Hwy 79), Anza, CA 92539. The work is service calls and diagnostics, wire and drop pipe, check valves and well seals, pump and motor replacement, pressure tanks and switches, and a little drilling. Rancho Mirage, Palm Desert, La Quinta, Thousand Palms, and Thermal are towns on the same stretch where we have already worked. Those are Recent Work area pages, not extra city hubs.",
            "A Thermal pressure-switch job is published because that is the kind of ticket this valley produces. If you are in Desert Hot Springs and the pump will not start, say so. If the tank is full and the house is dry, say that too. <a href=\"/pages/services/pressure-tanks.html\">Pressure tanks</a> and <a href=\"/pages/services/pump-repair.html\">pump repair</a> are the matching service pages. The Anza hub is <a href=\"/services/anza/\">here</a>.",
            "Founded 2020. CSLB C-57 #1086994. Voice (760) 440-8520. Text (760) 219-5877. Ramona is the other shop, at 1077 Main St Unit B. It is the long way for this valley.",
        ],
        'Coachella Valley proof: <a href="/recent-work/areas/desert-hot-springs.html">Desert Hot Springs recent work</a>.',
    ),
    "services/mountain-center/index.html": note(
        "Mountain Center, same Anza shop as Idyllwild",
        [
            "Mountain Center is the grade between Hemet and Idyllwild. The shop is Anza: 57174 CA-371 (US Hwy 79), Anza, CA 92539. Calls are service, pressure tank and switch replacement, pump and motor replacement, and controls. Idyllwild and Pine Cove are the next community on the same route. The Idyllwild hub is <a href=\"/services/idyllwild/\">here</a>.",
            "A pressure tank on a cabin and a pump that has to come out are different jobs. Tell us which one you think you have, and whether the well house can freeze. <a href=\"/pages/services/pressure-tanks.html\">Pressure tanks and switches</a> and <a href=\"/pages/services/pump-repair.html\">pump repair</a> cover those two. Storage tanks: <a href=\"/pages/services/water-storage-tanks.html\">float switches and tanks</a>.",
            "Founded 2020. CSLB C-57 #1086994. Text (760) 219-5877 if you cannot talk. Put the gate combo in the first message. Area pages: <a href=\"/recent-work/areas/mountain-center.html\">Mountain Center</a> and <a href=\"/recent-work/areas/idyllwild.html\">Idyllwild</a>.",
        ],
        'Mountain proof is the area pages: <a href="/recent-work/areas/mountain-center.html">Mountain Center recent work</a> and <a href="/recent-work/areas/idyllwild.html">Idyllwild recent work</a>.',
    ),
    "pages/services/water-storage-tanks.html": note(
        "How a storage tank call actually goes",
        [
            "We do not sell a tank from a photo of an empty pad. The first question is whether the float failed or the pump failed. A pump-up float that sticks leaves the tank empty. A pump-down float that sticks leaves the pump running. Float weights and ball floats do the same thing when they hang up. That is the job we see most.",
            "When the tank itself is done, we deliver and remove them, including 3,000 gallon PVC tanks and 5,000 and 10,000 gallon tanks. Pads are the 24x24x3 pads, with a gravel ring when the ground needs it. Bulkhead fittings and epoxy are the leaks at the tank wall. If a booster and a tank are both wrong, we diagnose the pair. The booster page is <a href=\"/pages/services/booster-pumps.html\">here</a>.",
            "Two shops. Ramona at 1077 Main St Unit B. Anza at 57174 CA-371 (US Hwy 79). Founded 2020. CSLB C-57 #1086994. The guide is <a href=\"/blog/water-storage-tank-guide.html\">the storage tank article</a>. The cards below are finished jobs.",
        ],
        "Field photos of tank and float jobs are in the cards below.",
    ),
    "pages/services/booster-pumps.html": note(
        "Booster calls are not well pulls",
        [
            "A full storage tank and a dry house is a booster ticket. A locked motor, a weeping mechanical seal, or a constant-pressure package that faulted are the jobs we replace and diagnose. Three-phase booster motors are in that mix. We do not list model numbers. Brands we already service are on the <a href=\"/pages/brands-we-service.html\">brands page</a>: Franklin Electric, Grundfos, Goulds, Pentair, and the others named there.",
            "Say whether the tank has water before we roll. That is the whole load-out. Ramona shop: 1077 Main St Unit B, Ramona, CA 92065. Anza shop: 57174 CA-371 (US Hwy 79), Anza, CA 92539. Founded 2020. CSLB C-57 #1086994. If the well pump is the thing that died, that is <a href=\"/pages/services/pump-repair.html\">pump repair</a>, not this page.",
            "Constant-pressure packages get a transducer and a drive, not a guess. Pressure tanks next to the booster are <a href=\"/pages/services/pressure-tanks.html\">their own page</a>. The cards below are booster jobs we already finished.",
        ],
        "Booster field photos are in the cards below.",
    ),
    "pages/services/pressure-tanks.html": note(
        "Short-cycling is usually the tank",
        [
            "A pump that starts and stops every few seconds is often a waterlogged pressure tank, not a dead motor. We replace tanks, replace or adjust pressure switches, and repair the plumbing at the tank tee. On a constant-pressure system the transducer and the tank get replaced together when both are done. Lost pressure gets a diagnostic before anyone talks about a new submersible.",
            "Read <a href=\"/blog/how-to-check-pressure-tank.html\">how to check a pressure tank</a> and <a href=\"/blog/bladder-tank-vs-pressure-tank.html\">bladder tank versus pressure tank</a> if you want the background. Storage tanks with floats are a different piece of equipment: <a href=\"/pages/services/water-storage-tanks.html\">water storage tanks</a>.",
            "Ramona shop, 1077 Main St Unit B, Ramona, CA 92065. Anza shop, 57174 CA-371 (US Hwy 79), Anza, CA 92539. Founded 2020. CSLB C-57 #1086994. Voice (760) 440-8520. Text (760) 219-5877. Tell us what the gauge is doing.",
        ],
        "Pressure tank and switch photos are in the cards below.",
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
