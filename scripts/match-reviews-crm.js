#!/usr/bin/env node
/**
 * Match Google reviews to CRM clients by name to get city data
 * Uses Supabase CRM database instead of Jobber API
 * v6: Direct CRM query for faster, more reliable matching
 */

const fs = require('fs');
const { createClient } = require('@supabase/supabase-js');

// Supabase credentials
const SUPABASE_URL = 'https://htzsnpqrrrdfleldgybn.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0enNucHFycnJkZmxlbGRneWJuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTkxNDQ0OCwiZXhwIjoyMDg1NDkwNDQ4fQ.7YxD2rqsh0CfESPK3DBLC4dhZL5kJy8XDtyinBgU49c';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Load Google reviews
const allReviews = JSON.parse(fs.readFileSync('/Users/jarvis/clawd/scws-gmb/reviews-all.json', 'utf8'));

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

// Helper: normalize name for comparison
function normalizeName(name) {
  return name.toLowerCase().trim()
    .replace(/[^a-z\s]/g, '') // Remove punctuation
    .replace(/\s+/g, ' ');     // Normalize spaces
}

// Helper: check if names match
function namesMatch(reviewName, customerName) {
  const normalizedReview = normalizeName(reviewName);
  const normalizedCustomer = normalizeName(customerName || '');
  
  // Exact match
  if (normalizedReview === normalizedCustomer) return true;
  
  // Customer name contains review name
  if (normalizedCustomer.includes(normalizedReview) && normalizedReview.length > 3) return true;
  
  // Review name contains customer name
  if (normalizedReview.includes(normalizedCustomer) && normalizedCustomer.length > 3) return true;
  
  // Last name match (split both and check last word)
  const reviewWords = normalizedReview.split(' ');
  const customerWords = normalizedCustomer.split(' ');
  if (reviewWords.length > 1 && customerWords.length > 1) {
    const reviewLast = reviewWords[reviewWords.length - 1];
    const customerLast = customerWords[customerWords.length - 1];
    if (reviewLast === customerLast && reviewLast.length > 2) return true;
  }
  
  return false;
}

// Match reviews to CRM clients
async function matchReviewsToClients() {
  const matched = [];
  const unmatched = [];
  
  // Get all customers with properties (for city data)
  console.log('\n📥 Fetching CRM customers...');
  const { data: customers, error } = await supabase
    .from('customers')
    .select('id, name, email, phone, billing_city, properties(city, address)');
  
  if (error) {
    console.error('Error fetching customers:', error);
    return { matched, unmatched };
  }
  
  console.log(`   Loaded ${customers.length} customers with property data`);
  
  // Build name lookup index
  const nameIndex = new Map();
  for (const customer of customers) {
    if (!customer.name) continue;
    const normalizedName = normalizeName(customer.name);
    nameIndex.set(normalizedName, customer);
  }
  
  console.log('\n🔍 Matching reviews...\n');
  
  for (const review of fiveStarReviews) {
    let matched_customer = null;
    
    // Try exact match first
    const normalizedReviewName = normalizeName(review.name);
    if (nameIndex.has(normalizedReviewName)) {
      matched_customer = nameIndex.get(normalizedReviewName);
    } else {
      // Try fuzzy match
      for (const customer of customers) {
        if (customer.name && namesMatch(review.name, customer.name)) {
          matched_customer = customer;
          break;
        }
      }
    }
    
    if (matched_customer) {
      // Get city from property first, then billing_city
      let city = matched_customer.properties?.[0]?.city || matched_customer.billing_city;
      let source = matched_customer.properties?.[0]?.city ? 'property' : 'billing';
      
      if (city) {
        matched.push({
          reviewer: review.name,
          city: city,
          text: review.text,
          date: review.date,
          crmMatch: matched_customer.name,
          customerId: matched_customer.id,
          citySource: source
        });
        console.log(`✓ ${review.name} → ${city} (matched: ${matched_customer.name}, source: ${source})`);
      } else {
        unmatched.push({ 
          reviewer: review.name, 
          reason: 'No city in CRM',
          crmMatch: matched_customer.name
        });
        console.log(`⚠ ${review.name} → No city (matched: ${matched_customer.name})`);
      }
    } else {
      unmatched.push({ reviewer: review.name, reason: 'Not found in CRM' });
      console.log(`✗ ${review.name} → Not found in CRM`);
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
  console.log('\n🔍 Matching Google reviews to CRM clients...');
  
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
  console.log(`  Total matched reviews: ${matched.length}`);
  
  process.exit(0);
})();
