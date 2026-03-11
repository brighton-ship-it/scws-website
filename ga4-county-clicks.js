const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const client = new BetaAnalyticsDataClient({
  keyFilename: '/Users/jarvis/clawd/scws-gmb/service-account.json'
});

const propertyId = '451542729';

// San Diego, Riverside, and Imperial county cities
const sdCities = ['San Diego', 'Ramona', 'Julian', 'Escondido', 'Poway', 'El Cajon', 'Santee', 'La Mesa', 'Chula Vista', 'Oceanside', 'Carlsbad', 'Encinitas', 'Vista', 'San Marcos', 'Valley Center', 'Fallbrook', 'Lakeside', 'Alpine', 'Jamul', 'Dulzura', 'Potrero', 'Campo', 'Pine Valley', 'Descanso', 'Borrego Springs', 'Warner Springs', 'Palomar Mountain'];
const rivCities = ['Temecula', 'Murrieta', 'Hemet', 'San Jacinto', 'Menifee', 'Perris', 'Lake Elsinore', 'Wildomar', 'Winchester', 'Anza', 'Aguanga', 'Idyllwild', 'Mountain Center', 'Riverside', 'Corona', 'Palm Springs', 'Palm Desert', 'Indio', 'Coachella', 'Desert Hot Springs', 'Cathedral City', 'Rancho Mirage', 'La Quinta', 'Banning', 'Beaumont', 'Calimesa'];
const impCities = ['El Centro', 'Calexico', 'Brawley', 'Imperial', 'Holtville', 'Westmorland', 'Calipatria', 'Seeley', 'Ocotillo', 'Plaster City'];

const allLocal = [...sdCities, ...rivCities, ...impCities].map(c => c.toLowerCase());

async function run() {
  const [response] = await client.runReport({
    property: `properties/${propertyId}`,
    dateRanges: [{ startDate: '2026-03-09', endDate: '2026-03-09' }],
    dimensions: [{ name: 'city' }, { name: 'sessionDefaultChannelGroup' }],
    metrics: [{ name: 'sessions' }, { name: 'engagedSessions' }],
    dimensionFilter: {
      filter: {
        fieldName: 'sessionDefaultChannelGroup',
        stringFilter: { matchType: 'EXACT', value: 'Organic Search' }
      }
    }
  });

  let sdCount = 0, rivCount = 0, impCount = 0, total = 0;
  const cityBreakdown = { sd: {}, riv: {}, imp: {} };

  for (const row of response.rows || []) {
    const city = row.dimensionValues[0].value;
    const sessions = parseInt(row.metricValues[0].value);
    total += sessions;
    
    const cityLower = city.toLowerCase();
    if (sdCities.map(c => c.toLowerCase()).includes(cityLower)) {
      sdCount += sessions;
      cityBreakdown.sd[city] = (cityBreakdown.sd[city] || 0) + sessions;
    } else if (rivCities.map(c => c.toLowerCase()).includes(cityLower)) {
      rivCount += sessions;
      cityBreakdown.riv[city] = (cityBreakdown.riv[city] || 0) + sessions;
    } else if (impCities.map(c => c.toLowerCase()).includes(cityLower)) {
      impCount += sessions;
      cityBreakdown.imp[city] = (cityBreakdown.imp[city] || 0) + sessions;
    }
  }

  console.log('=== ORGANIC SESSIONS BY COUNTY (March 9, 2026) ===\n');
  console.log(`Total organic sessions: ${total}`);
  console.log(`\n📍 LOCAL (3 counties): ${sdCount + rivCount + impCount} sessions (${((sdCount + rivCount + impCount) / total * 100).toFixed(1)}%)\n`);
  
  console.log(`San Diego County: ${sdCount}`);
  Object.entries(cityBreakdown.sd).sort((a,b) => b[1]-a[1]).forEach(([c, n]) => console.log(`  ${c}: ${n}`));
  
  console.log(`\nRiverside County: ${rivCount}`);
  Object.entries(cityBreakdown.riv).sort((a,b) => b[1]-a[1]).forEach(([c, n]) => console.log(`  ${c}: ${n}`));
  
  console.log(`\nImperial County: ${impCount}`);
  Object.entries(cityBreakdown.imp).sort((a,b) => b[1]-a[1]).forEach(([c, n]) => console.log(`  ${c}: ${n}`));
}

run().catch(console.error);
