#!/usr/bin/env node
// GA4 Local Traffic Report - Shows organic traffic by city for SD County

const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const path = require('path');

const PROPERTY_ID = '396700369';
const KEY_FILE = path.join(process.env.HOME, 'clawd/credentials/google-analytics-service-account.json');

// San Diego County cities to track
const SD_COUNTY_CITIES = [
  'san diego', 'escondido', 'oceanside', 'carlsbad', 'vista', 'el cajon',
  'encinitas', 'chula vista', 'san marcos', 'poway', 'la mesa', 'santee',
  'ramona', 'julian', 'alpine', 'lakeside', 'fallbrook', 'valley center',
  'temecula', 'murrieta', 'bonsall', 'pauma valley', 'palomar mountain',
  'borrego springs', 'warner springs', 'descanso', 'pine valley', 'campo',
  'potrero', 'jamul', 'spring valley', 'lemon grove', 'national city',
  'imperial beach', 'coronado', 'la jolla', 'del mar', 'solana beach',
  'rancho santa fe', 'rancho bernardo', 'scripps ranch', 'mira mesa',
  'clairemont', 'university city', 'kearny mesa', 'mission valley'
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
    
    if (SD_COUNTY_CITIES.some(sd => city.toLowerCase().includes(sd))) {
      localSessions += sessions;
      localCities.push({ city, sessions });
    }
  }

  console.log(`\n=== GA4 ORGANIC TRAFFIC (${startDate}) ===\n`);
  console.log(`Total organic sessions: ${totalSessions}`);
  console.log(`SD County sessions: ${localSessions} (${((localSessions/totalSessions)*100).toFixed(1)}%)\n`);
  
  if (localCities.length > 0) {
    console.log('Local Cities:');
    localCities.forEach(c => console.log(`  ${c.city}: ${c.sessions}`));
  }
  
  console.log('\nTop 15 Cities (all):');
  cities.slice(0, 15).forEach(c => console.log(`  ${c.city}: ${c.sessions}`));
}

runReport().catch(console.error);
