#!/usr/bin/env node
const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const path = require('path');
const c = new BetaAnalyticsDataClient({ keyFilename: path.join(process.env.HOME, 'clawd/credentials/google-analytics-service-account.json') });
const SERVICE = new Set([
  'san diego','escondido','oceanside','carlsbad','vista','el cajon','encinitas','chula vista','san marcos','poway','la mesa','santee','ramona','julian','alpine','lakeside','fallbrook','valley center','bonsall','pauma valley','palomar mountain','borrego springs','warner springs','descanso','pine valley','campo','potrero','jamul','spring valley','lemon grove','national city','imperial beach','coronado','la jolla','del mar','solana beach','rancho santa fe','rancho bernardo','scripps ranch','mira mesa','clairemont','university city','kearny mesa','mission valley',
  'temecula','murrieta','hemet','san jacinto','menifee','wildomar','lake elsinore','perris','riverside','corona','moreno valley','beaumont','banning','palm springs','palm desert','indio','coachella','la quinta','cathedral city','desert hot springs','idyllwild','anza','aguanga','sage','winchester','french valley','sun city','nuevo','homeland','east hemet','valle vista','green acres','rancho mirage',
  'san bernardino','ontario','rancho cucamonga','fontana','rialto','redlands','chino','chino hills','upland','yucaipa','highland','colton','loma linda','grand terrace','big bear','big bear lake','running springs','crestline','lake arrowhead','wrightwood','phelan','pinon hills','hesperia','victorville','apple valley','oak hills','adelanto','lucerne valley','twentynine palms','yucca valley','joshua tree','morongo valley','pioneertown','landers','barstow','needles'
]);
(async()=>{
  const [r] = await c.runReport({
    property: 'properties/396700369',
    dateRanges:[{startDate:'2026-04-07',endDate:'2026-04-07'}],
    dimensions:[{name:'city'}],
    metrics:[{name:'sessions'}],
    dimensionFilter:{filter:{fieldName:'region',stringFilter:{value:'California'}}},
    limit:500
  });
  let inArea=0, outArea=0, total=0;
  const hits=[], misses=[];
  for(const row of r.rows||[]){
    const city=row.dimensionValues[0].value;
    const s=+row.metricValues[0].value;
    total+=s;
    if(SERVICE.has(city.toLowerCase())){ inArea+=s; hits.push([city,s]); }
    else { outArea+=s; misses.push([city,s]); }
  }
  hits.sort((a,b)=>b[1]-a[1]);
  misses.sort((a,b)=>b[1]-a[1]);
  console.log(`CA total: ${total}`);
  console.log(`In service area: ${inArea}`);
  console.log(`Outside: ${outArea}`);
  console.log('\nTop in-area cities:');
  hits.slice(0,10).forEach(h=>console.log(`  ${h[0]}: ${h[1]}`));
  console.log('\nTop out-of-area CA cities:');
  misses.slice(0,10).forEach(m=>console.log(`  ${m[0]}: ${m[1]}`));
})();
