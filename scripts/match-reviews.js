#!/usr/bin/env node
/**
 * Match Google Reviews to Jobber Clients to get cities
 */

const fs = require('fs');
const path = require('path');

// Load reviews
const reviewsPath = '/Users/jarvis/clawd/scws-gmb/reviews.json';
const credentialsPath = '/Users/jarvis/clawd/jobber_credentials.json';

const reviews = JSON.parse(fs.readFileSync(reviewsPath, 'utf8'));
const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

// Extract 5-star reviews
const fiveStarReviews = [];
for (const location of reviews) {
  for (const review of location.reviews) {
    if (review.starRating === 'FIVE') {
      fiveStarReviews.push({
        name: review.reviewer.displayName,
        text: review.comment || '',
        date: review.createTime.split('T')[0],
        location: location.address.locality
      });
    }
  }
}

console.log(`Found ${fiveStarReviews.length} 5-star reviews`);

// Extract unique names for searching
const uniqueNames = [...new Set(fiveStarReviews.map(r => r.name))];
console.log(`Unique reviewer names: ${uniqueNames.length}`);

// GraphQL query to search clients by name
async function searchClient(name) {
  const query = `
    query SearchClients($searchTerm: String!) {
      clients(searchTerm: $searchTerm, first: 5) {
        nodes {
          id
          firstName
          lastName
          companyName
          billingAddress {
            city
            street
            province
            postalCode
          }
        }
      }
    }
  `;

  try {
    const response = await fetch(credentials.api_endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${credentials.access_token}`,
        'X-JOBBER-GRAPHQL-VERSION': credentials.graphql_version
      },
      body: JSON.stringify({ query, variables: { searchTerm: name } })
    });

    const data = await response.json();
    if (data.errors) {
      console.error(`Error searching "${name}":`, data.errors[0].message);
      return null;
    }
    return data.data?.clients?.nodes || [];
  } catch (err) {
    console.error(`Error searching "${name}":`, err.message);
    return null;
  }
}

// Get city from client
function getCityFromClient(client) {
  return client.billingAddress?.city || null;
}

// Match name to client
function nameMatches(reviewerName, client) {
  const reviewLower = reviewerName.toLowerCase();
  const firstName = (client.firstName || '').toLowerCase();
  const lastName = (client.lastName || '').toLowerCase();
  const fullName = `${firstName} ${lastName}`.trim();
  
  // Exact match
  if (reviewLower === fullName) return true;
  
  // First name + last initial
  if (lastName && reviewLower.includes(firstName) && reviewLower.includes(lastName[0])) return true;
  
  // Just last name match (for common patterns like "John S" matching "John Smith")
  if (firstName && lastName && reviewLower.startsWith(firstName) && reviewLower.length < fullName.length + 3) {
    return true;
  }
  
  return false;
}

async function main() {
  const reviewsByCity = {};
  let matched = 0;
  let unmatched = 0;
  
  console.log('\nSearching Jobber for reviewer matches...\n');
  
  for (const review of fiveStarReviews) {
    // Skip reviews without text (less useful)
    if (!review.text) {
      unmatched++;
      continue;
    }
    
    // Clean up name for searching
    let searchName = review.name;
    // Remove common suffixes/prefixes
    searchName = searchName.replace(/\s*\([^)]*\)/g, ''); // Remove parenthetical
    searchName = searchName.replace(/#\d+/g, ''); // Remove #6 etc
    searchName = searchName.trim();
    
    // Skip obvious non-personal names
    if (searchName.includes('Retreat') || searchName.includes('Videos') || 
        searchName.includes('omg') || searchName.length < 3) {
      unmatched++;
      continue;
    }
    
    const clients = await searchClient(searchName);
    
    if (clients && clients.length > 0) {
      // Find best match
      for (const client of clients) {
        const city = getCityFromClient(client);
        if (city && nameMatches(review.name, client)) {
          const cityKey = city.toLowerCase().replace(/\s+/g, '-');
          if (!reviewsByCity[cityKey]) {
            reviewsByCity[cityKey] = [];
          }
          reviewsByCity[cityKey].push({
            name: review.name,
            text: review.text,
            date: review.date
          });
          matched++;
          console.log(`✓ ${review.name} → ${city}`);
          break;
        }
      }
    }
    
    // Rate limit - be nice to Jobber API
    await new Promise(r => setTimeout(r, 200));
  }
  
  unmatched = fiveStarReviews.length - matched;
  
  console.log(`\n=== Results ===`);
  console.log(`Matched: ${matched}`);
  console.log(`Unmatched: ${unmatched}`);
  console.log(`Cities with reviews: ${Object.keys(reviewsByCity).length}`);
  
  // Save results
  const outputPath = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';
  fs.writeFileSync(outputPath, JSON.stringify(reviewsByCity, null, 2));
  console.log(`\nSaved to ${outputPath}`);
  
  // Print city summary
  console.log('\nReviews by city:');
  for (const [city, cityReviews] of Object.entries(reviewsByCity).sort((a, b) => b[1].length - a[1].length)) {
    console.log(`  ${city}: ${cityReviews.length} reviews`);
  }
}

main().catch(console.error);
