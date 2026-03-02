#!/usr/bin/env node
/**
 * Match Google Reviews to Jobber Clients by City
 * Searches Jobber for reviewer names to extract their city
 */

const fs = require('fs');
const path = require('path');

// Paths
const REVIEWS_PATH = path.join(__dirname, '../../scws-gmb/reviews.json');
const CREDENTIALS_PATH = path.join(__dirname, '../../jobber_credentials.json');
const OUTPUT_PATH = path.join(__dirname, 'reviews-by-city.json');

// Load credentials
const creds = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));

// GraphQL query to search clients by name
async function searchJobberClient(name) {
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
          }
        }
      }
    }
  `;

  try {
    const response = await fetch(creds.api_endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${creds.access_token}`,
        'X-JOBBER-GRAPHQL-VERSION': creds.graphql_version
      },
      body: JSON.stringify({
        query,
        variables: { searchTerm: name }
      })
    });

    const data = await response.json();
    if (data.errors) {
      console.error(`  Error searching for "${name}":`, data.errors[0].message);
      return null;
    }
    return data.data?.clients?.nodes || [];
  } catch (err) {
    console.error(`  Fetch error for "${name}":`, err.message);
    return null;
  }
}

// Extract city from client data
function getCityFromClient(client) {
  if (client.billingAddress?.city) {
    return { city: client.billingAddress.city };
  }
  return null;
}

// Normalize name for comparison
function normalizeName(name) {
  return name.toLowerCase()
    .replace(/[^a-z\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Check if names match
function namesMatch(reviewerName, clientName) {
  const rNorm = normalizeName(reviewerName);
  const cNorm = normalizeName(clientName);
  
  // Direct match
  if (rNorm === cNorm) return true;
  
  // Partial match (first + last name)
  const rParts = rNorm.split(' ');
  const cParts = cNorm.split(' ');
  
  // Match first and last name
  if (rParts.length >= 2 && cParts.length >= 2) {
    if (rParts[0] === cParts[0] && rParts[rParts.length-1] === cParts[cParts.length-1]) {
      return true;
    }
  }
  
  // Match if reviewer first name matches client first name and client has matching last initial
  if (rParts.length >= 1 && cParts.length >= 1) {
    if (rParts[0] === cParts[0]) return true;
  }
  
  return false;
}

async function main() {
  console.log('Loading reviews...');
  const reviews = JSON.parse(fs.readFileSync(REVIEWS_PATH, 'utf8'));
  
  // Collect all 5-star reviews
  const fiveStarReviews = [];
  for (const location of reviews) {
    for (const review of location.reviews || []) {
      if (review.starRating === 'FIVE' && review.reviewer?.displayName) {
        fiveStarReviews.push({
          name: review.reviewer.displayName,
          text: review.comment || '',
          date: review.createTime?.split('T')[0] || '',
          location: location.address?.locality || ''
        });
      }
    }
  }
  
  console.log(`Found ${fiveStarReviews.length} 5-star reviews to match\n`);
  
  // Match reviews to cities
  const reviewsByCity = {};
  const matched = [];
  const unmatched = [];
  
  for (let i = 0; i < fiveStarReviews.length; i++) {
    const review = fiveStarReviews[i];
    
    // Skip reviews with obvious non-real names
    if (review.name.includes('#') || review.name.length < 3) {
      unmatched.push(review);
      continue;
    }
    
    process.stdout.write(`[${i+1}/${fiveStarReviews.length}] Searching: ${review.name}...`);
    
    const clients = await searchJobberClient(review.name);
    
    if (!clients || clients.length === 0) {
      process.stdout.write(' no match\n');
      unmatched.push(review);
      continue;
    }
    
    // Find best matching client
    let matchedClient = null;
    for (const client of clients) {
      const fullName = `${client.firstName || ''} ${client.lastName || ''}`.trim() || client.name;
      if (namesMatch(review.name, fullName)) {
        const cityData = getCityFromClient(client);
        if (cityData?.city) {
          matchedClient = { ...client, cityData };
          break;
        }
      }
    }
    
    if (matchedClient) {
      const city = matchedClient.cityData.city;
      process.stdout.write(` → ${city}\n`);
      
      if (!reviewsByCity[city]) {
        reviewsByCity[city] = [];
      }
      
      reviewsByCity[city].push({
        name: review.name,
        text: review.text,
        date: review.date
      });
      matched.push(review);
    } else {
      process.stdout.write(' no city found\n');
      unmatched.push(review);
    }
    
    // Rate limit
    await new Promise(r => setTimeout(r, 200));
  }
  
  // Save results
  console.log(`\nSaving to ${OUTPUT_PATH}...`);
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(reviewsByCity, null, 2));
  
  // Summary
  console.log('\n=== SUMMARY ===');
  console.log(`Total 5-star reviews: ${fiveStarReviews.length}`);
  console.log(`Matched to cities: ${matched.length}`);
  console.log(`Unmatched: ${unmatched.length}`);
  console.log(`\nCities with testimonials:`);
  
  const sortedCities = Object.entries(reviewsByCity)
    .sort((a, b) => b[1].length - a[1].length);
  
  for (const [city, reviews] of sortedCities) {
    console.log(`  ${city}: ${reviews.length} review(s)`);
  }
}

main().catch(console.error);
