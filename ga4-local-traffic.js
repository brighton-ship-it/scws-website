#!/usr/bin/env node
// GA4 Local Traffic Report - Shows organic traffic by city for SD County

const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const path = require('path');

const PROPERTY_ID = '396700369';
const KEY_FILE = path.join(process.env.HOME, 'clawd/credentials/google-analytics-service-account.json');

// Local cities to track (SD + Riverside + San Bernardino counties)
const LOCAL_CITIES = [
  // San Diego County
  'san diego', 'escondido', 'oceanside', 'carlsbad', 'vista', 'el cajon',
  'encinitas', 'chula vista', 'san marcos', 'poway', 'la mesa', 'santee',
  'ramona', 'julian', 'alpine', 'lakeside', 'fallbrook', 'valley center',
  'bonsall', 'pauma valley', 'palomar mountain',
  'borrego springs', 'warner springs', 'descanso', 'pine valley', 'campo',
  'potrero', 'jamul', 'spring valley', 'lemon grove', 'national city',
  'imperial beach', 'coronado', 'la jolla', 'del mar', 'solana beach',
  'rancho santa fe', 'rancho bernardo', 'scripps ranch', 'mira mesa',
  'clairemont', 'university city', 'kearny mesa', 'mission valley',
  // Riverside County
  'temecula', 'murrieta', 'hemet', 'san jacinto', 'menifee', 'wildomar',
  'lake elsinore', 'perris', 'riverside', 'corona', 'moreno valley',
  'beaumont', 'banning', 'palm springs', 'palm desert', 'indio', 'coachella',
  'la quinta', 'cathedral city', 'desert hot springs', 'idyllwild', 'anza',
  'aguanga', 'sage', 'winchester', 'french valley', 'sun city', 'nuevo',
  'homeland', 'east hemet', 'valle vista', 'green acres', 'rancho mirage',
  // San Bernardino County
  'san bernardino', 'ontario', 'rancho cucamonga', 'fontana', 'rialto',
  'redlands', 'highland', 'upland', 'apple valley', 'victorville', 'hesperia',
  'big bear lake', 'big bear city', 'lake arrowhead', 'running springs',
  'crestline', 'twin peaks', 'blue jay', 'cedar glen', 'skyforest',
  'rimforest', 'green valley lake', 'yucaipa', 'calimesa', 'loma linda',
  'colton', 'grand terrace', 'barstow', 'twentynine palms', 'yucca valley',
  'joshua tree', 'lucerne valley', 'wrightwood', 'phelan', 'pinon hills'
];

async function runReport() {
  const client = new BetaAnalyticsDataClient({
    keyFilename: KEY_FILE
  });

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const startDate = yesterday.toISOString().split('T')[0];
  
  const [response] = await client.runReport({
    property: `properties/${PROPERTY_ID}`,
    dateRanges: [{ startDate, endDate: startDate }],
    dimensions: [{ name: 'city' }],
    metrics: [{ name: 'sessions' }],
    dimensionFilter: {
      filter: {
        fieldName: 'sessionDefaultChannelGroup',
        stringFilter: { value: 'Organic Search' }
      }
    },
    orderBys: [{ metric: { metricName: 'sessions' }, desc: true }],
    limit: 100
  });

  let totalSessions = 0;
  let localSessions = 0;
  const cities = [];
  const localCities = [];

  for (const row of response.rows || []) {
    const city = row.dimensionValues[0].value;
    const sessions = parseInt(row.metricValues[0].value);
    totalSessions += sessions;
    cities.push({ city, sessions });
    
    if (LOCAL_CITIES.some(sd => city.toLowerCase().includes(sd))) {
      localSessions += sessions;
      localCities.push({ city, sessions });
    }
  }

  console.log(`\n=== GA4 ORGANIC TRAFFIC (${startDate}) ===\n`);
  console.log(`Total organic sessions: ${totalSessions}`);
  console.log(`Local sessions (SD+Riverside+SB): ${localSessions} (${((localSessions/totalSessions)*100).toFixed(1)}%)\n`);
  
  if (localCities.length > 0) {
    console.log('Local Cities:');
    localCities.forEach(c => console.log(`  ${c.city}: ${c.sessions}`));
  }
  
  console.log('\nTop 15 Cities (all):');
  cities.slice(0, 15).forEach(c => console.log(`  ${c.city}: ${c.sessions}`));
}

runReport().catch(console.error);
