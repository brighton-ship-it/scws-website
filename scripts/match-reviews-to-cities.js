#!/usr/bin/env node
/**
 * Match Google Reviews to Jobber clients to get cities
 */

const fs = require('fs');
const https = require('https');
const path = require('path');

const REVIEWS_PATH = '/Users/jarvis/clawd/scws-gmb/reviews.json';
const CREDS_PATH = '/Users/jarvis/clawd/jobber_credentials.json';
const OUTPUT_PATH = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';

// Load reviews
const allReviews = JSON.parse(fs.readFileSync(REVIEWS_PATH, 'utf8'));
const creds = JSON.parse(fs.readFileSync(CREDS_PATH, 'utf8'));

// Extract 5-star reviews with reviewer names
const fiveStarReviews = [];
for (const location of allReviews) {
  const locationName = location.address?.locality || 'Unknown';
  for (const review of location.reviews || []) {
    if (review.starRating === 'FIVE' && review.reviewer?.displayName) {
      fiveStarReviews.push({
        name: review.reviewer.displayName,
        text: review.comment || '',
        date: review.createTime?.split('T')[0] || '',
        locationName
      });
    }
  }
}

console.log(`Found ${fiveStarReviews.length} 5-star reviews to match\n`);

// Search for client in Jobber
function searchClient(name) {
  return new Promise((resolve, reject) => {
    const query = JSON.stringify({
      query: `query SearchClients($searchTerm: String!) {
        clients(searchTerm: $searchTerm, first: 5) {
          nodes {
            id
            name
            billingAddress { city street postalCode }
            clientProperties { nodes { address { city street } } }
          }
        }
      }`,
      variables: { searchTerm: name }
    });

    const options = {
      hostname: 'api.getjobber.com',
      path: '/api/graphql',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${creds.access_token}`,
        'X-JOBBER-GRAPHQL-VERSION': creds.graphql_version
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(body);
          resolve(result.data?.clients?.nodes || []);
        } catch (e) {
          resolve([]);
        }
      });
    });

    req.on('error', () => resolve([]));
    req.write(query);
    req.end();
  });
}

// Normalize name for matching
function normalizeName(name) {
  return name.toLowerCase().replace(/[^a-z ]/g, '').trim();
}

// Extract city from full address string (e.g., "123 Main St, City, CA 92123")
function extractCityFromStreet(street) {
  if (!street) return null;
  
  // Pattern: street, city, state zip
  const match = street.match(/,\s*([A-Za-z\s]+),\s*(?:California|CA)\s*\d{5}/i);
  if (match) {
    return match[1].trim();
  }
  return null;
}

// Get best city from client data
function getCityFromClient(client) {
  // Try billing address city first
  if (client.billingAddress?.city?.trim()) {
    return client.billingAddress.city.trim();
  }
  
  // Try property address
  const prop = client.clientProperties?.nodes?.[0];
  if (prop?.address?.city?.trim()) {
    return prop.address.city.trim();
  }
  
  // Try extracting from billing street
  if (client.billingAddress?.street) {
    const city = extractCityFromStreet(client.billingAddress.street);
    if (city) return city;
  }
  
  // Try extracting from property street
  if (prop?.address?.street) {
    const city = extractCityFromStreet(prop.address.street);
    if (city) return city;
  }
  
  return null;
}

// Main matching logic
async function matchReviews() {
  const reviewsByCity = {};
  let matched = 0;
  let unmatched = 0;

  for (const review of fiveStarReviews) {
    // Clean up display name (remove emojis, extra chars)
    const cleanName = review.name.replace(/[^\w\s'-]/g, '').trim();
    
    // Skip generic/business names
    if (!cleanName || cleanName.length < 3) {
      unmatched++;
      continue;
    }

    // Try searching with full name first
    let clients = await searchClient(cleanName);
    
    // If no results, try first name only
    if (clients.length === 0) {
      const firstName = cleanName.split(' ')[0];
      if (firstName.length >= 3) {
        clients = await searchClient(firstName);
      }
    }
    
    // Look for a matching name
    let matchedCity = null;
    const normalizedReviewName = normalizeName(cleanName);
    
    for (const client of clients) {
      const normalizedClientName = normalizeName(client.name);
      
      // Check if names match (either exact or first+last in either order)
      const reviewParts = normalizedReviewName.split(' ').filter(p => p.length > 1);
      const clientParts = normalizedClientName.split(' ').filter(p => p.length > 1);
      
      // Must share at least 2 name parts for multi-word names, or 1 for single names
      const sharedParts = reviewParts.filter(p => clientParts.includes(p));
      
      const isMatch = sharedParts.length >= 2 || 
          (reviewParts.length === 1 && clientParts.includes(reviewParts[0])) ||
          normalizedClientName.includes(normalizedReviewName) ||
          normalizedReviewName.includes(normalizedClientName);
      
      if (isMatch) {
        matchedCity = getCityFromClient(client);
        if (matchedCity) {
          break;
        }
      }
    }

    if (matchedCity) {
      // Normalize city name (title case)
      matchedCity = matchedCity.split(' ')
        .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
        .join(' ');

      if (!reviewsByCity[matchedCity]) {
        reviewsByCity[matchedCity] = [];
      }

      reviewsByCity[matchedCity].push({
        name: review.name,
        text: review.text,
        date: review.date
      });

      console.log(`✅ ${review.name} → ${matchedCity}`);
      matched++;
    } else {
      console.log(`❌ ${review.name} (no match)`);
      unmatched++;
    }

    // Small delay to avoid rate limiting
    await new Promise(r => setTimeout(r, 100));
  }

  // Save results
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(reviewsByCity, null, 2));
  
  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`Matched: ${matched}`);
  console.log(`Unmatched: ${unmatched}`);
  console.log(`Cities found: ${Object.keys(reviewsByCity).length}`);
  console.log(`\nSaved to: ${OUTPUT_PATH}`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);

  // Print summary by city
  console.log('Reviews by City:');
  for (const [city, reviews] of Object.entries(reviewsByCity).sort((a, b) => b[1].length - a[1].length)) {
    console.log(`  ${city}: ${reviews.length} reviews`);
  }

  return { matched, unmatched, cities: Object.keys(reviewsByCity).length };
}

matchReviews().catch(console.error);
