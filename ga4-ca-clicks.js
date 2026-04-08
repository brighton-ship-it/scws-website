#!/usr/bin/env node
const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const path = require('path');
const PROPERTY_ID = '396700369';
const KEY_FILE = path.join(process.env.HOME, 'clawd/credentials/google-analytics-service-account.json');
const c = new BetaAnalyticsDataClient({ keyFilename: KEY_FILE });
(async()=>{
  const [r] = await c.runReport({
    property: `properties/${PROPERTY_ID}`,
    dateRanges:[{startDate:'2026-04-07',endDate:'2026-04-07'}],
    dimensions:[{name:'date'},{name:'region'}],
    metrics:[{name:'sessions'},{name:'screenPageViews'},{name:'eventCount'}],
    dimensionFilter:{filter:{fieldName:'country',stringFilter:{value:'United States'}}},
    limit:200
  });
  let yT={s:0,p:0,e:0},tT={s:0,p:0,e:0};
  for(const row of r.rows||[]){
    const d=row.dimensionValues[0].value, reg=row.dimensionValues[1].value;
    if(reg!=='California')continue;
    const s=+row.metricValues[0].value,p=+row.metricValues[1].value,e=+row.metricValues[2].value;
    if(d==='20260406'){yT.s+=s;yT.p+=p;yT.e+=e;}
    else if(d==='20260407'){tT.s+=s;tT.p+=p;tT.e+=e;}
  }
  console.log('CA traffic:');
  console.log(`  Yesterday (Apr 6): ${yT.s} sessions, ${yT.p} pageviews, ${yT.e} events`);
  console.log(`  Today (Apr 7):     ${tT.s} sessions, ${tT.p} pageviews, ${tT.e} events`);
})();
