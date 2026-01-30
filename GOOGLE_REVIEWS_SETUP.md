# Google Reviews Widget Setup

## Quick Start (5 minutes)

### Step 1: Get a Google Cloud API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing (your Google Workspace should work)
3. Go to **APIs & Services** → **Library**
4. Search for and enable:
   - **Places API**
   - **Maps JavaScript API**
5. Go to **APIs & Services** → **Credentials**
6. Click **Create Credentials** → **API Key**
7. Click on the key to restrict it:
   - **Application restrictions**: HTTP referrers
   - Add your domains: `scwellservice.com/*`, `*.scwellservice.com/*`
   - **API restrictions**: Restrict to Places API and Maps JavaScript API

### Step 2: Add to Website

1. Open `js/google-reviews.js`
2. Replace `YOUR_API_KEY_HERE` with your actual API key

### Step 3: Add Scripts to HTML

Add these lines before `</body>` in your HTML:

```html
<!-- Google Maps API with Places library -->
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places"></script>
<!-- Reviews Widget -->
<script src="js/google-reviews.js"></script>
```

### Step 4: Use in HTML

Add these data attributes where you want live data:

```html
<!-- Rating number -->
<span data-reviews-rating>4.9</span>

<!-- Rating text -->
<span data-reviews-text>on Google</span>

<!-- Total review count (both locations) -->
<span data-reviews-count>108 reviews</span>
```

## Place IDs

Your business Place IDs:
- **Ramona**: `ChIJnVbrUVH7_YARQO2fqNKjo40`
- **Anza**: `ChIJj4LVzZgR24ARH4bwK2fOYc4`

## Costs

Google gives you $200/month free credit. The Places API costs ~$0.017 per request.
At 1000 page views/day = ~$0.51/day = ~$15/month (well under free tier).

The widget caches results for 60 minutes to minimize API calls.

## Display Modes

In `google-reviews.js`, you can change `displayMode`:
- `'highest'` - Shows the best rating (4.9)
- `'average'` - Shows weighted average of both locations  
- `'both'` - Shows both ratings (4.7/4.9)
