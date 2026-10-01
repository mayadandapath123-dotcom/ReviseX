"""Biology clusters - Class 10 Science, chapters 5, 6, 7, 8 and 13.

Life Processes, Control and Coordination, How Do Organisms Reproduce, Heredity,
and Our Environment. Four of these five chapters were below a hundred questions,
and biology is the branch where attribute clustering works best: organs and their
functions, glands and their hormones, defects and their corrections are all
naturally sets of four or more siblings sharing one attribute.
"""

from __future__ import annotations

FACTS = [
    # ══════════════════════════════════════════════════════════════════
    # Chapter 5 - Life Processes
    # ══════════════════════════════════════════════════════════════════
    ("sci-bio-life.nutrition", "function of", [
        ("Stomata", "Exchange of gases and loss of water as vapour"),
        ("Guard cells", "Opening and closing of the stomatal pore"),
        ("Chlorophyll", "Absorbing light energy during photosynthesis"),
        ("Root hairs", "Absorbing water and minerals from the soil"),
        ("Salivary amylase", "Breaking starch down into simpler sugars in the mouth"),
        ("Pepsin", "Digesting proteins in an acidic medium"),
        ("Trypsin", "Digesting proteins in the alkaline medium of the small intestine"),
        ("Lipase", "Digesting fats"),
        ("Bile juice", "Emulsifying large fat globules into smaller ones"),
        ("Villi of the small intestine", "Increasing the surface area for absorption of digested food"),
        ("Mucus lining the stomach", "Protecting the inner wall from hydrochloric acid"),
    ], "easy"),

    ("sci-bio-life.nutrition", "occurs in", [
        ("Photosynthesis", "Chloroplasts of green plant cells"),
        ("Glycolysis, the first step of glucose breakdown", "The cytoplasm of the cell"),
        ("Complete oxidation of pyruvate", "The mitochondria"),
        ("Fermentation producing ethanol and carbon dioxide", "Yeast cells, in the absence of oxygen"),
        ("Formation of lactic acid", "Muscle cells during a shortage of oxygen"),
        ("Digestion of fats", "The small intestine, aided by bile and lipase"),
        ("Absorption of digested food", "The villi of the small intestine"),
        ("Absorption of water from undigested food", "The large intestine"),
    ], "medium"),

    ("sci-bio-life.nutrition", "example of", [
        ("Holozoic nutrition", "Human beings and amoeba"),
        ("Autotrophic nutrition", "Green plants"),
        ("Saprophytic nutrition", "Fungi, yeast and many bacteria"),
        ("Parasitic nutrition", "Cuscuta, ticks, leeches and tapeworms"),
        ("A holozoic feeder taking in solid food", "An amoeba engulfing food with pseudopodia"),
    ], "medium"),

    ("sci-bio-life.respiration", "produces", [
        ("Aerobic respiration of one glucose molecule", "Carbon dioxide, water and 38 ATP molecules"),
        ("Anaerobic respiration in yeast", "Ethanol, carbon dioxide and only 2 ATP molecules"),
        ("Anaerobic respiration in human muscle", "Lactic acid and a small amount of energy"),
        ("Breakdown of glucose in the cytoplasm", "Pyruvate, a three-carbon compound"),
        ("Exchange of gases in the alveoli", "Oxygen entering blood and carbon dioxide leaving it"),
    ], "medium"),

    ("sci-bio-life.respiration", "term for", [
        ("The energy currency of the cell", "ATP"),
        ("The respiratory pigment in humans", "Haemoglobin"),
        ("The balloon-like sacs where gases are exchanged", "Alveoli"),
        ("The muscle that changes thoracic cavity volume", "Diaphragm"),
        ("Breathing rate in aquatic animals", "Much faster than in terrestrial animals"),
    ], "easy"),

    ("sci-bio-life.transport", "carries", [
        ("Xylem tissue", "Water and minerals absorbed by the roots"),
        ("Phloem tissue", "Food synthesised in the leaves, to all other parts"),
        ("Arteries", "Blood away from the heart, under high pressure"),
        ("Veins", "Blood towards the heart, through valves that prevent backflow"),
        ("Capillaries", "Exchange of materials between blood and surrounding cells"),
        ("Platelets", "Clotting of blood at the site of an injury"),
        ("Lymph", "Digested and absorbed fat, and drained excess fluid from tissues"),
        ("Red blood cells", "Oxygen, carried by haemoglobin"),
        ("White blood cells", "Defence against infection"),
    ], "easy"),

    ("sci-bio-life.transport", "receives", [
        ("The right atrium", "Deoxygenated blood returning from the body"),
        ("The right ventricle", "Deoxygenated blood from the right atrium"),
        ("The left atrium", "Oxygenated blood from the lungs"),
        ("The left ventricle", "Oxygenated blood, which it pumps to the whole body"),
        ("The lungs", "Deoxygenated blood for release of carbon dioxide"),
    ], "medium"),

    ("sci-bio-life.transport", "found in", [
        ("A single circulatory passage through the heart", "Fish"),
        ("An incompletely divided three-chambered heart", "Amphibians and reptiles"),
        ("A four-chambered heart with complete separation", "Birds and mammals"),
        ("Double circulation", "Human beings, where blood passes through the heart twice in one cycle"),
        ("The thickest muscular wall", "The left ventricle"),
    ], "medium"),

    ("sci-bio-life.excretion", "performed by", [
        ("Removal of nitrogenous waste from blood", "The kidneys"),
        ("Filtration of blood under pressure", "The glomerulus"),
        ("Collection of the filtrate", "Bowman's capsule"),
        ("Selective reabsorption of glucose and water", "The tubular part of the nephron"),
        ("Removal of waste in unicellular organisms", "Diffusion through the cell membrane"),
        ("Excretion in plants", "Falling leaves, resin and gum, and storage in vacuoles"),
    ], "easy"),

    ("sci-bio-life.excretion", "term for", [
        ("The functional unit of the kidney", "Nephron"),
        ("The cup-shaped end of a nephron", "Bowman's capsule"),
        ("The ball of capillaries inside Bowman's capsule", "Glomerulus"),
        ("Artificial removal of waste from blood", "Haemodialysis"),
        ("The main nitrogenous waste in humans", "Urea"),
    ], "easy"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 6 - Control and Coordination
    # ══════════════════════════════════════════════════════════════════
    ("sci-bio-control.nervous", "controls", [
        ("The cerebrum", "Thinking, memory, voluntary actions and sensory perception"),
        ("The cerebellum", "Posture, balance and the precision of voluntary movement"),
        ("The medulla", "Involuntary actions such as blood pressure, salivation and vomiting"),
        ("The hypothalamus", "Hunger, thirst, sleep and body temperature"),
        ("The spinal cord", "Reflex actions, and carrying signals between brain and body"),
        ("The pons", "Regulation of respiration"),
    ], "easy"),

    ("sci-bio-control.nervous", "term for", [
        ("The basic unit of the nervous system", "Neuron"),
        ("The gap between two neurons", "Synapse"),
        ("The part of a neuron that receives information", "Dendrite"),
        ("The part of a neuron that conducts an impulse away from the cell body", "Axon"),
        ("The path taken by a reflex action", "Reflex arc"),
        ("Nerves arising from the brain", "Cranial nerves, of which there are 12 pairs"),
        ("Nerves arising from the spinal cord", "Spinal nerves, of which there are 31 pairs"),
        ("The part of the nervous system controlling internal organs involuntarily", "Autonomic nervous system"),
        ("The brain and spinal cord together", "Central nervous system"),
    ], "easy"),

    ("sci-bio-control.reflex", "example of", [
        ("A reflex action", "Pulling a hand away from a hot object before feeling pain"),
        ("A voluntary action", "Deciding to write or to chew food"),
        ("An involuntary action", "Salivation, vomiting and the movement of food in the alimentary canal"),
        ("A reflex centred in the spinal cord", "Knee-jerk response"),
        ("The protective value of a reflex", "Responding to danger faster than thought allows"),
    ], "medium"),

    ("sci-bio-control.hormones", "secreted by", [
        ("Insulin", "The pancreas"),
        ("Thyroxine", "The thyroid gland"),
        ("Adrenaline", "The adrenal gland"),
        ("Growth hormone", "The pituitary gland"),
        ("Testosterone", "The testes"),
        ("Oestrogen", "The ovaries"),
    ], "easy"),

    ("sci-bio-control.hormones", "function of", [
        ("Insulin", "Regulating the level of sugar in the blood"),
        ("Thyroxine", "Regulating the metabolism of carbohydrates, proteins and fats"),
        ("Adrenaline", "Preparing the body for stress by raising heart rate and breathing"),
        ("Growth hormone", "Growth and development of the body"),
        ("Testosterone", "Development of male secondary sexual characters"),
        ("Oestrogen", "Development of female secondary sexual characters"),
    ], "easy"),

    ("sci-bio-control.hormones", "caused by", [
        ("Goitre", "A deficiency of iodine in the diet"),
        ("Diabetes", "Insufficient secretion of insulin"),
        ("Dwarfism", "Insufficient secretion of growth hormone in childhood"),
        ("Gigantism", "Excess secretion of growth hormone in childhood"),
        ("Cretinism", "Deficiency of thyroxine in children, causing stunted growth and low intelligence"),
        ("Increased heart rate and blood supply to muscles", "Release of adrenaline in a frightening situation"),
    ], "medium"),

    ("sci-bio-control.plants", "function of", [
        ("Auxin", "Cell elongation and growth of the shoot towards light"),
        ("Gibberellin", "Stem elongation and helping seeds to germinate"),
        ("Cytokinin", "Cell division and delaying the ageing of leaves"),
        ("Abscisic acid", "Inhibiting growth, causing wilting and promoting seed dormancy"),
        ("Ethylene", "Ripening of fruits"),
    ], "easy"),

    ("sci-bio-control.plants", "term for", [
        ("Growth of a shoot towards light", "Phototropism"),
        ("Growth of a root towards gravity", "Positive geotropism"),
        ("Growth of a pollen tube towards the ovule", "Chemotropism"),
        ("Growth of a root towards water", "Hydrotropism"),
        ("Movement of a tendril around a support", "Thigmotropism"),
        ("Rapid non-directional folding of Mimosa pudica leaves on touch", "A nastic movement"),
        ("Chemicals used by plants for coordination", "Phytohormones"),
    ], "medium"),

    ("sci-bio-control.plants", "explained by", [
        ("Coordination in plants without a nervous system", "Chemical signalling by hormones and electrical signals via ion movement"),
        ("Bending of a shoot towards light", "Auxin accumulating on the shaded side and elongating those cells"),
        ("Slower response in plants than in animals", "Plant responses are growth-based rather than muscle-based"),
        ("Non-directional response to touch", "Change in the amount of water in cells, as in Mimosa"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 8 - Heredity
    # ══════════════════════════════════════════════════════════════════
    ("sci-bio-heredity.mendel", "used by", [
        ("The plant Mendel worked on", "The garden pea, Pisum sativum"),
        ("A contrasting pair of characters Mendel studied", "Tall stem and dwarf stem"),
        ("Another contrasting pair Mendel studied", "Round seeds and wrinkled seeds"),
        ("A seed colour pair Mendel studied", "Yellow and green"),
        ("A flower colour pair Mendel studied", "Violet and white"),
        ("The scientist called the father of genetics", "Gregor Johann Mendel"),
        ("The number of pairs of contrasting characters Mendel studied", "Seven"),
    ], "easy"),

    ("sci-bio-heredity.mendel", "ratio of", [
        ("Phenotypes in the F2 generation of a monohybrid cross", "3 : 1"),
        ("Genotypes in the F2 generation of a monohybrid cross", "1 : 2 : 1"),
        ("Phenotypes in the F2 generation of a dihybrid cross", "9 : 3 : 3 : 1"),
        ("Traits visible in the F1 generation", "Only the dominant trait"),
        ("Traits reappearing in the F2 generation", "The recessive trait, in one quarter"),
    ], "medium"),

    ("sci-bio-heredity.mendel", "concluded that", [
        ("Characters in the F1 generation", "One form dominated over the other"),
        ("Characters disappearing in F1", "Were present but not expressed, and reappeared in F2"),
        ("Each parent's contribution", "Two copies of a factor, of which only one passes to a gamete"),
        ("Inheritance of two characters together", "Occurred independently of each other"),
        ("The basis of a trait", "A factor, now called a gene"),
    ], "hard"),

    ("sci-bio-heredity.terms", "means", [
        ("Heredity", "The transmission of characters from parents to offspring"),
        ("Variation", "Differences in characters among individuals of a species"),
        ("Gene", "A unit of inheritance, a segment of DNA on a chromosome"),
        ("Allele", "One of the alternative forms of a gene"),
        ("Dominant trait", "The trait expressed in the F1 generation"),
        ("Recessive trait", "The trait suppressed in F1 and reappearing in F2"),
        ("Genotype", "The genetic constitution of an individual"),
        ("Phenotype", "The observable characteristics of an individual"),
        ("Homozygous", "Having two identical alleles, such as TT or tt"),
        ("Heterozygous", "Having two different alleles, such as Tt"),
        ("Acquired trait", "A trait developed during a lifetime and not passed on to offspring"),
    ], "easy"),

    # TT, Tt and tt differ only by case, and case is the whole distinction:
    # homozygous dominant, heterozygous and homozygous recessive. Folding case
    # would collapse three answers into one, so this cluster opts out.
    ("sci-bio-heredity.terms", "example of", [
        ("An acquired trait", "Weight gained through diet, or muscle built by exercise"),
        ("An inherited trait", "Colour of eyes, or the ability to roll the tongue"),

        ("Homologous organs", "The forelimbs of a frog, a lizard, a bird and a human"),
        ("Analogous organs", "The wings of a bird and the wings of an insect"),
        ("Evidence of evolution from preserved traces", "Fossils"),
    ], "medium"),

    # TT, Tt and tt differ only by case, and case is the whole distinction:
    # homozygous dominant, heterozygous and homozygous recessive. The generator
    # folds case before comparing options, so this cluster opts out of that. The
    # attribute says "written as" because "example of" would ask the question
    # backwards - the subject here is the description and the value the notation.
    ("sci-bio-heredity.terms", "written as", [
        ("A homozygous tall genotype", "TT"),
        ("A heterozygous tall genotype", "Tt"),
        ("A homozygous dwarf genotype", "tt"),
        ("A homozygous round-seed genotype", "RR"),
        ("A heterozygous round-seed genotype", "Rr"),
        ("A homozygous wrinkled-seed genotype", "rr"),
    ], "medium", True),

    ("sci-bio-heredity.terms", "proposed by", [
        ("The theory of evolution by natural selection", "Charles Darwin, in On the Origin of Species"),
        ("Tracing relationships from differences in DNA sequences", "Molecular phylogeny"),
        ("Homologous organs as evidence", "Common ancestry despite different functions"),
        ("Analogous organs as evidence", "Convergence, not common ancestry"),
    ], "hard"),

    ("sci-bio-heredity.sex", "determined by", [
        ("Sex in human beings", "The sex chromosome inherited from the father"),
        ("A male's sex chromosomes", "XY"),
        ("A female's sex chromosomes", "XX"),
        ("An egg cell's sex chromosome", "Always X"),
        ("A sperm cell's sex chromosome", "Either X or Y"),
        ("The total number of chromosomes in a human body cell", "46, in 23 pairs"),
        ("The number of autosomes in a human body cell", "22 pairs"),
        ("The number of chromosomes in a human gamete", "23"),
        ("The number of chromosomes in a human zygote", "46"),
    ], "easy"),

    ("sci-bio-heredity.sex", "explained by", [
        ("Every child having a 50 per cent chance of being a boy", "Half the sperm carry Y and half carry X"),
        ("Parents not being responsible for the sex of a child", "The sperm, not the egg, decides it"),
        ("Halving of chromosomes in gametes", "So the zygote restores the species number"),
        ("Variation being important for survival", "It allows a species to adapt to a changing environment"),
        ("Asexual reproduction producing little variation", "Only one parent contributes DNA"),
    ], "hard"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 13 - Our Environment
    # ══════════════════════════════════════════════════════════════════
    ("sci-bio-env.ecosystem", "role of", [
        ("A producer", "Green plants that make their own food by photosynthesis"),
        ("A consumer", "An organism that depends on producers, directly or indirectly"),
        ("A decomposer", "Bacteria and fungi that break down dead organic matter"),
        ("A herbivore", "An animal that feeds on plants"),
        ("A carnivore", "An animal that feeds on the flesh of other animals"),
        ("An omnivore", "An animal that eats both plants and animals"),
        ("Scavengers", "Animals that feed on dead bodies, such as vultures and crows"),
        ("Abiotic components", "Sunlight, temperature, water, soil and air"),
    ], "easy"),

    ("sci-bio-env.ecosystem", "term for", [
        ("A self-sustaining system of living and non-living components", "Ecosystem"),
        ("A series of organisms feeding on one another", "Food chain"),
        ("A network of interconnected food chains", "Food web"),
        ("The position of an organism in a food chain", "Trophic level"),
        ("The flow of energy in an ecosystem", "Unidirectional, from producers to higher levels"),
        ("The ultimate source of energy for an ecosystem", "The Sun"),
    ], "easy"),

    ("sci-bio-env.energy-flow", "stated by", [
        ("The ten per cent law", "Only about ten per cent of energy passes to the next trophic level"),
        ("The scientist who proposed the ten per cent law", "Lindeman"),
        ("The fate of the remaining ninety per cent", "Lost as heat, or used in the organism's own life processes"),
        ("The usual maximum number of trophic levels", "Three or four, because so little energy remains"),
        ("Energy entering producers", "About one per cent of the sunlight falling on them"),
        ("The direction of energy flow", "One way, from the Sun through producers to consumers"),
    ], "medium"),

    ("sci-bio-env.energy-flow", "explained by", [
        ("Fewer organisms at higher trophic levels", "Progressive loss of energy between levels"),
        ("Why food chains are short", "Energy available becomes too small to support more levels"),
        ("Why harmful chemicals concentrate at the top", "Biological magnification along the food chain"),
        ("Why the flow of energy is one-way", "Energy lost as heat cannot be reused by producers"),
    ], "hard"),

    # Every value is distinct. Two subjects sharing the value "Biodegradable"
    # would collapse the pool for both: with fewer than three distinct siblings
    # the generator cannot build options and drops the item entirely, and reverse
    # recall ("which is biodegradable?") has no single answer to point at.
    ("sci-bio-env.waste", "classified as", [
        ("Paper, vegetable peel and fruit waste", "Biodegradable, broken down by microorganisms"),
        ("Plastic, glass and metals", "Non-biodegradable, persisting in the environment"),
        ("DDT and BHC pesticides", "Non-biodegradable, and magnified along food chains"),
        ("Cotton cloth and wood", "Biodegradable and suitable for composting"),
        ("Polythene bags and aluminium foil", "Non-biodegradable, best avoided at source"),
        ("Sewage and animal dung", "Biodegradable, and usable in a biogas plant"),
    ], "easy"),

    ("sci-bio-env.waste", "caused by", [
        ("Ozone in the upper atmosphere", "Protection of living organisms from ultraviolet radiation"),
        ("Depletion of the ozone layer", "Chlorofluorocarbons used in refrigeration and aerosols"),
        ("The location of the ozone layer", "The stratosphere"),
        ("The chemical formula of ozone", "O3"),
        ("Biological magnification", "Accumulation of non-biodegradable chemicals at higher trophic levels"),
        ("Landfill problems", "Leachate contaminating groundwater and generating methane"),
    ], "medium"),

    ("sci-bio-env.waste", "managed by", [
        ("Kitchen and garden waste", "Composting, or biogas plants"),
        ("Plastic and metal waste", "Recycling"),
        ("Mixed municipal waste", "Segregation at source into biodegradable and non-biodegradable"),
        ("Hospital and laboratory waste", "Incineration under controlled conditions"),
        ("Reducing waste volume", "The three R's: reduce, reuse and recycle"),
        ("World Environment Day", "Celebrated on 5 June every year"),
    ], "medium"),
]

DEFINITIONS = [
    ("sci-bio-life.nutrition", [
        ("Nutrition", "The process by which an organism takes in food and uses it for growth, repair and energy."),
        ("Photosynthesis", "The process by which green plants make their own food from carbon dioxide and water using sunlight and chlorophyll."),
        ("Transpiration", "The loss of water as vapour from the aerial parts of a plant, mainly through stomata."),
        ("Translocation", "The transport of soluble products of photosynthesis through the phloem."),
        ("Digestion", "The breakdown of complex food substances into simpler, absorbable forms."),
        ("Emulsification", "The breaking of large fat globules into smaller droplets so that enzymes can act on them."),
        ("Peristalsis", "The rhythmic contraction and relaxation of the alimentary canal that pushes food forward."),
        ("Life processes", "The basic functions an organism must perform to stay alive: nutrition, respiration, transport and excretion."),
        ("Respiration", "The process of releasing energy from food by breaking down glucose."),
        ("Breathing", "The physical exchange of gases between an organism and its surroundings."),
    ], "easy"),

    ("sci-bio-life.transport", [
        ("Double circulation", "The passage of blood through the heart twice in one complete cycle, once to the lungs and once to the body."),
        ("Blood pressure", "The force exerted by flowing blood on the walls of blood vessels."),
        ("Systolic pressure", "The pressure in the arteries when the ventricles contract."),
        ("Diastolic pressure", "The pressure in the arteries when the ventricles relax."),
        ("Excretion", "The removal of harmful metabolic waste from the body."),
        ("Osmoregulation", "The control of the amount of water and salts in the body."),
    ], "medium"),

    ("sci-bio-control.nervous", [
        ("Stimulus", "A change in the environment detected by a receptor."),
        ("Receptor", "A specialised structure that detects a stimulus and starts a nerve impulse."),
        ("Effector", "A muscle or gland that responds to a nerve impulse."),
        ("Nerve impulse", "An electrochemical signal travelling along a neuron."),
        ("Reflex action", "A sudden, involuntary response to a stimulus that does not involve the thinking part of the brain."),
        ("Neurotransmitter", "A chemical that carries a signal across the synapse to the next neuron."),
        ("Coordination", "The working together of different parts of the body to produce an organised response."),
        ("Hormone", "A chemical messenger secreted by an endocrine gland and carried by blood to a target organ."),
        ("Endocrine gland", "A ductless gland that secretes hormones directly into the blood."),
        ("Feedback mechanism", "A process by which the secretion of a hormone is regulated by its own effect."),
    ], "easy"),

    ("sci-bio-heredity.terms", [
        ("Evolution", "The gradual change in the inherited characteristics of a population over generations."),
        ("Speciation", "The formation of a new species from an existing one."),
        ("Natural selection", "The survival and reproduction of individuals better suited to their environment."),
        ("Fossil", "The preserved trace or remains of a living organism from a past geological age."),
        ("Gene", "A segment of DNA that codes for one protein and controls one characteristic."),
        ("DNA", "Deoxyribonucleic acid, the molecule in a cell that carries hereditary information."),
        ("Chromosome", "A thread-like structure in the nucleus carrying genes, made of DNA and protein."),
        ("Sex chromosome", "A chromosome that determines the sex of an individual; X or Y in human beings."),
        ("Autosome", "Any chromosome that is not a sex chromosome."),
    ], "easy"),

    ("sci-bio-env.ecosystem", [
        ("Environment", "Everything surrounding an organism, including both living and non-living components."),
        ("Biotic component", "The living parts of an ecosystem: producers, consumers and decomposers."),
        ("Abiotic component", "The non-living parts of an ecosystem: sunlight, temperature, water, soil and air."),
        ("Trophic level", "The step in a food chain at which an organism feeds."),
        ("Biological magnification", "The progressive increase in the concentration of a non-biodegradable substance at each higher trophic level."),
        ("Biodegradable substance", "A substance that can be broken down into simple harmless substances by microorganisms."),
        ("Non-biodegradable substance", "A substance that cannot be broken down by biological processes and persists in the environment."),
        ("Compost", "Organic matter decomposed by microorganisms and used to enrich soil."),
        ("Incineration", "The burning of waste at high temperature to reduce its volume."),
    ], "easy"),
]
