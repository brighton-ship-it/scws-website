# SCWS Website Image Audit Report
**Date:** 2026-03-12

## 📊 Summary

- **Total Pages Scanned:** 9,920
- **Total Images Found:** 34,875
- **Pages with No Images:** 20
- **Pages Missing og:image:** 843

## 🚨 Critical Issues

### Broken/Missing Images
- **Empty src attributes:** 2
- **Broken relative paths:** 112

#### Empty src attributes:
- `gallery.html`
- `recent-work/index.html`

#### Broken relative paths:
- `blog/well-service-san-jacinto.html` → `../images/hero-mountain-foothills.jpg?v=2`
- `blog/well-service-oak-glen.html` → `../images/hero-default.jpg?v=2`
- `blog/well-service-dulzura.html` → `../images/hero-rural-hills.jpg?v=2`
- `blog/well-service-jamul.html` → `../images/hero-jamul-mountains.jpg?v=2`
- `blog/well-service-tecate.html` → `../images/hero-rural-hills.jpg?v=2`
- `blog/well-drilling-contractor.html` → `../images/hero-contractor-license.jpg?v=2`
- `blog/well-service-victorville.html` → `../images/hero-well-drilling.jpg?v=2`
- `blog/well-service-rancho-santa-fe.html` → `../images/hero-rancho-santa-fe.jpg?v=2`
- `blog/hydrofracturing-well-service.html` → `/assets/images/blog-images/hydrofracturing.png`
- `blog/well-service-lakeside.html` → `../images/hero-lakeside-river.jpg?v=2`
- `blog/well-service-de-luz.html` → `../images/hero-de-luz-wilderness.jpg?v=2`
- `blog/well-water-insurance-coverage.html` → `/assets/images/blog-images/insurance-coverage.png`
- `blog/well-water-insurance-coverage.html` → `/assets/images/article-categories/costs.png`
- `blog/well-water-insurance-coverage.html` → `/assets/images/article-categories/repair.png`
- `blog/well-service-santee.html` → `../images/hero-santee.jpg?v=2`
- `blog/well-water-for-irrigation-landscaping.html` → `/assets/images/blog-images/irrigation-well.png`
- `blog/well-service-apple-valley.html` → `../images/hero-desert-landscape.jpg?v=2`
- `blog/well-service-el-cajon.html` → `../images/hero-east-county.jpg?v=2`
- `blog/well-drilling-moreno-valley.html` → `../images/hero-well-drilling.jpg?v=2`
- `blog/well-drilling-companies-near-me.html` → `../images/hero-drilling-rig.jpg?v=2`
- ... and 92 more

## 🔍 SEO & Accessibility Issues

### Missing Alt Text
- **Total:** 1 images
- **Impact:** Hurts SEO and accessibility

### Missing og:image Tags
- **Total:** 843 pages
- **Impact:** Poor social sharing CTR

#### Sample pages missing og:image:
- `pump-repair.html`
- `well-drilling.html`
- `privacy-policy.html`
- `terms.html`
- `404.html`
- `ransom-pump.html`
- `cost-calculator.html`
- `heritage-well-service.html`
- `emergency.html`
- `free-guide.html`
- ... and 833 more

## ⚡ Performance Issues (Core Web Vitals)

### Missing Width/Height Attributes
- **Total:** 26,506 images
- **Impact:** Causes Cumulative Layout Shift (CLS), hurts Core Web Vitals

### Non-Optimized Image Formats
- **Total:** 0
## 🌐 External Images
- **Total:** 258
- **Impact:** Slower load times, dependency on external services

#### Sample external images:
- `images.unsplash.com` (258 images)

## 🖼️ Most Commonly Used Images
*Detecting placeholder/stock image overuse*

- `../images/logo-text-only-3x.png` — used **8,808 times**
- `/assets/images/article-categories/maintenance.png` — used **6,002 times**
- `/assets/images/article-categories/troubleshooting.png` — used **5,990 times**
- `/assets/images/article-categories/pressure-issues.png` — used **5,080 times**
- `/images/logo-text-only-3x.png` — used **2,710 times**
- `/assets/images/article-categories/agricultural.png` — used **1,208 times**
- `/assets/images/article-categories/water-quality.png` — used **915 times**
- `/assets/images/blog-images/well-service-5.png` — used **323 times**
- `/assets/images/article-categories/emergency.png` — used **313 times**
- `/assets/images/article-categories/drilling.png` — used **303 times**
- `/assets/images/blog-images/well-service-3.png` — used **275 times**
- `/assets/images/blog-images/well-service-2.png` — used **269 times**
- `/assets/images/blog-images/well-service-1.png` — used **246 times**
- `/assets/images/blog-images/well-service-4.png` — used **244 times**
- `/assets/images/blog-images/well-drilling-5.png` — used **166 times**
- `/assets/images/blog-images/well-drilling-3.png` — used **139 times**
- `/assets/images/blog-images/well-drilling-4.png` — used **120 times**
- `/assets/images/blog-images/hard-water.png` — used **118 times**
- `/assets/images/blog-images/well-drilling-1.png` — used **109 times**
- `/assets/images/blog-images/well-drilling-2.png` — used **91 times**

## 📈 Image Format Distribution

- `.png` — 34,391 images
- `.jpg` — 151 images
- `.jpg?v=2` — 73 images
- `.jpg?v=2fit=crop` — 12 images
- `.jpgfit=crop` — 6 images

## 📄 Pages with No Images
- **Total:** 20
- **Impact:** Missed engagement opportunity

#### Sample pages:
- `emergency.html`
- `tools/inventory/index.html`
- `tools/welldepth/index.html`
- `node_modules/bignumber.js/doc/API.html`
- `blog/well-pump-repair-alpine.html`
- `public/fuel-tracker.html`
- `public/pump-sizing-tool.html`
- `public/app/fuel-tracker.html`
- `public/app/index.html`
- `public/app/splash.html`
- `public/app/well-depth.html`
- `public/app/pump-sizing-tool.html`
- `downloads/well-pump-warning-signs.html`
- `pages/service-area.html`
- `pages/videos.html`
- ... and 5 more

## ✅ Recommendations

### 🚨 High Priority

1. **Fix 112 broken image paths** — These images won't load
3. **Add og:image tags to 843 pages** — Improves social sharing CTR

### ⚡ Performance

4. **Add width/height to 26,506 images** — Prevents layout shift (CLS)
6. **Consider hosting 258 external images locally** — Better performance & control

### 📸 Content

7. **Add images to 20 pages** — Visual content improves engagement
8. **Replace overused stock images** — 10 images appear on 50+ pages

---

*Generated by SCWS Image Audit Script*