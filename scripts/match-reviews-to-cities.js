#!/usr/bin/env node
/**
 * Match Google Reviews to Cities via Jobber
 * Searches Jobber for reviewer names and extracts their city
 */

const fs = require('fs');
const path = require('path');

// Load credentials
const creds = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/jobber_credentials.json', 'utf8'));

// Load reviews
const reviews = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-gmb/reviews.json', 'utf8'));

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
            street
            postalCode
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
      console.error(`Error searching for ${name}:`, data.errors[0].message);
      return null;
    }
    return data.data?.clients?.nodes || [];
  } catch (err) {
    console.error(`Failed to search for ${name}:`, err.message);
    return null;
  }
}

function extractCity(client) {
  if (client.billingAddress?.city) {
    return client.billingAddress.city;
  }
  return null;
}

function cleanName(displayName) {
  // Remove nicknames in parentheses, emojis, etc.
  return displayName
    .replace(/\(.*?\)/g, '')
    .replace(/[^\w\s'-]/g, '')
    .trim();
}

function nameMatch(reviewerName, clientName) {
  const rn = reviewerName.toLowerCase().trim();
  const cn = clientName.toLowerCase().trim();
  
  // Exact match
  if (rn === cn) return true;
  
  // Check if reviewer name parts are in client name
  const rParts = rn.split(/\s+/);
  const cParts = cn.split(/\s+/);
  
  // At least first and last name match
  if (rParts.length >= 2 && cParts.length >= 2) {
    const firstMatch = rParts[0] === cParts[0];
    const lastMatch = rParts[rParts.length - 1] === cParts[cParts.length - 1];
    if (firstMatch && lastMatch) return true;
  }
  
  // First name match for single names
  if (rParts.length === 1 && rParts[0] === cParts[0]) return true;
  
  return false;
}

async function main() {
  console.log('Matching Google Reviews to Cities via Jobber\n');
  
  // Collect all 5-star reviews with comments
  const fiveStarReviews = [];
  for (const location of reviews) {
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
  
  console.log(`Found ${fiveStarReviews.length} 5-star reviews with comments\n`);
  
  const reviewsByCity = {};
  const matched = [];
  const unmatched = [];
  
  // Process each review
  for (const review of fiveStarReviews) {
    const cleanedName = cleanName(review.name);
    console.log(`Searching for: ${cleanedName}`);
    
    const clients = await searchJobberClient(cleanedName);
    
    if (clients && clients.length > 0) {
      // Find best match
      let bestMatch = null;
      for (const client of clients) {
        if (nameMatch(cleanedName, client.name)) {
          bestMatch = client;
          break;
        }
      }
      
      if (bestMatch) {
        const city = extractCity(bestMatch);
        if (city) {
          const normalizedCity = city.trim();
          console.log(`  ✓ Matched to ${bestMatch.name} in ${normalizedCity}`);
          
          if (!reviewsByCity[normalizedCity]) {
            reviewsByCity[normalizedCity] = [];
          }
          
          reviewsByCity[normalizedCity].push({
            name: review.name,
            text: review.text,
            date: review.date
          });
          
          matched.push({ reviewer: review.name, client: bestMatch.name, city: normalizedCity });
        } else {
          console.log(`  ~ Matched ${bestMatch.name} but no city found`);
          unmatched.push(review.name);
        }
      } else {
        console.log(`  ✗ No name match in results`);
        unmatched.push(review.name);
      }
    } else {
      console.log(`  ✗ No results`);
      unmatched.push(review.name);
    }
    
    // Rate limiting
    await new Promise(r => setTimeout(r, 200));
  }
  
  // Save results
  const outputPath = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';
  fs.writeFileSync(outputPath, JSON.stringify(reviewsByCity, null, 2));
  
  console.log('\n' + '='.repeat(50));
  console.log(`\n✅ RESULTS:`);
  console.log(`   Matched: ${matched.length} reviews`);
  console.log(`   Unmatched: ${unmatched.length} reviews`);
  console.log(`\n📍 Cities with testimonials:`);
  
  const sortedCities = Object.entries(reviewsByCity)
    .sort((a, b) => b[1].length - a[1].length);
  
  for (const [city, cityReviews] of sortedCities) {
    console.log(`   ${city}: ${cityReviews.length} reviews`);
  }
  
  console.log(`\n💾 Saved to: ${outputPath}`);
}

main().catch(console.error);
