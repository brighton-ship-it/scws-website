#!/usr/bin/env node
const { BetaAnalyticsDataClient } = require('@google-analytics/data');
const path = require('path');
const c = new BetaAnalyticsDataClient({ keyFilename: path.join(process.env.HOME, 'clawd/credentials/google-analytics-service-account.json') });
(async()=>{
  const [r] = await c.runReport({
    property: 'properties/396700369',
    dateRanges:[{startDate:'7daysAgo',endDate:'today'}],
    dimensions:[{name:'date'},{name:'region'}],
    metrics:[{name:'sessions'},{name:'screenPageViews'}],
    dimensionFilter:{filter:{fieldName:'country',stringFilter:{value:'United States'}}},
    limit:500
  });
  let caS=0,caP=0,usS=0,usP=0;
  const byDay={};
  for(const row of r.rows||[]){
    const d=row.dimensionValues[0].value, reg=row.dimensionValues[1].value;
    const s=+row.metricValues[0].value, p=+row.metricValues[1].value;
    usS+=s; usP+=p;
    if(reg==='California'){
      caS+=s; caP+=p;
      byDay[d]=(byDay[d]||[0,0]);
      byDay[d][0]+=s; byDay[d][1]+=p;
    }
  }
  console.log(`Last 7 days — US total: ${usS} sessions / ${usP} pageviews`);
  console.log(`California: ${caS} sessions / ${caP} pageviews (${(caS/usS*100).toFixed(1)}%)\n`);
  console.log('CA by day:');
  for(const d of Object.keys(byDay).sort()){
    const dd=`${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6)}`;
    console.log(`  ${dd}: ${byDay[d][0]} sessions / ${byDay[d][1]} pageviews`);
  }
})();
