# SCWS Website Fix: Edge-to-Edge Layout + Hero Image Cache Busting
**Date:** March 12, 2026  
**Commit:** `c8c38d6ac`

## Issues Fixed

### 1. ✅ Edge-to-Edge Layout on Mobile Safari
**Problem:** White padding around emergency banner, header, and hero image on iOS Safari

**Fix Applied:**
- Added inline CSS to all 9,917 HTML files forcing:
  ```css
  html, body {
      margin: 0 !important;
      padding: 0 !important;
      overflow-x: hidden;
  }
  ```
- This overrides any conflicting styles and ensures edge-to-edge layout on mobile

### 2. ✅ Hero Image Cache Busting
**Problem:** Brighton's phone still showing old AI construction worker images despite repo having correct photos

**Fix Applied:**
- Added `?v=2` cache-busting query string to all 97 hero image references
- Example: `hero-pump-service.jpg` → `hero-pump-service.jpg?v=2`
- Forces browsers to fetch the new images instead of using cached versions

## Deployment Details

**Repository:** https://github.com/brighton-ship-it/scws-website.git  
**Hosting:** GitHub Pages  
**CDN:** Fastly  

**Files Modified:** 9,917 HTML files  
**Hero Images Updated:** 97 references  
**Edge-to-Edge Styles Added:** 9,917 pages  

## Verification

✅ Live site tested: https://scwellservice.com/blog/well-pump-installation-cost.html
- Edge-to-edge CSS present in `<head>`
- Hero image has `?v=2` cache-busting parameter
- No broken HTML

## For Brighton

The fixes are now live on scwellservice.com. You may need to:
1. **Hard refresh your iPhone Safari** (hold refresh button → "Reload Without Content Blockers")
2. **Clear Safari cache** if the old images still appear
3. **Wait 10 minutes** for CDN cache to fully expire (cache-control: max-age=600)

If you still see the old hero images after clearing cache, they should update automatically within 10 minutes as the CDN cache expires.

## Technical Notes

- The site uses GitHub Pages with Fastly CDN
- CDN caching is set to 10 minutes (max-age=600)
- Deployment took ~90 seconds after git push
- All HTML files validated and no syntax errors introduced
