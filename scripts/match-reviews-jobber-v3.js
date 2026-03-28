#!/usr/bin/env node
/**
 * Match Google Reviews to Cities via Jobber (v3)
 * Pulls fresh reviews from reviews-all.json, searches Jobber for 5-star reviewer names
 */

const fs = require('fs');

const creds = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/jobber_credentials.json', 'utf8'));
const allReviews = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-gmb/reviews-all.json', 'utf8'));

// Rate limit: small delay between requests
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function searchJobber(name) {
  const query = `
    query SearchClients($searchTerm: String!) {
      clients(searchTerm: $searchTerm, first: 5) {
        nodes {
          id
          name
          firstName
          lastName
          billingAddress { city street postalCode }
        }
      }
    }
  `;

  const response = await fetch(creds.api_endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${creds.access_token}`,
      'X-JOBBER-GRAPHQL-VERSION': creds.graphql_version || '2025-06-16'
    },
    body: JSON.stringify({ query, variables: { searchTerm: name } })
  });

  const data = await response.json();
  if (data.errors) {
    if (data.errors[0]?.message?.includes('token')) {
      console.error('TOKEN EXPIRED - need re-auth');
      process.exit(1);
    }
    return [];
  }
  return data.data?.clients?.nodes || [];
}

function cleanName(displayName) {
  return displayName
    .replace(/\(.*?\)/g, '')
    .replace(/[^\w\s'-]/g, '')
    .trim();
}

function getCity(client) {
  if (client.billingAddress?.city) return client.billingAddress.city;
  return null;
}

function nameMatch(reviewerName, client) {
  const rn = reviewerName.toLowerCase().trim();
  const cn = (client.name || `${client.firstName} ${client.lastName}`).toLowerCase().trim();
  
  if (rn === cn) return true;
  
  // Check first+last
  const rParts = rn.split(/\s+/);
  const cParts = cn.split(/\s+/);
  
  if (rParts.length >= 2 && cParts.length >= 2) {
    // First name and last name match
    if (rParts[0] === cParts[0] && rParts[rParts.length-1] === cParts[cParts.length-1]) return true;
    // Last name match + first name starts with same letter
    if (rParts[rParts.length-1] === cParts[cParts.length-1] && rParts[0][0] === cParts[0][0]) return 'partial';
  }
  
  return false;
}

async function main() {
  const fiveStarReviews = [];
  
  for (const loc of allReviews) {
    const locName = loc.address?.locality || 'Unknown';
    for (const r of loc.reviews || []) {
      if (r.starRating === 'FIVE') {
        fiveStarReviews.push({
          name: r.reviewer?.displayName || 'Anonymous',
          text: r.comment || '',
          date: r.createTime?.split('T')[0] || '',
          gmbLocation: locName
        });
      }
    }
  }

  console.log(`Found ${fiveStarReviews.length} five-star reviews to match`);
  
  const reviewsByCity = {};
  let matched = 0;
  let unmatched = 0;
  const unmatchedNames = [];

  for (let i = 0; i < fiveStarReviews.length; i++) {
    const review = fiveStarReviews[i];
    const cleanedName = cleanName(review.name);
    
    if (cleanedName.toLowerCase() === 'anonymous' || cleanedName.length < 3) {
      unmatchedNames.push(review.name);
      unmatched++;
      continue;
    }

    // Search Jobber
    const clients = await searchJobber(cleanedName);
    await sleep(200); // rate limit
    
    let city = null;
    let bestMatch = null;

    for (const client of clients) {
      const match = nameMatch(cleanedName, client);
      if (match === true) {
        city = getCity(client);
        bestMatch = client;
        break;
      } else if (match === 'partial' && !bestMatch) {
        city = getCity(client);
        bestMatch = client;
      }
    }

    if (city) {
      // Normalize city name
      city = city.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
      
      if (!reviewsByCity[city]) reviewsByCity[city] = [];
      reviewsByCity[city].push({
        name: review.name,
        text: review.text,
        date: review.date
      });
      matched++;
      process.stdout.write(`✓ ${cleanedName} → ${city}\n`);
    } else {
      unmatched++;
      unmatchedNames.push(cleanedName);
      process.stdout.write(`✗ ${cleanedName}\n`);
    }
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

  const outPath = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';
  fs.writeFileSync(outPath, JSON.stringify(sorted, null, 2));

  console.log(`\n=== RESULTS ===`);
  console.log(`Matched: ${matched}/${fiveStarReviews.length}`);
  console.log(`Unmatched: ${unmatched}`);
  console.log(`Cities: ${Object.keys(sorted).length}`);
  console.log(`\nCities with testimonials:`);
  for (const [city, reviews] of Object.entries(sorted)) {
    console.log(`  ${city}: ${reviews.length} review(s)`);
  }
  console.log(`\nUnmatched names (${unmatchedNames.length}):`);
  for (const n of unmatchedNames.slice(0, 30)) {
    console.log(`  - ${n}`);
  }
  if (unmatchedNames.length > 30) console.log(`  ... and ${unmatchedNames.length - 30} more`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
