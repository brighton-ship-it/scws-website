#!/usr/bin/env node
// Match Google Reviews to cities using:
// 1. GMB location (Ramona vs Anza regions)
// 2. City mentions in review text
// 3. Manual mapping for common areas

const fs = require('fs');

const REVIEWS_FILE = '/Users/jarvis/clawd/scws-gmb/reviews.json';
const OUTPUT_FILE = '/Users/jarvis/clawd/scws-website/scripts/reviews-by-city.json';

// San Diego County cities served from Ramona office
const SD_COUNTY_CITIES = [
  'Ramona', 'Julian', 'Alpine', 'Escondido', 'Valley Center', 'Poway', 
  'Lakeside', 'El Cajon', 'Santee', 'Jamul', 'Descanso', 'Pine Valley',
  'Boulevard', 'Campo', 'Potrero', 'Mount Laguna', 'Wynola', 'Santa Ysabel',
  'Warner Springs', 'Borrego Springs', 'Fallbrook', 'Bonsall', 'Pauma Valley',
  'San Diego', 'Oceanside', 'Vista', 'Carlsbad', 'Encinitas', 'La Mesa'
];

// Riverside County cities served from Anza office  
const RIVERSIDE_CITIES = [
  'Anza', 'Aguanga', 'Temecula', 'Murrieta', 'Hemet', 'San Jacinto',
  'Idyllwild', 'Mountain Center', 'Palm Desert', 'Menifee', 'Wildomar',
  'Lake Elsinore', 'Winchester', 'French Valley', 'Sage', 'Garner Valley',
  'Pinyon Pines', 'Cahuilla', 'Rancho California', 'De Luz', 'Fallbrook'
];

function extractCityFromText(text) {
  if (!text) return null;
  
  const allCities = [...SD_COUNTY_CITIES, ...RIVERSIDE_CITIES];
  const textLower = text.toLowerCase();
  
  for (const city of allCities) {
    // Check for city mention in text (case-insensitive)
    if (textLower.includes(city.toLowerCase())) {
      return city;
    }
  }
  return null;
}

function getRegionCity(gmbLocation) {
  // Map GMB location to a region - use location name as fallback city
  if (gmbLocation.toLowerCase().includes('anza')) {
    return 'Anza';
  } else if (gmbLocation.toLowerCase().includes('ramona')) {
    return 'Ramona';
  }
  return null;
}

function main() {
  // Load reviews
  const reviews = JSON.parse(fs.readFileSync(REVIEWS_FILE, 'utf8'));
  
  // Process reviews
  const reviewsByCity = {};
  const stats = { total: 0, matched: 0, byTextMatch: 0, byRegion: 0 };
  
  for (const location of reviews) {
    const gmbLocation = location.address?.locality || 'Unknown';
    
    for (const review of location.reviews) {
      // Only process 5-star reviews with text
      if (review.starRating !== 'FIVE' || !review.comment) continue;
      
      stats.total++;
      
      const reviewData = {
        name: review.reviewer.displayName,
        text: review.comment,
        date: review.createTime?.split('T')[0]
      };
      
      // Try to extract city from review text
      let city = extractCityFromText(review.comment);
      
      if (city) {
        stats.byTextMatch++;
        console.log(`✓ Text match: "${review.reviewer.displayName}" → ${city}`);
      } else {
        // Fall back to GMB region
        city = getRegionCity(gmbLocation);
        if (city) {
          stats.byRegion++;
          console.log(`○ Region: "${review.reviewer.displayName}" → ${city} (from ${gmbLocation} GMB)`);
        }
      }
      
      if (city) {
        if (!reviewsByCity[city]) {
          reviewsByCity[city] = [];
        }
        reviewsByCity[city].push(reviewData);
        stats.matched++;
      }
    }
  }
  
  // Sort cities by review count
  const sortedCities = Object.keys(reviewsByCity).sort(
    (a, b) => reviewsByCity[b].length - reviewsByCity[a].length
  );
  
  // Create sorted output
  const sortedOutput = {};
  for (const city of sortedCities) {
    sortedOutput[city] = reviewsByCity[city];
  }
  
  // Save results
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(sortedOutput, null, 2));
  
  console.log('\n=== SUMMARY ===');
  console.log(`Total 5-star reviews with text: ${stats.total}`);
  console.log(`Matched to cities: ${stats.matched}`);
  console.log(`  - By text mention: ${stats.byTextMatch}`);
  console.log(`  - By GMB region: ${stats.byRegion}`);
  console.log(`\nCities with testimonials:`);
  
  for (const city of sortedCities) {
    console.log(`  ${city}: ${reviewsByCity[city].length} reviews`);
  }
  
  console.log(`\nSaved to: ${OUTPUT_FILE}`);
}

main();
