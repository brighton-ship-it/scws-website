#!/usr/bin/env node
const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const path = require('path');
const c = new BetaAnalyticsDataClient({ keyFilename: path.join(process.env.HOME, 'clawd/credentials/google-analytics-service-account.json') });

const SERVICE = new Set([
  'san diego','escondido','oceanside','carlsbad','vista','el cajon','encinitas','chula vista','san marcos','poway','la mesa','santee','ramona','julian','alpine','lakeside','fallbrook','valley center','bonsall','pauma valley','palomar mountain','borrego springs','warner springs','descanso','pine valley','campo','potrero','jamul','spring valley','lemon grove','national city','imperial beach','coronado','la jolla','del mar','solana beach','rancho santa fe','rancho bernardo','scripps ranch','mira mesa','clairemont','university city','kearny mesa','mission valley',
  'temecula','murrieta','hemet','san jacinto','menifee','wildomar','lake elsinore','perris','riverside','corona','moreno valley','beaumont','banning','palm springs','palm desert','indio','coachella','la quinta','cathedral city','desert hot springs','idyllwild','anza','aguanga','sage','winchester','french valley','sun city','nuevo','homeland','east hemet','valle vista','green acres','rancho mirage',
  'san bernardino','ontario','rancho cucamonga','fontana','rialto','redlands','chino','chino hills','upland','yucaipa','highland','colton','loma linda','grand terrace','big bear','big bear lake','running springs','crestline','lake arrowhead','wrightwood','phelan','pinon hills','hesperia','victorville','apple valley','oak hills','adelanto','lucerne valley','twentynine palms','yucca valley','joshua tree','morongo valley','pioneertown','landers','barstow','needles'
]);

async function getServiceAreaTrend() {
  console.log('📊 SERVICE AREA TRAFFIC TREND (Before vs After Drop)\n');
  
  // May 21-June 3 (before drop)
  console.log('BEFORE DROP (May 21 - June 3):');
  const [before] = await c.runReport({
    property: 'properties/396700369',
    dateRanges:[{startDate:'2026-05-21',endDate:'2026-06-03'}],
    dimensions:[{name:'city'}],
    metrics:[{name:'sessions'}],
    dimensionFilter:{andGroup:{expressions:[
      {filter:{fieldName:'region',stringFilter:{value:'California'}}},
      {notExpression:{filter:{fieldName:'sessionDefaultChannelGroup',stringFilter:{value:'Paid Search'}}}}
    ]}},
    limit:1000
  });
  
  let beforeInArea=0, beforeTotal=0;
  for(const row of before.rows||[]){
    const city=row.dimensionValues[0].value;
    const s=+row.metricValues[0].value;
    beforeTotal+=s;
    if(SERVICE.has(city.toLowerCase())){ beforeInArea+=s; }
  }
  
  console.log(`  Total CA organic: ${beforeTotal}`);
  console.log(`  Service area: ${beforeInArea} (${(beforeInArea/beforeTotal*100).toFixed(1)}%)`);
  console.log(`  Outside area: ${beforeTotal-beforeInArea}`);
  console.log(`  Avg/day: ${(beforeInArea/14).toFixed(1)} service area sessions\n`);
  
  // June 4-17 (after drop)
  console.log('AFTER DROP (June 4 - June 17):');
  const [after] = await c.runReport({
    property: 'properties/396700369',
    dateRanges:[{startDate:'2026-06-04',endDate:'2026-06-17'}],
    dimensions:[{name:'city'}],
    metrics:[{name:'sessions'}],
    dimensionFilter:{andGroup:{expressions:[
      {filter:{fieldName:'region',stringFilter:{value:'California'}}},
      {notExpression:{filter:{fieldName:'sessionDefaultChannelGroup',stringFilter:{value:'Paid Search'}}}}
    ]}},
    limit:1000
  });
  
  let afterInArea=0, afterTotal=0;
  for(const row of after.rows||[]){
    const city=row.dimensionValues[0].value;
    const s=+row.metricValues[0].value;
    afterTotal+=s;
    if(SERVICE.has(city.toLowerCase())){ afterInArea+=s; }
  }
  
  console.log(`  Total CA organic: ${afterTotal}`);
  console.log(`  Service area: ${afterInArea} (${(afterInArea/afterTotal*100).toFixed(1)}%)`);
  console.log(`  Outside area: ${afterTotal-afterInArea}`);
  console.log(`  Avg/day: ${(afterInArea/14).toFixed(1)} service area sessions\n`);
  
  // Calculate change
  const beforeAvg = beforeInArea/14;
  const afterAvg = afterInArea/14;
  const change = ((afterAvg - beforeAvg) / beforeAvg * 100).toFixed(1);
  
  console.log('📈 SERVICE AREA CHANGE:');
  console.log(`  Before: ${beforeAvg.toFixed(1)} sessions/day`);
  console.log(`  After: ${afterAvg.toFixed(1)} sessions/day`);
  console.log(`  Change: ${change > 0 ? '+' : ''}${change}%`);
  
  console.log('\n💡 INTERPRETATION:');
  if(Math.abs(change) < 10) {
    console.log('  ✅ Service area traffic is STABLE - the drop was mostly wasted traffic!');
  } else if(change < 0) {
    console.log(`  ⚠️ Service area traffic down ${Math.abs(change)}% - this hurts business`);
  } else {
    console.log(`  ✅ Service area traffic UP ${change}% - drop doesn't matter!`);
  }
}

getServiceAreaTrend().catch(console.error);
