# SCWS Website Quality Control Report

**Generated:** 2025-02-05  
**Total HTML Files Checked:** 521

---

## 📊 Summary

| Category | Issues Found | Severity |
|----------|-------------|----------|
| Wrong Phone Numbers | 80 files | 🔴 HIGH |
| Missing Images | 22 images | 🔴 HIGH |
| Missing Chat Widget | 6 blog posts | 🟡 MEDIUM |
| Missing lead-gen.js | 10 files | 🟡 MEDIUM |
| Missing Exit Popup | ALL pages | 🟡 MEDIUM |
| Missing Meta Description | 5 files | 🟠 LOW |
| Missing H1 Tag | 1 file | 🟠 LOW |
| Duplicate Titles | 4 duplicates | 🟠 LOW |
| Missing Title Tag | 1 file | 🟠 LOW |

---

## 🔴 CRITICAL ISSUES

### 1. Wrong Phone Number (80 files)

These files contain the **wrong phone number** `(760) 440-9430` or `7604409430` instead of the correct `(760) 440-8520`:

**Cost Pages:**
- `blog/cost-to-drill-100-foot-well.html`
- `blog/cost-to-drill-200-foot-well.html`
- `blog/cost-to-drill-300-foot-well.html`
- `blog/cost-to-drill-400-foot-well.html`
- `blog/cost-to-drill-500-foot-well.html`

**Emergency Repair Pages:**
- `blog/emergency-well-repair-alpine.html`
- `blog/emergency-well-repair-carlsbad.html`
- `blog/emergency-well-repair-el-cajon.html`
- `blog/emergency-well-repair-encinitas.html`
- `blog/emergency-well-repair-escondido.html`
- `blog/emergency-well-repair-fallbrook.html`
- `blog/emergency-well-repair-hemet.html`
- `blog/emergency-well-repair-julian.html`
- `blog/emergency-well-repair-la-mesa.html`
- `blog/emergency-well-repair-lakeside.html`
- `blog/emergency-well-repair-murrieta.html`
- `blog/emergency-well-repair-oceanside.html`
- `blog/emergency-well-repair-poway.html`
- `blog/emergency-well-repair-ramona.html`
- `blog/emergency-well-repair-san-diego.html`
- `blog/emergency-well-repair-san-marcos.html`
- `blog/emergency-well-repair-santee.html`
- `blog/emergency-well-repair-temecula.html`
- `blog/emergency-well-repair-valley-center.html`
- `blog/emergency-well-repair-vista.html`

**How-To Pages:**
- `blog/how-to-adjust-pressure-switch.html`
- `blog/how-to-check-pressure-tank.html`
- `blog/how-to-chlorinate-well-yourself.html`
- `blog/how-to-find-buried-well.html`
- `blog/how-to-increase-well-water-pressure.html`
- `blog/how-to-measure-well-depth.html`
- `blog/how-to-reset-well-pump.html`
- `blog/how-to-test-well-water-at-home.html`
- `blog/how-to-winterize-well-pump.html`

**Well Drilling Location Pages:**
- `blog/well-drilling-alpine.html`
- `blog/well-drilling-carlsbad.html`
- `blog/well-drilling-el-cajon.html`
- `blog/well-drilling-encinitas.html`
- `blog/well-drilling-escondido.html`
- `blog/well-drilling-la-mesa.html`
- `blog/well-drilling-lakeside.html`
- `blog/well-drilling-oceanside.html`
- `blog/well-drilling-poway.html`
- `blog/well-drilling-ramona.html`
- `blog/well-drilling-san-marcos.html`
- `blog/well-drilling-santee.html`
- `blog/well-drilling-valley-center.html`
- `blog/well-drilling-vista.html`
- `blog/well-drilling-cost-per-foot-california.html`

**Well Pump Repair Location Pages:**
- `blog/well-pump-repair-carlsbad.html`
- `blog/well-pump-repair-el-cajon.html`
- `blog/well-pump-repair-encinitas.html`
- `blog/well-pump-repair-fallbrook.html`
- `blog/well-pump-repair-julian.html`
- `blog/well-pump-repair-la-mesa.html`
- `blog/well-pump-repair-lakeside.html`
- `blog/well-pump-repair-murrieta.html`
- `blog/well-pump-repair-oceanside.html`
- `blog/well-pump-repair-ramona.html`
- `blog/well-pump-repair-san-jacinto.html`
- `blog/well-pump-repair-san-marcos.html`
- `blog/well-pump-repair-santee.html`
- `blog/well-pump-repair-temecula.html`
- `blog/well-pump-repair-vista.html`

**Other Blog Pages:**
- `blog/jet-pump-cost.html`
- `blog/submersible-pump-cost.html`
- `blog/well-pump-installation-cost-local.html`
- `blog/well-pump-making-noise.html`
- `blog/well-pump-overheating.html`
- `blog/well-pump-tripping-breaker.html`
- `blog/well-pump-wont-turn-off.html`
- `blog/well-pump-wont-turn-on.html`

**Well Service Location Pages:**
- `blog/well-service-calimesa.html`
- `blog/well-service-cherry-valley.html`
- `blog/well-service-desert-hot-springs.html`
- `blog/well-service-dulzura.html`
- `blog/well-service-guatay.html`
- `blog/well-service-homeland.html`
- `blog/well-service-nuevo.html`
- `blog/well-service-tecate.html`

**FIX:** Find and replace all instances of `7604409430` and `(760) 440-9430` with `7604408520` and `(760) 440-8520`.

---

### 2. Missing Images (22 files)

These image files are referenced in blog posts but don't exist:

```
images/agricultural-well.jpg
images/alpine-oak-landscape.jpg
images/avocado-grove-irrigation.jpg
images/bonsall-avocado-irrigation.jpg
images/corona-citrus-landscape.jpg
images/de-luz-remote-property.jpg
images/deep-desert-well.jpg
images/deep-well-drilling.jpg
images/descanso-mountain-home.jpg
images/escondido-avocado-grove.jpg
images/estate-well-system.jpg
images/jamul-ranch-landscape.jpg
images/julian-apple-orchard.jpg
images/lakeside-lindo-lake.jpg
images/poway-estate-property.jpg
images/rainbow-horse-ranch.jpg
images/ramona-vineyard-landscape.jpg
images/residential-well-system.jpg
images/valley-center-avocado-grove.jpg
images/well-drilling-rig-action.jpg
images/well-pump-motor.jpg
images/well-pump-service.jpg
```

**FIX:** Either create/download these images or update the blog posts to use existing hero images.

---

## 🟡 MEDIUM PRIORITY ISSUES

### 3. Blog Posts Missing Chat Widget (6 files)

These blog posts are missing the chat widget JS:

- `blog/how-much-to-drill-a-well.html`
- `blog/how-to-tell-if-well-pump-is-bad.html`
- `blog/well-pump-repair-alpine.html`
- `blog/well-service-big-bear-lake.html`
- `blog/well-service-hesperia.html`
- `blog/well-service-nuevo.html`

**FIX:** Add `<script src="/js/chat-widget.js"></script>` before closing `</body>` tag.

---

### 4. Pages Missing lead-gen.js (Sticky Phone Header) (10 files)

- `cost-calculator.html`
- `free-guide.html`
- `downloads/well-pump-warning-signs.html`
- `public/fuel-tracker.html`
- `public/pump-sizing-tool.html`
- `public/app/fuel-tracker.html`
- `public/app/index.html`
- `public/app/splash.html`
- `public/app/well-depth.html`
- `public/app/pump-sizing-tool.html`

**Note:** The `public/` and `downloads/` folders may be intentionally excluded (app/tool pages). However, `cost-calculator.html` and `free-guide.html` should have the sticky header.

**FIX:** Add `<script src="js/lead-gen.js"></script>` to `cost-calculator.html` and `free-guide.html`.

---

### 5. Exit Popup Not Implemented (ALL pages)

No pages include `exit-popup.js` and the file does not exist in `/js/`.

**FIX:** Create `js/exit-popup.js` and add it to key pages (homepage, blog posts, service pages).

---

## 🟠 LOW PRIORITY ISSUES

### 6. Missing Meta Description (5 files)

- `privacy-policy.html`
- `terms.html`
- `404.html`
- `public/app/splash.html`
- `downloads/well-pump-warning-signs.html`

**FIX:** Add appropriate meta descriptions to each page.

---

### 7. Missing H1 Tag (1 file)

- `blog/well-pump-repair-alpine.html`

**FIX:** Add an H1 heading to the page content.

---

### 8. Duplicate Titles (4 pairs)

| Title | Count |
|-------|-------|
| Well Depth Lookup - SCWS | 2 |
| Pump Sizing Tool \| Southern California Well Service | 2 |
| Fuel Tracker \| SCWS | 2 |
| Contact Us \| Southern California Well Service | 2 |

**Note:** Duplicates are acceptable for tool/app pages that exist in multiple locations.

---

### 9. Missing Title Tag (1 file)

- `public/app/splash.html`

---

## ✅ PASSING CHECKS

### All Blog Posts Have CTAs ✓
All 420+ blog posts include the `blog-cta-box` section for lead generation.

### No Empty Alt Tags ✓
All image alt attributes have content.

### Footer Present on All Main Pages ✓
Footer consistently appears across pages.

### Navigation Consistent ✓
Nav structure matches across pages.

### Cost Calculator Page Works ✓
`cost-calculator.html` loads with proper structure, styles, and interactivity.

### Free Guide Page Works ✓
`free-guide.html` loads with proper structure, form, and styling.

### Main Phone Number Correct (in core pages) ✓
`(760) 440-8520` appears correctly 381+ times in core pages.

### Internal Links from Homepage Valid ✓
All links from index.html resolve to existing files.

---

## 📋 RECOMMENDED FIXES (Priority Order)

### 1. **URGENT - Fix Wrong Phone Numbers**
```bash
# Run from scws-website directory
find . -name "*.html" -exec sed -i '' \
  -e 's/7604409430/7604408520/g' \
  -e 's/(760) 440-9430/(760) 440-8520/g' \
  -e 's/760-440-9430/760-440-8520/g' {} \;
```

### 2. **HIGH - Create Missing Images**
Either source 22 location-specific images or update blog posts to use existing hero images.

### 3. **MEDIUM - Add Chat Widget to 6 Blog Posts**
Add chat-widget.js to the 6 blog posts missing it.

### 4. **MEDIUM - Add Sticky Header to Lead Pages**
Add lead-gen.js to cost-calculator.html and free-guide.html.

### 5. **MEDIUM - Create Exit Popup**
Create exit-popup.js and deploy to key conversion pages.

### 6. **LOW - Add Meta Descriptions**
Add meta descriptions to privacy-policy.html, terms.html, and 404.html.

---

## 📊 Statistics

| Metric | Count |
|--------|-------|
| Total HTML Files | 521 |
| Blog Posts | 420+ |
| Location Pages | 70+ |
| Service Pages | 7 |
| Root Pages | 8 |
| Images (main) | 53 |
| Images (blog) | 62 |

---

*Report generated by QC subagent*
