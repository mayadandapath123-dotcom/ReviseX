"""Geography clusters - Contemporary India II.

Seven chapters: Resources and Development, Forest and Wildlife Resources, Water
Resources, Agriculture, Minerals and Energy Resources, Manufacturing Industries,
and Lifelines of National Economy.

Difficulty is set by what the student has to DO. Naming the classification of a
resource is recall and is marked easy; the generator then escalates the reverse
form ("which classification applies to...") to medium and the negative form
("which statement is NOT correct?") to hard, which is genuinely what those forms
demand.
"""

from __future__ import annotations

CLUSTERS = [
    # ══════════════════════════════════════════════════════════════════
    # Chapter 1 - Resources and Development
    # ══════════════════════════════════════════════════════════════════
    ("ss-geo-resources.types", "classified as", [
        ("Resources on the basis of origin", "Biotic and abiotic"),
        ("Resources on the basis of exhaustibility", "Renewable and non-renewable"),
        ("Resources on the basis of ownership", "Individual, community, national and international"),
        ("Resources on the basis of status of development", "Potential, developed, stock and reserves"),
        ("Biotic resources", "Obtained from the biosphere and having life"),
        ("Abiotic resources", "Composed of non-living things such as rocks and metals"),
        ("Renewable resources", "Renewable by physical, chemical or mechanical processes"),
        ("Non-renewable resources", "Formed over very long geological time"),
        ("Potential resources", "Found in a region but not yet utilised"),
        ("Developed resources", "Surveyed, with quality and quantity determined"),
        ("Stock", "Materials that could meet needs but lack appropriate technology"),
        ("Reserves", "A subset of stock usable with existing technology but kept for the future"),
        ("Community-owned resources", "Grazing grounds, ponds and burial grounds"),
        ("National resources", "Everything within political boundaries and oceanic areas up to 12 nautical miles"),
        ("International resources", "Regulated by international institutions beyond 200 nautical miles"),
        ("Individual resources", "Owned privately by an individual, such as plots and houses"),
    ], "easy"),

    ("ss-geo-resources.types", "example of", [
        ("A biotic resource", "Humans, flora and fauna"),
        ("An abiotic resource", "Rocks and metals"),
        ("A renewable resource", "Solar and wind energy, water, forests"),
        ("A non-renewable resource", "Coal, petroleum and minerals"),
        ("A potential resource", "Solar and wind energy in Rajasthan and Gujarat, not fully developed"),
        ("A stock resource", "Water, which cannot yet be used as fuel for lack of technology"),
        ("A reserve", "Water in a dam reserved for future power generation"),
        ("An international resource", "Oceanic resources beyond the exclusive economic zone"),
        ("A community resource", "Village grazing grounds"),
    ], "easy"),

    ("ss-geo-resources.soil", "found in", [
        ("Alluvial soil", "River deltas and the northern plains"),
        ("Black soil, also called regur", "The Deccan plateau, Maharashtra and Gujarat"),
        ("Red and yellow soil", "Crystalline igneous rocks in low-rainfall parts of the eastern and southern Deccan"),
        ("Laterite soil", "Areas of high temperature and heavy rainfall"),
        ("Arid soil", "Western Rajasthan and parts of Gujarat"),
        ("Forest soil", "Hilly and mountainous regions"),
        ("Bangar alluvium", "Older alluvium away from rivers, with calcareous nodules called kankar"),
        ("Khadar alluvium", "Newer alluvium near rivers, finer and more fertile"),
    ], "easy"),

    ("ss-geo-resources.soil", "best suited for", [
        ("Black soil", "Cotton"),
        ("Alluvial soil", "Sugarcane, paddy, wheat and pulses"),
        ("Laterite soil", "Tea, coffee, cashew and tapioca"),
        ("Arid soil", "Crops grown with irrigation, such as wheat in Rajasthan"),
        ("Red soil", "Millets and oilseeds"),
        ("Forest soil", "Spices, tea, coffee and fruits"),
        ("Black soil's moisture retention", "Dry farming without irrigation"),
    ], "easy"),

    ("ss-geo-resources.soil", "controlled by", [
        ("Gully erosion", "Contour bunding, check dams and gully plugging"),
        ("Sheet erosion", "Contour ploughing and strip cropping"),
        ("Wind erosion", "Shelter belts of trees planted in rows"),
        ("Ravine formation in the Chambal basin", "Afforestation and control of overgrazing"),
        ("Loss of soil moisture", "Mulching with organic matter"),
        ("Erosion on steep slopes", "Terrace cultivation in the western and central Himalayas"),
        ("Runoff speed on farmland", "Ploughing along contour lines"),
        ("Soil loss between crop rows", "Leaving grass strips between cropped strips"),
    ], "medium"),

    ("ss-geo-resources.soil", "term for", [
        ("Deep channels cut by running water on slopes", "Gullies"),
        ("Land cut by gullies and unusable for cultivation", "Badland"),
        ("Gullies in the Chambal basin", "Ravines"),
        ("Steps cut across a slope for cultivation", "Terraces"),
        ("Strips of grass left between cropped strips", "Strip cropping"),
        ("Rows of trees planted to check wind", "Shelter belts"),
        ("Covering bare ground with organic matter", "Mulching"),
        ("Older alluvium with kankar nodules", "Bangar"),
        ("Newer, finer and more fertile alluvium", "Khadar"),
    ], "medium"),

    ("ss-geo-resources.planning", "associated with", [
        ("The Club of Rome's 'Limits to Growth'", "The first warning of resource depletion, in 1972"),
        ("The Brundtland Commission Report 'Our Common Future'", "Introducing sustainable development in 1987"),
        ("Agenda 21", "Declared at the 1992 Rio de Janeiro Earth Summit"),
        ("The World Summit on Sustainable Development", "Held at Johannesburg in 2002"),
        ("'There is enough for everybody's need and not for anybody's greed'", "Mahatma Gandhi"),
        ("'Small is Beautiful'", "E.F. Schumacher's Gandhian economics"),
        ("Resource planning in India", "Identification, evaluation and action-oriented planning"),
        ("Uneven distribution of resources in India", "The need for planning at regional and national level"),
    ], "medium"),

    ("ss-geo-resources.land-use", "means", [
        ("Net sown area", "Land sown at least once in an agricultural year"),
        ("Gross cropped area", "Land sown more than once in the same agricultural year"),
        ("Fallow land", "Land left uncultivated for one or less than five years"),
        ("Culturable wasteland", "Land left uncultivated for more than five years"),
        ("Land not available for cultivation", "Barren land and land put to non-agricultural use"),
        ("Permanent pastures and grazing land", "Land used for grazing livestock"),
        ("Forest area", "Land recorded as forest by the revenue department"),
        ("The National Forest Policy target", "33 per cent of area under forest cover"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 2 - Forest and Wildlife Resources
    # ══════════════════════════════════════════════════════════════════
    ("ss-geo-forest.categories", "classified as", [
        ("Normal species", "Species whose population is considered stable"),
        ("Endangered species", "Species in danger of extinction"),
        ("Vulnerable species", "Species whose population has declined to a level likely to become endangered"),
        ("Rare species", "Species with small populations that may become endangered"),
        ("Endemic species", "Species found only in particular areas, isolated by natural barriers"),
        ("Extinct species", "Species not found despite searches of known areas"),
    ], "easy"),

    ("ss-geo-forest.categories", "example of", [
        ("An extinct species in India", "The Asiatic cheetah and the pink-headed duck"),
        ("An endangered species in India", "The blackbuck, the crocodile and the Indian wild ass"),
        ("A vulnerable species in India", "The blue sheep, the Asiatic elephant and the gangetic dolphin"),
        ("A rare species in India", "The hornbill"),
        ("An endemic species in India", "The Nicob pigeon and the Andaman teal"),
        ("A normal species in India", "Cattle, sal and pine"),
    ], "easy"),

    ("ss-geo-forest.conservation", "provided for", [
        ("The Indian Wildlife (Protection) Act", "Protection of habitats and a ban on hunting, passed in 1972"),
        ("Project Tiger", "Launched in 1973 to save the tiger population"),
        ("Joint Forest Management", "Village institutions protecting degraded forest land"),
        ("Sacred groves", "Community protection of pristine forest patches"),
        ("National parks", "Strict protection of whole ecosystems"),
        ("Wildlife sanctuaries", "Protection of particular species"),
        ("Biosphere reserves", "Conservation of genetic diversity in situ"),
        ("The Forest Rights Act of 2006", "Recognition of forest-dwelling communities' rights"),
    ], "medium"),

    ("ss-geo-forest.movements", "originated in", [
        ("The Chipko movement", "The Garhwal Himalayas"),
        ("The Beej Bachao Andolan", "Tehri"),
        ("The Narmada Bachao Andolan", "The Narmada valley"),
        ("Joint Forest Management", "West Bengal, later formalised in Odisha"),
        ("The Silent Valley protest", "Kerala"),
        ("The Appiko movement", "Karnataka"),
        ("The Navdanya seed network", "Dehradun"),
    ], "easy"),

    ("ss-geo-forest.movements", "aimed at", [
        ("Chipko", "Hugging trees to stop commercial felling"),
        ("Beej Bachao Andolan", "Conserving traditional seed varieties"),
        ("Narmada Bachao Andolan", "Opposing large dams and displacement"),
        ("Joint Forest Management", "Sharing forest produce with protecting villages"),
        ("The Silent Valley protest", "Preserving an evergreen forest from a hydro project"),
        ("Navdanya", "Seed saving and farmers' rights"),
    ], "medium"),

    ("ss-geo-forest.conservation", "threatened by", [
        ("Tiger populations", "Poaching for skin and bones, and shrinking habitat"),
        ("Asiatic cheetahs in India", "Habitat loss and the decline of prey animals"),
        ("Rhino populations", "Poaching for horn"),
        ("Forest cover", "Agricultural expansion and developmental projects"),
        ("Wetlands", "Drainage for cultivation and urban growth"),
        ("Riverine species", "Dams blocking migration and changing flow"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 3 - Water Resources
    # ══════════════════════════════════════════════════════════════════
    ("ss-geo-water.scarcity", "caused by", [
        ("Water scarcity", "A large and growing population, unequal access and over-exploitation"),
        ("Groundwater depletion", "Over-irrigation in Punjab, Haryana and western Uttar Pradesh"),
        ("Water stress in cities", "Overcrowding and irregular supply"),
        ("Inter-state water disputes", "Sharing of the costs and benefits of multipurpose projects"),
        ("Declining water tables", "Pumping for intensive irrigation of water-hungry crops"),
        ("Water pollution", "Domestic and industrial waste discharged untreated"),
    ], "hard"),

    ("ss-geo-water.dams", "built on", [
        ("The Bhakra Nangal project", "The Satluj"),
        ("The Hirakud project", "The Mahanadi"),
        ("The Damodar Valley Corporation", "The Damodar"),
        ("The Sardar Sarovar project", "The Narmada"),
        ("The Tehri Dam", "The Bhagirathi"),
        ("The Rihand project", "The Rihand in Uttar Pradesh"),
        ("The Tungabhadra project", "The Tungabhadra"),
        ("The Koyna project", "The Koyna in Maharashtra"),
        ("The Nagarjuna Sagar project", "The Krishna"),
    ], "easy"),

    ("ss-geo-water.dams", "purpose of", [
        ("A multipurpose river project", "Irrigation, electricity, flood control, navigation and fish breeding"),
        ("'Temples of modern India'", "Jawaharlal Nehru's description of the dams"),
        ("Criticism of large dams", "Sedimentation, displacement and ecological damage"),
        ("An inter-state water dispute", "Allocation of river water between states"),
        ("Sardar Sarovar's benefit", "Irrigation and power across four states"),
        ("Narmada Bachao Andolan's objection", "Submergence of villages without adequate rehabilitation"),
    ], "medium"),

    ("ss-geo-water.harvesting", "practised in", [
        ("Rooftop rainwater harvesting", "Meghalaya, Tamil Nadu and Karnataka"),
        ("Bamboo drip irrigation", "Meghalaya, a two-hundred-year-old system"),
        ("Guls and kuls diversion channels", "The western Himalayas"),
        ("Johads", "Rural Rajasthan"),
        ("Khadins and tanks", "Jaisalmer and the rest of Rajasthan"),
        ("Tankas for drinking water", "Bikaner, Phalodi and Barmer"),
        ("Inundation canals", "The flood plains of Bengal"),
        ("Check dams", "Rajasthan and Gujarat"),
        ("Percolation tanks", "Maharashtra"),
        ("Rooftop collection mandated by law", "Tamil Nadu, the first state to make it compulsory"),
    ], "easy"),

    ("ss-geo-water.harvesting", "term for", [
        ("The purest natural water in the desert", "Palar pani"),
        ("An underground tank storing drinking water", "Tankas"),
        ("An earthen check dam in a gully", "Johad"),
        ("A diversion channel in the hills", "Gul or kul"),
        ("Tapping groundwater by gravity through bamboo pipes", "Bamboo drip irrigation"),
        ("A field bunded to retain moisture in arid areas", "Khadin"),
        ("Storing flood water on fields", "Inundation canal"),
    ], "medium"),

    ("ss-geo-water.scarcity", "solved by", [
        ("Seasonal urban shortage", "Rainwater harvesting on rooftops"),
        ("Rural drinking-water shortage", "Recharge of wells and construction of tankas"),
        ("Groundwater over-draft", "Regulating extraction and shifting to less water-hungry crops"),
        ("River pollution", "Treating effluent before discharge"),
        ("Drought-prone farmland", "Khadins and contour bunds to retain soil moisture"),
        ("Uneven monsoon distribution", "Storage and inter-basin transfer"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 4 - Agriculture
    # ══════════════════════════════════════════════════════════════════
    ("ss-geo-agriculture.cropping", "sown in", [
        ("Rabi crops", "Winter, from October to December, harvested in summer"),
        ("Kharif crops", "The onset of the monsoon, harvested in September and October"),
        ("Zaid crops", "The short summer season between rabi and kharif"),
    ], "easy"),

    ("ss-geo-agriculture.cropping", "example of", [
        ("Rabi crops", "Wheat, barley, peas, gram and mustard"),
        ("Kharif crops", "Paddy, maize, jowar, bajra, tur, moong, urad, cotton and jute"),
        ("Zaid crops", "Watermelon, muskmelon, cucumber, vegetables and fodder crops"),
        ("A plantation crop", "Tea, coffee, rubber and sugarcane"),
        ("A fibre crop", "Cotton and jute"),
        ("An oilseed crop", "Groundnut, mustard, coconut and soyabean"),
        ("A food grain crop", "Rice, wheat, millets and pulses"),
    ], "easy"),

    ("ss-geo-agriculture.crops", "requires", [
        ("Rice", "Temperature above 25 degrees Celsius, high humidity and rainfall above 100 cm"),
        ("Wheat", "A cool growing season, bright sunshine at ripening and 50 to 75 cm of rainfall"),
        ("Millets such as jowar, bajra and ragi", "Low rainfall and poor soils"),
        ("Sugarcane", "A hot and humid climate with 75 to 100 cm of rainfall"),
        ("Tea", "A warm, moist and frost-free climate with well-drained loamy soil"),
        ("Cotton", "Black soil, high temperature, light rainfall and 210 frost-free days"),
        ("Jute", "Well-drained fertile soil in flood plains and high temperature"),
        ("Rubber", "A moist and humid climate with rainfall above 200 cm"),
        ("Coffee", "Well-drained loamy soil on hill slopes"),
        ("Groundnut", "Sandy soil and low rainfall"),
        ("Maize", "Moderate temperature, moderate rainfall and alluvial soil"),
        ("Bajra", "Shallow and sandy soil in Rajasthan"),
    ], "medium"),

    ("ss-geo-agriculture.crops", "produced mainly in", [
        ("Rice", "West Bengal, Uttar Pradesh and Punjab"),
        ("Wheat", "Uttar Pradesh, Punjab and Haryana"),
        ("Jute", "West Bengal, Bihar and Assam"),
        ("Tea", "Assam, Darjeeling and the Nilgiris"),
        ("Cotton", "Maharashtra and Gujarat"),
        ("Sugarcane", "Uttar Pradesh and Maharashtra"),
        ("Rubber", "Kerala"),
        ("Coffee", "Karnataka"),
        ("Millets", "Rajasthan, Karnataka and Maharashtra"),
        ("Groundnut", "Gujarat"),
        ("Maize", "Karnataka, Uttar Pradesh and Bihar"),
        ("Ragi", "Karnataka, Tamil Nadu and Rajasthan"),
    ], "easy"),

    ("ss-geo-agriculture.reforms", "introduced", [
        ("The Green Revolution", "High-yielding variety seeds, fertilisers and assured irrigation"),
        ("The White Revolution, or Operation Flood", "A sharp rise in milk production"),
        ("Bhoodan and Gramdan", "Vinoba Bhave's gift of land to the landless"),
        ("Land consolidation of holdings", "Post-Independence reform to reduce fragmentation"),
        ("Cooperatives", "Collective credit, marketing and processing"),
        ("Minimum Support Price", "Assured prices for key crops"),
        ("The Kisan Credit Card", "Simplified credit access for farmers"),
        ("Crop insurance schemes", "Protection against drought, flood, cyclone, fire and disease"),
        ("Gramin banks", "Rural credit at concessional rates"),
        ("Personal Accident Insurance Scheme", "Protection for farmers"),
        ("Special weather bulletins and agricultural programmes", "Information reaching farmers on radio and television"),
    ], "medium"),

    ("ss-geo-agriculture.reforms", "faced by", [
        ("Indian agriculture today", "Falling public investment in irrigation and power"),
        ("Small and marginal farmers", "Reduced availability of capital and credit"),
        ("Farm incomes", "Withdrawal of subsidies raising the cost of production"),
        ("Grain producers", "Reduced import duties and competition from developed countries"),
        ("Rural employment", "Shift away from farming towards non-farm activities"),
        ("Water tables", "Continued over-use of groundwater"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 5 - Minerals and Energy Resources
    # ══════════════════════════════════════════════════════════════════
    ("ss-geo-minerals.minerals", "occurs as", [
        ("Minerals in igneous and metamorphic rocks", "Veins and lodes in cracks, faults and joints"),
        ("Minerals in sedimentary rocks", "Beds and layers, formed by deposition and accumulation"),
        ("Placer deposits", "Alluvial deposits in valley floors and at the base of hills"),
        ("Minerals in ocean water", "Common salt, magnesium and bromine"),
        ("Decomposed surface rocks", "Residual masses of ore left after soluble material washed away"),
        ("Bauxite", "A residual deposit formed by leaching of laterite rock"),
    ], "easy"),

    ("ss-geo-minerals.minerals", "example of", [
        ("A placer deposit mineral", "Gold, silver, tin and platinum"),
        ("A ferrous mineral", "Iron ore and manganese"),
        ("A non-ferrous mineral", "Copper, bauxite, lead and zinc"),
        ("A non-metallic mineral", "Mica, limestone and sulphur"),
        ("A conventional energy source", "Coal, petroleum, natural gas and firewood"),
        ("A non-conventional energy source", "Solar, wind, tidal, geothermal and biogas"),
        ("A rat-hole mineral deposit", "Coal in the north-eastern states, mined through narrow tunnels"),
    ], "easy"),

    ("ss-geo-minerals.minerals", "used for", [
        ("Limestone", "Cement, iron and steel, and chemical industries"),
        ("Bauxite", "Aluminium, which is strong, light and resistant"),
        ("Copper", "Electrical cables, electronics and chemical industries"),
        ("Mica", "Electrical and electronic industries for its low power loss"),
        ("Manganese", "Steel making, bleaching powder, insecticides and paints"),
        ("Rock phosphate", "Fertiliser manufacture"),
        ("Sulphur", "Sulphuric acid and the chemical industry"),
        ("Thorium and uranium", "Atomic energy generation"),
    ], "easy"),

    ("ss-geo-minerals.ferrous", "found in", [
        ("Magnetite, the finest iron ore", "Tamil Nadu and Karnataka, with up to 70 per cent iron"),
        ("Hematite, the most important industrial iron ore", "A belt stretching across Odisha, Jharkhand and Chhattisgarh"),
        ("The Odisha-Jharkhand belt", "Badampahar in Odisha and Singhbhum in Jharkhand"),
        ("The Durg-Bastar-Durgapur belt", "Bailadila in Chhattisgarh"),
        ("The Bellary-Chitradurga-Chikkamagaluru-Tumakuru belt", "Kudremukh in Karnataka"),
        ("The Maharashtra-Goa belt", "Ratnagiri in Maharashtra and Goa"),
        ("Manganese ore", "Odisha, Karnataka, Madhya Pradesh, Maharashtra and Goa"),
        ("Coal", "The Damodar valley, Jharia, Raniganj and Bokaro"),
    ], "easy"),

    ("ss-geo-minerals.energy", "located in", [
        ("Neyveli lignite mines", "Tamil Nadu"),
        ("The Jharia and Raniganj coalfields", "Jharkhand and West Bengal"),
        ("The Mumbai High field", "Offshore Maharashtra"),
        ("The Digboi oilfield", "Assam"),
        ("The Ankleshwar oilfield", "Gujarat, in the Bharuch district"),
        ("The Cambay basin", "Gujarat, onshore and offshore"),
        ("Kalpakkam atomic power station", "Tamil Nadu, on the Coromandel coast"),
        ("Narora atomic power station", "Uttar Pradesh"),
        ("Tarapur atomic power station", "Maharashtra"),
        ("Rawatbhata atomic power station", "Rajasthan"),
        ("Kakrapar atomic power station", "Gujarat, on the Tapti river"),
        ("Geothermal energy projects", "Manikaran in Himachal Pradesh and the Puga Valley in Ladakh"),
        ("Wind energy farms", "Tamil Nadu, Gujarat, Rajasthan and Maharashtra"),
        ("The largest solar power plant", "Bhadla in Rajasthan"),
        ("Natural gas fields", "Krishna-Godavari basin and Tripura"),
    ], "easy"),

    ("ss-geo-minerals.energy", "produced by", [
        ("Solar energy", "Photovoltaic technology converting sunlight directly into electricity"),
        ("Wind energy", "Turbines driven by moving air"),
        ("Biogas", "Decomposition of plant and animal waste, more efficient than gobar gas"),
        ("Tidal energy", "Floodgates built across inlets to trap the tide"),
        ("Geothermal energy", "Steam from hot springs and underground reservoirs"),
        ("Nuclear energy", "Fission of uranium and thorium"),
        ("Hydroelectricity", "Falling water turning turbines in a dam"),
    ], "easy"),

    ("ss-geo-minerals.energy", "advantage of", [
        ("Non-conventional sources", "Renewable, pollution-free and locally available"),
        ("Biogas in rural areas", "Uses waste, improves soil quality and reduces fuelwood demand"),
        ("Solar power in Rajasthan", "High solar radiation and available barren land"),
        ("Wind power in Tamil Nadu", "Consistent coastal winds and existing grid access"),
        ("Nuclear power", "Very high energy output from a small fuel mass"),
        ("Small hydro projects", "Low environmental impact compared with large dams"),
    ], "medium"),

    ("ss-geo-minerals.minerals", "conserved by", [
        ("Minerals, being non-renewable", "Improved technology to use low-grade ores at low cost"),
        ("Iron ore reserves", "Recycling of scrap metal"),
        ("Fossil fuels", "A shift to non-conventional sources"),
        ("Mining areas", "Planned and sustainable use, and reclamation of mined land"),
        ("Mica and limestone", "Reducing waste during extraction and processing"),
        ("Energy generally", "Efficient use and conservation habits"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 6 - Manufacturing Industries
    # ══════════════════════════════════════════════════════════════════
    ("ss-geo-industries.importance", "contributes", [
        ("Manufacturing to India's GDP", "About 17 per cent"),
        ("Industry as a whole, with mining, electricity and gas", "About 27 per cent of GDP"),
        ("Agriculture to GDP", "The largest single share of national income"),
        ("Employment in manufacturing", "Second only to agriculture"),
        ("Foreign exchange from manufacturing", "Exports of finished goods"),
        ("Regional development from industry", "Removal of regional disparities"),
    ], "easy"),

    ("ss-geo-industries.importance", "significance of", [
        ("Agriculture and industry", "They are not exclusive of each other but move together"),
        ("Agro-industries", "Boosting agricultural productivity through demand"),
        ("Industry's role in agriculture", "Providing irrigation pumps, fertilisers and machinery"),
        ("Manufacturing's role in exports", "Expanding trade and bringing in foreign exchange"),
        ("Industrialisation's role in employment", "Diversifying income away from agriculture alone"),
        ("National Industrial Policy", "Removing constraints on growth"),
    ], "medium"),

    ("ss-geo-industries.agro-based", "located in", [
        ("The cotton textile industry", "Mumbai, Ahmedabad and the Chhota Nagpur belt"),
        ("The jute textile industry", "The Hooghly basin in West Bengal"),
        ("The sugar industry", "Uttar Pradesh, Maharashtra and Karnataka"),
        ("Tea processing", "Assam, Darjeeling and the Nilgiris"),
        ("The vegetable oil industry", "Gujarat and Rajasthan"),
        ("The silk industry", "Karnataka and Assam"),
        ("The rubber industry", "Kerala and Tamil Nadu"),
    ], "easy"),

    ("ss-geo-industries.agro-based", "explained by", [
        ("Jute mills clustering in the Hooghly basin", "Proximity to jute areas, cheap water transport and abundant water"),
        ("The sugar industry shifting south and west", "Cane there has higher sucrose content and a longer crushing season"),
        ("Cotton mills closing in cities", "Competition from synthetics and power cuts"),
        ("The handloom sector surviving", "Demand for specialised and traditional cloth"),
        ("Khadi and village industries", "Employment and low capital requirement"),
        ("Aluminium smelting near power sources", "Very high electricity requirement"),
    ], "hard"),

    ("ss-geo-industries.importance", "classified as", [
        ("An industry based on raw material from agriculture", "Agro-based industry"),
        ("An industry based on minerals", "Mineral-based industry"),
        ("An industry whose products feed other industries", "Basic or key industry"),
        ("An industry not tied to a raw material location", "Footloose industry"),
        ("An industry owned and run by the government", "Public sector industry"),
        ("An industry owned by individuals or a group", "Private sector industry"),
        ("An industry owned jointly by the state and individuals", "Joint sector industry"),
        ("An industry run by suppliers of raw material or producers", "Cooperative sector industry"),
    ], "medium"),

    ("ss-geo-industries.pollution", "caused by", [
        ("Air pollution", "Smoke from factories, brick kilns, refineries and smelting plants"),
        ("Water pollution", "Organic and inorganic industrial waste discharged into rivers"),
        ("Thermal pollution", "Hot water from plants and factories released into rivers and ponds"),
        ("Land and soil pollution", "Dumping of solid waste such as glass and chemical effluent"),
        ("Noise pollution", "Industrial machinery and construction causing hearing impairment"),
    ], "medium"),

    ("ss-geo-industries.pollution", "controlled by", [
        ("Air pollution from industry", "Particulate control, gas treatment and oil in place of coal"),
        ("Water pollution from industry", "Treating effluent in primary, secondary and tertiary stages"),
        ("Water demand of industry", "Rainwater harvesting and recycling process water"),
        ("Energy use", "More efficient equipment and better housekeeping"),
        ("Noise", "Silencers, acoustic insulation and protective gear"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 7 - Lifelines of National Economy
    # ══════════════════════════════════════════════════════════════════
    ("ss-geo-lifelines.transport", "measured by", [
        ("Road density", "The length of road per 100 square kilometres of area"),
        ("National highways", "Linking major cities, maintained by the central public works department"),
        ("State highways", "Linking a state capital to district headquarters"),
        ("District roads", "Linking a district headquarters to other places, maintained by the Zilla Parishad"),
        ("Rural roads", "Linking villages to towns, built under the Pradhan Mantri Grameen Sadak Yojana"),
        ("Border roads", "Strategic roads in border areas, built by the Border Roads Organisation"),
    ], "easy"),

    ("ss-geo-lifelines.transport", "known for", [
        ("Railways", "The principal mode of freight and passenger transport over long distances"),
        ("Pipelines", "Transport of crude oil, petroleum products and natural gas"),
        ("Waterways", "The cheapest mode, best suited to heavy and bulky goods"),
        ("Airways", "The fastest, most comfortable and prestigious mode"),
        ("Helicopter services of Pawan Hans", "Offshore operations and difficult terrain"),
        ("National Waterway 1", "The Ganga between Allahabad and Haldia, about 1620 km"),
        ("National Waterway 2", "The Brahmaputra between Sadiya and Dhubri, about 891 km"),
        ("National Waterway 3", "The West Coast Canal between Kottapuram and Kollam, about 205 km"),
        ("Ropeways and cableways", "Movement in hilly and inaccessible terrain"),
    ], "easy"),

    ("ss-geo-lifelines.transport", "located at", [
        ("Kolkata port", "A tidal riverine port on the Hooghly"),
        ("Mumbai port", "The largest port, with a spacious natural and well-sheltered harbour"),
        ("Jawaharlal Nehru port", "The largest container port, developed as a hub for Mumbai"),
        ("Vishakhapatnam port", "The deepest landlocked and best-protected port on the east coast"),
        ("Kochi port", "A natural harbour serving south-western India"),
        ("Chennai port", "The oldest artificial port on the east coast"),
        ("Kandla port in Kachchh", "The first port developed after Independence, a tidal port"),
        ("Paradip port", "Odisha, mainly exporting iron ore"),
        ("Haldia port", "A subsidiary port relieving congestion at Kolkata"),
        ("Marmagao port", "Goa, the premier iron ore exporting port"),
        ("New Mangalore port", "Karnataka, exporting Kudremukh iron ore"),
        ("Thoothukudi port", "Tamil Nadu, at the south-eastern tip of the peninsula"),
    ], "easy"),

    ("ss-geo-lifelines.pipelines", "connects", [
        ("The Hazira-Vijaipur-Jagdishpur gas pipeline", "Hazira in Gujarat to Vijaipur in Madhya Pradesh and Jagdishpur in Uttar Pradesh"),
        ("The Salaya-Mathura pipeline", "Gujarat to refineries in Punjab, via Mathura and Delhi"),
        ("The Mumbai High pipeline", "Offshore fields to the mainland"),
        ("The Assam-Kanpur pipeline", "Upper Assam oilfields to Kanpur, via Guwahati, Barauni and Allahabad"),
        ("Slurry pipelines", "Transporting solid material as a slurry"),
    ], "medium"),

    ("ss-geo-lifelines.trade", "means", [
        ("Trade", "The exchange of goods among people, states and countries"),
        ("International trade", "Trade between two or more countries"),
        ("Balance of trade", "The difference between a country's exports and imports"),
        ("A favourable balance of trade", "Exports exceeding imports"),
        ("An unfavourable balance of trade", "Imports exceeding imports"),
        ("Invisible trade", "Trade in services, of which tourism is a large part"),
        ("Tourism as a trade", "A major earner of foreign exchange and employment"),
    ], "easy"),

    ("ss-geo-lifelines.trade", "supports", [
        ("Tourism in India", "Foreign exchange earnings and millions of jobs"),
        ("Air travel in the north-east", "Difficult terrain where surface transport is limited"),
        ("Special provisions for the north-eastern states", "Concessional fares to promote connectivity"),
        ("The Indian railway network", "Movement of goods across the country"),
        ("Pipelines", "Continuous supply of oil and gas to refineries and fertiliser plants"),
        ("Coastal shipping", "Cheap movement of bulk cargo between ports"),
    ], "medium"),

    # ── Forest and industry, extended ──────────────────────────────────
    ("ss-geo-forest.categories", "term for", [
        ("A species not found even after searching the areas where it was known to exist", "Extinct species"),
        ("A species in danger of extinction, with too few individuals left to recover", "Endangered species"),
        ("A species whose population has fallen enough that it may soon become endangered", "Vulnerable species"),
        ("A species with a small population that may become endangered or vulnerable", "Rare species"),
        ("A species found only in particular isolated areas", "Endemic species"),
        ("A species whose population is not currently at risk", "Normal species"),
    ], "easy"),

    ("ss-geo-forest.movements", "known for", [
        ("The Chipko movement", "Hugging trees to stop commercial felling in the Garhwal Himalayas"),
        ("The Beej Bachao Andolan", "Campaigning to preserve traditional seed varieties"),
        ("The Navdanya movement", "Protecting native seeds and encouraging farmers to use them"),
        ("Joint forest management", "Villagers protecting degraded forest land for a share of its produce"),
        ("The tradition of sacred groves", "Communities preserving patches of forest as part of worship"),
        ("The Appiko movement", "Extending the tree-hugging method into Karnataka's forests"),
    ], "medium"),

    ("ss-geo-industries.pollution", "caused by", [
        ("Air pollution from industry", "Burning of fuel and the release of smoke and gases into the air"),
        ("Thermal pollution of water bodies", "Release of heated water from plants into rivers and ponds"),
        ("Noise pollution around industrial areas", "Machinery, generators and hammering inside industrial units"),
        ("Land degradation near industrial sites", "Dumping of solid waste and chemicals on open ground"),
    ], "medium"),

    ("ss-geo-industries.agro-based", "example of", [
        ("An agro-based industry", "A cotton textile mill working on raw cotton from farms"),
        ("A mineral-based industry", "An iron and steel plant working on iron ore and coking coal"),
        ("A cooperative sector industry", "A sugar mill owned by the cane growers who supply it"),
        ("A public sector industry", "A steel plant owned and managed by the government"),
        ("A joint sector industry", "An undertaking owned together by the state and private investors"),
        ("A private sector industry", "A unit owned and run by an individual or a company"),
    ], "easy"),
]
