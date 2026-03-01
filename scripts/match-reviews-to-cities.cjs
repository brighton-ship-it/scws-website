#!/usr/bin/env node
const https = require('https');
const fs = require('fs');
const creds = require('/Users/jarvis/clawd/jobber_credentials.json');

// Read reviews
const reviews = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-gmb/reviews.json', 'utf8'));

// Extract 5-star reviews with meaningful text
const fiveStarReviews = [];
reviews.forEach(location => {
  location.reviews.forEach(r => {
    if (r.starRating === 'FIVE' && r.reviewer?.displayName) {
      fiveStarReviews.push({
        name: r.reviewer.displayName,
        text: r.comment || '',
        date: r.createTime?.split('T')[0] || '',
        location: location.address?.locality || 'Unknown'
      });
    }
  });
});

console.log(`Found ${fiveStarReviews.length} 5-star reviews to process`);

// Simpler GraphQL query - just billing address
const query = `
query SearchClients($searchTerm: String!) {
  clients(searchTerm: $searchTerm, first: 5) {
    nodes {
      id
      name
      billingAddress {
        city
        street
        postalCode
      }
    }
  }
}
`;

function searchJobber(name) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      query,
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
          if (result.errors) {
            resolve({ error: result.errors[0].message });
          } else if (result.data?.clients?.nodes?.length > 0) {
            const client = result.data.clients.nodes[0];
            const city = client.billingAddress?.city || null;
            resolve({ name: client.name, city });
          } else {
            resolve({ name: null, city: null });
          }
        } catch (e) {
          resolve({ error: e.message });
        }
      });
    });

    req.on('error', e => resolve({ error: e.message }));
    req.write(data);
    req.end();
  });
}

async function processReviews() {
  const reviewsByCity = {};
  let matched = 0;
  let unmatched = 0;
  let errors = 0;

  for (let i = 0; i < fiveStarReviews.length; i++) {
    const review = fiveStarReviews[i];
    
    // Clean up name for search (remove nicknames in parens, etc)
    let searchName = review.name
      .replace(/\s*\([^)]*\)\s*/g, '')  // Remove (Joyful#1) etc
      .replace(/[#@]/g, '')
      .trim();
    
    // Skip obvious non-names
    if (searchName.toLowerCase().includes('google') || 
        searchName.toLowerCase() === 'a google user' ||
        searchName.length < 3) {
      unmatched++;
      continue;
    }

    console.log(`[${i+1}/${fiveStarReviews.length}] Searching: ${searchName}`);
    
    const result = await searchJobber(searchName);
    
    if (result.error) {
      console.log(`  Error: ${result.error}`);
      errors++;
      // If auth error, stop
      if (result.error.includes('Unauthorized') || result.error.includes('token') || result.error.includes('expired')) {
        console.log('\n⚠️ Auth error - token may be expired');
        break;
      }
    } else if (result.city) {
      console.log(`  ✅ Match: ${result.name} → ${result.city}`);
      const city = result.city.trim();
      if (!reviewsByCity[city]) {
        reviewsByCity[city] = [];
      }
      reviewsByCity[city].push({
        name: review.name,
        text: review.text,
        date: review.date
      });
      matched++;
    } else {
      console.log(`  ❌ No match`);
      unmatched++;
    }

    // Rate limit - be nice to API
    await new Promise(r => setTimeout(r, 200));
  }

  // Sort cities and reviews
  const sortedResult = {};
  Object.keys(reviewsByCity).sort().forEach(city => {
    sortedResult[city] = reviewsByCity[city].sort((a, b) => 
      new Date(b.date) - new Date(a.date)
    );
  });

  // Write output
  const outputPath = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';
  fs.writeFileSync(outputPath, JSON.stringify(sortedResult, null, 2));

  console.log('\n=== Summary ===');
  console.log(`Total 5-star reviews: ${fiveStarReviews.length}`);
  console.log(`Matched to cities: ${matched}`);
  console.log(`Unmatched: ${unmatched}`);
  console.log(`Errors: ${errors}`);
  console.log(`\nCities with testimonials:`);
  Object.entries(sortedResult).forEach(([city, revs]) => {
    console.log(`  ${city}: ${revs.length} reviews`);
  });
  console.log(`\nSaved to: ${outputPath}`);
}

processReviews().catch(console.error);
