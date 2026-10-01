"""Chemistry clusters - Class 10 Science, chapters 1, 2, 3 and 4.

Chemical Reactions and Equations, Acids Bases and Salts, Metals and Non-metals,
and Carbon and its Compounds. Chapters 3 and 4 were the last two in the bank
below the hundred-question floor, both sitting at 95, and the reason was
structural rather than a shortage of ideas: those chapters had been authored
almost entirely as one-line definitions, which yield one question each, while
facts yield three. Chapter 3 carried 13 definitions against 11 facts.

Chemistry clusters unusually well on attribute because so much of the syllabus is
a table read across: metal and its behaviour with water, ore and the process that
converts it, organic compound and its formula, substance and the process that
makes it. Each of those is one attribute with many subjects, which is exactly the
shape the generator wants.

Values inside a cluster are kept distinct on purpose. The generator builds the
reverse-recall form - "which subject has this value?" - only when no other item in
the file carries the same value under the same attribute, so a repeated value
quietly costs a third of a cluster's output. The same gate runs across the whole
file rather than one cluster, so "reaction of" and "use of" are each used in only
one chapter here and their values are checked against each other.

Formula clusters carry `case_sensitive=True`. Chemical notation is one of the few
places where folding case would be actively wrong: CO is carbon monoxide and Co is
cobalt, and a distractor check that treated them as equal would accept a
mistranscription as a duplicate of the answer.

Overlap with the older chemistry files was checked before writing. The existing
facts already give the pH of pure water, gastric juice, lemon juice, blood and
sodium hydroxide; the litmus, phenolphthalein and methyl orange colour changes;
the chemical formulae and main uses of the five common salts; and the molecular
formulae of methane, ethane, ethene, ethyne, ethanol and ethanoic acid. Those
subjects are deliberately absent here, and the new clusters cover what surrounds
them instead - other indicators, other pH ranges, chemical names alongside
formulae, the processes that make each salt, and the longer carbon chains.

No figure here is invented: the pH values, the 443 K dehydration temperature, the
373 K conversion of gypsum, the acid-rain threshold of 5.6 and the general
formulae are the values the NCERT text states.
"""

from __future__ import annotations

FACTS = [
    # ══════════════════════════════════════════════════════════════════
    # Chapter 1 - Chemical Reactions and Equations
    # ══════════════════════════════════════════════════════════════════
    ("sci-chem-ch1.reaction-types", "classified as", [
        ("Burning of magnesium ribbon in air", "A combination reaction"),
        ("Heating of limestone, CaCO3, to give quicklime", "A thermal decomposition reaction"),
        ("Zinc granules added to dilute sulphuric acid", "A displacement reaction"),
        ("Mixing silver nitrate solution with sodium chloride solution", "A double displacement reaction, and also a precipitation reaction"),
        ("Passing electricity through water", "An electrolytic decomposition reaction"),
        ("Exposing silver chloride to bright sunlight", "A photochemical decomposition reaction"),
        ("Rusting of iron left in damp air", "A slow oxidation"),
        ("Burning of natural gas in a kitchen stove", "An exothermic reaction"),
        ("Barium hydroxide mixed with ammonium chloride", "An endothermic reaction that makes the vessel feel cold"),
        ("Copper oxide heated with hydrogen", "A redox reaction in which copper oxide is reduced"),
    ], "medium"),

    ("sci-chem-ch1.effects", "energy change in", [
        ("Respiration inside living cells", "Exothermic, because glucose is oxidised and heat is released"),
        ("Decomposition of vegetable matter into compost", "Exothermic, and the compost heap warms up"),
        ("Digestion of food in the body", "Exothermic overall, since large molecules are broken down"),
        ("Photosynthesis in a green leaf", "Endothermic, because sunlight is absorbed to build glucose"),
        ("Thermal decomposition of calcium carbonate", "Endothermic, because heat must be supplied continuously"),
        ("Dissolving quicklime in water", "Exothermic, with hissing and the formation of slaked lime"),
        ("Decomposition of ferrous sulphate crystals on heating", "Endothermic, giving ferric oxide along with sulphur dioxide and sulphur trioxide"),
    ], "medium"),

    ("sci-chem-ch1.observations", "observation of", [
        ("Burning magnesium ribbon in air", "A dazzling white flame, and a white powder left behind"),
        ("Mixing lead nitrate solution with potassium iodide solution", "A yellow precipitate of lead iodide"),
        ("Mixing barium chloride solution with sodium sulphate solution", "A white precipitate of barium sulphate"),
        ("Adding zinc granules to dilute hydrochloric acid", "Bubbles of a colourless gas, with the tube becoming warm"),
        ("Silver chloride left in bright sunlight", "The white solid turning grey"),
        ("Electrolysis of water, with the gases collected separately", "Twice as much gas at one electrode as at the other"),
        ("The gas from zinc and dilute acid, tested with a burning splinter", "A pop, which shows that the gas is hydrogen"),
        ("Carbon dioxide passed through lime water", "The lime water turning milky"),
        ("Ferric chloride solution mixed with ammonium hydroxide", "A reddish-brown precipitate"),
    ], "medium"),

    ("sci-chem-ch1.redox", "role in a redox reaction", [
        ("A substance that gains oxygen or loses hydrogen", "The substance that is oxidised"),
        ("A substance that loses oxygen or gains hydrogen", "The substance that is reduced"),
        ("Oxygen added to another substance during a reaction", "The oxidising agent"),
        ("Hydrogen added to an unsaturated compound over nickel", "The reducing agent"),
        ("Copper oxide in its reaction with hydrogen", "The substance that is reduced, because it loses oxygen"),
        ("Hydrogen in its reaction with copper oxide", "The substance that is oxidised, because it gains oxygen"),
        ("Chlorine added to a solution of a bromide", "The oxidising agent, because it takes electrons away"),
    ], "hard"),

    ("sci-chem-ch1.equations", "information in", [
        ("A skeletal chemical equation", "The reactants and products by formula, but not the correct number of each"),
        ("A balanced chemical equation", "The formulas of every reactant and product together with the ratio in which they react"),
        ("The state symbols s, l, g and aq", "Whether each substance is a solid, a liquid, a gas or dissolved in water"),
        ("A condition written above the arrow", "The temperature, pressure, catalyst or light the reaction needs"),
        ("The coefficient placed before a formula", "How many molecules or formula units of that substance take part"),
        ("A downward arrow after a formula", "That the substance is formed as an insoluble precipitate"),
        ("An upward arrow after a formula", "That the substance escapes as a gas"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 2 - Acids, Bases and Salts
    # ══════════════════════════════════════════════════════════════════
    ("sci-chem-ch2.ph", "pH of", [
        ("Clean rain water", "Slightly below 7, because dissolved carbon dioxide makes it weakly acidic"),
        ("Acid rain", "Below 5.6, which is the level at which rain counts as acidic"),
        ("Most soils in which crops grow well", "Between 6.5 and 7.5"),
        ("Vinegar", "About 2.4"),
        ("Milk of magnesia, used as an antacid", "About 10"),
        ("A solution of washing soda", "About 11, since it is a basic salt"),
        ("The inside of a person's mouth soon after a meal", "Falls below 5.5 as bacteria turn sugar into acid"),
        ("A solution of sodium chloride in water", "About 7, because it is a salt of a strong acid and a strong base"),
        ("A solution of ammonium chloride in water", "Below 7, because it is a salt of a strong acid and a weak base"),
    ], "medium"),

    ("sci-chem-ch2.indicators", "behaviour as an indicator", [
        ("Turmeric", "Stays yellow in acid and turns reddish-brown in base"),
        ("Red cabbage extract", "Purple when neutral, red in acid and green in base"),
        ("China rose solution", "Turns dark pink in acid and green in base"),
        ("Onion paste", "Keeps its smell in acid but loses it in base, so it is an olfactory indicator"),
        ("Clove oil", "Smells in acid but not in base, which makes it useful where litmus cannot be used"),
        ("Vanilla essence", "Retains its smell in acid and loses it in base"),
        ("Blue litmus paper", "Changes to red only in acid and stays blue in base"),
        ("Red litmus paper", "Changes to blue only in base and stays red in acid"),
    ], "medium"),

    ("sci-chem-ch2.compounds", "produced by", [
        ("Sodium hydroxide", "The chlor-alkali process, in which brine is electrolysed"),
        ("Chlorine gas at the anode during the chlor-alkali process", "Electrolysis of brine, along with hydrogen at the cathode"),
        ("Bleaching powder", "Passing chlorine gas through dry slaked lime"),
        ("Baking soda", "Reacting a cold concentrated salt solution with ammonia and carbon dioxide"),
        ("Plaster of Paris", "Heating gypsum to 373 K so that it loses part of its water of crystallisation"),
        ("Washing soda", "Recrystallising sodium carbonate from its solution"),
        ("Slaked lime", "Adding water to quicklime in a strongly exothermic reaction"),
    ], "medium"),

    ("sci-chem-ch2.compounds", "chemical name of", [
        ("Baking soda", "Sodium hydrogen carbonate"),
        ("Washing soda", "Sodium carbonate decahydrate"),
        ("Bleaching powder", "Calcium oxychloride"),
        ("Plaster of Paris", "Calcium sulphate hemihydrate"),
        ("Common salt", "Sodium chloride"),
        ("Quicklime", "Calcium oxide"),
        ("Slaked lime", "Calcium hydroxide"),
        ("Gypsum", "Calcium sulphate dihydrate"),
        ("Marble and limestone", "Calcium carbonate"),
    ], "easy"),

    ("sci-chem-ch2.acids", "found in", [
        ("Citric acid", "Oranges, lemons and other citrus fruit"),
        ("Acetic acid", "Vinegar"),
        ("Tartaric acid", "Tamarind, grapes and unripe mango"),
        ("Oxalic acid", "Tomato and spinach"),
        ("Lactic acid", "Curd and sour milk"),
        ("Formic acid", "The sting of an ant and of a nettle leaf"),
        ("Hydrochloric acid", "The gastric juice secreted in the stomach"),
        ("Ascorbic acid", "Amla and citrus fruit, where it acts as vitamin C"),
    ], "easy"),

    ("sci-chem-ch2.acids", "use of", [
        ("Sulphuric acid", "Car batteries, and as the starting material for many other chemicals"),
        ("Hydrochloric acid", "Cleaning metal surfaces and in the stomach to help digestion"),
        ("Nitric acid", "Making fertilisers and explosives"),
        ("Acetic acid", "Preserving food as vinegar"),
        ("Citric acid", "Flavouring food and as a mild cleaning agent"),
        ("Tartaric acid", "Making baking powder, together with sodium hydrogen carbonate"),
    ], "medium"),

    ("sci-chem-ch2.bases", "use of", [
        ("Sodium hydroxide", "Making soap, paper and rayon, and clearing blocked drains"),
        ("Calcium hydroxide", "Whitewashing walls, and neutralising acidic soil"),
        ("Magnesium hydroxide", "An antacid that neutralises excess stomach acid"),
        ("Ammonium hydroxide", "Cleaning glass and as a laboratory reagent"),
        ("Slaked lime in farming", "Treating soil that has become too acidic"),
    ], "medium"),

    ("sci-chem-ch2.neutralisation", "salt from", [
        ("Hydrochloric acid and sodium hydroxide", "Sodium chloride, a neutral salt"),
        ("Sulphuric acid and sodium hydroxide", "Sodium sulphate"),
        ("Nitric acid and potassium hydroxide", "Potassium nitrate"),
        ("Acetic acid and sodium hydroxide", "Sodium ethanoate"),
        ("Hydrochloric acid and ammonia", "Ammonium chloride"),
        ("Carbonic acid and sodium hydroxide", "Sodium carbonate or sodium hydrogen carbonate, depending on the amounts used"),
        ("Nitric acid and sodium hydroxide", "Sodium nitrate"),
    ], "medium"),

    ("sci-chem-ch2.compounds", "effect of", [
        ("An acid on blue litmus paper", "Turning it red"),
        ("A base on red litmus paper", "Turning it blue"),
        ("An acid on a reactive metal such as zinc", "Producing a salt and hydrogen gas"),
        ("An acid on a metal carbonate", "Producing a salt, water and carbon dioxide"),
        ("A base on an ammonium salt", "Releasing ammonia gas, which has a sharp smell"),
        ("Excess carbon dioxide on lime water that has already turned milky", "Clearing it again, as soluble calcium hydrogen carbonate forms"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 3 - Metals and Non-metals
    # ══════════════════════════════════════════════════════════════════
    ("sci-chem-ch3.properties", "categorised as", [
        ("A metal that can be beaten into thin sheets", "Malleable"),
        ("A metal that can be drawn out into thin wires", "Ductile"),
        ("A metal that gives a ringing sound when struck hard", "Sonorous"),
        ("An oxide that reacts with both acids and bases to give salt and water", "Amphoteric"),
        ("A non-metal that is a very good conductor of electricity", "An exception to the usual behaviour of non-metals"),
        ("Sodium, potassium and lithium", "Soft metals that can be cut with a knife"),
        ("Diamond", "The hardest known natural substance, with a very high melting point"),
        ("Iodine", "A non-metal that still shows a metallic shine"),
    ], "easy"),

    ("sci-chem-ch3.properties", "reaction of", [
        ("Sodium with cold water", "Violent, giving sodium hydroxide and hydrogen, and the metal moves about on the surface"),
        ("Potassium with cold water", "Even more violent, and the hydrogen produced catches fire at once"),
        ("Calcium with cold water", "Steady but gentle, with bubbles of hydrogen sticking to the metal and lifting it"),
        ("Magnesium with hot water", "Slow, forming magnesium hydroxide and hydrogen"),
        ("Aluminium with steam", "Forms aluminium oxide and hydrogen"),
        ("Iron with steam", "Forms Fe3O4 and hydrogen, but only when the iron is red hot"),
        ("Copper and silver with water or steam", "No reaction at all, however hot the water"),
        ("Magnesium with dilute hydrochloric acid", "Very fast, with much hydrogen evolved and the tube becoming hot"),
        ("Zinc with dilute hydrochloric acid", "Steady bubbling, giving zinc chloride and hydrogen"),
        ("Iron with dilute hydrochloric acid", "Slow, giving iron(II) chloride and hydrogen"),
        ("Copper with dilute hydrochloric acid", "No visible change, because copper lies below hydrogen in the reactivity series"),
        ("Gold with any dilute acid", "No reaction, which is why gold keeps its shine"),
        ("Aluminium in air at ordinary temperature", "Forms a thin, tightly held layer of aluminium oxide that protects the metal beneath"),
    ], "medium"),

    ("sci-chem-ch3.reactivity", "reactivity of", [
        ("Potassium", "The highest of all the metals in the series"),
        ("Sodium", "Second highest, just below potassium"),
        ("Calcium", "High, but clearly below sodium"),
        ("Magnesium", "Above aluminium and well above zinc"),
        ("Aluminium", "Between magnesium and zinc"),
        ("Zinc", "Above iron but below aluminium"),
        ("Iron", "Above lead and below zinc"),
        ("Hydrogen", "Placed between lead and copper as a reference point, though it is not a metal"),
        ("Copper", "Below hydrogen, so it cannot push hydrogen out of a dilute acid"),
        ("Mercury", "Below copper and above silver"),
        ("Silver", "Very low, reacting only with substances such as sulphur in the air"),
        ("Gold", "The lowest in the series, and unaffected by air, water or ordinary acids"),
    ], "medium"),

    ("sci-chem-ch3.displacement", "observation for", [
        ("An iron nail left in copper sulphate solution", "The blue colour fades and a reddish-brown coating of copper forms on the nail"),
        ("A copper wire dipped in silver nitrate solution", "The solution slowly turns blue and shining silver crystals grow on the wire"),
        ("Zinc granules added to copper sulphate solution", "The blue colour disappears and copper is deposited as a reddish-brown solid"),
        ("Copper added to zinc sulphate solution", "No change, because copper is less reactive than zinc and cannot displace it"),
        ("Iron added to zinc sulphate solution", "No change, because iron is less reactive than zinc"),
        ("Zinc added to iron sulphate solution", "The pale green colour fades, since zinc displaces iron"),
        ("Silver added to copper sulphate solution", "No change, because silver is less reactive than copper"),
    ], "medium"),

    ("sci-chem-ch3.extraction", "purpose of", [
        ("Crushing and then grinding the mined ore", "Reducing it to a fine powder so that the unwanted material can be separated"),
        ("Concentrating the ore before heating", "Removing as much of the gangue as possible so that later steps use less energy"),
        ("Roasting a concentrated sulphide ore", "Heating it strongly in the presence of air to convert the sulphide into an oxide"),
        ("Calcining a concentrated carbonate ore", "Heating it strongly in the absence of air to drive off carbon dioxide and leave the oxide"),
        ("Reducing the metal oxide with carbon or a more reactive metal", "Obtaining the free metal from its oxide"),
        ("Electrolytic reduction of a molten chloride", "Extracting a metal too reactive to be reduced by carbon"),
        ("Electrolytic refining", "Purifying an impure metal until it is almost completely free of other elements"),
        ("Adding a flux during smelting", "Combining with the gangue to form a slag that can be removed"),
    ], "medium"),

    ("sci-chem-ch3.extraction", "role in electrolytic refining", [
        ("A thick block of the impure metal", "Anode"),
        ("A thin strip of the pure metal", "Cathode"),
        ("A solution of a salt of the metal, slightly acidified", "Electrolyte"),
        ("The impurities that do not dissolve and settle below the anode", "Anode mud"),
        ("The pure metal that deposits during the process", "A coating on the cathode"),
    ], "medium"),

    ("sci-chem-ch3.extraction", "extraction method for", [
        ("Zinc, iron, tin and lead", "Reduction of their oxides with carbon or carbon monoxide"),
        ("Copper from its sulphide ore", "Roasting followed by reduction, and then electrolytic refining"),
        ("Mercury from cinnabar, HgS", "Roasting in air, since its oxide breaks down on heating to give the metal"),
        ("Gold and platinum", "No chemical extraction at all, because they occur in the free state"),
        ("Iron in a blast furnace", "Reducing iron oxide with carbon monoxide made from coke"),
    ], "hard"),

    ("sci-chem-ch3.ionic", "property of", [
        ("An ionic compound at room temperature", "Solid, hard and usually crystalline"),
        ("The melting and boiling points of an ionic compound", "High, because a great deal of energy is needed to break the attraction between ions"),
        ("An ionic compound placed in water", "Usually dissolves"),
        ("An ionic compound placed in kerosene or petrol", "Usually does not dissolve"),
        ("An ionic compound in the solid state with a battery connected", "Does not conduct, because the ions are held in fixed positions"),
        ("An ionic compound when molten or dissolved in water", "Conducts well, because the ions are free to move"),
        ("An ionic compound when struck with a hammer", "Tends to break rather than bend, since a shifted layer puts like charges together"),
    ], "medium"),

    ("sci-chem-ch3.ionic", "formed by", [
        ("Sodium chloride", "Sodium losing one electron and chlorine gaining it"),
        ("Magnesium chloride", "Magnesium losing two electrons, one to each of two chlorine atoms"),
        ("Sodium oxide", "Two sodium atoms each losing one electron to a single oxygen atom"),
        ("Magnesium oxide", "Magnesium losing two electrons to oxygen"),
        ("Aluminium oxide", "Two aluminium atoms losing six electrons in total to three oxygen atoms"),
        ("Calcium chloride", "Calcium losing two electrons, one to each of two chlorine atoms"),
    ], "medium"),

    ("sci-chem-ch3.alloys", "use of", [
        ("Brass", "Fittings, taps, door handles and decorative articles"),
        ("Bronze", "Statues, medals and bearings"),
        ("Solder", "Joining electrical wires and components on a circuit board"),
        ("Stainless steel", "Cutlery, sinks and surgical instruments"),
        ("Duralumin", "Aircraft bodies, because it is light yet strong"),
        ("An amalgam of a metal", "Dental fillings"),
        ("Steel with a low carbon content", "Structures and vehicle bodies, where strength and formability are both needed"),
        ("Galvanised iron", "Roofing sheets, buckets and water pipes"),
    ], "easy"),

    ("sci-chem-ch3.alloys", "composition of", [
        ("Duralumin", "Aluminium with copper, magnesium and manganese"),
        ("Steel", "Iron with a small, controlled amount of carbon"),
        ("German silver", "Copper, zinc and nickel, and despite the name it contains no silver"),
        ("Gunmetal", "Copper, tin and zinc"),
        ("Cast iron", "Iron with about two to four percent carbon, which makes it brittle"),
    ], "medium"),

    ("sci-chem-ch3.properties", "protection offered by", [
        ("A coat of paint", "Keeping air and moisture away from the surface of the metal"),
        ("A layer of grease or oil", "Shielding moving parts from moisture, so that rust cannot form"),
        ("A layer of zinc applied by galvanisation", "Corroding in place of the iron, since zinc is the more reactive of the two"),
        ("Chromium plating", "Providing a hard, shiny surface that does not corrode easily"),
        ("Anodising aluminium", "Building a thick oxide layer that resists further attack"),
        ("Mixing a metal with others to form an alloy", "Changing the composition so that the material no longer corrodes readily"),
        ("Keeping iron dry and covered", "Removing the moisture that rusting needs"),
    ], "medium"),

    ("sci-chem-ch3.properties", "necessary condition for", [
        ("Rusting of iron", "Both air and moisture acting together over time"),
        ("Tarnishing of silver", "Contact with sulphur compounds in the air"),
        ("Corrosion of copper in damp air", "Reaction with moisture, carbon dioxide and oxygen to give a green basic carbonate"),
        ("Rancidity of food containing fats and oils", "Exposure to air, which slowly oxidises the fats"),
        ("Preventing rancidity in a packet of chips", "Flushing the packet with nitrogen and sealing it"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 4 - Carbon and its Compounds
    # ══════════════════════════════════════════════════════════════════
    ("sci-chem-ch4.bonding", "type of bond in", [
        ("A molecule of hydrogen, H2", "One single covalent bond"),
        ("A molecule of oxygen, O2", "One double covalent bond"),
        ("A molecule of nitrogen, N2", "One triple covalent bond"),
        ("A molecule of methane, CH4", "Four single covalent bonds"),
        ("A molecule of ethane, C2H6", "Seven single covalent bonds, one of them joining the two carbon atoms"),
        ("A molecule of ethene, C2H4", "One double bond between the carbon atoms and four single bonds to hydrogen"),
        ("A molecule of ethyne, C2H2", "One triple bond between the carbon atoms and two single bonds to hydrogen"),
        ("A crystal of sodium chloride", "Ionic bonds, formed by the transfer rather than the sharing of electrons"),
    ], "medium"),

    ("sci-chem-ch4.bonding", "typical behaviour of", [
        ("Covalent compounds on heating", "Melting and boiling at fairly low temperatures, because the forces between molecules are weak"),
        ("Covalent compounds in water", "Generally not dissolving, since they carry no charge"),
        ("Covalent compounds in an electric circuit", "Not conducting, because there are no ions to carry the current"),
        ("Carbon when it combines with other elements", "Sharing its four valence electrons rather than losing or gaining them"),
        ("Carbon with itself", "Linking into long chains, branched chains and rings, which is called catenation"),
        ("An ionic compound in water", "Dissolving and then conducting the current"),
    ], "medium"),

    ("sci-chem-ch4.bonding", "explanation for", [
        ("The very large number of carbon compounds", "Catenation together with tetravalency"),
        ("The stability of long carbon chains", "The carbon-carbon bond being strong enough to hold them together"),
        ("The absence of ions in most carbon compounds", "Carbon sharing its four valence electrons rather than losing or gaining them"),
        ("Diamond and graphite behaving so differently", "The different ways in which their carbon atoms are bonded together"),
    ], "hard"),

    ("sci-chem-ch4.bonding", "use of", [
        ("Diamond", "Cutting tools, drill bits, and jewellery"),
        ("Graphite", "Pencil leads, electrodes and a dry lubricant"),
        ("Coke", "A reducing agent in extracting metals, and a fuel"),
        ("Charcoal", "Adsorbing gases and colouring matter, and burning as a smokeless fuel"),
        ("Activated charcoal", "Filtering water and trapping gases in a mask"),
        ("Lamp black", "A black pigment in ink and paint"),
        ("Fullerene", "Research, because its molecules form closed cages of carbon atoms"),
    ], "medium"),

    ("sci-chem-ch4.functional-groups", "suffix in the name of", [
        ("An alkane", "-ane"),
        ("An alkene", "-ene"),
        ("An alkyne", "-yne"),
        ("An alcohol", "-ol"),
        ("An aldehyde", "-al"),
        ("A ketone", "-one"),
        ("A carboxylic acid", "-oic acid"),
    ], "easy", True),

    ("sci-chem-ch4.nomenclature", "root word for", [
        ("A carbon chain of one atom", "meth-"),
        ("A carbon chain of two atoms", "eth-"),
        ("A carbon chain of three atoms", "prop-"),
        ("A carbon chain of four atoms", "but-"),
        ("A carbon chain of five atoms", "pent-"),
        ("A carbon chain of six atoms", "hex-"),
        ("A carbon chain of seven atoms", "hept-"),
        ("A carbon chain of eight atoms", "oct-"),
    ], "easy", True),

    ("sci-chem-ch4.nomenclature", "prefix for", [
        ("Chlorine taking the place of a hydrogen in the chain", "chloro-"),
        ("Bromine taking the place of a hydrogen in the chain", "bromo-"),
        ("An iodine atom taking the place of a hydrogen in the chain", "iodo-"),
    ], "medium", True),

    ("sci-chem-ch4.nomenclature", "molecular formula of", [
        ("Propane", "C3H8"),
        ("Butane", "C4H10"),
        ("Pentane", "C5H12"),
        ("Hexane", "C6H14"),
        ("Propene", "C3H6"),
        ("Butene", "C4H8"),
        ("Propyne", "C3H4"),
        ("Butyne", "C4H6"),
        ("Methanol", "CH3OH"),
        ("Propanol", "C3H7OH"),
        ("Ethanal", "CH3CHO"),
        ("Propanone", "CH3COCH3"),
        ("Methanoic acid", "HCOOH"),
        ("Propanoic acid", "C2H5COOH"),
        ("Benzene", "C6H6"),
        ("Cyclohexane", "C6H12"),
    ], "medium", True),

    ("sci-chem-ch4.homologous", "difference between consecutive members of", [
        ("A homologous series in molecular formula", "CH2"),
        ("A homologous series in molecular mass", "14 u"),
        ("A homologous series in the number of carbon atoms", "One"),
        ("A homologous series in chemical properties", "Hardly any, because the same functional group is present throughout"),
        ("A homologous series in physical properties", "A regular gradation as the molecular mass increases"),
    ], "medium"),

    ("sci-chem-ch4.homologous", "second member of", [
        ("The alkane series", "Ethane, C2H6"),
        ("The alkene series", "Propene, C3H6"),
        ("The alkyne series", "Propyne, C3H4"),
        ("The alcohol series", "Ethanol, C2H5OH"),
        ("The carboxylic acid series", "Ethanoic acid, CH3COOH"),
        ("The aldehyde series", "Ethanal, CH3CHO"),
    ], "medium"),

    ("sci-chem-ch4.properties", "reaction of", [
        ("Methane burnt in plenty of air", "Complete combustion, giving a clean blue flame, carbon dioxide and water"),
        ("An unsaturated hydrocarbon heated with hydrogen over nickel", "An addition reaction, in which the double or triple bond is saturated"),
        ("Ethene added to bromine water", "Decolourising it, which is the standard test for unsaturation"),
        ("A saturated hydrocarbon left with chlorine in sunlight", "A substitution reaction, in which chlorine replaces hydrogen atom by atom"),
        ("Ethanol warmed with ethanoic acid in the presence of concentrated sulphuric acid", "Esterification, giving a sweet-smelling ester"),
        ("Ethanol heated with concentrated sulphuric acid at 443 K", "Dehydration, giving ethene"),
        ("Ethanol dropped onto sodium metal", "Giving sodium ethoxide and hydrogen, which burns with a pop"),
        ("Ethanoic acid added to sodium hydrogen carbonate", "Giving sodium ethanoate, water and carbon dioxide, which turns lime water milky"),
        ("Ethanoic acid added to sodium hydroxide", "A neutralisation, giving sodium ethanoate and water"),
        ("An ester boiled with sodium hydroxide", "Saponification, giving back the alcohol and the sodium salt of the acid"),
        ("Ethanoic acid cooled below 290 K", "Freezing into an ice-like solid, which is why the pure acid is called glacial acetic acid"),
    ], "hard"),

    ("sci-chem-ch4.properties", "flame of", [
        ("A saturated hydrocarbon such as methane burnt in plenty of air", "Clean and blue, because combustion is complete"),
        ("An unsaturated hydrocarbon burnt in air", "Sooty and yellow, because combustion is incomplete"),
        ("Camphor burnt in air", "Very sooty, since it has a high proportion of carbon"),
        ("Benzene burnt in air", "Smoky, with much unburnt carbon escaping"),
        ("Ethanol burnt in air", "Blue and without soot, giving carbon dioxide and water"),
    ], "medium"),

    ("sci-chem-ch4.soaps", "behaviour in water of", [
        ("The long hydrocarbon tail of a soap molecule", "Repelling water and attaching itself to oil and grease, so it is called hydrophobic"),
        ("The ionic end of a soap molecule", "Dissolving in water and pointing outward, so it is called hydrophilic"),
        ("Soap molecules surrounding a drop of oil", "Arranging into a spherical cluster called a micelle, with the tails inside and the heads outside"),
        ("A micelle carrying trapped oil", "Staying suspended in water, since its outer surface is charged and the micelles repel one another"),
        ("Soap in water that contains calcium and magnesium ions", "Reacting with them to form an insoluble scum instead of a lather"),
        ("A detergent in water that contains calcium and magnesium ions", "Still lathering and cleansing, because its calcium and magnesium salts remain soluble"),
    ], "hard"),

    ("sci-chem-ch4.soaps", "effect of", [
        ("Calcium and magnesium ions in hard water", "Formation of an insoluble scum with soap, which wastes the soap"),
        ("Using a detergent instead of soap in hard water", "Normal lathering and cleansing, with no scum"),
        ("Adding common salt during soap making", "Separating the soap out of the solution, so that it floats and can be collected"),
        ("Agitating cloth with soap and water", "Lifting oily dirt into micelles so that it rinses away"),
        ("Using very soft water for washing", "Soap lathering freely, with none wasted on forming scum"),
    ], "medium"),
]


DEFINITIONS = [
    ("sci-chem-ch1.equations", [
        ("Skeletal chemical equation", "An unbalanced equation that gives the formulas of the reactants and products but not the correct number of each."),
        ("Word equation", "An equation written with the names of the reactants and products instead of their chemical formulas."),
        ("Precipitate", "An insoluble solid that separates out of a solution during a chemical reaction."),
        ("Thermal decomposition", "The breaking up of a compound into simpler substances when it is heated."),
        ("Electrolytic decomposition", "The breaking up of a compound into simpler substances by passing an electric current through it."),
        ("Photochemical decomposition", "The breaking up of a compound into simpler substances when it is exposed to light."),
    ], "medium"),

    ("sci-chem-ch2.acids", [
        ("Mineral acid", "An acid obtained from minerals of the earth rather than from living things, such as hydrochloric, sulphuric or nitric acid."),
        ("Organic acid", "An acid produced by plants or animals, such as citric acid, acetic acid or lactic acid."),
        ("Dilution of an acid", "Adding water to concentrated acid slowly and with stirring, while the mixture warms because the process is exothermic."),
    ], "medium"),

    ("sci-chem-ch2.bases", [
        ("Basic oxide", "An oxide, usually of a metal, that reacts with an acid to give a salt and water."),
        ("Acidic oxide", "An oxide, usually of a non-metal, that reacts with a base to give a salt and water."),
        ("Antacid", "A mild base taken to neutralise the excess acid in the stomach and relieve indigestion."),
    ], "medium"),

    ("sci-chem-ch2.compounds", [
        ("Chlor-alkali process", "The electrolysis of brine, in which sodium chloride solution gives sodium hydroxide along with chlorine at the anode and hydrogen at the cathode."),
        ("Neutral salt", "A salt formed by a strong acid and a strong base, whose solution in water has a pH close to seven."),
        ("Acidic salt", "A salt whose solution in water turns blue litmus red, formed when a strong acid is only partly neutralised."),
    ], "medium"),

    ("sci-chem-ch3.properties", [
        ("Lustre", "The shine on the freshly cut surface of a metal, caused by the way it reflects light."),
        ("Brittleness", "The tendency of a substance to break into pieces rather than bend when it is struck, which is typical of non-metals."),
        ("Anodising", "A process in which a clean aluminium article is made the anode and electrolysed so that a thicker protective oxide layer forms on it."),
    ], "medium"),

    ("sci-chem-ch3.extraction", [
        ("Metallurgy", "The set of operations by which a metal is obtained from its ore and then purified."),
        ("Concentration of ore", "The removal of as much of the gangue as possible from the mined ore before it is heated."),
        ("Flux", "A substance added during smelting that combines with the gangue to form a fusible slag which can be removed."),
        ("Slag", "The fusible mass formed when the flux reacts with the gangue, which floats on the molten metal and is drawn off."),
        ("Electrolytic refining", "The purification of a metal in which the impure metal is the anode, a thin strip of the pure metal is the cathode, and a salt of the metal is the electrolyte."),
        ("Anode mud", "The insoluble impurities that settle below the anode during the electrolytic refining of a metal."),
        ("Smelting", "The reduction of a metal oxide to the free metal by heating it strongly with a reducing agent such as coke."),
    ], "medium"),

    ("sci-chem-ch3.ionic", [
        ("Ionic compound", "A compound made up of ions held together by strong electrostatic forces, formed by the complete transfer of electrons from a metal to a non-metal."),
        ("Electrovalent bond", "Another name for an ionic bond, emphasising that it is formed by the transfer of valence electrons."),
        ("Cation", "A positively charged ion formed when an atom loses one or more electrons."),
        ("Anion", "A negatively charged ion formed when an atom gains one or more electrons."),
    ], "easy"),

    ("sci-chem-ch3.reactivity", [
        ("Displacement of a metal", "The replacement of a less reactive metal in its salt solution by a more reactive metal, which is how the reactivity series is confirmed."),
    ], "medium"),

    ("sci-chem-ch3.alloys", [
        ("Duralumin", "An alloy of aluminium with copper, magnesium and manganese, which is light and strong and is used in aircraft bodies."),
        ("Stainless steel", "An alloy of iron with chromium, nickel and a little carbon, which resists corrosion and is used for cutlery and surgical instruments."),
        ("Solder", "An alloy of lead and tin with a low melting point, used for joining electrical wires."),
    ], "medium"),

    ("sci-chem-ch4.bonding", [
        ("Covalent compound", "A compound whose atoms are joined by shared pairs of electrons, and which therefore has no ions to conduct a current."),
        ("Electron dot structure", "A representation of a molecule in which only the valence electrons of each atom are shown as dots around its symbol."),
        ("Allotrope", "One of two or more different physical forms of the same element, such as diamond, graphite and fullerene for carbon."),
        ("Catenation", "The property of an element, seen most strongly in carbon, of forming bonds with atoms of the same element to give chains, branches and rings."),
    ], "medium"),

    ("sci-chem-ch4.functional-groups", [
        ("Heteroatom", "An atom other than carbon or hydrogen in the chain of an organic compound, which along with the functional group gives the compound its properties."),
        ("Alcohol", "An organic compound containing a hydroxyl group attached to a carbon chain, named with the suffix -ol."),
        ("Aldehyde", "An organic compound containing a -CHO group at the end of a carbon chain, named with the suffix -al."),
        ("Ketone", "An organic compound in which a carbonyl group is attached to two carbon atoms, named with the suffix -one."),
        ("Carboxylic acid", "An organic compound containing a -COOH group, named with the suffix -oic acid and weakly acidic in water."),
        ("Alkane", "A saturated hydrocarbon in which every carbon-carbon bond is single, following the general formula CnH2n+2."),
        ("Alkene", "An unsaturated hydrocarbon containing one carbon-carbon double bond, following the general formula CnH2n."),
        ("Alkyne", "An unsaturated hydrocarbon containing one carbon-carbon triple bond, following the general formula CnH2n-2."),
    ], "easy"),

    ("sci-chem-ch4.nomenclature", [
        ("IUPAC name", "The systematic name of a compound, built from a root word for the length of the carbon chain, a prefix for any substituent and a suffix for the functional group."),
        ("Structural formula", "A way of writing a compound that shows how its atoms are bonded to one another, rather than only how many of each there are."),
    ], "medium"),

    ("sci-chem-ch4.homologous", [
        ("Homolog", "Any one member of a homologous series, differing from the next by a CH2 unit and by fourteen units of molecular mass."),
    ], "easy"),

    ("sci-chem-ch4.properties", [
        ("Addition reaction", "A reaction in which atoms are added to an unsaturated compound across its double or triple bond, converting it into a saturated one."),
        ("Substitution reaction", "A reaction in which one atom or group in a saturated compound is replaced by another, such as hydrogen being replaced by chlorine in sunlight."),
        ("Combustion", "The burning of a substance in air or oxygen with the release of heat and light."),
        ("Complete combustion", "The burning of a carbon compound in enough air to give only carbon dioxide and water, with a clean blue flame."),
    ], "medium"),

    ("sci-chem-ch4.soaps", [
        ("Soap", "A sodium or potassium salt of a long-chain fatty acid, whose molecule has a water-repelling hydrocarbon tail and a water-attracting ionic head."),
        ("Hydrophobic end", "The long hydrocarbon tail of a soap molecule, which repels water and attaches to oil and grease."),
        ("Hydrophilic end", "The ionic end of a soap molecule, which dissolves in water and faces outward in a micelle."),
        ("Scum", "The insoluble calcium or magnesium salt that soap forms in hard water, which settles as a sticky deposit and wastes the soap."),
        ("Hard water", "Water that contains salts of calcium and magnesium, so that soap does not lather in it until those salts are removed."),
    ], "medium"),
]
