"""History clusters - India and the Contemporary World II.

Five chapters: The Rise of Nationalism in Europe, Nationalism in India, The
Making of a Global World, The Age of Industrialisation, and Print Culture and
the Modern World.

Authored as dense attribute clusters (see author_dense.py for why four or more
siblings matter). Values are stated in original wording from the CBSE/NCERT
Class 10 syllabus; where a date is contested by historians the version printed in
the textbook is the one used, because that is what a student is examined on.
"""

from __future__ import annotations

CLUSTERS = [
    # ══════════════════════════════════════════════════════════════════
    # Chapter 1 - The Rise of Nationalism in Europe
    # ══════════════════════════════════════════════════════════════════
    ("ss-hist-nationalism-europe.events", "year of", [
        ("The Act of Union between England and Scotland", "1707"),
        ("The French Revolution", "1789"),
        ("Ireland's incorporation into the United Kingdom", "1801"),
        ("Napoleon's Civil Code", "1804"),
        ("The Treaty of Vienna", "1815"),
        ("The Greek War of Independence", "1821"),
        ("The Treaty of Constantinople recognising Greece", "1832"),
        ("The Zollverein customs union", "1834"),
        ("Philipp Veit's painting of Germania", "1848"),
        ("The proclamation of a united Italy", "1861"),
        ("The proclamation of the German Empire", "1871"),
    ], "easy"),

    ("ss-hist-nationalism-europe.events", "associated with", [
        ("German unification", "Otto von Bismarck"),
        ("Italian diplomatic leadership", "Count Cavour"),
        ("The Young Italy society", "Giuseppe Mazzini"),
        ("The Red Shirts expedition to Sicily", "Giuseppe Garibaldi"),
        ("The Congress of Vienna", "Duke Metternich"),
        ("Support for the Greek cause among European poets", "Lord Byron"),
        ("The allegorical painting of Germania", "Philipp Veit"),
        ("The French allegory of the Republic", "Marianne"),
        ("Napoleon's administrative reforms", "The Civil Code of 1804"),
        ("The restoration of the Bourbon dynasty", "The Treaty of Vienna"),
    ], "easy"),

    ("ss-hist-nationalism-europe.liberalism", "meant", [
        ("The word 'liberal'", "Freedom for the individual and equality before the law"),
        ("Political liberalism in the 1840s", "Government by consent and an end to autocracy"),
        ("Economic liberalism", "Freedom of markets and the removal of state restrictions"),
        ("The Zollverein", "Abolition of tariff barriers and a common currency system"),
        ("Liberal nationalism for the middle class", "Freedom of markets and movement of goods"),
        ("Suffrage under Napoleonic rule", "A right limited to property-owning men"),
        ("The Napoleonic Code", "Abolition of privileges based on birth"),
        ("Liberalism's Latin root 'liber'", "Free"),
    ], "easy"),

    ("ss-hist-nationalism-europe.unification", "occurred through", [
        ("German unification", "Three wars over seven years led by Prussia"),
        ("Italian unification", "War, diplomacy and a popular expedition"),
        ("The capture of Rome", "Annexation of the Papal States in 1870"),
        ("British nation-state formation", "A long-drawn-out process, not a revolution"),
        ("The Act of Union of 1707", "The creation of the United Kingdom of Great Britain"),
        ("Prussia's victory over France", "Proclamation of Kaiser William I at Versailles"),
        ("The unification of Italy's south", "Garibaldi's march into the Kingdom of the Two Sicilies"),
        ("England's domination of the British Isles", "Suppression of Irish Catholic identity"),
    ], "medium"),

    ("ss-hist-nationalism-europe.romanticism", "used", [
        ("Folk songs and dances", "To carry nationalist feeling to a largely illiterate audience"),
        ("The Grimm brothers' collections", "To recover a German national identity through folk tales"),
        ("Karol Kurpinski's operas", "To express the Polish nationalist struggle"),
        ("The Polish language under Russian rule", "As a marker of national resistance"),
        ("Allegorical female figures", "To give an abstract nation a concrete form"),
        ("The oak leaves in Germania's crown", "As a symbol of German heroism"),
        ("The broken chain in Marianne's imagery", "As a symbol of freedom from oppression"),
        ("Vernacular opera and folk music", "To build a shared cultural identity"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 2 - Nationalism in India
    # ══════════════════════════════════════════════════════════════════
    ("ss-hist-nationalism-india.non-cooperation", "year of", [
        ("The Rowlatt Act", "1919, passed in March"),
        ("The Jallianwala Bagh massacre", "13 April 1919"),
        ("The formation of the Khilafat Committee in Bombay", "1919"),
        ("Gandhi's book Hind Swaraj", "1909"),
        ("The Non-Cooperation Movement approved at the Nagpur session", "1920"),
        ("The Chauri Chaura incident", "1922"),
        ("The formation of the Swaraj Party", "1923"),
        ("The arrival of the Simon Commission in India", "1928"),
    ], "easy"),

    ("ss-hist-nationalism-india.non-cooperation", "called for", [
        ("The Non-Cooperation Movement in towns", "Surrender of titles and boycott of civil services"),
        ("Boycott of foreign cloth", "A reduction of imports and the revival of Indian handloom"),
        ("The picketing of liquor shops", "As part of the boycott programme"),
        ("Students", "To leave government-controlled schools and colleges"),
        ("The Khilafat issue", "A joint Hindu-Muslim platform against the British"),
        ("Gandhi at the Nagpur session", "Full launch of Non-Cooperation in December 1920"),
        ("The withdrawal after Chauri Chaura", "An immediate end to the movement in 1922"),
        ("C.R. Das and Motilal Nehru", "Council entry to obstruct government from within"),
    ], "medium"),

    ("ss-hist-nationalism-india.civil-disobedience", "year of", [
        ("The launch of the Civil Disobedience Movement", "1930"),
        ("The signing of the Gandhi-Irwin Pact", "5 March 1931"),
        ("The Second Round Table Conference in London", "1931"),
        ("The signing of the Poona Pact", "September 1932"),
        ("The relaunch of Civil Disobedience after the pact failed", "1932"),
        ("The Quit India Movement", "1942"),
        ("Indian Independence", "1947"),
    ], "easy"),

    ("ss-hist-nationalism-india.civil-disobedience", "distinguished itself by", [
        ("Civil Disobedience, unlike Non-Cooperation", "Refusal to obey unjust laws as well as boycott"),
        ("The movement's participation", "Inclusion of women, peasants and business classes"),
        ("Industrialists' support", "Protection against foreign imports and a favourable rupee ratio"),
        ("Peasants' demand", "Reduction of revenue and abolition of begar"),
        ("Rich peasants' grievance", "The trade depression and falling prices"),
        ("Poor peasants' grievance", "The inability to pay rent to landlords"),
        ("The movement's limitation", "Ambiguity towards untouchability and the Dalit demand"),
        ("Dr B.R. Ambedkar's position", "Separate electorates for Dalits"),
    ], "hard"),

    ("ss-hist-nationalism-india.salt-march", "recorded as", [
        ("The distance covered by the Dandi March", "240 miles"),
        ("The number of volunteers who set out with Gandhi", "78"),
        ("The starting point of the march", "Sabarmati ashram"),
        ("The destination of the march", "The coastal village of Dandi"),
        ("The act that broke the law", "Boiling sea water to make salt"),
        ("The recipient of Gandhi's ultimatum letter", "Lord Irwin"),
        ("The reason salt was chosen", "It was consumed alike by the rich and the poorest"),
        ("The date Gandhi reached Dandi", "6 April 1930"),
        ("The date the march began", "12 March 1930"),
        ("The number of demands in Gandhi's letter", "Eleven"),
    ], "easy"),

    ("ss-hist-nationalism-india.participants", "led by", [
        ("The Awadh peasant movement", "Baba Ramchandra"),
        ("The Gudem Hills tribal movement in Andhra Pradesh", "Alluri Sitaram Raju"),
        ("The Swaraj Party", "Motilal Nehru and C.R. Das"),
        ("The Simon Commission boycott", "The slogan 'Go back Simon'"),
        ("The Lahore Congress session of 1929", "Jawaharlal Nehru as president"),
        ("The demand for separate electorates for Muslims", "Muhammad Ali Jinnah"),
        ("The Dalit demand for political empowerment", "Dr B.R. Ambedkar"),
        ("The Lahore resolution of 1940", "Muhammad Ali Jinnah and the Muslim League"),
    ], "easy"),

    ("ss-hist-nationalism-india.pacts", "agreed between", [
        ("The Gandhi-Irwin Pact", "Mahatma Gandhi and Lord Irwin"),
        ("The Poona Pact", "Mahatma Gandhi and Dr B.R. Ambedkar"),
        ("The Lucknow Pact of 1916", "The Congress and the Muslim League"),
        ("The Round Table Conferences", "The British government and Indian delegates"),
        ("The Communal Award", "Separate electorates granted by Ramsay MacDonald"),
        ("The Poona Pact's outcome", "Reserved seats for Depressed Classes within joint electorates"),
    ], "easy"),

    ("ss-hist-nationalism-india.pacts", "resulted in", [
        ("The Rowlatt Act", "Detention without trial"),
        ("The Jallianwala Bagh massacre", "General Dyer firing on a peaceful gathering"),
        ("The Simon Commission", "The boycott slogan 'Go back Simon'"),
        ("The Chauri Chaura incident", "The withdrawal of the Non-Cooperation Movement"),
        ("The Poona Pact", "Reservation of seats for the Depressed Classes"),
        ("The Gandhi-Irwin Pact", "Gandhi's attendance at the London conference"),
        ("The Vernacular Press Act", "Curbs on Indian-language newspapers"),
        ("The Quit India Movement", "Mass arrests and the call to 'Do or Die'"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 3 - The Making of a Global World
    # ══════════════════════════════════════════════════════════════════
    ("ss-hist-global-world.great-depression", "year of", [
        ("Columbus's voyage to the Americas", "1492"),
        ("Vasco da Gama's arrival in India", "1498"),
        ("The Irish Potato Famine", "1845"),
        ("Abolition of the Corn Laws in Britain", "1846"),
        ("The Wall Street Crash", "October 1929"),
        ("The beginning of the Great Depression", "1929"),
        ("The Bretton Woods Conference", "1944"),
        ("Establishment of the IMF and the World Bank", "1945"),
        ("Signing of GATT", "1947"),
        ("The Rinderpest cattle plague in Africa", "1890s"),
    ], "easy"),

    ("ss-hist-global-world.bretton-woods", "purpose of", [
        ("The International Monetary Fund", "Dealing with external surpluses and deficits of members"),
        ("The World Bank", "Financing post-war reconstruction and development"),
        ("GATT", "Reducing tariffs and other barriers to trade"),
        ("The Bretton Woods exchange-rate system", "Fixed rates anchored to the US dollar"),
        ("The anchor of the fixed-rate system", "The US dollar, itself convertible into gold"),
        ("The two Bretton Woods institutions", "The IMF and the World Bank"),
        ("Post-war employment policy", "Full employment in the industrial West"),
        ("The system's collapse", "US withdrawal from fixed convertibility in 1971"),
    ], "medium"),

    ("ss-hist-global-world.colonialism", "consequence of", [
        ("Abolition of the Corn Laws", "Cheaper grain imports and abandoned British farmland"),
        ("Cheap imported grain", "Migration from the English countryside to cities and abroad"),
        ("Refrigerated ships", "Cheaper meat reaching European tables"),
        ("Rinderpest in Africa", "Loss of livelihoods and forced entry into wage labour"),
        ("Indentured migration from India", "Labour for plantations in the Caribbean, Mauritius and Fiji"),
        ("Colonial conquest of Africa", "European control of land and resources"),
        ("The shift of trade to Bombay", "Decline of older ports such as Surat and Hooghly"),
        ("European investment abroad", "Growing interdependence of national economies"),
    ], "hard"),

    ("ss-hist-global-world.silk-route", "connected", [
        ("The Silk Route", "China with Europe and North Africa"),
        ("Indian Ocean trade", "India with Arabia and the east coast of Africa"),
        ("Pre-modern Buddhist missionaries", "China, Korea and Japan"),
        ("Marco Polo's travels", "Europe with the court of China"),
        ("Chinese silk exports", "Rome and West Asia through Central Asia"),
        ("The Indian subcontinent's trade", "Spices, textiles and precious metals"),
        ("Arab merchants' networks", "The Red Sea, the Persian Gulf and the Indian coast"),
        ("European demand for Asian goods", "The search for a sea route to India"),
    ], "easy"),

    ("ss-hist-global-world.great-depression", "caused", [
        ("Agricultural overproduction", "A collapse of farm prices worldwide"),
        ("The withdrawal of US overseas loans", "Bank failures across Europe"),
        ("The US doubling of import duties", "A severe contraction of world trade"),
        ("Falling prices and rising debt", "Ruined peasant households in India"),
        ("Unemployment in the industrial world", "Mass migration and protest movements"),
        ("The Depression in India", "A fall in export and import volumes by half"),
        ("Jute growers in Bengal", "Collapse of gunny bag exports"),
        ("The return of Indian overseas migrants", "Reduced remittance income"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 4 - The Age of Industrialisation
    # ══════════════════════════════════════════════════════════════════
    ("ss-hist-industrialisation.before-factories", "invented by", [
        ("The spinning jenny", "James Hargreaves"),
        ("The improved steam engine, patented in 1781", "James Watt"),
        ("The flying shuttle loom", "John Kay"),
        ("The cotton mill as an integrated system", "Richard Arkwright"),
        ("The first practical locomotive engine", "Richard Trevithick"),
    ], "easy"),

    ("ss-hist-industrialisation.before-factories", "described", [
        ("Proto-industrialisation", "Large-scale production for the market outside factories"),
        ("The putting-out system", "Merchants supplying money to peasants and artisans"),
        ("Guilds", "Associations that controlled production and prices"),
        ("Cottage industry", "Household production of textiles before mechanisation"),
        ("The merchant's role", "Organising production without owning a factory"),
        ("Rural labour in winter", "Seasonal work for proto-industrial merchants"),
    ], "easy"),

    ("ss-hist-industrialisation.factories", "year of", [
        ("Watt's steam engine patent", "1781"),
        ("The first cotton mill in Bombay", "1854"),
        ("The first jute mill in Bengal", "1855"),
        ("Tata's Central India Spinning and Weaving Company at Nagpur", "1877"),
        ("The Swadeshi movement's boost to Indian industry", "1905"),
        ("The boom in Indian cotton exports during the First World War", "1914"),
    ], "easy"),

    ("ss-hist-industrialisation.factories", "role of", [
        ("The gomastha", "A Company agent who supervised weavers and supplied advances"),
        ("The jobber", "A trusted old worker who recruited from his own village"),
        ("The fly-shuttle loom", "Producing wider cloth without extra hands"),
        ("Steam power in the mill", "Driving spinning and weaving machinery"),
        ("The typical early factory worker", "A seasonal migrant returning to the village"),
        ("Handloom production", "Surviving alongside mills for coarse and specialised cloth"),
        ("Manchester goods", "Competing with Indian textiles in world markets"),
        ("Indian mills' output", "Coarse cotton cloth, much of it for domestic use"),
    ], "medium"),

    ("ss-hist-industrialisation.india-textiles", "declined because", [
        ("The port of Surat", "European companies secured concessions from local courts"),
        ("The port of Hooghly", "Trade shifted to Bengal under Company control"),
        ("Raw cotton supply to weavers", "Exports to Britain raised prices at home"),
        ("Weavers in Bengal", "They revolted against the Company's advances"),
        ("Indian handloom weavers", "Cheap Manchester goods flooded the market"),
        ("The Indian silk and muslin trade", "Foreign competition and Company monopoly"),
        ("Weavers' bargaining power", "The gomastha system fixed prices unilaterally"),
        ("Cottage textile production", "Mill-made yarn undercut hand-spun yarn"),
    ], "hard"),

    ("ss-hist-industrialisation.india-textiles", "associated with", [
        ("The China trade and Carr Tagore and Company", "Dwarkanath Tagore"),
        ("The Central India Spinning, Weaving and Manufacturing Company", "Jamsetji Nusserwanji Tata"),
        ("Bombay's Parsi and Marwari merchants", "Setting up the first Indian mills"),
        ("Bengal's jute industry", "Scottish and British capital"),
        ("The export of Indian opium to China", "Financing Company trade"),
        ("Elgin and Bharat mills", "Indian-owned cotton manufacturing"),
        ("Kanpur, Bombay and Madras", "Concentration of Indian cotton mills"),
        ("The First World War", "Reduced Manchester imports into India"),
    ], "easy"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 5 - Print Culture and the Modern World
    # ══════════════════════════════════════════════════════════════════
    ("ss-hist-print-culture.gutenberg", "year of", [
        ("The Diamond Sutra, the earliest printed book", "868"),
        ("Gutenberg's development of the printing press", "1430s"),
        ("Gutenberg's printing of the Bible", "1455"),
        ("Martin Luther's Ninety-Five Theses", "1517"),
        ("Luther's German translation of the New Testament", "1522"),
        ("The complete Luther Bible in German", "1534"),
        ("The Index of Prohibited Books", "1558"),
        ("Caxton's introduction of printing to England", "1476"),
    ], "easy"),

    ("ss-hist-print-culture.gutenberg", "linked to", [
        ("Movable metal type in Europe", "Johann Gutenberg"),
        ("The first major printed book in Europe", "The 42-line Bible"),
        ("Financing of Gutenberg's press", "Johann Fust"),
        ("The challenge to the Catholic Church's authority", "Martin Luther's printed theses"),
        ("Humanist criticism of print", "Erasmus, who feared a flood of foolish books"),
        ("Church control over printed matter", "The Index of Prohibited Books"),
        ("Woodblock printing in East Asia", "China, Japan and Korea"),
        ("Hand printing in Japan", "Buddhist temples and illustrated books"),
    ], "easy"),

    ("ss-hist-print-culture.print-india", "year of", [
        ("The first printing press in India, at Goa", "1556"),
        ("The first Tamil book printed by Catholic priests", "1579"),
        ("The Bengal Gazette started by Hicky", "1780"),
        ("Publication of Rashasundari Devi's Amar Jiban", "1876"),
        ("The Vernacular Press Act", "1878"),
        ("Publication of Tarabai Shinde's Stri Purush Tulana", "1882"),
        ("The Bombay Samachar, Asia's oldest newspaper", "1822"),
        ("Raja Rammohun Roy's Sambad Kaumudi", "1821"),
    ], "easy"),

    ("ss-hist-print-culture.print-india", "associated with", [
        ("Sambad Kaumudi", "Raja Rammohun Roy"),
        ("Kesari and Mahratta", "Bal Gangadhar Tilak"),
        ("The Bengal Gazette", "James Augustus Hicky"),
        ("Amar Jiban, the first known Bengali autobiography", "Rashasundari Devi"),
        ("Stri Purush Tulana", "Tarabai Shinde"),
        ("Chhote Aur Bade Ka Sawal", "Kashibaba, a Kanpur millworker"),
        ("Battala woodcuts", "Cheap popular prints of nineteenth-century Calcutta"),
        ("Nawal Kishore Press at Lucknow", "Lithographic printing in Urdu"),
        ("The Vernacular Press Act", "Lord Lytton's government"),
        ("Sudarshan Chakr", "Kashibaba's later collection of poems"),
    ], "easy"),

    ("ss-hist-print-culture.manuscripts", "written in", [
        ("Manuscripts in pre-colonial India", "Sanskrit, Arabic and Persian"),
        ("Mughal court records and literature", "Persian"),
        ("Regional devotional texts", "Vernacular languages"),
        ("Palm-leaf manuscripts", "A fragile material that broke easily"),
        ("Handwritten copies in India", "Expensive, delicate and hard to read"),
        ("Bengali prose before print", "Mostly religious and administrative"),
    ], "easy"),

    ("ss-hist-print-culture.manuscripts", "limitation of", [
        ("Manuscript copying", "Slow, costly and prone to errors"),
        ("Palm-leaf manuscripts", "Fragile and easily damaged by handling"),
        ("Handwritten texts", "Too expensive for ordinary readers"),
        ("Scribal production", "Could not meet growing demand for books"),
        ("Manuscript literacy", "Confined largely to elites and priests"),
        ("Copying in India", "Irregular handwriting that was hard to read"),
    ], "medium"),

    ("ss-hist-print-culture.gutenberg", "effect of", [
        ("The printing press on book cost", "Books became cheaper and faster to produce"),
        ("Print on reading audiences", "A shift from hearing texts to reading them"),
        ("Print on the Reformation", "Luther's theses spread far beyond Wittenberg"),
        ("Print on religious authority", "Readers could compare interpretations themselves"),
        ("The printing press on knowledge", "Multiple copies preserved texts reliably"),
        ("Cheap print on popular culture", "Ballads, almanacs and folk tales circulated widely"),
        ("Print on dissent", "Critics of the Church could reach an audience"),
        ("Print on the fear of rulers", "Control of print became control of opinion"),
    ], "hard"),

    # ── Industrialisation and the global world, extended ───────────────
    # The Age of Industrialisation and The Making of a Global World were both
    # running below 160 questions. These clusters stay on the causal chains the
    # chapters actually trace, which is what source-based questions ask about.
    ("ss-hist-industrialisation.before-factories", "resulted in", [
        ("The expansion of world trade from the seventeenth century", "Merchants in towns turning outward to the countryside for production"),
        ("Powerful craft guilds holding monopolies in European towns", "Newcomers being unable to set up business inside the town"),
        ("Guild control over production, prices and membership", "Merchants moving their orders to peasants and artisans in villages"),
        ("A single merchant employing several hundred people across villages", "Production staying within family units rather than factories"),
        ("Cloth merchants supplying world markets from European ports", "The putting-out system spreading out from the towns"),
    ], "medium"),

    ("ss-hist-industrialisation.factories", "led to", [
        ("Cotton becoming the leading sector of early industrial growth", "Demand for raw cotton rising and its price climbing steeply"),
        ("Factory production spreading across many industries", "Workers being drawn from the countryside into industrial towns"),
        ("Demand for labour remaining seasonal in several industries", "Workers going back to their villages during the slack months"),
        ("News of work travelling through villages and districts", "Large numbers arriving in the cities looking for employment"),
        ("New machines such as the spinning jenny coming into use", "Hand spinners and handloom weavers losing their livelihood"),
    ], "medium"),

    ("ss-hist-industrialisation.india-textiles", "resulted in", [
        ("Machine-made British goods entering Indian markets", "Indian textile exports declining and weavers losing buyers"),
        ("Weavers being unable to buy raw cotton at a fair price", "Many abandoning weaving and turning to agricultural labour"),
        ("European companies gaining control of Indian sea trade", "Local bankers and traders losing their financing role"),
        ("The American Civil War cutting off cotton supplies to Britain", "Raw cotton exports from India rising and prices soaring"),
        ("Cotton mills beginning production inside India", "Handloom weaving losing further ground to mill-made cloth"),
    ], "hard"),

    ("ss-hist-global-world.colonialism", "resulted in", [
        ("European conquest of large parts of Africa and Asia", "Local economies being reshaped to serve the colonial power"),
        ("The world market expanding through the nineteenth century", "Food being shipped from distant farms to European tables"),
        ("Rinderpest reaching Africa in the late 1880s", "Cattle dying on an enormous scale and pastoral livelihoods collapsing"),
        ("Indentured labour being recruited from India", "Workers bound by contract to serve one employer in a distant colony"),
        ("Colonial rule over plantation economies", "Cash crops displacing food cultivation across wide regions"),
    ], "hard"),

    ("ss-hist-global-world.bretton-woods", "purpose of", [
        ("The United States dollar under the Bretton Woods system", "Being fixed to gold at an official price and anchoring other currencies"),
        ("The International Bank for Reconstruction and Development", "Financing post-war reconstruction and later development"),
        ("The Bretton Woods system of fixed exchange rates", "Keeping currencies stable and trade predictable after the war"),
        ("Achieving full employment in the industrial West", "Being an explicit goal of the post-war settlement"),
        ("Consultation between the major industrial economies", "Sustaining growth and stability through the post-war decades"),
    ], "hard"),
]
