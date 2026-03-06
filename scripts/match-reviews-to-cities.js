#!/usr/bin/env node
/**
 * Match Google Reviews to Jobber Clients to get city data
 */

const fs = require('fs');
const path = require('path');

const JOBBER_CREDS = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/jobber_credentials.json'));
const REVIEWS_PATH = '/Users/jarvis/clawd/scws-gmb/reviews.json';
const OUTPUT_PATH = path.join(__dirname, 'reviews-by-city.json');

async function searchJobberClients(searchTerm) {
  const query = `
    query SearchClients($searchTerm: String!) {
      clients(searchTerm: $searchTerm, first: 5) {
        nodes {
          id
          name
          firstName
          lastName
          billingAddress {
            city
            street
            postalCode
          }
        }
      }
    }
  `;

  try {
    const response = await fetch('https://api.getjobber.com/api/graphql', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${JOBBER_CREDS.access_token}`,
        'X-JOBBER-GRAPHQL-VERSION': '2023-11-15'
      },
      body: JSON.stringify({ query, variables: { searchTerm } })
    });

    const data = await response.json();
    
    if (data.errors) {
      console.error(`  Error searching for "${searchTerm}":`, data.errors[0]?.message);
      return null;
    }
    
    if (data.message) {
      console.error(`  API error: ${data.message}`);
      return null;
    }

    return data.data?.clients?.nodes || [];
  } catch (err) {
    console.error(`  Network error searching for "${searchTerm}":`, err.message);
    return null;
  }
}

function extractCity(client) {
  // Try billing address city
  if (client.billingAddress?.city && client.billingAddress.city.trim()) {
    return client.billingAddress.city.trim();
  }
  
  // Try to parse city from street address (format: "Street, City, State ZIP")
  const street = client.billingAddress?.street || '';
  const parts = street.split(',');
  if (parts.length >= 3) {
    // Format: "123 Main St, City, CA 92xxx"
    const cityPart = parts[parts.length - 2]?.trim();
    if (cityPart && !cityPart.match(/^\d/)) {
      return cityPart;
    }
  }
  
  return null;
}

function normalizeNameForSearch(displayName) {
  // Remove common suffixes/patterns that won't match
  return displayName
    .replace(/\s*\(.*?\)\s*/g, '') // Remove parenthetical text
    .replace(/#\d+/g, '')          // Remove # followed by numbers
    .replace(/['']s?\s*$/i, '')    // Remove possessives
    .trim();
}

function namesMatch(reviewerName, clientName) {
  const normalize = (s) => s.toLowerCase().replace(/[^a-z\s]/g, '').trim();
  const reviewer = normalize(reviewerName);
  const client = normalize(clientName);
  
  // Direct match
  if (reviewer === client) return true;
  
  // Check if last names match
  const reviewerParts = reviewer.split(/\s+/);
  const clientParts = client.split(/\s+/);
  
  if (reviewerParts.length >= 2 && clientParts.length >= 1) {
    const reviewerLast = reviewerParts[reviewerParts.length - 1];
    const clientLast = clientParts[clientParts.length - 1];
    
    // Last name must match
    if (reviewerLast === clientLast) {
      // If we have first names, check first 3 chars
      if (reviewerParts.length >= 1 && clientParts.length >= 1) {
        const reviewerFirst = reviewerParts[0].slice(0, 3);
        const clientFirst = clientParts[0].slice(0, 3);
        if (reviewerFirst === clientFirst) {
          return true;
        }
      }
    }
  }
  
  // Check if reviewer name contains client name or vice versa
  if (reviewer.includes(client) || client.includes(reviewer)) {
    return true;
  }
  
  return false;
}

async function main() {
  console.log('Loading reviews...');
  const reviewsData = JSON.parse(fs.readFileSync(REVIEWS_PATH));
  
  // Extract all 5-star reviews with text
  const fiveStarReviews = [];
  for (const location of reviewsData) {
    for (const review of location.reviews) {
      if (review.starRating === 'FIVE' && review.comment) {
        fiveStarReviews.push({
          name: review.reviewer.displayName,
          text: review.comment,
          date: review.createTime.split('T')[0],
          location: location.address.locality
        });
      }
    }
  }
  
  console.log(`Found ${fiveStarReviews.length} 5-star reviews with text`);
  
  // Match reviews to clients
  const reviewsByCity = {};
  const matched = [];
  const unmatched = [];
  
  for (const review of fiveStarReviews) {
    const searchName = normalizeNameForSearch(review.name);
    
    // Skip single-word names or usernames
    if (!searchName.includes(' ') || searchName.length < 5) {
      console.log(`Skipping: ${review.name} (single word/short)`);
      unmatched.push(review.name);
      continue;
    }
    
    console.log(`Searching: ${searchName}`);
    
    const clients = await searchJobberClients(searchName);
    
    if (clients && clients.length > 0) {
      // Find best matching client
      let bestMatch = null;
      
      for (const client of clients) {
        const fullName = client.name || `${client.firstName} ${client.lastName}`.trim();
        if (namesMatch(searchName, fullName)) {
          const city = extractCity(client);
          if (city) {
            bestMatch = { client, city };
            break;
          }
        }
      }
      
      if (bestMatch) {
        const city = bestMatch.city;
        console.log(`  ✓ Matched to ${city}`);
        
        if (!reviewsByCity[city]) {
          reviewsByCity[city] = [];
        }
        
        reviewsByCity[city].push({
          name: review.name,
          text: review.text,
          date: review.date
        });
        
        matched.push(review.name);
      } else {
        console.log('  ✗ No matching client with city');
        unmatched.push(review.name);
      }
    } else {
      console.log('  ✗ No clients found');
      unmatched.push(review.name);
    }
    
    // Rate limiting - wait 150ms between requests
    await new Promise(r => setTimeout(r, 150));
  }
  
  // Save results
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(reviewsByCity, null, 2));
  
  console.log('\n=== RESULTS ===');
  console.log(`Total 5-star reviews with text: ${fiveStarReviews.length}`);
  console.log(`Matched to cities: ${matched.length}`);
  console.log(`Unmatched: ${unmatched.length}`);
  console.log('\nCities with testimonials:');
  for (const [city, reviews] of Object.entries(reviewsByCity).sort((a, b) => b[1].length - a[1].length)) {
    console.log(`  ${city}: ${reviews.length} review(s)`);
  }
  
  console.log(`\nSaved to: ${OUTPUT_PATH}`);
}

main().catch(console.error);
