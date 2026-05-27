#!/usr/bin/env node
/**
 * Rebuild reviews-by-city.json from review-matches.json + reviews-all.json
 */

const fs = require('fs');

const matches = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-website/scripts/review-matches.json', 'utf8'));
const allReviews = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-gmb/reviews-all.json', 'utf8'));

// Build lookup map of all reviews by reviewer name
const reviewLookup = {};
for (const loc of allReviews) {
  for (const r of loc.reviews || []) {
    const name = r.reviewer?.displayName;
    if (name && r.starRating === 'FIVE') {
      reviewLookup[name] = {
        name: name,
        text: r.comment || '',
        date: r.createTime?.split('T')[0] || ''
      };
    }
  }
}

// Build city-based structure
const reviewsByCity = {};

for (const match of matches.matched) {
  let city = match.city;
  if (!city) continue;
  
  // Normalize city name (title case)
  city = city.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  
  const review = reviewLookup[match.reviewer];
  if (!review) {
    console.log(`⚠ No review found for ${match.reviewer}`);
    continue;
  }
  
  if (!reviewsByCity[city]) {
    reviewsByCity[city] = [];
  }
  
  reviewsByCity[city].push(review);
}

// Sort reviews within each city by date (newest first)
for (const city of Object.keys(reviewsByCity)) {
  reviewsByCity[city].sort((a, b) => b.date.localeCompare(a.date));
}

// Sort cities alphabetically
const sorted = {};
for (const city of Object.keys(reviewsByCity).sort()) {
  sorted[city] = reviewsByCity[city];
}

// Save
const outPath = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';
fs.writeFileSync(outPath, JSON.stringify(sorted, null, 2));

console.log(`✓ Rebuilt reviews-by-city.json`);
console.log(`  Cities: ${Object.keys(sorted).length}`);
console.log(`  Total reviews: ${Object.values(sorted).reduce((sum, arr) => sum + arr.length, 0)}`);
console.log('');
console.log('Reviews by city:');
for (const [city, reviews] of Object.entries(sorted)) {
  console.log(`  ${city}: ${reviews.length}`);
}
