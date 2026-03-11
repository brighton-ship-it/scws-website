const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const path = require('path');

const client = new BetaAnalyticsDataClient({
  keyFilename: path.join(process.env.HOME, 'clawd/credentials/google-analytics-service-account.json')
});

const propertyId = '396700369';

// Cities by county - added San Bernardino
const sdCities = ['san diego', 'ramona', 'julian', 'escondido', 'poway', 'el cajon', 'santee', 'la mesa', 'chula vista', 'oceanside', 'carlsbad', 'encinitas', 'vista', 'san marcos', 'valley center', 'fallbrook', 'lakeside', 'alpine', 'jamul', 'dulzura', 'potrero', 'campo', 'pine valley', 'descanso', 'borrego springs', 'warner springs', 'palomar mountain', 'rancho santa fe', 'del mar', 'solana beach', 'la jolla', 'coronado', 'national city', 'imperial beach', 'spring valley', 'lemon grove', 'bonsall', 'pauma valley'];
const rivCities = ['temecula', 'murrieta', 'hemet', 'san jacinto', 'menifee', 'perris', 'lake elsinore', 'wildomar', 'winchester', 'anza', 'aguanga', 'idyllwild', 'mountain center', 'riverside', 'corona', 'palm springs', 'palm desert', 'indio', 'coachella', 'desert hot springs', 'cathedral city', 'rancho mirage', 'la quinta', 'banning', 'beaumont', 'calimesa', 'moreno valley', 'norco'];
const sbCities = ['san bernardino', 'ontario', 'rancho cucamonga', 'fontana', 'rialto', 'redlands', 'upland', 'victorville', 'hesperia', 'apple valley', 'big bear', 'big bear lake', 'lake arrowhead', 'crestline', 'running springs', 'yucaipa', 'highland', 'loma linda', 'colton', 'chino', 'chino hills', 'twentynine palms', 'yucca valley', 'joshua tree', 'barstow', 'needles', 'lucerne valley', 'phelan', 'oak hills', 'wrightwood'];
const impCities = ['el centro', 'calexico', 'brawley', 'imperial', 'holtville', 'westmorland', 'calipatria', 'seeley', 'ocotillo'];

async function run() {
  const [response] = await client.runReport({
    property: `properties/${propertyId}`,
    dateRanges: [{ startDate: '2026-03-09', endDate: '2026-03-09' }],
    dimensions: [{ name: 'city' }, { name: 'sessionDefaultChannelGroup' }],
    metrics: [{ name: 'sessions' }],
    dimensionFilter: {
      filter: {
        fieldName: 'sessionDefaultChannelGroup',
        stringFilter: { matchType: 'EXACT', value: 'Organic Search' }
      }
    }
  });

  let sdCount = 0, rivCount = 0, sbCount = 0, impCount = 0, total = 0;
  const cityBreakdown = { sd: {}, riv: {}, sb: {}, imp: {} };

  for (const row of response.rows || []) {
    const city = row.dimensionValues[0].value;
    const sessions = parseInt(row.metricValues[0].value);
    total += sessions;
    
    const cityLower = city.toLowerCase();
    if (sdCities.includes(cityLower)) {
      sdCount += sessions;
      cityBreakdown.sd[city] = (cityBreakdown.sd[city] || 0) + sessions;
    } else if (rivCities.includes(cityLower)) {
      rivCount += sessions;
      cityBreakdown.riv[city] = (cityBreakdown.riv[city] || 0) + sessions;
    } else if (sbCities.includes(cityLower)) {
      sbCount += sessions;
      cityBreakdown.sb[city] = (cityBreakdown.sb[city] || 0) + sessions;
    } else if (impCities.includes(cityLower)) {
      impCount += sessions;
      cityBreakdown.imp[city] = (cityBreakdown.imp[city] || 0) + sessions;
    }
  }

  const localTotal = sdCount + rivCount + sbCount + impCount;
  console.log('=== ORGANIC SESSIONS BY COUNTY (March 9, 2026) ===\n');
  console.log(`Total organic sessions: ${total}`);
  console.log(`LOCAL (4 counties): ${localTotal} sessions (${((localTotal) / total * 100).toFixed(1)}%)\n`);
  
  console.log(`📍 San Diego: ${sdCount}`);
  Object.entries(cityBreakdown.sd).sort((a,b) => b[1]-a[1]).forEach(([c, n]) => console.log(`   ${c}: ${n}`));
  
  console.log(`\n📍 Riverside: ${rivCount}`);
  if (Object.keys(cityBreakdown.riv).length === 0) console.log('   (none)');
  Object.entries(cityBreakdown.riv).sort((a,b) => b[1]-a[1]).forEach(([c, n]) => console.log(`   ${c}: ${n}`));

  console.log(`\n📍 San Bernardino: ${sbCount}`);
  if (Object.keys(cityBreakdown.sb).length === 0) console.log('   (none)');
  Object.entries(cityBreakdown.sb).sort((a,b) => b[1]-a[1]).forEach(([c, n]) => console.log(`   ${c}: ${n}`));
  
  console.log(`\n📍 Imperial: ${impCount}`);
  if (Object.keys(cityBreakdown.imp).length === 0) console.log('   (none)');
  Object.entries(cityBreakdown.imp).sort((a,b) => b[1]-a[1]).forEach(([c, n]) => console.log(`   ${c}: ${n}`));
}

run().catch(console.error);
