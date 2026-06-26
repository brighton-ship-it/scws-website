#!/usr/bin/env node
/**
 * Match Google reviews to Jobber clients using local CSV export
 * v6: CSV-based matching for better reliability
 */

const fs = require('fs');
const { parse } = require('csv-parse/sync');

// Load reviews
const allReviews = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-gmb/reviews-all.json', 'utf8'));

// Load Jobber clients CSV
const clientsCsv = fs.readFileSync('/Users/jarvis/clawd/scws/jobber-exports/clients_all.csv', 'utf8');
const clients = parse(clientsCsv, {
  columns: true,
  skip_empty_lines: true
});

console.log(`📊 Loaded ${clients.length} clients from Jobber export`);

// Extract all 5-star reviews
const fiveStarReviews = [];
for (const loc of allReviews) {
  for (const r of loc.reviews || []) {
    if (r.starRating === 'FIVE') {
      const name = r.reviewer?.displayName;
      if (name) {
        fiveStarReviews.push({
          name: name,
          text: r.comment || '',
          date: r.createTime?.split('T')[0] || '',
          location: loc.name
        });
      }
    }
  }
}

console.log(`📊 Found ${fiveStarReviews.length} five-star reviews from GMB\n`);

// Normalize name for matching
function normalizeName(name) {
  return name.toLowerCase()
    .replace(/[^\w\s]/g, '') // Remove punctuation
    .replace(/\s+/g, ' ')     // Normalize whitespace
    .trim();
}

// Match reviews to clients
const matched = [];
const unmatched = [];

for (const review of fiveStarReviews) {
  const reviewName = normalizeName(review.name);
  const reviewWords = reviewName.split(' ');
  
  let bestMatch = null;
  let bestScore = 0;
  
  for (const client of clients) {
    // Build searchable client name variations
    const firstName = client['First Name'] || '';
    const lastName = client['Last Name'] || '';
    const displayName = client['Display Name'] || '';
    const companyName = client['Company Name'] || '';
    
    const clientVariations = [
      normalizeName(`${firstName} ${lastName}`),
      normalizeName(displayName),
      normalizeName(companyName),
      normalizeName(firstName),
      normalizeName(lastName)
    ].filter(v => v.length > 0);
    
    // Score each variation
    for (const clientName of clientVariations) {
      if (!clientName) continue;
      
      let score = 0;
      
      // Exact match = best
      if (clientName === reviewName) {
        score = 100;
      }
      // One contains the other
      else if (clientName.includes(reviewName) || reviewName.includes(clientName)) {
        score = 80;
      }
      // Word-by-word matching
      else {
        const clientWords = clientName.split(' ');
        const matchingWords = reviewWords.filter(w => clientWords.includes(w)).length;
        score = (matchingWords / Math.max(reviewWords.length, clientWords.length)) * 60;
      }
      
      if (score > bestScore) {
        bestScore = score;
        bestMatch = client;
      }
    }
  }
  
  // Accept matches with score >= 60
  if (bestMatch && bestScore >= 60) {
    const city = bestMatch['Billing City'] || bestMatch['Service City'] || null;
    const citySource = bestMatch['Billing City'] ? 'billing' : 'service';
    
    if (city) {
      matched.push({
        reviewer: review.name,
        city: city,
        text: review.text,
        date: review.date,
        jobberMatch: bestMatch['Display Name'],
        matchScore: Math.round(bestScore),
        citySource: citySource
      });
      console.log(`✓ ${review.name} → ${city} (${bestMatch['Display Name']}, score: ${Math.round(bestScore)})`);
    } else {
      unmatched.push({ reviewer: review.name, reason: 'No city in Jobber' });
      console.log(`⚠ ${review.name} → No city (matched ${bestMatch['Display Name']})`);
    }
  } else {
    unmatched.push({ reviewer: review.name, reason: 'Not found in Jobber' });
    console.log(`✗ ${review.name} → Not found`);
  }
}

console.log('\n📊 Results:');
console.log(`  Matched: ${matched.length}`);
console.log(`  Unmatched: ${unmatched.length}`);
console.log(`  Match rate: ${((matched.length / fiveStarReviews.length) * 100).toFixed(1)}%`);

// Save match results
fs.writeFileSync(
  '/Users/jarvis/clawd/scws-website/scripts/review-matches.json',
  JSON.stringify({ matched, unmatched }, null, 2)
);

// Build reviews-by-city structure
const reviewsByCity = {};

for (const match of matched) {
  let city = match.city;
  if (!city) continue;
  
  // Normalize city name (title case)
  city = city.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  
  if (!reviewsByCity[city]) {
    reviewsByCity[city] = [];
  }
  
  reviewsByCity[city].push({
    name: match.reviewer,
    text: match.text,
    date: match.date
  });
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

fs.writeFileSync(
  '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json',
  JSON.stringify(sorted, null, 2)
);

console.log('\n📍 Reviews by city:');
const cities = Object.keys(sorted).sort();
for (const city of cities) {
  console.log(`  ${city}: ${sorted[city].length} reviews`);
}

console.log(`\n✓ Saved to reviews-by-city.json`);
console.log(`  Total cities: ${cities.length}`);
console.log(`  Total reviews: ${matched.length}`);
