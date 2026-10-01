"""Civics clusters - Democratic Politics II.

Five chapters: Power Sharing, Federalism, Gender Religion and Caste, Political
Parties, and Outcomes of Democracy.

The Belgium and Sri Lanka comparison carries a lot of precise figures, and they
are the ones most often examined, so they are clustered densely on purpose: a
student who has mixed up the Flemish and Wallonia percentages will meet both
numbers as distractors to each other.
"""

from __future__ import annotations

CLUSTERS = [
    # ══════════════════════════════════════════════════════════════════
    # Chapter 1 - Power Sharing
    # ══════════════════════════════════════════════════════════════════
    ("ss-civ-power-sharing.belgium-srilanka", "share of population in", [
        ("Dutch speakers in Belgium as a whole", "59 per cent"),
        ("French speakers in Belgium as a whole", "40 per cent"),
        ("German speakers in Belgium", "About 1 per cent"),
        ("French speakers in Brussels", "80 per cent"),
        ("Dutch speakers in Brussels", "20 per cent"),
        ("Sinhala speakers in Sri Lanka", "74 per cent"),
        ("Tamil speakers in Sri Lanka", "18 per cent"),
    ], "easy"),

    ("ss-civ-power-sharing.belgium-srilanka", "year of", [
        ("The Act recognising Sinhala as the only official language", "1956"),
        ("The constitutional amendment giving a separate government to Brussels", "1970-1993, four amendments"),
        ("The start of the Sri Lankan civil war", "1983"),
        ("The end of the Sri Lankan civil war", "2009"),
        ("Belgium's first major constitutional reform", "1970"),
    ], "easy"),

    ("ss-civ-power-sharing.belgium-srilanka", "resulted in", [
        ("Majoritarian measures in Sri Lanka", "Growing alienation among Sri Lankan Tamils"),
        ("The demand for Tamil Eelam", "An armed conflict and a long civil war"),
        ("Accommodation in Belgium", "Peaceful coexistence between the two language communities"),
        ("Brussels' separate government", "Equal representation for French and Dutch speakers"),
        ("The Community government in Belgium", "Elected by language groups regardless of where they live"),
        ("Refusing to share power in Sri Lanka", "Internal conflict that damaged national unity"),
    ], "hard"),

    ("ss-civ-power-sharing.forms", "means", [
        ("Horizontal distribution of power", "Sharing among the legislature, executive and judiciary"),
        ("Vertical division of power", "Sharing among the union, state and local governments"),
        ("Community government", "Sharing among social groups, such as language communities in Belgium"),
        ("Coalition government", "Sharing among political parties that form an alliance"),
        ("Checks and balances", "Each organ of government restraining the others"),
        ("Reserved constituencies", "Sharing of political power with weaker sections"),
    ], "easy"),

    ("ss-civ-power-sharing.why", "reason for", [
        ("Power sharing being good in itself", "It is the very spirit of democracy"),
        ("Reducing the possibility of conflict between social groups", "A prudential reason: sharing prevents conflict"),
        ("Ensuring the stability of political order", "A prudential reason: sharing avoids majority tyranny"),
        ("People having a right to be consulted on how they are governed", "A moral reason for power sharing"),
        ("Legitimacy of government", "A government of the people requires sharing power with them"),
        ("Accommodating diversity", "Preventing the tyranny of the majority"),
    ], "medium"),

    ("ss-civ-power-sharing.why", "illustrated by", [
        ("The prudential approach", "Belgium's accommodation of its two language communities"),
        ("The failure to share power", "Sri Lanka's majoritarianism and civil war"),
        ("A moral justification", "The claim that people have a right to be consulted"),
        ("Horizontal power sharing", "India's system of checks and balances"),
        ("Vertical power sharing", "India's three levels of government"),
        ("Community power sharing", "Belgium's Community government"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 2 - Federalism
    # ══════════════════════════════════════════════════════════════════
    ("ss-civ-federalism.features", "requires", [
        ("Two or more levels of government", "Each governing the same citizens"),
        ("Jurisdiction of each level", "Specified in the constitution"),
        ("Constitutional guarantee of authority", "Each level's existence and powers protected"),
        ("Changing basic constitutional provisions", "Consent of both the central and the state governments"),
        ("Financial autonomy of each level", "Separately specified sources of revenue"),
        ("Interpreting the constitution", "Courts acting as an umpire between levels"),
        ("Specified objectives of the federation", "Safeguarding unity while accommodating diversity"),
    ], "medium"),

    ("ss-civ-federalism.features", "distinguished by", [
        ("A coming-together federation", "Independent states uniting voluntarily, as in the USA"),
        ("A holding-together federation", "A large country dividing power between centre and units, as in India"),
        ("A unitary system", "Only one level of government, or sub-units subordinate to the centre"),
        ("India's federal structure", "A holding-together federation with a strong centre"),
    ], "hard"),

    ("ss-civ-federalism.india", "listed in", [
        ("Defence, banking, communications and currency", "The Union List"),
        ("Police, trade, commerce, agriculture and irrigation", "The State List"),
        ("Education, forest, trade unions, marriage, adoption and succession", "The Concurrent List"),
        ("Subjects not mentioned in any of the three lists", "Residuary subjects, which go to the Union"),
        ("Areas too small to be separate states but not mergeable", "Union Territories, run by the central government"),
        ("Number of subjects in the Union List", "About 97"),
        ("Number of subjects in the State List", "About 66"),
        ("Number of subjects in the Concurrent List", "About 47"),
    ], "medium"),

    ("ss-civ-federalism.india", "measured by", [
        ("Number of Scheduled Languages in India", "22"),
        ("Share of Indians speaking Hindi", "About 40 per cent"),
        ("India's official language", "Hindi, which is not declared the national language"),
        ("States in the Indian Union", "28 states and 8 Union Territories"),
        ("The basis of state formation in 1950s India", "Language"),
        ("A successful experiment in federalism", "Linguistic states and flexible centre-state relations"),
    ], "easy"),

    ("ss-civ-federalism.decentralisation", "provided for", [
        ("Regular elections to local government bodies", "Made constitutionally mandatory in 1992"),
        ("Reservation for SC, ST and OBC in local bodies", "Made mandatory by the 1992 amendment"),
        ("Reservation of at least one-third of positions for women", "Introduced by the 1992 amendment"),
        ("An independent State Election Commission", "Created to conduct panchayat and municipal elections"),
        ("Sharing of power and revenue with local bodies", "Required of state governments"),
        ("Panchayati Raj", "Village, block and district level rural local government"),
        ("Municipalities and municipal corporations", "Urban local government"),
        ("Gram Sabha", "A meeting of all adults in a village on the panchayat's voter list"),
    ], "medium"),

    ("ss-civ-federalism.decentralisation", "structured as", [
        ("The village level", "The Gram Panchayat, headed by the Sarpanch"),
        ("The block level", "The Panchayat Samiti or Block"),
        ("The district level", "The Zila Parishad"),
        ("A small town", "A municipality"),
        ("A big city", "A municipal corporation, headed by the Mayor"),
    ], "easy"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 3 - Gender, Religion and Caste
    # ══════════════════════════════════════════════════════════════════
    ("ss-civ-gender.gender", "reflected in", [
        ("Lower female literacy", "Girls dropping out to support the family"),
        ("Unequal wages for equal work", "Women paid less than men for the same labour"),
        ("A declining child sex ratio", "Preference for sons and sex-selective abortion"),
        ("Unpaid domestic labour", "Women cooking, cleaning and caring for children"),
        ("Low political representation", "Women holding a small share of seats in legislatures"),
        ("Reservation proposed for women in local bodies", "At least one-third of positions"),
        ("Women's reservation Bill", "One-third of seats in Lok Sabha and state assemblies"),
    ], "medium"),

    ("ss-civ-gender.gender", "term for", [
        ("Social divisions based on sexual division of labour", "Gender"),
        ("Politics that stresses the interests of one religious group", "Communalism"),
        ("A society where men and women get equal opportunities", "An egalitarian society"),
        ("Public expression of religion in politics", "Communal politics"),
        ("A state that does not favour any religion", "A secular state"),
        ("A hierarchy of social groups based on descent", "Caste"),
    ], "easy"),

    ("ss-civ-gender.religion", "guaranteed by", [
        ("India's secularism", "No official religion is given constitutional status"),
        ("Freedom to profess and practise any religion", "The Constitution's Fundamental Rights"),
        ("The right to reform religion", "Freedom of conscience"),
        ("State intervention in religious matters", "Allowed to ensure equality within religious communities"),
        ("A ban on religion-based discrimination", "Fundamental Rights"),
        ("Reservation and protective measures", "Permitted for socially backward groups"),
    ], "medium"),

    ("ss-civ-gender.religion", "expressed as", [
        ("Religious prejudice and stereotypes", "Everyday communalism"),
        ("A quest for political dominance of one community", "Communal politics"),
        ("Religious symbols and rituals in elections", "Communal mobilisation"),
        ("Demands for a separate political unit", "Communalism in its most extreme form"),
        ("State support to a religious community", "A violation of secularism"),
    ], "hard"),

    ("ss-civ-gender.caste", "operates through", [
        ("Caste in politics", "Parties selecting candidates who can win the local caste arithmetic"),
        ("Politics in caste", "Caste identities being reshaped by political competition"),
        ("Caste-based reservation", "Constitutional provisions for SC, ST and OBC"),
        ("Appeals to caste sentiment in elections", "Vote-bank politics"),
        ("Caste and economic status", "Overlapping but not identical inequalities"),
        ("Caste in public life", "Declining influence in cities but persistent in rural areas"),
    ], "hard"),

    ("ss-civ-gender.caste", "weakened by", [
        ("Economic development and urbanisation", "Occupational mobility across caste lines"),
        ("Education and literacy", "Reduced acceptance of caste hierarchy"),
        ("Constitutional provisions and laws", "Abolition of untouchability and caste discrimination"),
        ("Political mobilisation of lower castes", "Assertion of political rights"),
        ("Inter-caste marriage and migration", "Blurring of rigid boundaries"),
        ("Land reforms", "Reduced landlord power based on caste"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 4 - Political Parties
    # ══════════════════════════════════════════════════════════════════
    ("ss-civ-parties.functions", "carried out by", [
        ("Contesting elections", "Political parties, by fielding candidates"),
        ("Putting forward policies and programmes", "Political parties, through their manifestos"),
        ("Making laws in the legislature", "Political parties, through their members in the legislature"),
        ("Forming and running the government", "The ruling party or coalition"),
        ("Playing the role of the opposition", "Parties that lose elections"),
        ("Shaping public opinion", "Political parties and pressure groups"),
        ("Providing access to government machinery and welfare schemes", "Political parties"),
    ], "easy"),

    ("ss-civ-parties.types", "consists of", [
        ("A one-party system", "Only one party allowed to rule, as in China"),
        ("A two-party system", "Power usually shifts between two main parties, as in the USA and UK"),
        ("A multi-party system", "Several parties compete, as in India"),
        ("A coalition government", "Two or more parties joining to form a government"),
        ("A recognised party", "One given facilities by the Election Commission on set criteria"),
        ("A registered but unrecognised party", "One that has not met the recognition criteria"),
    ], "easy"),

    ("ss-civ-parties.types", "recognition requires", [
        ("A national party", "At least six per cent of votes in Lok Sabha or in four state assemblies, plus four Lok Sabha seats"),
        ("A state party", "At least six per cent of votes in a state assembly election plus two seats"),
        ("A recognised national party", "An election symbol reserved for exclusive use"),
        ("A registered party", "Registration with the Election Commission"),
    ], "hard"),

    ("ss-civ-parties.national", "founded in", [
        ("The Bharatiya Janata Party", "1980"),
        ("The Indian National Congress", "1885"),
        ("The Communist Party of India (Marxist)", "1964"),
        ("The Bahujan Samaj Party", "1984"),
        ("The Nationalist Congress Party", "1999"),
        ("The Trinamool Congress", "1998"),
        ("The Aam Aadmi Party", "2012"),
        ("The Communist Party of India", "1925"),
    ], "medium"),

    ("ss-civ-parties.national", "symbol of", [
        ("The Bharatiya Janata Party", "Lotus"),
        ("The Indian National Congress", "Hand"),
        ("The Communist Party of India (Marxist)", "Hammer, sickle and star"),
        ("The Bahujan Samaj Party", "Elephant"),
        ("The Nationalist Congress Party", "Clock"),
        ("The Aam Aadmi Party", "Broom"),
        ("The Trinamool Congress", "Grass and flowers"),
    ], "easy"),

    ("ss-civ-parties.national", "example of", [
        ("A state party of Punjab", "The Shiromani Akali Dal"),
        ("A state party of Tamil Nadu", "The Dravida Munnetra Kazhagam"),
        ("A state party of Andhra Pradesh", "The Telugu Desam Party"),
        ("A state party of Odisha", "The Biju Janata Dal"),
        ("A state party of Assam", "The Asom Gana Parishad"),
        ("A state party of West Bengal", "The Trinamool Congress before national recognition"),
    ], "medium"),

    ("ss-civ-parties.functions", "challenged by", [
        ("Lack of internal democracy", "Power concentrated in a few top leaders"),
        ("Dynastic succession", "Family members inheriting leadership"),
        ("Growing use of money and muscle power", "Parties backing candidates who can win by any means"),
        ("Absence of a real choice for voters", "Parties differing little in ideology and practice"),
        ("Criminalisation of politics", "Candidates with criminal cases contesting elections"),
        ("Weak organisational structure", "No regular membership or internal elections"),
    ], "hard"),

    ("ss-civ-parties.functions", "reformed by", [
        ("The anti-defection law", "A constitutional amendment preventing MPs and MLAs from switching parties"),
        ("Affidavits of property and criminal cases", "Making candidates disclose assets and pending cases"),
        ("A law regulating internal affairs", "Mandating organisational elections and membership registers"),
        ("State funding of elections", "Reducing dependence on private money"),
        ("Pressure from citizens and the media", "Forcing parties to be more open"),
        ("Public participation", "Joining parties and making them accountable"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 5 - Outcomes of Democracy
    # ══════════════════════════════════════════════════════════════════
    ("ss-civ-outcomes.accountable", "expected of", [
        ("An accountable government", "Following rules and procedures, and being answerable to citizens"),
        ("A responsive government", "Attending to the needs and expectations of the people"),
        ("A legitimate government", "Being elected by the people through free and fair elections"),
        ("Transparency in democracy", "Citizens being able to examine how decisions were taken"),
        ("Norms and procedures in a democracy", "Slower decisions, but ones that are more acceptable"),
    ], "medium"),

    ("ss-civ-outcomes.equality", "assessed by", [
        ("Economic growth under democracy", "Compared with non-democratic regimes over 1950 to 2000"),
        ("Growth rates of dictatorships between 1950 and 2000", "Slightly higher than those of democracies"),
        ("Democracy's advantage", "Being more acceptable because growth is shared and legitimate"),
        ("Inequality in democracies", "High and often rising, despite formal equality"),
        ("Poverty reduction", "Slower than expected in many democracies, including India"),
        ("The top of society's share of income", "Growing faster than the bottom's"),
    ], "hard"),

    ("ss-civ-outcomes.equality", "promoted by", [
        ("Accommodation of social diversity", "Respect for differences and mechanisms to negotiate conflict"),
        ("Dignity and freedom of citizens", "Legal recognition of equality, including for women"),
        ("Claims of disadvantaged groups", "Recognition of their rights by democratic politics"),
        ("Democratic government", "Improving the dignity of all citizens"),
        ("Public support for democracy", "Sustained even when people criticise its performance"),
    ], "medium"),

    ("ss-civ-outcomes.assessment", "judged by", [
        ("Whether democracy delivers", "Accountable, responsive and legitimate government"),
        ("Economic outcomes", "Growth, development and reduction of inequality"),
        ("Social outcomes", "Accommodation of diversity and dignity of citizens"),
        ("Political outcomes", "Freedom, choice and participation"),
        ("Democracy's greatest strength", "Its ability to generate its own support among the people"),
    ], "medium"),

    ("ss-civ-outcomes.assessment", "distinguished from", [
        ("A dictatorship", "No elected government and no citizen control over decisions"),
        ("A non-democratic regime's economic record", "Growth without legitimacy or equality"),
        ("Democracy's procedures", "Slower than authoritarian rule but more acceptable"),
        ("Corruption in democracies", "Present, but exposed and contested in public"),
    ], "hard"),

    # ── Chapter 5 continued ────────────────────────────────────────────
    # Outcomes of Democracy was the thinnest chapter in the subject. These
    # clusters stay inside what the chapter actually argues: it makes almost no
    # numerical claims, so none are invented here, and the content is the
    # reasoning a candidate has to reproduce rather than figures to recall.
    ("ss-civ-outcomes.accountable", "guaranteed by", [
        ("Citizens being able to examine how a decision was taken", "Published norms and recorded procedures"),
        ("Rulers being replaceable without violence", "Elections held at regular, fixed intervals"),
        ("The executive being questioned between elections", "A legislature with the right to demand answers"),
        ("Official conduct being visible to the public", "A free press that reports on government decisions"),
        ("A citizen's right to ask for official information", "Statutory right to information"),
    ], "medium"),

    ("ss-civ-outcomes.accountable", "consequence of", [
        ("Decisions taking longer in a democracy", "Deliberation, negotiation and open procedure"),
        ("A decision being accepted even by those who lost the argument", "Those affected having taken part in making it"),
        ("A government being answerable for its performance", "The possibility of removing it at the next election"),
        ("A wrong decision eventually being corrected", "Public debate and the chance of a change of government"),
        ("Grievances being voiced rather than suppressed", "Freedom of expression and a permitted opposition"),
    ], "hard"),

    ("ss-civ-outcomes.accountable", "term for", [
        ("A government that follows its own stated norms and procedures", "Accountable government"),
        ("A government that attends to what people need and expect", "Responsive government"),
        ("A government that people accept because they chose it", "Legitimate government"),
        ("A citizen's ability to find out how a decision was reached", "Transparency"),
        ("The comparison between what democracy promises and what it delivers", "Assessment of democratic outcomes"),
    ], "easy"),

    ("ss-civ-outcomes.equality", "reason for", [
        ("Democracies being unable to end economic inequality on their own", "Inequality depending on who holds resources, not on the form of government"),
        ("Growth rates of democracies and dictatorships being close between 1950 and 2000", "Both systems containing fast-growing and stagnant countries"),
        ("Democratic growth being considered preferable despite similar rates", "Its gains being shared and its government chosen by the people"),
        ("Poverty falling more slowly than citizens hoped in several democracies", "Growth being unevenly distributed between groups and regions"),
        ("Public dissatisfaction persisting in functioning democracies", "Citizens holding their rulers to a standard the rulers rarely meet fully"),
    ], "hard"),

    ("ss-civ-outcomes.equality", "illustrated by", [
        ("Formal equality coexisting with real inequality", "Equal voting rights alongside widening income gaps"),
        ("Democracy improving the dignity of citizens", "Disadvantaged groups pressing claims that are then recognised"),
        ("Democracy improving the dignity of women", "Legal recognition of equality and the ability to protest unfair treatment"),
        ("Caste-based claims being addressed in a democracy", "Recognition of the claims of historically disadvantaged groups"),
        ("Freedom and dignity being democracy's clearest advantage", "Its record on these compared with its record on growth"),
    ], "medium"),

    ("ss-civ-outcomes.assessment", "example of", [
        ("A political outcome of democracy", "Citizens choosing who governs and being free to change that choice"),
        ("An economic outcome of democracy", "Growth being pursued alongside attempts to reduce inequality"),
        ("A social outcome of democracy", "Differences between communities being accommodated rather than suppressed"),
        ("A sign that democracy is functioning rather than failing", "Citizens complaining about how their rulers behave"),
        ("A limitation of democracy rather than of its rulers", "Slow decisions caused by consultation and procedure"),
    ], "medium"),

    ("ss-civ-outcomes.assessment", "significance of", [
        ("Treating complaints as integral to democracy", "Showing that citizens expect their rulers to answer to them"),
        ("Comparing democracies with one another rather than with an ideal", "Judging each against what democracy can realistically deliver"),
        ("Assessing outcomes rather than only institutions", "Revealing whether elections and legislatures actually improve lives"),
        ("Public support surviving criticism of performance", "Indicating that people value the system more than any one government"),
        ("Democracy generating its own support among the people", "Being the reason it outlasts regimes that rule by force alone"),
    ], "hard"),

    ("ss-civ-outcomes.assessment", "sustained by", [
        ("Popular support for democracy", "Citizens valuing being able to choose and question their rulers"),
        ("The legitimacy of a democratic government", "Free and fair elections that the losers accept"),
        ("The accommodation of social diversity", "Respect for difference and agreed ways of negotiating conflict"),
        ("Continued improvement in dignity and freedom", "Citizens pressing claims and institutions recognising them"),
        ("Trust between citizens and rulers over time", "Rulers following procedure and citizens being able to verify it"),
    ], "medium"),

    # ── Wider civics top-up ────────────────────────────────────────────
    ("ss-civ-power-sharing.why", "illustrated by", [
        ("The prudential case for power sharing", "Sharing reducing the chance of conflict between social groups"),
        ("The moral case for power sharing", "Power belonging to the people who are governed by it"),
        ("Vertical division of power in practice", "Different levels of government each holding their own authority"),
        ("Horizontal division of power in practice", "Legislature, executive and judiciary checking one another"),
        ("Community government as a form of power sharing", "Different social groups being given a share in decisions about themselves"),
        ("Coalition government as power sharing", "Several parties sharing executive authority after an election"),
    ], "easy"),

    ("ss-civ-federalism.features", "guaranteed by", [
        ("The distribution of powers between levels of government", "A written constitution that both levels must respect"),
        ("The authority of each level over its own subjects", "Constitutional protection of its own area of power"),
        ("Changes to the basic arrangement of powers", "Agreement of both the centre and the constituent units"),
        ("Disputes between levels of government", "A judiciary empowered to interpret the constitution"),
        ("Revenue for each level of government", "Constitutionally specified sources of its own income"),
        ("The existence of more than one level of government", "The same citizens being governed by each of them"),
    ], "medium"),

    ("ss-civ-gender.caste", "reflected in", [
        ("Caste inequality in everyday life", "Denial of dignity and unequal treatment between groups"),
        ("Caste entering politics", "Parties choosing candidates expected to attract a caste bloc"),
        ("Caste shaping electoral outcomes", "Voters favouring candidates from their own community"),
        ("Political mobilisation on caste lines", "Appeals to caste feeling in campaigns and slogans"),
        ("Caste combining with other identities", "Class, region and community acting together in voting"),
        ("Caste not deciding every election", "No constituency being entirely one caste, and coalitions being needed"),
    ], "hard"),

    ("ss-civ-parties.functions", "challenged by", [
        ("Internal democracy within parties", "Power concentrated in a small group at the top"),
        ("Transparent functioning of parties", "Decisions and accounts not being open to members or voters"),
        ("Fair competition between parties", "Money and muscle power being used to win elections"),
        ("Voters being offered a real choice", "Parties differing little in what they actually propose"),
        ("Parties being held to account by citizens", "Distrust of politicians spreading to the parties themselves"),
        ("Nominating candidates who can win", "Pressure to field those with money or influence over merit"),
    ], "medium"),
]
