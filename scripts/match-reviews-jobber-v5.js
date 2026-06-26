#!/usr/bin/env node
/**
 * Match Google reviews to Jobber clients by name to get city data
 * Then rebuild reviews-by-city.json
 * v5: Check both billingAddress and properties[].address for city
 */

const fs = require('fs');

// Load data
const allReviews = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-gmb/reviews-all.json', 'utf8'));
const credentials = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/jobber_credentials.json', 'utf8'));

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

console.log(`Found ${fiveStarReviews.length} five-star reviews from GMB`);

// Query Jobber for clients matching these names
async function matchReviewsToClients() {
  const matched = [];
  const unmatched = [];
  
  for (const review of fiveStarReviews) {
    // Try to find client in Jobber by name - include properties
    const query = `
      query SearchClients($searchTerm: String!) {
        clients(searchTerm: $searchTerm, first: 5) {
          nodes {
            id
            firstName
            lastName
            billingAddress {
              city
              province
            }
            properties {
              address {
                city
                province
                street1
              }
            }
          }
        }
      }
    `;
    
    try {
      const response = await fetch(credentials.api_endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json',
          'X-JOBBER-GRAPHQL-VERSION': credentials.graphql_version
        },
        body: JSON.stringify({
          query: query,
          variables: { searchTerm: review.name }
        })
      });
      
      const result = await response.json();
      
      if (result.data?.clients?.nodes?.length > 0) {
        // Find best match
        const client = result.data.clients.nodes[0];
        const fullName = `${client.firstName} ${client.lastName}`.toLowerCase().trim();
        const reviewName = review.name.toLowerCase().trim();
        
        // Check if it's a reasonable match (allow for minor differences)
        const isMatch = fullName.includes(reviewName) || 
                       reviewName.includes(fullName) ||
                       (fullName.length > 0 && reviewName.split(' ').some(word => fullName.includes(word)));
        
        if (isMatch) {
          // Try billingAddress first, then properties
          let city = client.billingAddress?.city;
          let source = 'billing';
          
          if (!city && client.properties && client.properties.length > 0) {
            city = client.properties[0].address?.city;
            source = 'property';
          }
          
          if (city) {
            matched.push({
              reviewer: review.name,
              city: city,
              text: review.text,
              date: review.date,
              jobberMatch: `${client.firstName} ${client.lastName}`,
              citySource: source
            });
            console.log(`✓ Matched: ${review.name} → ${city} (${source})`);
          } else {
            unmatched.push({ reviewer: review.name, reason: 'No city in Jobber' });
            console.log(`⚠ ${review.name} → No city in Jobber`);
          }
        } else {
          unmatched.push({ reviewer: review.name, reason: 'Name mismatch' });
          console.log(`⚠ ${review.name} → Name mismatch`);
        }
      } else {
        unmatched.push({ reviewer: review.name, reason: 'Not found in Jobber' });
        console.log(`✗ ${review.name} → Not found in Jobber`);
      }
      
      // Rate limit: wait 100ms between requests
      await new Promise(resolve => setTimeout(resolve, 100));
      
    } catch (error) {
      console.error(`Error matching ${review.name}:`, error.message);
      unmatched.push({ reviewer: review.name, reason: error.message });
    }
  }
  
  return { matched, unmatched };
}

// Build reviews-by-city structure
function buildReviewsByCity(matches) {
  const reviewsByCity = {};
  
  for (const match of matches) {
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
  
  return sorted;
}

// Main execution
(async () => {
  console.log('\n🔍 Matching reviews to Jobber clients...\n');
  
  const { matched, unmatched } = await matchReviewsToClients();
  
  console.log('\n📊 Results:');
  console.log(`  Matched: ${matched.length}`);
  console.log(`  Unmatched: ${unmatched.length}`);
  console.log(`  Match rate: ${((matched.length / fiveStarReviews.length) * 100).toFixed(1)}%`);
  
  // Save match results
  fs.writeFileSync(
    '/Users/jarvis/clawd/scws-website/scripts/review-matches.json',
    JSON.stringify({ matched, unmatched }, null, 2)
  );
  
  // Build and save reviews-by-city
  const reviewsByCity = buildReviewsByCity(matched);
  fs.writeFileSync(
    '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json',
    JSON.stringify(reviewsByCity, null, 2)
  );
  
  console.log('\n📍 Reviews by city:');
  const cities = Object.keys(reviewsByCity).sort();
  for (const city of cities) {
    console.log(`  ${city}: ${reviewsByCity[city].length} reviews`);
  }
  
  console.log(`\n✓ Saved to reviews-by-city.json`);
  console.log(`  Total cities: ${cities.length}`);
  console.log(`  Total reviews: ${matched.length}`);
})();
