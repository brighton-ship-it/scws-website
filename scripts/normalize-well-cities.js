#!/usr/bin/env node

/**
 * Normalize well city names and generate statistics
 * Handles typos, case inconsistencies, and merges duplicates
 */

const fs = require('fs');
const path = require('path');

// Load well data
const wellDataPath = path.join(__dirname, '../tools/welldepth/well_data.json');
const wellData = JSON.parse(fs.readFileSync(wellDataPath, 'utf8'));
const wells = wellData.wells;

console.log(`Loaded ${wells.length} wells from well_data.json`);

// Known city name mappings (correcting typos and variations)
const cityMappings = {
  // San Bernardino variations
  'san bernadino': 'San Bernardino',
  'san bernadine': 'San Bernardino',
  'san barnardino': 'San Bernardino',
  
  // Twentynine Palms variations
  '29 palms': 'Twentynine Palms',
  'twentynine palms': 'Twentynine Palms',
  'twenty nine palms': 'Twentynine Palms',
  '29-palms': 'Twentynine Palms',
  
  // Aguanga variations
  'agauanga': 'Aguanga',
  'agaung': 'Aguanga',
  
  // Pioneertown variations
  'pioneer town': 'Pioneertown',
  'poineertown': 'Pioneertown',
  
  // Johnson Valley variations
  'johnson': 'Johnson Valley',
  
  // Lucerne variations
  'lucerne': 'Lucerne Valley',
  
  // Morongo variations
  'morongo': 'Morongo Valley',
  
  // Oak Glen
  'oak glen': 'Oak Glen',
  'oakglen': 'Oak Glen',
  
  // Rancho Cucamonga
  'rancho cucamonga': 'Rancho Cucamonga',
  'ranchocucamonga': 'Rancho Cucamonga',
  'r.c.': 'Rancho Cucamonga',
  
  // Chino variations
  'chino hiils': 'Chino Hills',
  'chino hils': 'Chino Hills',
  
  // Cherry Valley
  'cherry valley': 'Cherry Valley',
  
  // West Cajon Valley
  'west cajon valley': 'West Cajon Valley',
  
  // Oro Grande
  'oro grande': 'Oro Grande',
  
  // Big Bear variations
  'big bear lake': 'Big Bear Lake',
  'big bear city': 'Big Bear City',
  
  // Cedarpines Park
  'cedarpines park': 'Cedarpines Park',
  
  // Lake Arrowhead
  'lake arrowhead': 'Lake Arrowhead',
  
  // Lytle Creek
  'lytle creek': 'Lytle Creek',
  
  // Running Springs
  'running springs': 'Running Springs',
  
  // Twin Peaks
  'twin peaks': 'Twin Peaks',
  
  // Parker Dam
  'parker dam': 'Parker Dam',
  
  // El Mirage
  'el mirage': 'El Mirage',
  
  // Pinon Hills
  'pinon hills': 'Pinon Hills',
  
  // Wondervalley variations
  'wondervalley': 'Wonder Valley',
  'wonder valley': 'Wonder Valley',
  
  // Grand Terrace
  'grand terrace': 'Grand Terrace',
  
  // Loma Linda
  'loma linda': 'Loma Linda',
  
  // Angelus Oaks
  'angelus oaks': 'Angelus Oaks',
  'angelus oak': 'Angelus Oaks',
  
  // Bloomington
  'bloomington': 'Bloomington',
  
  // Devore
  'devore': 'Devore',
  
  // Highland
  'highland': 'Highland',
  
  // Eastvale
  'eastvale': 'Eastvale',
  
  // Ontairo (typo)
  'ontairo': 'Ontario',
  
  // Redlands variations
  'relands': 'Redlands',
  
  // Yucaipa
  'yucaipa': 'Yucaipa',
  
  // Mentone
  'mentone': 'Mentone',
  
  // Colton
  'colton': 'Colton',
  
  // Rialto
  'rialto': 'Rialto',
  
  // Fontana
  'fontana': 'Fontana',
  
  // Montclair
  'montclair': 'Montclair',
  
  // Baldwin Lake
  'baldwin lake': 'Baldwin Lake',
  
  // Fawnskin
  'fawnskin': 'Fawnskin',
  
  // Landers
  'landers': 'Landers',
  
  // Cadiz
  'cadiz': 'Cadiz',
  
  // Earp
  'earp': 'Earp',
  
  // Essex
  'essex': 'Essex',
  
  // Ludlow
  'ludlow': 'Ludlow',
  
  // Baker
  'baker': 'Baker',
  
  // Nipton
  'nipton': 'Nipton',
  
  // Needles
  'needles': 'Needles',
  
  // Newberrysprings (no space)
  'newberrysprings': 'Newberry Springs',
  
  // hinkley (lowercase)
  'hinkley': 'Hinkley',
  
  // phelan (lowercase)
  'phelan': 'Phelan',
  
  // Boron
  'boron': 'Boron',
  
  // Daggett
  'daggett': 'Daggett',
  
  // Yermo
  'yermo': 'Yermo',
  
  // Helendale
  'helendale': 'Helendale',
  
  // Bloomington
  'bloomington': 'Bloomington',
  
  // Adelanto
  'adelanto': 'Adelanto',
  
  // Victorville
  'victorville': 'Victorville'
};

/**
 * Normalize a city name
 */
function normalizeCity(rawCity, county) {
  if (!rawCity || rawCity.trim() === '') {
    return null;
  }
  
  let city = rawCity.trim();
  const cityLower = city.toLowerCase();
  
  // Check exact mapping
  if (cityMappings[cityLower]) {
    return cityMappings[cityLower];
  }
  
  // Title case (capitalize each word)
  city = city.split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
  
  return city;
}

/**
 * Get decade from year
 */
function getDecade(year) {
  if (!year || year < 1900 || year > 2030) return null;
  return `${Math.floor(year / 10) * 10}s`;
}

/**
 * Extract year from WCR number (format: WCR####-######)
 */
function extractYear(wcr) {
  if (!wcr) return null;
  const match = wcr.match(/WCR(\d{4})/);
  if (match) {
    return parseInt(match[1]);
  }
  return null;
}

/**
 * Normalize use type
 */
function normalizeUse(use) {
  if (!use || use === 'Unknown' || use === 'Unknown Unknown') return 'Unknown';
  return use.replace('Water Supply ', '').trim();
}

/**
 * Calculate median
 */
function median(arr) {
  if (arr.length === 0) return null;
  const sorted = arr.slice().sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 
    ? (sorted[mid - 1] + sorted[mid]) / 2 
    : sorted[mid];
}

// Process wells
console.log('Normalizing city names...');

const cityStats = {};
const unmapped = new Set();
let wellsWithCity = 0;
let wellsWithoutCity = 0;

wells.forEach(well => {
  const rawCity = well.city;
  const county = well.county;
  
  if (!rawCity || rawCity.trim() === '') {
    wellsWithoutCity++;
    unmapped.add('(empty)');
    return;
  }
  
  wellsWithCity++;
  const normalizedCity = normalizeCity(rawCity, county);
  
  if (!normalizedCity) {
    unmapped.add(rawCity);
    return;
  }
  
  // Initialize city stats
  if (!cityStats[normalizedCity]) {
    cityStats[normalizedCity] = {
      county: county || 'Unknown',
      count: 0,
      depths: [],
      yields: [],
      staticLevels: [],
      decades: {},
      uses: {}
    };
  }
  
  const stats = cityStats[normalizedCity];
  stats.count++;
  
  // Depth
  if (well.depth && well.depth > 0 && well.depth < 5000) {
    stats.depths.push(well.depth);
  }
  
  // Yield
  if (well.yield && well.yield > 0 && well.yield < 10000) {
    stats.yields.push(well.yield);
  }
  
  // Static level
  if (well.staticLevel && well.staticLevel > 0 && well.staticLevel < 2000) {
    stats.staticLevels.push(well.staticLevel);
  }
  
  // Decade
  const year = extractYear(well.wcr);
  if (year) {
    const decade = getDecade(year);
    if (decade) {
      stats.decades[decade] = (stats.decades[decade] || 0) + 1;
    }
  }
  
  // Use type
  const use = normalizeUse(well.use);
  stats.uses[use] = (stats.uses[use] || 0) + 1;
});

console.log(`Wells with city: ${wellsWithCity}`);
console.log(`Wells without city: ${wellsWithoutCity}`);
console.log(`Normalized cities: ${Object.keys(cityStats).length}`);
console.log(`Unmapped names: ${unmapped.size}`);

// Filter cities with < 5 wells
const minWells = 5;
const filteredCities = {};

Object.entries(cityStats).forEach(([city, stats]) => {
  if (stats.count >= minWells) {
    filteredCities[city] = stats;
  }
});

console.log(`Cities with ${minWells}+ wells: ${Object.keys(filteredCities).length}`);

// Calculate final statistics
const output = {};

Object.entries(filteredCities).forEach(([city, stats]) => {
  const avgDepth = stats.depths.length > 0 
    ? Math.round(stats.depths.reduce((a, b) => a + b, 0) / stats.depths.length)
    : null;
  const medianDepth = median(stats.depths);
  const minDepth = stats.depths.length > 0 ? Math.min(...stats.depths) : null;
  const maxDepth = stats.depths.length > 0 ? Math.max(...stats.depths) : null;
  
  const avgYield = stats.yields.length > 0
    ? Math.round(stats.yields.reduce((a, b) => a + b, 0) / stats.yields.length * 10) / 10
    : null;
  const medianYield = stats.yields.length > 0 ? median(stats.yields) : null;
  
  const avgStaticLevel = stats.staticLevels.length > 0
    ? Math.round(stats.staticLevels.reduce((a, b) => a + b, 0) / stats.staticLevels.length)
    : null;
  const medianStaticLevel = stats.staticLevels.length > 0 ? median(stats.staticLevels) : null;
  
  output[city] = {
    county: stats.county,
    count: stats.count,
    avgDepth,
    minDepth,
    maxDepth,
    medianDepth: medianDepth ? Math.round(medianDepth) : null,
    avgYield,
    medianYield: medianYield ? Math.round(medianYield * 10) / 10 : null,
    avgStaticLevel,
    medianStaticLevel: medianStaticLevel ? Math.round(medianStaticLevel) : null,
    wellsByDecade: stats.decades,
    wellsByUse: stats.uses
  };
});

// Write output
const outputPath = path.join(__dirname, 'city-well-stats.json');
fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf8');
console.log(`\nWrote city statistics to ${outputPath}`);

// Print summary
console.log('\n=== SUMMARY ===');
console.log(`Total wells: ${wells.length}`);
console.log(`Wells with city data: ${wellsWithCity} (${Math.round(wellsWithCity / wells.length * 100)}%)`);
console.log(`Normalized city names: ${Object.keys(cityStats).length}`);
console.log(`Cities with ${minWells}+ wells: ${Object.keys(filteredCities).length}`);

// Wells by county
const countyCount = {};
wells.forEach(w => {
  const c = w.county || 'Unknown';
  countyCount[c] = (countyCount[c] || 0) + 1;
});
console.log('\nWells by county:');
Object.entries(countyCount)
  .sort((a, b) => b[1] - a[1])
  .forEach(([county, count]) => {
    console.log(`  ${county}: ${count}`);
  });

// Top 20 cities
console.log('\nTop 20 cities by well count:');
Object.entries(output)
  .sort((a, b) => b[1].count - a[1].count)
  .slice(0, 20)
  .forEach(([city, stats]) => {
    console.log(`  ${city}: ${stats.count} wells, avg depth ${stats.avgDepth}ft, ${stats.county} County`);
  });

console.log('\n✅ City normalization complete!');
