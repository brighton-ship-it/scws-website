#!/usr/bin/env node
// Match Google Reviews to Jobber clients to get city info

const fs = require('fs');
const path = require('path');

const REVIEWS_FILE = '/Users/jarvis/clawd/scws-gmb/reviews.json';
const CREDS_FILE = '/Users/jarvis/clawd/jobber_credentials.json';
const OUTPUT_FILE = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';

async function queryJobber(accessToken, query) {
  const response = await fetch('https://api.getjobber.com/api/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
      'X-JOBBER-GRAPHQL-VERSION': '2024-12-11'
    },
    body: JSON.stringify({ query })
  });
  return response.json();
}

async function searchClient(accessToken, name) {
  // Clean up the name - remove nicknames in parentheses
  const cleanName = name.replace(/\s*\([^)]*\)\s*/g, '').trim();
  
  const query = `
    query {
      clients(searchTerm: "${cleanName}", first: 5) {
        nodes {
          id
          name
          firstName
          lastName
          billingAddress {
            city
            state
          }
          properties {
            nodes {
              address {
                city
                state
              }
            }
          }
        }
      }
    }
  `;
  
  return queryJobber(accessToken, query);
}

async function main() {
  // Load reviews
  const reviews = JSON.parse(fs.readFileSync(REVIEWS_FILE, 'utf8'));
  const creds = JSON.parse(fs.readFileSync(CREDS_FILE, 'utf8'));
  
  // Extract 5-star reviews with text from both locations
  const fiveStarReviews = [];
  
  for (const location of reviews) {
    const locationName = location.address?.locality || 'Unknown';
    
    for (const review of location.reviews) {
      if (review.starRating === 'FIVE' && review.comment) {
        fiveStarReviews.push({
          name: review.reviewer.displayName,
          text: review.comment,
          date: review.createTime?.split('T')[0],
          locationGMB: locationName
        });
      }
    }
  }
  
  console.log(`Found ${fiveStarReviews.length} 5-star reviews with text`);
  
  // Try to match each reviewer to Jobber
  const reviewsByCity = {};
  let matched = 0;
  let unmatched = 0;
  const matchDetails = [];
  
  for (const review of fiveStarReviews) {
    try {
      const result = await searchClient(creds.access_token, review.name);
      
      if (result.data?.clients?.nodes?.length > 0) {
        const client = result.data.clients.nodes[0];
        
        // Try to get city from property first, then billing address
        let city = null;
        if (client.properties?.nodes?.[0]?.address?.city) {
          city = client.properties.nodes[0].address.city;
        } else if (client.billingAddress?.city) {
          city = client.billingAddress.city;
        }
        
        if (city) {
          // Normalize city name
          city = city.charAt(0).toUpperCase() + city.slice(1).toLowerCase();
          
          if (!reviewsByCity[city]) {
            reviewsByCity[city] = [];
          }
          
          reviewsByCity[city].push({
            name: review.name,
            text: review.text,
            date: review.date
          });
          
          matched++;
          matchDetails.push({ reviewer: review.name, city, jobberName: client.name });
          console.log(`✓ Matched: ${review.name} → ${city}`);
        } else {
          unmatched++;
          console.log(`✗ No city for: ${review.name}`);
        }
      } else {
        unmatched++;
        console.log(`✗ No match: ${review.name}`);
      }
      
      // Rate limit
      await new Promise(r => setTimeout(r, 200));
      
    } catch (err) {
      console.error(`Error searching for ${review.name}:`, err.message);
      unmatched++;
    }
  }
  
  // Save results
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(reviewsByCity, null, 2));
  
  console.log('\n=== SUMMARY ===');
  console.log(`Total 5-star reviews with text: ${fiveStarReviews.length}`);
  console.log(`Matched to cities: ${matched}`);
  console.log(`Unmatched: ${unmatched}`);
  console.log(`\nCities with testimonials:`);
  
  const sortedCities = Object.entries(reviewsByCity)
    .sort((a, b) => b[1].length - a[1].length);
  
  for (const [city, cityReviews] of sortedCities) {
    console.log(`  ${city}: ${cityReviews.length} reviews`);
  }
  
  console.log(`\nSaved to: ${OUTPUT_FILE}`);
}

main().catch(console.error);
