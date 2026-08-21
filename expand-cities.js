#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const CITIES_DIR = '/Users/jarvis/clawd/scws-website/pages/locations/cities';

const cityData = {
  'oceanside': {
    name: 'Oceanside',
    geology: `Oceanside's coastal location creates unique well drilling challenges and opportunities. The city sits on varied geology — sandy and alluvial soils near the coast transitioning to clay-rich deposits inland. The proximity to Camp Pendleton means much of the eastern area remains undeveloped and ideal for private wells.`,
    geologyDetails: `Wells in Oceanside typically range from 200-400 feet deep. Coastal properties require careful well design to prevent saltwater intrusion from the Pacific Ocean. Inland areas, particularly around Morro Hills and the San Luis Rey River valley, often find excellent water quality in the deeper alluvial formations. We've drilled and serviced wells throughout inland Oceanside and understand the local aquifer dynamics and coastal challenges.`,
    problems: [
      { title: 'Saltwater intrusion concerns', desc: 'Coastal wells need proper depth and casing design to prevent seawater contamination in the aquifer' },
      { title: 'Clay layer complications', desc: 'Inland areas have dense clay layers that require specialized drilling techniques' },
      { title: 'Pressure tank failures', desc: 'Hard water mineral buildup can cause premature tank failure in Oceanside wells' },
      { title: 'Pump burnout', desc: 'High sediment loads in some areas can wear out pumps faster than average' },
      { title: 'Well screen clogging', desc: 'Iron bacteria and mineral deposits reduce well efficiency over time' }
    ],
    faqs: [
      { q: 'How deep are wells in Oceanside?', a: 'Most Oceanside wells are 200-400 feet deep. Coastal properties typically need deeper wells (300-400 ft) to avoid saltwater contamination, while inland areas often find good water at 200-300 feet. Areas near the San Luis Rey River have excellent groundwater availability.' },
      { q: 'Can I drill a well near the coast in Oceanside?', a: 'Yes, but it requires expert well design. We drill coastal wells deeper to access freshwater aquifers below the saltwater zone and use special casing techniques to prevent seawater intrusion. We\'ve successfully drilled wells in inland Oceanside, including near Camp Pendleton.' },
      { q: 'What does well water cost vs. municipal water in Oceanside?', a: 'After the initial well drilling investment ($15,000-$35,000 depending on depth), well water costs only your pump electricity — typically $30-80/month. Oceanside municipal water can cost $80-200+ monthly for average households, making wells cost-effective for long-term property owners.' },
      { q: 'How often should I service my Oceanside well?', a: 'We recommend annual well inspections for Oceanside properties. Coastal-area wells should be tested for salinity every 2-3 years. Regular maintenance prevents expensive emergencies and ensures your pump operates efficiently.' },
      { q: 'Do Oceanside wells need permits?', a: 'Yes, well drilling in San Diego County requires permits from the County Department of Environmental Health. We handle all permitting for you — we\'ve been working with the county since 2020 and know the exact requirements.' }
    ],
    neighborhoods: ['Morro Hills', 'Mission San Luis Rey', 'Rancho Del Oro', 'Fire Mountain', 'Peacock Hills', 'Ivey Ranch', 'Arrowood', 'South Oceanside']
  },
  
  'pauma-valley': {
    name: 'Pauma Valley',
    geology: `Pauma Valley is a rural mountain valley nestled in the foothills of Palomar Mountain. The area sits on ancient granite bedrock overlaid with decomposed granite and alluvial deposits. This makes for excellent well drilling conditions once you penetrate the surface weathered rock.`,
    geologyDetails: `Wells in Pauma Valley typically range from 200-500 feet deep. The valley floor has shallower water tables, while hillside properties often require deeper drilling through granite. The area's agricultural heritage means many existing wells serve large properties with high water demands. We understand the geology of this mountain valley and have extensive experience drilling in granite formations.`,
    problems: [
      { title: 'Granite bedrock drilling', desc: 'Hard granite requires specialized drill bits and slower drilling progress' },
      { title: 'Variable water tables', desc: 'Hillside properties have unpredictable water depths requiring careful site assessment' },
      { title: 'Seasonal flow variations', desc: 'Agricultural wells can experience reduced flow during dry seasons' },
      { title: 'Pump sizing challenges', desc: 'Large properties need high-capacity pumps that require expert selection' },
      { title: 'Lightning damage', desc: 'Mountain locations are prone to lightning strikes that can damage well electrical systems' }
    ],
    faqs: [
      { q: 'How deep are wells in Pauma Valley?', a: 'Most Pauma Valley wells are 200-500 feet deep. Valley floor properties typically find water at 200-300 feet, while hillside locations may require 400-500 feet to reach adequate water-bearing fractures in the granite. Agricultural properties often drill deeper for higher flow rates.' },
      { q: 'Can you drill through granite in Pauma Valley?', a: 'Absolutely. Granite drilling is our specialty. We use diamond-tipped bits and rotary-percussion drilling techniques designed for hard rock formations. Pauma Valley\'s granite is challenging but drillable with the right equipment and experience.' },
      { q: 'What flow rates can I expect from a Pauma Valley well?', a: 'Flow rates vary significantly based on location. Valley floor wells typically produce 10-30 GPM, while hillside granite wells may produce 5-15 GPM. Agricultural properties often need 20+ GPM, which we can achieve by drilling to the right depth and fracture zones.' },
      { q: 'How much does well drilling cost in Pauma Valley?', a: 'Pauma Valley well drilling typically costs $15,000-$45,000 depending on depth and rock hardness. Granite drilling is more expensive per foot than soft formations, but Pauma Valley\'s water quality makes it worthwhile for long-term property value.' },
      { q: 'Do I need a well for agricultural use in Pauma Valley?', a: 'For avocados, citrus, or other crops requiring consistent irrigation, a well is almost essential. Municipal water isn\'t available in rural Pauma Valley, and hauling water is impractical and expensive for agriculture.' }
    ],
    neighborhoods: ['Pauma Valley', 'Valley Center Road Area', 'Palomar Mountain Road', 'West Lilac Road', 'Cole Grade', 'Magee Road', 'Pala Mesa', 'Rural Estates']
  },
  
  'rancho-santa-fe': {
    name: 'Rancho Santa Fe',
    geology: `Rancho Santa Fe sits on rolling hills with mixed sedimentary and granitic geology. The area's estate properties and horse ranches have a long history of private wells serving large homes and agricultural operations. The geology varies from Tertiary sedimentary formations to intrusive granite.`,
    geologyDetails: `Wells in Rancho Santa Fe typically range from 300-600 feet deep. The area's hilly terrain means water tables vary significantly by location. Many wells serve large estates with guest houses, horse facilities, and extensive landscaping requiring high water production. We've drilled throughout Rancho Santa Fe and understand the complex geology and high standards expected in this community.`,
    problems: [
      { title: 'Deep water tables', desc: 'Hillside estates often require 400-600 ft wells, increasing drilling costs' },
      { title: 'High capacity demands', desc: 'Large estates with horse facilities need wells producing 20-40+ GPM' },
      { title: 'Water quality expectations', desc: 'High-end properties expect pristine water requiring filtration systems' },
      { title: 'Aesthetic requirements', desc: 'Wellheads and equipment must be discreetly located and landscaped' },
      { title: 'Property value protection', desc: 'Well work must meet high standards to maintain property values' }
    ],
    faqs: [
      { q: 'How deep are wells in Rancho Santa Fe?', a: 'Most Rancho Santa Fe wells are 300-600 feet deep. The rolling hills mean water tables vary significantly. Valley properties may find water at 300-400 feet, while hilltop estates often require 500-600+ feet. We conduct thorough site assessments before drilling.' },
      { q: 'Can a well serve a large estate property?', a: 'Absolutely. We regularly drill high-capacity wells for Rancho Santa Fe estates. With proper well design and pump sizing, a well can easily serve a main house, guest house, horse facilities, and extensive landscaping. Many estates produce 25-40+ GPM sustainably.' },
      { q: 'What about water quality in Rancho Santa Fe wells?', a: 'Rancho Santa Fe wells typically have excellent water quality. Most wells produce clean water with minimal treatment needed. We test every well and can design filtration systems for any specific concerns (iron, hardness, etc.).' },
      { q: 'Will a well affect my property value?', a: 'A properly drilled and maintained well actually increases property value in Rancho Santa Fe. Wells reduce operating costs and provide water independence — attractive features for estate buyers. We ensure all work meets the community\'s high standards.' },
      { q: 'How much does well drilling cost in Rancho Santa Fe?', a: 'Rancho Santa Fe wells typically cost $25,000-$60,000+ depending on depth and capacity requirements. Deep wells serving large estates are at the higher end. The investment pays off through reduced water bills and increased property value.' }
    ],
    neighborhoods: ['The Covenant', 'Rancho Pacifica', 'Fairbanks Ranch', 'Del Rayo Downs', 'The Bridges', 'Cielo', 'Rancho Valencia', 'Los Morros']
  },
  
  'san-jacinto': {
    name: 'San Jacinto',
    geology: `San Jacinto sits on the valley floor with deep alluvial deposits from thousands of years of mountain runoff. The San Jacinto Valley is one of the most productive water-bearing areas in Riverside County, with thick layers of sand, gravel, and clay overlying basement rock.`,
    geologyDetails: `Wells in San Jacinto typically range from 150-350 feet deep. The valley's alluvial geology provides excellent water production. Many agricultural and residential wells serve the area's growing population and remaining farmland. The proximity to the San Jacinto Mountains means excellent groundwater recharge. We've drilled extensively in the San Jacinto Valley and understand the local aquifer characteristics.`,
    problems: [
      { title: 'Groundwater overdraft', desc: 'Valley has experienced declining water tables in some areas due to agricultural pumping' },
      { title: 'Seasonal variations', desc: 'Water levels fluctuate based on mountain snowmelt and rainfall patterns' },
      { title: 'Well interference', desc: 'High well density in some neighborhoods can cause drawdown issues' },
      { title: 'Sediment in water', desc: 'Alluvial wells can have sand infiltration requiring proper well screen design' },
      { title: 'Depth uncertainty', desc: 'Water tables vary across the valley requiring site-specific assessment' }
    ],
    faqs: [
      { q: 'How deep are wells in San Jacinto?', a: 'Most San Jacinto wells are 150-350 feet deep. The valley floor has relatively shallow groundwater, though depths vary by location. Older wells may be shallower (150-200 ft), while newer wells often go deeper (250-350 ft) to access more stable water zones.' },
      { q: 'Is groundwater declining in San Jacinto?', a: 'Some areas have experienced water table decline due to agricultural pumping, but the valley still has good water availability. We drill to depths that access stable water zones less affected by seasonal variations. Proper well construction ensures long-term water security.' },
      { q: 'Can I use well water for landscaping in San Jacinto?', a: 'Yes! San Jacinto well water is excellent for landscaping. The water quality is generally good, and using well water for irrigation instead of municipal water saves significantly on utility bills — often $100-300+ monthly during summer.' },
      { q: 'What does well drilling cost in San Jacinto?', a: 'San Jacinto well drilling typically costs $12,000-$30,000 depending on depth. The relatively soft alluvial geology makes drilling faster and less expensive than mountain or bedrock locations. This is one of the more affordable areas for well drilling.' },
      { q: 'Do I need a permit to drill a well in San Jacinto?', a: 'Yes, Riverside County requires well permits. We handle all permitting and ensure your well meets county regulations. San Jacinto wells are straightforward to permit as the area has a long well-drilling history.' }
    ],
    neighborhoods: ['Downtown San Jacinto', 'Soboba Springs', 'Seven Hills', 'Mountain View', 'Valle Vista', 'Gilman Hot Springs', 'Ramona Bowl', 'West End']
  },
  
  'san-marcos': {
    name: 'San Marcos',
    geology: `San Marcos features diverse inland North County terrain, from rolling hills to valley areas. The geology includes Tertiary sedimentary formations, alluvial deposits, and some granitic intrusions. The Twin Oaks and Richland areas have particular well drilling potential.`,
    geologyDetails: `Wells in San Marcos typically range from 200-400 feet deep. The varied terrain means water tables differ significantly by neighborhood. Western San Marcos near the Lake San Marcos area has different geology than eastern areas approaching the mountains. We've drilled throughout San Marcos and can assess your specific property's well potential.`,
    problems: [
      { title: 'Variable geology', desc: 'Mixed rock types require flexible drilling approaches and equipment' },
      { title: 'Development pressure', desc: 'Increasing urbanization affects groundwater recharge patterns' },
      { title: 'Hard water issues', desc: 'Many San Marcos wells have high mineral content requiring softening' },
      { title: 'Seasonal flow changes', desc: 'Some wells experience reduced flow during extended dry periods' },
      { title: 'Permit complexity', desc: 'Developed areas have strict well setback requirements from property lines' }
    ],
    faqs: [
      { q: 'How deep are wells in San Marcos?', a: 'Most San Marcos wells are 200-400 feet deep. Western areas near Lake San Marcos typically need 250-350 feet, while eastern hillside properties may require 300-450 feet. The diverse terrain means each property needs individual assessment.' },
      { q: 'Can I drill a well in a residential San Marcos neighborhood?', a: 'It depends on your lot size and zoning. County regulations require specific setbacks from property lines, septic systems, and buildings. We assess your property and determine if well drilling is permitted. Many Twin Oaks and Richland area properties are suitable.' },
      { q: 'Is San Marcos well water safe to drink?', a: 'Yes, with proper testing and treatment if needed. San Marcos wells typically produce clean water, though some have hard water requiring softening. We test every well and recommend appropriate treatment systems. Many residents drink well water without issues.' },
      { q: 'What does well drilling cost in San Marcos?', a: 'San Marcos well drilling typically costs $15,000-$35,000 depending on depth and site conditions. The mixed geology means costs vary, but the area is generally mid-range for drilling expense. Long-term water cost savings make it worthwhile.' },
      { q: 'How do San Marcos wells compare to municipal water?', a: 'Municipal water in San Marcos costs $80-150+ monthly for average households. Well water costs only electricity ($30-60/month). Over 10-15 years, a well pays for itself through eliminated water bills. Plus you have water independence.' }
    ],
    neighborhoods: ['Twin Oaks', 'Richland', 'Discovery Hills', 'San Elijo Hills', 'Lake San Marcos', 'Woodland Park', 'Old Creek Ranch', 'Grand Avenue']
  },
  
  'santee': {
    name: 'Santee',
    geology: `Santee sits in East County San Diego on granitic bedrock typical of the Peninsular Ranges. The Santee Lakes area and surrounding communities have a mix of decomposed granite surface soils over solid granite basement rock. This creates excellent conditions for wells that tap fracture zones.`,
    geologyDetails: `Wells in Santee typically range from 200-500 feet deep. Granite drilling requires specialized equipment and expertise. The geology varies from deeply weathered decomposed granite to fresh, hard granite requiring diamond drilling. We've drilled throughout Santee and understand the local fracture patterns and water-bearing zones.`,
    problems: [
      { title: 'Granite hardness', desc: 'Solid granite requires slow, expensive drilling with specialized bits' },
      { title: 'Fracture zone location', desc: 'Water is found in fractures, requiring experience to target productive zones' },
      { title: 'Variable yields', desc: 'Granite wells can have unpredictable flow rates based on fracture density' },
      { title: 'Well depth uncertainty', desc: 'May need to drill deeper than expected to find adequate water' },
      { title: 'Lightning susceptibility', desc: 'East County storms can damage well electrical systems' }
    ],
    faqs: [
      { q: 'How deep are wells in Santee?', a: 'Most Santee wells are 200-500 feet deep. The granitic geology means water depth varies based on fracture zones. Some properties find excellent water at 250 feet, while others require 400-500 feet. We use geological assessment and local experience to target the best depths.' },
      { q: 'Can you drill through Santee\'s granite?', a: 'Yes, granite drilling is our specialty. Santee\'s granite is challenging but we use rotary-percussion drilling and diamond bits designed for hard rock. We\'ve drilled dozens of wells in East County granite and know how to reach water-bearing fractures efficiently.' },
      { q: 'What flow rates can I expect from a Santee well?', a: 'Santee granite wells typically produce 5-20 GPM, which is adequate for residential use (most homes need 6-10 GPM). Some wells in highly fractured zones produce 25+ GPM. We drill until we reach your target flow rate or determine the practical limit.' },
      { q: 'Is well water cheaper than Santee municipal water?', a: 'Significantly cheaper long-term. After the well drilling investment ($15,000-$40,000), well water costs only electricity ($30-70/month). Santee municipal water typically costs $90-180+ monthly, so wells pay for themselves over 8-12 years.' },
      { q: 'Do Santee wells need special maintenance?', a: 'Granite wells are actually low-maintenance. The hard rock doesn\'t cave or collapse like soft formations. We recommend annual pump inspections and water quality testing every few years. Santee wells are long-lasting investments.' }
    ],
    neighborhoods: ['Santee Lakes', 'Carlton Hills', 'Carlton Oaks', 'Riverview', 'Edgemont', 'Cuyamaca Street Area', 'West Santee', 'Fanita Ranch']
  },
  
  'spring-valley': {
    name: 'Spring Valley',
    geology: `Spring Valley is an East County suburb with mixed alluvial and granitic geology. The transition zone between valley deposits and mountain bedrock creates varied well drilling conditions. The proximity to Sweetwater Reservoir and the Sweetwater River valley influences groundwater availability.`,
    geologyDetails: `Wells in Spring Valley typically range from 200-400 feet deep. Western areas closer to the valley floor have alluvial deposits over granite, while eastern hillside properties drill primarily through granite. The area's geology has been shaped by ancient stream deposits and granitic intrusions. We understand Spring Valley's complex subsurface and can assess your property's well potential.`,
    problems: [
      { title: 'Mixed geology complexity', desc: 'Transition from alluvial to granite requires adaptable drilling techniques' },
      { title: 'Urban well constraints', desc: 'Developed areas have strict setback requirements limiting well placement' },
      { title: 'Water table variations', desc: 'Groundwater depth varies significantly across Spring Valley neighborhoods' },
      { title: 'Hard water minerals', desc: 'Many wells have elevated hardness requiring water softening systems' },
      { title: 'Permit challenges', desc: 'County regulations for wells in developed areas require careful navigation' }
    ],
    faqs: [
      { q: 'How deep are wells in Spring Valley?', a: 'Most Spring Valley wells are 200-400 feet deep. Valley floor properties typically find water at 200-300 feet in alluvial deposits, while hillside properties drilling through granite may require 350-450 feet. Each property is unique and needs assessment.' },
      { q: 'Can I drill a well on my Spring Valley property?', a: 'It depends on your lot size, zoning, and proximity to neighbors. County regulations require setbacks from property lines, buildings, and septic systems. We evaluate your property and determine if well drilling is feasible. Many larger lots qualify.' },
      { q: 'Is Spring Valley well water good quality?', a: 'Generally yes. Spring Valley wells typically produce clean water, though hardness (minerals) is common and many homeowners install softeners. We test every well for quality and recommend treatment if needed. Water is safe and reliable.' },
      { q: 'What does well drilling cost in Spring Valley?', a: 'Spring Valley well drilling typically costs $15,000-$35,000 depending on depth and geology encountered. Mixed alluvial/granite drilling is moderately priced. The investment pays off through eliminated monthly water bills over time.' },
      { q: 'How do Spring Valley wells compare to city water?', a: 'Spring Valley\'s municipal water (Helix Water District) costs $70-150+ monthly for average households. Well water costs only pump electricity ($30-60/month). Over 10-15 years, a well saves $12,000-27,000+ in water bills.' }
    ],
    neighborhoods: ['Casa de Oro', 'Mount Helix', 'Sweetwater', 'Rancho San Diego Border', 'Jamacha', 'Los Coches', 'Hillsdale', 'Spring Valley Proper']
  },
  
  'valley-center': {
    name: 'Valley Center',
    geology: `Valley Center is rural North County's agricultural heartland, famous for avocado and citrus groves. The area sits on decomposed granite with pockets of alluvial deposits in valley areas. The rolling hills and large properties make Valley Center ideal for private wells serving both agricultural and residential needs.`,
    geologyDetails: `Wells in Valley Center typically range from 200-600 feet deep. Agricultural wells serving large groves often drill deeper for higher flow rates (20-40+ GPM). The decomposed granite is relatively easy to drill compared to solid granite, but depths vary based on fracture zones and property elevation. We've drilled extensively in Valley Center and understand the area's agricultural water demands.`,
    problems: [
      { title: 'Agricultural capacity needs', desc: 'Avocado/citrus groves require high-flow wells producing 20-40+ GPM' },
      { title: 'Seasonal demand peaks', desc: 'Irrigation demand during dry season can stress well production' },
      { title: 'Variable water tables', desc: 'Hillside properties have unpredictable water depths' },
      { title: 'Granite drilling costs', desc: 'Deep wells through decomposed and solid granite increase expenses' },
      { title: 'Power requirements', desc: 'High-capacity pumps need adequate electrical service (often 240V)' }
    ],
    faqs: [
      { q: 'How deep are wells in Valley Center?', a: 'Most Valley Center wells are 200-600 feet deep. Residential wells average 250-400 feet, while agricultural wells serving groves often drill 400-600 feet to achieve 25-40 GPM flow rates needed for efficient irrigation. Decomposed granite is easier to drill than solid granite.' },
      { q: 'Can a well support avocado/citrus groves?', a: 'Absolutely. Valley Center\'s agriculture depends on wells. We design agricultural wells to provide the flow rate and reliability your grove needs. A typical 10-acre avocado grove needs 15-25 GPM; we regularly drill wells producing 30-50+ GPM for agricultural operations.' },
      { q: 'What does agricultural well drilling cost in Valley Center?', a: 'Valley Center agricultural wells typically cost $20,000-$60,000 depending on depth and required flow rate. High-capacity wells are more expensive but pay for themselves quickly — municipal water for irrigation would cost $500-2,000+ monthly for typical groves.' },
      { q: 'How reliable are Valley Center wells during drought?', a: 'Very reliable. Valley Center\'s deeper aquifers are resilient during drought. We drill to depths that access stable water zones less affected by surface conditions. Most agricultural wells maintained production even during California\'s recent multi-year droughts.' },
      { q: 'Do Valley Center wells need permits?', a: 'Yes, San Diego County requires well permits. We handle all permitting for agricultural and residential wells. Valley Center has a long well-drilling tradition and permitting is straightforward when done correctly.' }
    ],
    neighborhoods: ['Valley Center Proper', 'Woods Valley', 'Paradise Mountain', 'Pauma Heights', 'Valley View', 'Cole Grade', 'Circle R', 'Magee Road Area']
  },
  
  'vista': {
    name: 'Vista',
    geology: `Vista is inland North County with rolling hills and mixed geological formations. The area includes Tertiary sedimentary formations, alluvial deposits in valley areas, and some granitic intrusions. Buena Vista Creek and its tributaries have shaped the local geology and groundwater patterns.`,
    geologyDetails: `Wells in Vista typically range from 200-400 feet deep. The varied terrain means water tables differ by neighborhood. Western Vista near the creek valleys has shallower water tables, while eastern hillside properties often require deeper drilling. We've drilled throughout Vista and understand the local aquifer characteristics and geological variations.`,
    problems: [
      { title: 'Geological diversity', desc: 'Mixed rock types require flexible drilling approaches' },
      { title: 'Urban development pressure', desc: 'Increasing development affects groundwater recharge' },
      { title: 'Hard water minerals', desc: 'Many Vista wells produce hard water requiring softening' },
      { title: 'Permit complexity', desc: 'Developed areas have strict setback and placement requirements' },
      { title: 'Seasonal variations', desc: 'Some wells experience flow changes during dry periods' }
    ],
    faqs: [
      { q: 'How deep are wells in Vista?', a: 'Most Vista wells are 200-400 feet deep. Creek valley properties typically find water at 200-300 feet, while hillside locations may require 300-450 feet. The rolling terrain means each property needs individual geological assessment before drilling.' },
      { q: 'Can I drill a well in Vista city limits?', a: 'It depends on your property\'s zoning and lot size. County and city regulations require specific setbacks from property lines and structures. We assess your property and determine feasibility. Many larger-lot Vista properties can accommodate wells.' },
      { q: 'Is Vista well water good quality?', a: 'Generally yes. Vista wells typically produce clean water suitable for all household uses. Hardness (mineral content) is common, and many homeowners install water softeners. We test every well and recommend treatment if needed.' },
      { q: 'What does well drilling cost in Vista?', a: 'Vista well drilling typically costs $15,000-$35,000 depending on depth and site conditions. The mixed geology means costs vary by location, but Vista is generally mid-range for North County drilling expenses.' },
      { q: 'How do Vista wells compare to city water costs?', a: 'Vista Irrigation District water costs $75-160+ monthly for average households. Well water costs only pump electricity ($30-65/month). Over 10-15 years, a well saves $13,500-28,500+ in water bills while providing water independence.' }
    ],
    neighborhoods: ['Buena Vista', 'Old Town Vista', 'Shadowridge', 'Vista Village', 'Foothill', 'Sycamore Creek', 'Brengle Terrace', 'Sunrise']
  },
  
  'wildomar': {
    name: 'Wildomar',
    geology: `Wildomar sits in southwest Riverside County with alluvial and sedimentary geology typical of the Elsinore Valley area. The rapidly developing city has excellent groundwater availability, with thick alluvial deposits overlying deeper formations. The area's water table supports both residential and agricultural wells.`,
    geologyDetails: `Wells in Wildomar typically range from 200-400 feet deep. The valley's alluvial geology provides good water production. Many newer developments sit on former agricultural land where wells previously served farms. The transition to residential development means more properties are discovering the benefits of private wells for cost savings and water security.`,
    problems: [
      { title: 'Rapid development impacts', desc: 'Increased development changes groundwater recharge patterns' },
      { title: 'Variable water quality', desc: 'Some areas have naturally occurring minerals requiring treatment' },
      { title: 'Well depth variations', desc: 'Water tables vary across the valley floor and hillsides' },
      { title: 'Permit requirements', desc: 'Riverside County has specific well regulations for developing areas' },
      { title: 'Sediment issues', desc: 'Alluvial wells need proper screen design to prevent sand infiltration' }
    ],
    faqs: [
      { q: 'How deep are wells in Wildomar?', a: 'Most Wildomar wells are 200-400 feet deep. The alluvial valley floor has relatively consistent water tables, though depth varies by specific location. Newer wells typically drill to 250-350 feet to access stable water zones.' },
      { q: 'Can I drill a well in new Wildomar developments?', a: 'Yes, if your lot size and zoning permit it. Many larger-lot subdivisions in Wildomar are suitable for wells. We check county regulations for your specific property. Even in developing areas, wells can provide significant water cost savings.' },
      { q: 'Is Wildomar well water safe?', a: 'Yes, with proper testing and treatment if needed. Wildomar wells generally produce clean water, though some areas have natural minerals. We test every well for safety and quality, and recommend treatment systems if needed. Many residents use well water without issues.' },
      { q: 'What does well drilling cost in Wildomar?', a: 'Wildomar well drilling typically costs $15,000-$32,000 depending on depth. The alluvial geology makes drilling relatively straightforward and affordable compared to hard rock areas. This is good value for long-term water independence.' },
      { q: 'Do Wildomar wells save money vs. city water?', a: 'Significantly. Elsinore Valley Municipal Water District charges $85-180+ monthly for average households. Well water costs only electricity ($35-70/month). A well pays for itself in 8-12 years through eliminated water bills, then continues saving money indefinitely.' }
    ],
    neighborhoods: ['Windsong Valley', 'Marna O\'Brien Park Area', 'Clinton Keith Corridor', 'Bundy Canyon', 'Lake Country', 'Palomar Heights', 'Grand Avenue', 'Summerhouse']
  },
  
  'winchester': {
    name: 'Winchester',
    geology: `Winchester is an unincorporated community in Riverside County's agricultural belt. The area features alluvial and sedimentary geology similar to the broader Elsinore/Perris valley region. The rural character and large lot sizes make Winchester ideal for private wells serving both homes and small farms.`,
    geologyDetails: `Wells in Winchester typically range from 200-500 feet deep. Agricultural wells serving farms and vineyards often drill deeper for higher flow rates. The area's geology includes sand, gravel, and clay layers over deeper sedimentary formations. We've drilled extensively in rural Riverside County and understand Winchester's groundwater conditions and agricultural water needs.`,
    problems: [
      { title: 'Agricultural demand', desc: 'Farms and vineyards need high-capacity wells producing consistent flow' },
      { title: 'Water table variations', desc: 'Depth varies across the valley and hillside transition zones' },
      { title: 'Sediment in water', desc: 'Alluvial wells can have sand requiring proper well screen selection' },
      { title: 'Seasonal flow changes', desc: 'Agricultural wells may experience reduced flow during extended drought' },
      { title: 'Development pressure', desc: 'Rapid growth is changing the area\'s groundwater dynamics' }
    ],
    faqs: [
      { q: 'How deep are wells in Winchester?', a: 'Most Winchester wells are 200-500 feet deep. Residential wells average 200-350 feet, while agricultural wells serving farms often drill 350-500 feet to achieve higher flow rates (15-30+ GPM) needed for irrigation.' },
      { q: 'Can a well support agricultural use in Winchester?', a: 'Absolutely. Winchester\'s agriculture depends on wells. We design agricultural wells for the flow rate your operation needs. Typical small farms need 15-25 GPM; we regularly drill wells producing 25-40+ GPM for vineyards, pastures, and crop irrigation.' },
      { q: 'Is Winchester a good area for wells?', a: 'Yes, excellent. Winchester has good groundwater availability and large lots that easily accommodate wells. The rural character means fewer permit complications than urban areas. Many properties save $1,200-3,000+ annually by using well water instead of municipal water.' },
      { q: 'What does well drilling cost in Winchester?', a: 'Winchester well drilling typically costs $15,000-$40,000 depending on depth and capacity. Residential wells are toward the lower end; agricultural high-capacity wells are more expensive. The relatively soft geology makes drilling efficient and affordable.' },
      { q: 'Do Winchester wells need permits?', a: 'Yes, Riverside County requires well permits. We handle all permitting and ensure your well meets county regulations. Winchester has a strong agricultural well-drilling tradition and permitting is straightforward with experienced contractors.' }
    ],
    neighborhoods: ['Winchester Hills', 'Domenigoni Valley', 'Lindenberger Road', 'Scott Road Area', 'Borel Road', 'Sanderson Avenue', 'Rural Winchester', 'Agriculture Preserve']
  }
};

// Read template, inject sections, write back
function expandCity(filename) {
  const cityKey = filename.replace('.html', '');
  const data = cityData[cityKey];
  if (!data) {
    console.log(`⚠️  No data for ${filename}, skipping`);
    return false;
  }
  
  const filePath = path.join(CITIES_DIR, filename);
  let html = fs.readFileSync(filePath, 'utf-8');
  
  // Check if already expanded (has FAQ section)
  if (html.includes('<!-- FAQ Section -->')) {
    console.log(`✓ ${filename} already expanded, skipping`);
    return false;
  }
  
  // Find the existing geology section and replace it
  const geologySection = `    <section class="py-16 bg-slate-50">
        <div class="max-w-4xl mx-auto px-4">
            <h2 class="text-3xl font-bold text-center mb-8">${data.name} Geology & Well Drilling Conditions</h2>
            <div class="prose prose-lg max-w-none text-gray-700">
                <p>${data.geology}</p>
                <p>${data.geologyDetails}</p>
                <h3 class="text-2xl font-bold mt-8 mb-4">Common Well Problems in ${data.name}</h3>
                <ul class="list-disc pl-6 space-y-2">
${data.problems.map(p => `                    <li><strong>${p.title}:</strong> ${p.desc}</li>`).join('\n')}
                </ul>
            </div>
        </div>
    </section>`;
  
  const faqSection = `    <!-- FAQ Section -->
    <section class="py-16">
        <div class="max-w-4xl mx-auto px-4">
            <h2 class="text-3xl font-bold text-center mb-12">${data.name} Well Service FAQs</h2>
            <div class="space-y-6">
${data.faqs.map(f => `                <div class="bg-gray-50 rounded-lg p-6">
                    <h3 class="text-xl font-semibold mb-3">${f.q}</h3>
                    <p class="text-gray-700">${f.a}</p>
                </div>`).join('\n')}
            </div>
        </div>
    </section>`;
  
  const whyChooseSection = `    <!-- Why Choose SCWS -->
    <section class="py-16 bg-slate-50">
        <div class="max-w-4xl mx-auto px-4">
            <h2 class="text-3xl font-bold text-center mb-8">Why Choose Southern California Well Service?</h2>
            <div class="grid md:grid-cols-2 gap-8">
                <div class="flex gap-4">
                    <div class="text-accent text-3xl">✓</div>
                    <div>
                        <h3 class="font-bold text-lg mb-2">Local Expertise</h3>
                        <p class="text-gray-700">We've served ${data.name} for 20+ years. We know the geology, the regulations, and the specific challenges of this area.</p>
                    </div>
                </div>
                <div class="flex gap-4">
                    <div class="text-accent text-3xl">✓</div>
                    <div>
                        <h3 class="font-bold text-lg mb-2">C-57 Licensed & Insured</h3>
                        <p class="text-gray-700">Fully licensed well drilling contractors with $2M liability insurance. We follow all county regulations.</p>
                    </div>
                </div>
                <div class="flex gap-4">
                    <div class="text-accent text-3xl">✓</div>
                    <div>
                        <h3 class="font-bold text-lg mb-2">Proven Track Record</h3>
                        <p class="text-gray-700">Hundreds of successful wells drilled throughout the region. We understand local aquifer dynamics.</p>
                    </div>
                </div>
                <div class="flex gap-4">
                    <div class="text-accent text-3xl">✓</div>
                    <div>
                        <h3 class="font-bold text-lg mb-2">4.9★ Google Rating</h3>
                        <p class="text-gray-700">Reviews from customers across our service area.</p>
                    </div>
                </div>
                <div class="flex gap-4">
                    <div class="text-accent text-3xl">✓</div>
                    <div>
                        <h3 class="font-bold text-lg mb-2">Modern Equipment</h3>
                        <p class="text-gray-700">State-of-the-art drilling rigs and downhole video inspection. We use technology to drill accurately and diagnose problems fast.</p>
                    </div>
                </div>
                <div class="flex gap-4">
                    <div class="text-accent text-3xl">✓</div>
                    <div>
                        <h3 class="font-bold text-lg mb-2">Fair Pricing</h3>
                        <p class="text-gray-700">Honest estimates with no hidden fees. We explain exactly what you need — and what you don't.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>`;
  
  // Replace existing geology section
  html = html.replace(
    /<section class="py-16 bg-slate-50">[\s\S]*?<\/section>\s*<section class="py-16">/,
    geologySection + '\n\n' + faqSection + '\n\n' + whyChooseSection + '\n\n    <section class="py-16">'
  );
  
  // Update neighborhoods
  const neighborhoodGrid = data.neighborhoods.map(n => `                <div class="bg-gray-50 py-3 px-4 rounded">${n}</div>`).join('\n');
  html = html.replace(
    /(<h2 class="text-3xl font-bold text-center mb-8">.*? Areas We Serve<\/h2>\s*<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">)([\s\S]*?)(<\/div>)/,
    `$1\n${neighborhoodGrid}\n            $3`
  );
  
  // Update footer
  html = html.replace(
    /<p>© 2026 Southern California Well Service\. Proudly serving .*?\.<\/p>/,
    `<p>© 2026 Southern California Well Service. Proudly serving ${data.name}.</p>
            <p class="mt-2 text-sm">Last Updated: March 2026</p>`
  );
  
  fs.writeFileSync(filePath, html, 'utf-8');
  console.log(`✅ Expanded ${filename}`);
  return true;
}

// Process all cities
const cities = [
  'oceanside.html',
  'pauma-valley.html',
  'rancho-santa-fe.html',
  'san-jacinto.html',
  'san-marcos.html',
  'santee.html',
  'spring-valley.html',
  'valley-center.html',
  'vista.html',
  'wildomar.html',
  'winchester.html'
];

console.log('🚀 Expanding city pages...\n');
let count = 0;
cities.forEach(city => {
  if (expandCity(city)) count++;
});

console.log(`\n✨ Expanded ${count} city pages`);
