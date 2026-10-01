"""Economics clusters - Understanding Economic Development.

Five chapters: Development, Sectors of the Indian Economy, Money and Credit,
Globalisation and the Indian Economy, and Consumer Rights.

Income classification thresholds are quoted as the textbook does, with the year
stated, because those figures are revised periodically and a bare number would
be ambiguous by the time a student reads it.
"""

from __future__ import annotations

CLUSTERS = [
    # ══════════════════════════════════════════════════════════════════
    # Chapter 1 - Development
    # ══════════════════════════════════════════════════════════════════
    ("ss-eco-development.goals", "depends on", [
        ("A person's developmental goals", "Their life situation and what they consider important"),
        ("What may be development for one person", "Something destructive for another"),
        ("Conflicting developmental goals", "The need for a collective decision about the future"),
        ("Different persons' goals", "Being different, and sometimes in conflict"),
        ("A common goal for all", "One that a large number of people agree is important"),
        ("Development of a country", "The mix of goals its people collectively pursue"),
    ], "medium"),

    ("ss-eco-development.goals", "example of", [
        ("A developmental goal other than income", "Equal treatment, freedom, security and respect"),
        ("A goal of a landless rural labourer", "More days of work and better wages"),
        ("A goal of a prosperous farmer", "Cheap labour and higher prices for produce"),
        ("A goal of a girl child", "Freedom equal to her brother's, and time for study"),
        ("A goal of an industrialist", "Cheaper electricity and higher dams"),
        ("A goal of an Adivasi displaced by a dam", "Restoration of forest rights and livelihood"),
    ], "medium"),

    ("ss-eco-development.income", "measured by", [
        ("Total income of a country", "The sum of incomes of all its residents"),
        ("Per capita income", "National income divided by total population"),
        ("Average income", "Another name for per capita income"),
        ("The World Bank's classification", "Per capita income of countries, published in the World Development Report"),
        ("A limitation of average income", "It hides how unequal the distribution is"),
        ("Body Mass Index", "Weight in kilograms divided by the square of height in metres"),
    ], "easy"),

    ("ss-eco-development.income", "classified as", [
        ("A rich or high-income country in 2019", "Per capita income of US$ 12,056 per annum and above"),
        ("A low-income country in 2019", "Per capita income of US$ 1,036 per annum or less"),
        ("A low-middle income country in 2019", "Per capita income between US$ 1,036 and US$ 4,045"),
        ("India's income group in 2019", "Low-middle income"),
    ], "medium"),

    ("ss-eco-development.indicators", "measured by", [
        ("Infant Mortality Rate", "Children who die before the age of one year per 1,000 live births"),
        ("Literacy Rate", "The proportion of the population aged seven and above who can read and write"),
        ("Net Attendance Ratio", "Children aged six to ten attending school as a percentage of all children in that age group"),
        ("Human Development Index", "Health, education and income taken together"),
        ("Health status of a population", "Life expectancy, infant mortality and nutrition levels"),
        ("Educational attainment", "Literacy rate, gross enrolment and years of schooling"),
    ], "easy"),

    ("ss-eco-development.indicators", "published by", [
        ("The Human Development Index", "The United Nations Development Programme"),
        ("The World Development Report", "The World Bank, published annually"),
        ("Per capita income comparisons", "The World Bank"),
        ("Life expectancy data", "Health statistics compiled internationally"),
    ], "easy"),

    ("ss-eco-development.indicators", "explained by", [
        ("Kerala's low Infant Mortality Rate", "Adequate provision of basic health and educational services"),
        ("Better human development despite lower income", "Public provision of health, education and food"),
        ("Underweight children in India", "Inadequate nutrition and unequal access to services"),
        ("The importance of public facilities", "Individual income cannot buy everything a person needs"),
    ], "hard"),

    ("ss-eco-development.goals", "sustained by", [
        ("Over-irrigation in Punjab, Haryana and western Uttar Pradesh", "A falling groundwater table"),
        ("Districts in India with water levels below four metres", "About 300, as reported in groundwater surveys"),
        ("Crude oil reserves at present extraction rates", "Estimated to last about 50 more years"),
        ("Unsustainable use of resources", "Development becoming a threat to the future"),
        ("Sustainable development", "Meeting present needs without compromising future generations"),
        ("Groundwater depletion", "Over-use for water-intensive crops"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 2 - Sectors of the Indian Economy
    # ══════════════════════════════════════════════════════════════════
    ("ss-eco-sectors.primary", "includes", [
        ("The primary sector", "Activities that use natural resources directly"),
        ("Agriculture", "The largest activity within the primary sector"),
        ("Dairy and fishing", "Primary sector activities dependent on natural produce"),
        ("Forestry and mining", "Extraction of natural resources"),
        ("The primary sector's other name", "The agriculture and related sector"),
    ], "easy"),

    ("ss-eco-sectors.secondary", "includes", [
        ("The secondary sector", "Activities that transform natural products into other forms"),
        ("Manufacturing", "The main activity of the secondary sector"),
        ("Construction", "Building activity counted in the secondary sector"),
        ("The secondary sector's other name", "The industrial sector"),
        ("A sugar mill", "A secondary sector unit converting sugarcane into sugar"),
    ], "easy"),

    ("ss-eco-sectors.tertiary", "includes", [
        ("The tertiary sector", "Activities that support the primary and secondary sectors"),
        ("The tertiary sector's other name", "The service sector"),
        ("Transport and communication", "Tertiary services that move goods and information"),
        ("Banking, trade and insurance", "Tertiary services that handle money and exchange"),
        ("Education, health and information technology", "Tertiary services that develop people and process information"),
        ("A soft drink bottling unit", "Sometimes counted as manufacturing, sometimes as service"),
    ], "easy"),

    ("ss-eco-sectors.tertiary", "grew because", [
        ("Rising incomes", "Greater demand for services beyond basic needs"),
        ("Development of agriculture and industry", "A need for transport, trade and finance"),
        ("New services based on technology", "Information technology, call centres and software"),
        ("Globalisation", "Export of services such as IT and business process outsourcing"),
        ("Basic services", "Public demand for health, education and banking"),
    ], "medium"),

    ("ss-eco-sectors.tertiary", "measured by", [
        ("Gross Domestic Product", "The total value of all final goods and services produced in a year"),
        ("A final good", "One sold to the ultimate consumer, with intermediate goods counted once"),
        ("Value added", "The difference between the value of output and the value of inputs used"),
        ("An intermediate good", "One used up in producing another good"),
        ("The sectoral share of GDP", "Each sector's contribution to the total"),
    ], "medium"),

    ("ss-eco-sectors.tertiary", "shifted in", [
        ("Developed countries", "From the primary to the secondary and then to the tertiary sector"),
        ("India over the last few decades", "The tertiary sector becoming the largest producer"),
        ("India's employment pattern", "Most workers still in the primary sector despite its smaller share of output"),
        ("Production versus employment", "They do not shift together at the same pace"),
    ], "hard"),

    ("ss-eco-sectors.organised", "means", [
        ("The organised sector", "Enterprises registered with the government and following its rules"),
        ("The unorganised sector", "Small scattered units largely outside government control"),
        ("A worker in the organised sector", "Having security of employment and paid leave"),
        ("A worker in the unorganised sector", "Having no job security and no paid leave or holidays"),
        ("The public sector", "Enterprises owned and run by the government"),
        ("The private sector", "Enterprises owned and run by individuals or companies"),
    ], "easy"),

    ("ss-eco-sectors.organised", "protected by", [
        ("The Factories Act", "Rules on working conditions in factories"),
        ("The Minimum Wages Act", "A floor wage for workers"),
        ("The Payment of Gratuity Act", "A lump sum on retirement or leaving service"),
        ("The Shops and Establishments Act", "Rules for shops and commercial establishments"),
        ("Provident fund and health benefits", "Statutory benefits in the organised sector"),
        ("A fixed working day and overtime pay", "Norms in the organised sector"),
    ], "medium"),

    ("ss-eco-sectors.organised", "suffers from", [
        ("Disguised unemployment", "More people working than are actually needed, mainly on family farms"),
        ("Underemployment", "People working less than they are able and willing to"),
        ("Casual labour in cities", "Irregular work in construction, cart-pushing and petty vending"),
        ("Small-scale and casual workers", "Low wages and no security"),
        ("Seasonal work in agriculture", "Employment for only part of the year"),
    ], "hard"),

    ("ss-eco-sectors.organised", "addressed by", [
        ("The Mahatma Gandhi National Rural Employment Guarantee Act", "Passed in 2005, implemented in 2006"),
        ("The right to work under MGNREGA", "100 days of guaranteed wage employment in a financial year"),
        ("Eligibility under MGNREGA", "Every rural household whose adult members volunteer for unskilled manual work"),
        ("Reservation for women under MGNREGA", "One-third of the work"),
        ("If work is not provided within 15 days", "An unemployment allowance becomes payable"),
        ("Initial implementation of MGNREGA", "200 districts"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 3 - Money and Credit
    # ══════════════════════════════════════════════════════════════════
    ("ss-eco-money.money", "solves", [
        ("The double coincidence of wants", "Money acting as a medium of exchange"),
        ("Difficulty in barter", "The need for both parties to want what the other offers"),
        ("Divisibility of goods", "Money being divisible into any amount"),
        ("Storage of value", "Money being easy to carry and hold"),
        ("Exchange between strangers", "Money being accepted by everyone"),
    ], "easy"),

    ("ss-eco-money.money", "consists of", [
        ("Currency in India", "Paper notes and coins issued by the Reserve Bank of India"),
        ("Modern forms of money", "Currency and deposits with banks"),
        ("Demand deposits", "Deposits that can be withdrawn on demand and used by cheque"),
        ("A cheque", "A paper instructing a bank to pay a specific amount from the drawer's account"),
        ("Legal tender", "Currency that no one in India can refuse in settlement of a payment"),
        ("Rupee notes", "Issued by the Reserve Bank on behalf of the central government"),
    ], "easy"),

    ("ss-eco-money.banks", "performs", [
        ("Accepting deposits", "Paying depositors interest on them"),
        ("Lending money", "Charging a higher interest rate than it pays on deposits"),
        ("Keeping a small proportion as cash", "To pay depositors who come to withdraw"),
        ("Earning from the spread", "The difference between what is charged from borrowers and paid to depositors"),
        ("Mediating between depositors and borrowers", "The key function of banks"),
        ("Supervision by the Reserve Bank of India", "Ensuring banks maintain cash balance and lend to small borrowers"),
    ], "medium"),

    ("ss-eco-money.banks", "supervised by", [
        ("The Reserve Bank of India", "Monitoring banks' cash balance and lending patterns"),
        ("RBI's requirement on banks", "Lending to small borrowers, not just to big business"),
        ("RBI's requirement on reporting", "Banks submitting information on how much they lend and to whom"),
        ("Currency issue in India", "The Reserve Bank of India on behalf of the central government"),
    ], "medium"),

    ("ss-eco-money.credit", "divided into", [
        ("Formal sector credit", "Loans from banks and cooperatives, supervised by the RBI"),
        ("Informal sector credit", "Loans from moneylenders, traders, employers, relatives and friends"),
        ("Informal credit's main problem", "Very high interest rates and no supervision"),
        ("A debt trap", "Credit increasing earnings in one period but forcing distress in the next"),
        ("Terms of credit", "Interest rate, collateral, documentation and mode of repayment"),
        ("Collateral", "An asset the borrower owns and offers as security until the loan is repaid"),
    ], "medium"),

    ("ss-eco-money.credit", "needed by", [
        ("Small farmers and small producers", "Working capital and inputs before the harvest"),
        ("Festival and marriage expenses in rural India", "Often met through informal credit at high rates"),
        ("Urban self-employed households", "Credit for equipment and stock"),
        ("The poor lacking collateral", "Informal moneylenders, because banks require documents"),
        ("Expansion of formal credit", "Reducing dependence on informal sources"),
    ], "hard"),

    ("ss-eco-money.shg", "organised as", [
        ("Membership of a Self-Help Group", "Typically 15 to 20 members, usually women, from one neighbourhood"),
        ("Regular savings per member", "Rs 25 to Rs 100 or more, depending on ability"),
        ("Internal lending", "Members borrowing from the group's own savings"),
        ("Interest charged by the group", "Lower than what a moneylender charges"),
        ("Eligibility for a bank loan", "After one or two years of regular savings"),
        ("Collateral for the group's bank loan", "None required from individual members"),
        ("Repayment responsibility", "The group, not the individual member"),
        ("A social purpose of SHGs", "A forum for discussing health, nutrition and domestic violence"),
        ("Women's empowerment through SHGs", "Financial independence and a voice in the household"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 4 - Globalisation and the Indian Economy
    # ══════════════════════════════════════════════════════════════════
    ("ss-eco-globalisation.production", "means", [
        ("A Multinational Corporation", "A company that owns or controls production in more than one country"),
        ("Where an MNC sets up production", "Close to markets, with cheap labour and available raw materials"),
        ("Interlinking of production across countries", "Components made in different countries and assembled in one"),
        ("Ford Motors in India", "A plant near Chennai set up in 1995"),
        ("MNCs' role in globalisation", "The most powerful force spreading production across borders"),
        ("Joint ventures with local companies", "One way MNCs enter a new market"),
    ], "medium"),

    ("ss-eco-globalisation.production", "benefits from", [
        ("Cheap and skilled labour", "Lower production cost in the host country"),
        ("Proximity to markets", "Lower transport cost and faster delivery"),
        ("Favourable government policies", "Tax incentives and flexible labour rules"),
        ("Available raw materials", "Reduced input cost"),
        ("Good infrastructure", "Reliable power, transport and communication"),
        ("Acquisition of a local company", "Immediate access to an existing market"),
    ], "hard"),

    ("ss-eco-globalisation.trade", "results in", [
        ("Foreign trade", "Integration of markets of different countries"),
        ("Competition from imports", "Improved quality and lower prices for consumers"),
        ("More choice for consumers", "A wider range of goods available"),
        ("Producers competing across borders", "Even prices of similar goods tending to become equal"),
        ("Movement of goods, services, technology and capital", "The main channels of globalisation"),
        ("Movement of people", "Migration seeking better income, though far more restricted"),
    ], "medium"),

    ("ss-eco-globalisation.factors", "enabled by", [
        ("Improvement in technology", "Especially in transport and communication"),
        ("Containerisation", "Faster and cheaper movement of goods by sea"),
        ("Information technology", "Instant communication and outsourcing of services"),
        ("Liberalisation", "Removal of barriers and restrictions set by the government"),
        ("India's liberalisation", "Started in 1991"),
        ("Foreign trade barriers removed", "Quantitative restrictions and high import duties"),
    ], "easy"),

    ("ss-eco-globalisation.wto", "role of", [
        ("The World Trade Organisation", "Setting rules for international trade"),
        ("The WTO's founding", "Started in 1995"),
        ("The WTO's membership", "More than 160 countries"),
        ("The WTO's aim", "Liberalising foreign trade and investment"),
        ("Criticism of the WTO", "Rules often favour developed countries and force unfair conditions"),
        ("Developing countries' response", "Demanding fairer rules and resisting pressure"),
    ], "medium"),

    ("ss-eco-globalisation.trade", "affected", [
        ("Consumers in India", "More choice, better quality and lower prices"),
        ("Top Indian companies", "Benefited from investment, newer technology and export markets"),
        ("Small producers", "Hit by competition from cheap imports"),
        ("Workers", "More flexible employment with less job security"),
        ("India's service exports", "IT, software and business process services grew sharply"),
        ("Rural and informal workers", "Largely left out of globalisation's benefits"),
    ], "hard"),

    ("ss-eco-globalisation.factors", "made fairer by", [
        ("Government support to small producers", "Helping them improve production until they can compete"),
        ("Enforcing labour laws properly", "Protecting workers' rights"),
        ("Negotiating at the WTO", "Demanding fairer rules for developing countries"),
        ("Alliances among developing countries", "Joint resistance to unfair trade pressure"),
        ("Protecting certain industries temporarily", "Allowing domestic firms to grow"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 5 - Consumer Rights
    # ══════════════════════════════════════════════════════════════════
    ("ss-eco-consumer.rights", "guarantees", [
        ("The right to be informed", "Full information about the goods and services purchased"),
        ("The right to choose", "Selection from a range of goods and services at competitive prices"),
        ("The right to seek redressal", "Compensation against unfair trade practices and exploitation"),
        ("The right to representation", "Being heard in consumer forums"),
        ("The right to safety", "Protection against goods that are hazardous to health or life"),
        ("The right to basic needs", "Access to essential goods and services at reasonable prices"),
    ], "easy"),

    ("ss-eco-consumer.rights", "exercised through", [
        ("Checking the Maximum Retail Price", "Preventing overcharging above the printed price"),
        ("Asking for a bill or cash memo", "Proof of purchase, needed for a complaint"),
        ("Looking for certification marks", "Agmark, ISI and Hallmark"),
        ("Checking the expiry and manufacturing date", "Avoiding unsafe food and medicine"),
        ("The Right to Information Act of 2005", "Knowing how government departments function"),
        ("Consumer awareness campaigns", "Jago Grahak Jago"),
    ], "medium"),

    ("ss-eco-consumer.rights", "certified by", [
        ("Agmark", "Agricultural and livestock products"),
        ("The ISI mark", "Industrial and electrical products"),
        ("Hallmark", "The purity of gold and silver jewellery"),
        ("The Legal Metrology Act of 2009", "Standard weights and measures"),
        ("FSSAI standards", "Packaged food and beverages"),
    ], "easy"),

    ("ss-eco-consumer.redressal", "established by", [
        ("The Consumer Protection Act of 1986", "COPRA, which created the redressal machinery"),
        ("The Consumer Protection Act of 2019", "Replacing COPRA and adding product liability and e-commerce"),
        ("A District Consumer Disputes Redressal Commission", "Cases up to Rs 1 crore"),
        ("A State Consumer Disputes Redressal Commission", "Cases between Rs 1 crore and Rs 10 crore"),
        ("The National Consumer Disputes Redressal Commission", "Cases above Rs 10 crore"),
        ("Appeal from a District Commission", "To the State Commission within the prescribed period"),
        ("Consumer courts' purpose", "A simple, quick and inexpensive remedy"),
    ], "medium"),

    ("ss-eco-consumer.redressal", "hindered by", [
        ("Slow progress of consumer cases", "Long delays in hearings and judgements"),
        ("Weak enforcement of labour and market laws", "Exploitation continuing in practice"),
        ("Low consumer awareness in rural India", "Few people knowing their rights"),
        ("Small claims", "The cost and effort of a case exceeding the loss"),
        ("Scattered consumer groups", "About 700 groups working without coordination"),
        ("Lack of effective implementation", "Laws existing but not being enforced"),
    ], "hard"),

    ("ss-eco-consumer.rights", "exploited through", [
        ("Adulteration", "Adding inferior substances to food and other goods"),
        ("Underweight goods", "Selling less than the quantity paid for"),
        ("False claims and misleading advertisements", "Overstating quality or benefit"),
        ("No expiry date or label", "Concealing information about the product"),
        ("Overcharging above MRP", "Charging more than the printed price"),
        ("Absence of a complaint mechanism", "Leaving the consumer without remedy"),
    ], "medium"),

    # ── Consumer rights and globalisation, extended ────────────────────
    ("ss-eco-consumer.rights", "term for", [
        ("The right to be protected against goods and services that are hazardous", "Right to safety"),
        ("The right to know the full particulars of what is being bought", "Right to be informed"),
        ("The right to choose from a range of goods at competitive prices", "Right to choose"),
        ("The right to seek compensation against unfair trade practices", "Right to seek redressal"),
        ("The right to put one's case before a consumer court", "Right to represent"),
    ], "easy"),

    ("ss-eco-consumer.redressal", "provided by", [
        ("Consumer protection at the national level in India", "The National Consumer Disputes Redressal Commission"),
        ("Consumer protection at the state level in India", "The State Consumer Disputes Redressal Commission"),
        ("Consumer protection at the district level in India", "The District Consumer Disputes Redressal Forum"),
        ("The legal basis for consumer claims in India", "The Consumer Protection Act"),
        ("Independent evidence that goods meet declared standards", "Certification marks such as ISI, Agmark and Hallmark"),
    ], "medium"),

    ("ss-eco-globalisation.factors", "enabled by", [
        ("Producers placing different stages of production in different countries", "Improvement in transportation and communication technology"),
        ("Goods and services moving more freely between countries", "Removal of barriers to foreign trade and foreign investment"),
        ("Capital moving quickly across national borders", "Liberalisation of the rules governing financial flows"),
        ("Multinational corporations driving production across countries", "Access to cheap labour and to markets in host countries"),
        ("Markets of different countries becoming more integrated", "Foreign trade linking producers with buyers abroad"),
    ], "medium"),

    ("ss-eco-globalisation.wto", "term for", [
        ("The organisation that sets the rules for international trade", "The World Trade Organization"),
        ("The process of removing government barriers between economies", "Liberalisation"),
        ("A company that owns and manages production in several countries", "A multinational corporation"),
        ("The integration of markets and production across countries", "Globalisation"),
        ("Production of a single good spread across several countries", "Interlinked production"),
    ], "medium"),
]
