#!/usr/bin/env python3
"""Add a unique, sourced section to each town × service page.

The block is marked SERVICE_TOWN_LOCAL and is replaced on re-run.
Jobs come from recent-work/projects.json. Well figures come from
tools/welldepth/well_data.json. Review quotes come only from
pages/reviews.html, first name only, and only when that town is the
town on the review. No AggregateRating.
"""
from __future__ import annotations

import html
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from hub_schema_lib import SHOPS, city_display_name, html_is_noindex, serving_shop
from recent_work_lib import (
    ROOT,
    card_city_only,
    city_slug_from_location,
    extract_project_facts,
    is_boilerplate_summary,
    sanitize_public_text,
    slugify,
)

START = "<!-- SERVICE_TOWN_LOCAL_START -->"
END = "<!-- SERVICE_TOWN_LOCAL_END -->"
BLOCK_RE = re.compile(
    re.escape(START) + r".*?" + re.escape(END),
    re.S,
)
REVIEW_RE = re.compile(
    r'<div class="reviewer">([^<]+)</div>\s*'
    r'<div class="review-meta">([^<]*)</div>\s*'
    r'<p class="review-text">(.*?)</p>',
    re.S,
)
MAIN_RE = re.compile(r"</main>", re.I)
SERVICE_FILES = (
    "well-pump-repair.html",
    "booster-pump.html",
    "emergency-well-service.html",
    "pressure-tank.html",
    "water-testing.html",
    "water-treatment.html",
    "well-drilling.html",
    "well-inspection.html",
)
GAP_TOWNS = (
    "temecula",
    "murrieta",
    "poway",
    "alpine",
    "jamul",
    "lakeside",
    "escondido",
    "el-cajon",
    "valley-center",
    "fallbrook",
    "menifee",
    "perris",
)
# Perris service pages stay noindex. The town is still in this batch.
EXTRA_NOINDEX_TOWNS = frozenset({"perris"})
PHONE_DISPLAY = "(760) 440-8520"
PHONE_TEL = "tel:+17604408520"
HOURS = "Mon–Sun 7:00 AM–5:00 PM, with 24/7 emergency service"

SERVICE_META = {
    "well-pump-repair.html": {
        "name": "Well pump repair",
        "lower": "well pump repair",
        "overview": "/pages/services/pump-repair.html",
        "overview_label": "pump repair",
    },
    "booster-pump.html": {
        "name": "Booster pump service",
        "lower": "booster pump service",
        "overview": "/pages/services/booster-pumps.html",
        "overview_label": "booster pumps",
    },
    "emergency-well-service.html": {
        "name": "Emergency well service",
        "lower": "emergency well service",
        "overview": "/pages/services/emergency-well-service.html",
        "overview_label": "emergency well service",
    },
    "pressure-tank.html": {
        "name": "Pressure tank service",
        "lower": "pressure tank service",
        "overview": "/pages/services/pressure-tanks.html",
        "overview_label": "pressure tanks",
    },
    "water-testing.html": {
        "name": "Water testing",
        "lower": "water testing",
        "overview": "/pages/services/water-testing.html",
        "overview_label": "water testing",
    },
    "water-treatment.html": {
        "name": "Water treatment",
        "lower": "water treatment",
        "overview": "/water-treatment.html",
        "overview_label": "water treatment",
    },
    "well-drilling.html": {
        "name": "Well drilling",
        "lower": "well drilling",
        "overview": "/pages/services/well-drilling.html",
        "overview_label": "well drilling",
    },
    "well-inspection.html": {
        "name": "Well inspection",
        "lower": "well inspection",
        "overview": "/pages/services/well-inspection.html",
        "overview_label": "well inspection",
    },
}

REVIEW_WORDS = {
    "well-pump-repair.html": ("pump", "capacitor", "motor"),
    "emergency-well-service.html": ("emergency", "no water", "no running water", "weekend"),
    "well-inspection.html": ("inspect",),
    "pressure-tank.html": ("tank",),
    "booster-pump.html": ("booster",),
    "water-testing.html": ("sample", "water test"),
    "water-treatment.html": ("filter", "treatment"),
    "well-drilling.html": ("drill",),
}

_WELLS: dict | None = None
_HYPER: dict | None = None


def _hyperlocal() -> dict:
    global _HYPER
    if _HYPER is None:
        _HYPER = json.loads((ROOT / "scripts" / "city-hyperlocal-data.json").read_text(encoding="utf-8"))
    return _HYPER


def _well_file() -> dict:
    global _WELLS
    if _WELLS is None:
        _WELLS = json.loads((ROOT / "tools" / "welldepth" / "well_data.json").read_text(encoding="utf-8"))
    return _WELLS


def norm_city(name: str) -> str:
    text = (name or "").lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def city_matches_slug(slug: str, city: str) -> bool:
    """Match a DWR city tag to a town slug. Mixed case counts.

    A compacted form (DeLuz, Deluz) counts for a multi-word slug (de-luz).
    Extra words (Cuyamaca Peak, Rainbow, Fallbrook) do not.
    """
    target = norm_city(slug.replace("-", " "))
    city_norm = norm_city(city)
    if city_norm == target:
        return True
    compact = target.replace(" ", "")
    return bool(compact != target and city_norm == compact)


def as_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if number != number:  # NaN
        return None
    return number


def nearest_10(value: float) -> int:
    return int(round(value / 10.0) * 10)


def fmt_num(value: float) -> str:
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.1f}"


def roughly_range(q1: float, q3: float) -> str:
    start = nearest_10(q1)
    end = nearest_10(q3)
    if start == end:
        return f"roughly {start} ft"
    return f"roughly {start}–{end} ft"


class WellStats:
    def __init__(self, slug: str) -> None:
        payload = _well_file()
        self.source = str(payload.get("source") or "well completion file")
        self.generated = str(payload.get("generated") or "")
        depths: list[float] = []
        yields: list[float] = []
        for well in payload.get("wells") or []:
            if not city_matches_slug(slug, str(well.get("city") or "")):
                continue
            if str(well.get("use") or "").strip() != "Water Supply Domestic":
                continue
            depth = as_float(well.get("depth"))
            if depth is None or depth <= 0:
                continue
            depths.append(depth)
            flow = as_float(well.get("yield"))
            if flow is not None and flow > 0:
                yields.append(flow)
        depths.sort()
        self.n = len(depths)
        self.median_depth = statistics.median(depths) if depths else None
        self.q1 = self.q3 = None
        if self.n >= 8:
            q1, _mid, q3 = statistics.quantiles(depths, n=4, method="inclusive")
            self.q1 = q1
            self.q3 = q3
        self.n_yield = len(yields)
        self.median_yield = statistics.median(yields) if yields else None


def _file_label(stats: WellStats) -> str:
    when = f" (generated {stats.generated})" if stats.generated else ""
    return f"The {stats.source} file on this site{when}"


def count_sentence(town: str, stats: WellStats) -> str:
    label = _file_label(stats)
    if stats.n == 0:
        return f"{label} has no Water Supply Domestic wells tagged to {town}."
    noun = "well" if stats.n == 1 else "wells"
    return f"{label} tags {stats.n} Water Supply Domestic {noun} to {town}."


def depth_sentence(town: str, stats: WellStats) -> str:
    sentence = count_sentence(town, stats)
    if stats.median_depth is None:
        return sentence
    sentence += f" The median depth is {fmt_num(stats.median_depth)} ft."
    if stats.n >= 8 and stats.q1 is not None and stats.q3 is not None:
        sentence += f" The middle half are {roughly_range(stats.q1, stats.q3)}."
    return sentence


def yield_sentence(stats: WellStats) -> str:
    if stats.n == 0:
        return ""
    if stats.n_yield >= 5 and stats.median_yield is not None:
        return (
            f" Among the {stats.n_yield} of those wells with a reported yield, "
            f"the median yield is {fmt_num(stats.median_yield)} GPM."
        )
    if stats.n_yield:
        return (
            f" {stats.n_yield} of those wells include a yield. "
            "Fewer than five yield figures are in the file, so this page does not state a median yield."
        )
    return " None of those wells include a reported yield."


def well_paragraph(service_file: str, town: str, stats: WellStats) -> str:
    if service_file == "well-pump-repair.html":
        return (
            f"For well pump repair in {town}, depth and yield in the state file are the local reference. "
            + depth_sentence(town, stats)
            + yield_sentence(stats)
        )
    if service_file == "well-drilling.html":
        return (
            f"For well drilling in {town}, completed domestic wells in the state file are the depth reference, not a drilling quote. "
            + depth_sentence(town, stats)
        )
    if service_file == "well-inspection.html":
        return (
            f"For a well inspection in {town}, these are completed depths from the state file, not measurements from one visit. "
            + depth_sentence(town, stats)
        )
    if service_file == "booster-pump.html":
        if stats.n_yield >= 5 and stats.median_yield is not None:
            return (
                f"For booster pump service in {town}, reported yield is the local figure used here. "
                f"{stats.n_yield} Water Supply Domestic wells tagged to {town} include a yield, "
                f"and the median is {fmt_num(stats.median_yield)} GPM. "
                + count_sentence(town, stats)
            )
        if stats.n == 0:
            return (
                f"For booster pump service in {town}, no yield is listed because the state file has no domestic wells tagged to the town. "
                + count_sentence(town, stats)
            )
        return (
            f"For booster pump service in {town}, the state file tags {stats.n} Water Supply Domestic wells to {town} "
            f"and {stats.n_yield} of them include a yield. "
            "Fewer than five yield figures are in the file, so this page does not state a median yield."
        )
    if service_file == "pressure-tank.html":
        return (
            f"For pressure tank service in {town}, the state well file does not record tank size or precharge. "
            + count_sentence(town, stats)
        )
    if service_file == "water-testing.html":
        return (
            f"For water testing in {town}, the state well file does not include laboratory results. "
            + count_sentence(town, stats)
        )
    if service_file == "water-treatment.html":
        return (
            f"For water treatment in {town}, the state well file does not record filters, softeners, or other treatment equipment. "
            + count_sentence(town, stats)
        )
    if service_file == "emergency-well-service.html":
        sentence = (
            f"For emergency well service in {town}, the domestic-well count in the state file is the local figure used here. "
            + count_sentence(town, stats)
        )
        if stats.median_depth is not None:
            sentence += f" The median completed depth in that set is {fmt_num(stats.median_depth)} ft."
        return sentence
    raise KeyError(service_file)


def well_question(service_file: str, town: str) -> str:
    questions = {
        "well-pump-repair.html": f"How deep are the domestic wells tagged to {town}?",
        "well-drilling.html": f"What completed depths does the state file list for domestic wells in {town}?",
        "well-inspection.html": f"What does the state well file show for domestic wells in {town}?",
        "booster-pump.html": f"What yields are reported for domestic wells tagged to {town}?",
        "pressure-tank.html": f"Does the state well file list pressure tanks in {town}?",
        "water-testing.html": f"Does the state well file include water-test results for {town}?",
        "water-treatment.html": f"Does the state well file list treatment equipment in {town}?",
        "emergency-well-service.html": f"How many domestic wells in the state file are tagged to {town}?",
    }
    return questions[service_file]


def job_matches(service_file: str, project: dict) -> bool:
    title = project.get("title") or ""
    text = f"{title} {project.get('summary') or ''}"
    category = project.get("category") or ""
    if service_file == "pressure-tank.html":
        return category == "tank" or re.search(r"pressure tank|\bbladder\b", text, re.I) is not None
    if service_file == "booster-pump.html":
        return re.search(r"\bbooster\b", text, re.I) is not None
    if service_file == "water-testing.html":
        return re.search(
            r"\b(?:water tests?|bacteria|coliform|sample spigot|sampled)\b|\bfor testing\b",
            text,
            re.I,
        ) is not None
    if service_file == "water-treatment.html":
        pattern = (
            r"\b(?:water treatment|softener|chlorinator|iron filter|"
            r"spin-down|sand separator|auto-purge|filtration)\b"
        )
        if re.search(pattern, text, re.I) is None:
            return False
        # A passing mention in a pump note is not a treatment job.
        return category == "water-quality" or re.search(pattern, title, re.I) is not None
    if service_file == "well-drilling.html":
        return re.search(r"\b(?:drilling|drilled|new well)\b", text, re.I) is not None
    if service_file == "well-inspection.html":
        return re.search(
            r"\b(?:wellhead inspection|inspected the wellhead|production tests?|production check)\b",
            text,
            re.I,
        ) is not None
    if service_file == "emergency-well-service.html":
        return re.search(
            r"\b(?:emergency|no water|no-water|out of water|diagnostic|tripped|overload|overcurrent)\b",
            text,
            re.I,
        ) is not None
    if service_file == "well-pump-repair.html":
        if category != "pump":
            return False
        if re.search(r"\bbooster\b", title, re.I) and not re.search(r"\bwell pump\b", title, re.I):
            return False
        return re.search(r"\b(?:pump|motor)\b", text, re.I) is not None
    return False


def project_city_slug(project: dict) -> str:
    return city_slug_from_location(project.get("location") or "")


def _job_rank(project: dict) -> tuple:
    summary = project.get("summary") or ""
    rich = 0 if is_boilerplate_summary(summary) else 1
    return (rich, project.get("date") or "", len(summary))


def two_sentences(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:2]).strip()


def select_jobs(service_file: str, town: str, projects: list[dict], county: str) -> tuple[list[dict], list[dict]]:
    local: list[dict] = []
    nearby: list[dict] = []
    for project in projects:
        if not job_matches(service_file, project):
            continue
        slug = project.get("slug") or ""
        if not slug or not (ROOT / "recent-work" / f"{slug}.html").is_file():
            continue
        job_town = project_city_slug(project)
        if job_town == town:
            local.append(project)
            continue
        other = (_hyperlocal().get(job_town) or {}).get("county")
        if other and other == county:
            nearby.append(project)
    if local:
        rich = [project for project in local if not is_boilerplate_summary(project.get("summary") or "")]
        pool = rich or local
        pool.sort(key=_job_rank, reverse=True)
        shown = pool[:3]
        return shown, [], len(local) - len(shown)
    best_by_town: dict[str, dict] = {}
    for project in nearby:
        job_town = project_city_slug(project) or card_city_only(project.get("location") or "")
        current = best_by_town.get(job_town)
        if current is None or _job_rank(project) > _job_rank(current):
            best_by_town[job_town] = project
    chosen = sorted(best_by_town.values(), key=_job_rank, reverse=True)[:3]
    return [], chosen, 0


def job_plain_list(projects: list[dict], nearby: bool) -> str:
    parts = []
    for project in projects:
        place = card_city_only(project.get("location") or "") or "the area"
        when = (project.get("dateLabel") or project.get("date") or "").strip()
        title = re.sub(r"\s+", " ", project.get("title") or "Recent job").strip()
        if nearby:
            parts.append(f"{title} in {place} ({when})" if when else f"{title} in {place}")
        else:
            parts.append(f"{title} ({when})" if when else title)
    return "; ".join(parts)


def jobs_answer(
    service_lower: str,
    town: str,
    county: str,
    local: list[dict],
    nearby: list[dict],
    extra_local: int = 0,
) -> str:
    if local:
        sentence = (
            f"The public Recent Work file includes these {service_lower} jobs in {town}: "
            f"{job_plain_list(local, nearby=False)}."
        )
        if extra_local:
            noun = "job" if extra_local == 1 else "jobs"
            sentence += f" The file has {extra_local} more {service_lower} {noun} in {town}."
        return sentence
    if nearby:
        return (
            f"The public Recent Work file has no {service_lower} job in {town}. "
            f"Nearby {county} County jobs in that file include: {job_plain_list(nearby, nearby=True)}."
        )
    return (
        f"The public Recent Work file has no {service_lower} job in {town} "
        f"or in another {county} County town in that file."
    )


def shop_answer(service_name: str, town: str, shop_key: str) -> str:
    shop = SHOPS[shop_key]
    shop_name = "Ramona" if shop_key == "ramona" else "Anza"
    address = f"{shop['street']}, {shop['locality']}, CA {shop['postal']}"
    return (
        f"{service_name} in {town} is handled from the {shop_name} shop at {address}. "
        f"The shop phone is {PHONE_DISPLAY}. Shop hours are {HOURS}."
    )


def load_reviews() -> list[dict]:
    text = (ROOT / "pages" / "reviews.html").read_text(encoding="utf-8")
    reviews = []
    for name, meta, body in REVIEW_RE.findall(text):
        place = meta.split(",")[0].strip()
        reviews.append(
            {
                "first": name.strip().split()[0],
                "full": name.strip(),
                "town": slugify(place),
                "place": place,
                "html": body.strip(),
                "text": re.sub(r"<br\s*/?>", " ", body, flags=re.I),
            }
        )
    return reviews


def _review_score(review: dict, words: tuple[str, ...]) -> int:
    text = review["text"].lower()
    score = 0
    for word in words:
        if re.search(rf"\b{re.escape(word)}\b", text):
            score += 1
    return score


def assign_reviews(town: str, reviews: list[dict]) -> dict[str, dict | None]:
    town_reviews = [review for review in reviews if review["town"] == town]
    assigned: dict[str, dict | None] = {name: None for name in SERVICE_FILES}
    if not town_reviews:
        return assigned
    used: set[int] = set()
    for service_file in SERVICE_FILES:
        words = REVIEW_WORDS[service_file]
        ranked = sorted(
            ((-_review_score(review, words), index) for index, review in enumerate(town_reviews)),
        )
        for score, index in ranked:
            if score < 0 and index not in used:
                used.add(index)
                assigned[service_file] = town_reviews[index]
                break
    unused = [index for index in range(len(town_reviews)) if index not in used]
    cursor = 0
    for service_file in SERVICE_FILES:
        if assigned[service_file] is not None:
            continue
        if unused:
            assigned[service_file] = town_reviews[unused.pop(0)]
            continue
        assigned[service_file] = town_reviews[cursor % len(town_reviews)]
        cursor += 1
    return assigned


def review_note(review: dict, service_file: str) -> str:
    words = [word for word in REVIEW_WORDS[service_file] if re.search(rf"\b{re.escape(word)}\b", review["text"], re.I)]
    if words:
        listed = _join_words(words)
        return (
            f"A review from {review['first']} in {review['place']} is on the reviews page. "
            f"It mentions {listed}."
        )
    return (
        f"A review from {review['first']} in {review['place']} is on the reviews page. "
        "The review does not name this service. The words below are the review as published."
    )


def _join_words(words: list[str]) -> str:
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} and {words[1]}"
    return ", ".join(words[:-1]) + f", and {words[-1]}"


def review_quote_html(review: dict) -> str:
    parts = re.split(r"<br\s*/?>", review["html"], flags=re.I)
    return "<br>\n".join(html.escape(part) for part in parts)


def render_job_item(project: dict, nearby: bool) -> str:
    title = html.escape(re.sub(r"\s+", " ", project.get("title") or "Recent job").strip())
    slug = project.get("slug")
    place = html.escape(card_city_only(project.get("location") or "") or "the area")
    when = html.escape((project.get("dateLabel") or project.get("date") or "").strip())
    where = f"Nearby {place}" if nearby else place
    bits = [f'<a href="/recent-work/{html.escape(slug)}.html">{title}</a> — {where}']
    if when:
        bits.append(f", {when}")
    bits.append(".")
    quote = two_sentences(sanitize_public_text(project.get("summary") or ""))
    if quote:
        bits.append(f" {html.escape(quote, quote=False)}")
    facts = extract_project_facts(project.get("summary") or "")
    if facts:
        fact_text = "; ".join(f"{label} {value}" for label, value in facts)
        bits.append(f" Specs named in the job note: {html.escape(fact_text, quote=False)}.")
    return "<li>" + "".join(bits) + "</li>"


def render_block(
    *,
    town_slug: str,
    service_file: str,
    local: list[dict],
    nearby: list[dict],
    extra_local: int,
    stats: WellStats,
    review: dict | None,
    include_schema: bool,
) -> str:
    meta = SERVICE_META[service_file]
    town = city_display_name(town_slug)
    county = (_hyperlocal().get(town_slug) or {}).get("county") or ""
    shop_key = serving_shop(town_slug)
    shop_place = "Ramona" if shop_key == "ramona" else "Anza"
    well = well_paragraph(service_file, town, stats)
    jobs_text = jobs_answer(meta["lower"], town, county, local, nearby, extra_local)
    shop_text = shop_answer(meta["name"], town, shop_key)
    faqs = [
        (f"Which published {meta['lower']} jobs are in or near {town}?", jobs_text),
        (well_question(service_file, town), well),
        (f"Which shop handles {meta['lower']} in {town}?", shop_text),
    ]
    if local:
        lead = jobs_text
        rows = local
        is_nearby = False
    elif nearby:
        lead = (
            f"The public Recent Work file has no {meta['lower']} job in {town}. "
            f"These are {meta['lower']} jobs from other {county} County towns in that file:"
        )
        rows = nearby
        is_nearby = True
    else:
        lead = jobs_text
        rows = []
        is_nearby = False
    items = "\n".join(render_job_item(project, is_nearby) for project in rows)
    list_html = f"\n<ul>\n{items}\n</ul>" if items else ""
    review_html = ""
    if review is not None:
        review_html = (
            "\n<h3>Review on the reviews page</h3>\n"
            f"<p>{html.escape(review_note(review, service_file))}</p>\n"
            f"<blockquote><p>{review_quote_html(review)}</p></blockquote>\n"
            f"<p>{html.escape(review['first'])}, {html.escape(review['place'])}, "
            'on the <a href="/pages/reviews.html">reviews page</a>.</p>'
        )
    overview = meta["overview"]
    overview_html = ""
    if (ROOT / overview.lstrip("/")).is_file():
        overview_html = (
            f' and <a href="{html.escape(overview)}">{html.escape(meta["overview_label"])}</a>'
        )
    faq_html = "\n".join(
        f"<h3>{html.escape(question)}</h3>\n<p>{html.escape(answer)}</p>"
        for question, answer in faqs
    )
    schema = ""
    if include_schema:
        payload = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {"@type": "Answer", "text": answer},
                }
                for question, answer in faqs
            ],
        }
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).replace("<", "\\u003c")
        schema = f'\n<script type="application/ld+json">\n{encoded}\n</script>'
    intro = (
        f"{meta['name']} in {town} is dispatched from the {shop_place} shop. "
        f"Call <a href=\"{PHONE_TEL}\">{PHONE_DISPLAY}</a>. "
        "The notes below use the public Recent Work file and the site’s California DWR well-completion file. "
        f"A review is quoted only when the reviews page has one from {town}."
    )
    return (
        f"{START}\n"
        '<section id="service-town-local" class="service-town-local" '
        'style="max-width:1100px;margin:2rem auto;padding:1.25rem 1.5rem;border:1px solid #e2e8f0;'
        'border-radius:12px;background:#f8fafc;line-height:1.6;">\n'
        f"<h2>{html.escape(meta['name'])} in {html.escape(town)}: local record</h2>\n"
        f"<p>{intro}</p>\n"
        "<h3>Recent Work</h3>\n"
        f"<p>{html.escape(lead)}</p>{list_html}\n"
        "<h3>Well completion reports</h3>\n"
        f"<p>{html.escape(well)}</p>{review_html}\n"
        "<h3>Questions</h3>\n"
        f"{faq_html}\n"
        f"<p>Related pages: "
        f'<a href="/services/{html.escape(town_slug)}/">{html.escape(town)} well service</a>'
        f"{overview_html}.</p>\n"
        f"</section>{schema}\n"
        f"{END}"
    )


def insert_block(page: str, block: str) -> str:
    page_wo = BLOCK_RE.sub("", page)
    match = MAIN_RE.search(page_wo)
    if not match:
        raise ValueError("page has no </main>")
    prefix = page_wo[: match.start()].rstrip()
    return prefix + "\n" + block + "\n" + page_wo[match.start() :]


def target_towns() -> list[str]:
    found = []
    services = ROOT / "services"
    for path in sorted(services.iterdir()):
        if not path.is_dir():
            continue
        files = [path / name for name in SERVICE_FILES]
        if not all(item.is_file() for item in files):
            continue
        indexable = all(not html_is_noindex(item.read_text(encoding="utf-8")) for item in files)
        if indexable or path.name in EXTRA_NOINDEX_TOWNS:
            found.append(path.name)
    gap = [slug for slug in GAP_TOWNS if slug in found]
    rest = sorted(slug for slug in found if slug not in GAP_TOWNS)
    return gap + rest


def _outside_has_faq(page: str) -> bool:
    return "FAQPage" in BLOCK_RE.sub("", page)


def apply_service_town_sections(root: Path | None = None) -> dict[str, int]:
    """Insert or refresh the local section. Returns counts."""
    del root  # The helpers read ROOT. Tests pass HTML strings to insert_block.
    projects = json.loads((ROOT / "recent-work" / "projects.json").read_text(encoding="utf-8"))["projects"]
    reviews = load_reviews()
    changed = 0
    skipped = 0
    towns = target_towns()
    for town in towns:
        assigned = assign_reviews(town, reviews)
        stats = WellStats(town)
        for service_file in SERVICE_FILES:
            path = ROOT / "services" / town / service_file
            original = path.read_text(encoding="utf-8")
            county = (_hyperlocal().get(town) or {}).get("county") or ""
            local, nearby, extra_local = select_jobs(service_file, town, projects, county)
            block = render_block(
                town_slug=town,
                service_file=service_file,
                local=local,
                nearby=nearby,
                extra_local=extra_local,
                stats=stats,
                review=assigned[service_file],
                include_schema=not _outside_has_faq(original),
            )
            updated = insert_block(original, block)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed += 1
            else:
                skipped += 1
    return {"towns": len(towns), "changed": changed, "unchanged": skipped}


def assert_moreno_valley_reference() -> WellStats:
    """Guard the quartile method against the published Moreno Valley figure."""
    stats = WellStats("moreno-valley")
    if stats.n != 52 or stats.median_depth != 304:
        raise SystemExit(f"Moreno Valley domestic stats drifted: n={stats.n} median={stats.median_depth}")
    if stats.q1 is None or stats.q3 is None:
        raise SystemExit("Moreno Valley quartiles missing")
    if nearest_10(stats.q1) != 270 or nearest_10(stats.q3) != 440:
        raise SystemExit(f"Moreno Valley range drifted: {stats.q1}–{stats.q3}")
    if stats.n_yield != 49 or stats.median_yield != 10:
        raise SystemExit(f"Moreno Valley yield drifted: n={stats.n_yield} median={stats.median_yield}")
    return stats


if __name__ == "__main__":
    assert_moreno_valley_reference()
    counts = apply_service_town_sections()
    print(json.dumps(counts))
