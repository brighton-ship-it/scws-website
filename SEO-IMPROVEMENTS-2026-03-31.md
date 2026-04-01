# SEO Improvements - March 31, 2026

## Task 1: Sitemap Expansion ✅

**Problem:** The website had 744+ city service pages that were not included in any sitemap, making them invisible to Google.

**Solution:**
- Created `sitemap-services.xml` containing **753 URLs**:
  - All 744 city-specific service pages under `/services/{city}/{service}.html`
  - All 9 main service pages under `/pages/services/*.html`
- Updated `sitemap.xml` (the sitemap index) to include the new sitemap-services.xml
- Set `lastmod` to 2026-03-31 and `priority` to 0.8 for all service pages

**Result:** Google can now discover and index all service pages. This should significantly improve organic traffic from location-specific searches.

**Files Modified:**
- `sitemap.xml` - Added reference to sitemap-services.xml
- `sitemap-services.xml` - **NEW FILE** with 753 service page URLs

---

## Task 2: Internal Link Building ✅

**Problem:** Top 20 blog posts (189-36 clicks/month) had no internal links to service pages, missing opportunity to drive traffic to conversion pages.

**Solution:**
Added contextually relevant CTA boxes to all 20 top-performing blog posts:
1. ✅ no-water-from-well.html → diagnostics + pump-repair
2. ✅ best-submersible-pump-brands.html → pump-repair
3. ✅ well-tank-sizing-guide.html → maintenance
4. ✅ how-to-prime-well-pump-guide.html → pump-repair
5. ✅ well-pump-short-cycling.html → diagnostics + pump-repair
6. ✅ well-pump-runs-but-no-water.html → pump-repair + emergency
7. ✅ well-pressure-tank-sizing-guide.html → maintenance
8. ✅ average-well-cost.html → well-drilling
9. ✅ electric-bill-high-well-pump.html → diagnostics
10. ✅ signs-well-pump-failing.html → pump-repair
11. ✅ how-to-prime-well-pump.html → pump-repair
12. ✅ air-bubbles-in-well-water.html → diagnostics
13. ✅ well-pump-replacement-cost-breakdown-2026.html → pump-repair
14. ✅ best-pump-brand-for-deep-wells.html → pump-repair
15. ✅ well-pump-sizing-guide.html → pump-repair
16. ✅ well-pump-installation-cost.html → pump-repair + well-drilling
17. ✅ well-pump-runs-every-few-minutes.html → diagnostics
18. ✅ well-pump-sizing-calculator.html → pump-repair
19. ✅ black-specks-well-water.html → water-testing
20. ✅ cost-of-water-well-drilling.html → well-drilling

**CTA Format:**
Each CTA box includes:
- Professional, branded styling (SCWS green #4e9271)
- Service-specific messaging
- Direct link to relevant service page
- Click-to-call button (760) 440-8520
- Company credentials (Licensed C-57, 4.9★ rating)

**Expected Impact:**
- Improved internal PageRank flow to service pages
- Higher conversion rate from blog traffic
- Better user experience (readers get immediate help options)
- Reduced bounce rate

---

## Next Steps (Recommended)

1. **Submit updated sitemap to Google Search Console**
   - URL: https://scwellservice.com/sitemap.xml
   - Monitor indexing status over next 2-4 weeks

2. **Monitor performance:**
   - Track clicks from blog posts to service pages in GA4
   - Watch for increased impressions/clicks for city-specific service searches in GSC
   - Measure conversion rate from internal CTA links

3. **Deploy changes:**
   - All files are ready for deployment
   - No breaking changes - purely additive improvements

---

**Completion Date:** March 31, 2026
**Files Modified:** 21 total (1 sitemap index, 1 new sitemap, 20 blog posts)
**New URLs Discoverable:** 753 service pages
