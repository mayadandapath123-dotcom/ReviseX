"""Physics clusters - Class 10 Science, chapters 9, 10, 11 and 12.

Light - Reflection and Refraction, The Human Eye and the Colourful World,
Electricity, and Magnetic Effects of Electric Current. All four chapters were
below a hundred questions, and the two thinnest - Magnetic Effects at 64 and
Light at 86 - had almost no coverage at all in the earlier content: the mirrors
topic carried two items and series/parallel combinations carried two.

Physics clusters well on attribute because the chapter content is largely sets of
siblings sharing one relationship: parts and their functions, defects and their
corrections, phenomena and their explanations, devices and what they convert.

Values inside a cluster are kept distinct on purpose. The generator builds the
reverse-recall form - "which subject has this value?" - only when no other item
in the file carries the same value under the same attribute, so a repeated value
quietly costs a third of a cluster's output.

No figure here is invented: the refractive indices, the 25 cm near point, the
220 V and 50 Hz domestic supply and the fuse ratings are the values the NCERT
text states, and qualitative claims are used wherever the text makes none.
"""

from __future__ import annotations

FACTS = [
    # ══════════════════════════════════════════════════════════════════
    # Chapter 9 - Light: Reflection and Refraction
    # ══════════════════════════════════════════════════════════════════
    ("sci-phy-light.mirrors", "term for", [
        ("The centre point of the reflecting surface of a spherical mirror", "Pole"),
        ("The centre of the sphere of which a spherical mirror forms a part", "Centre of curvature"),
        ("The straight line joining the pole to the centre of curvature", "Principal axis"),
        ("The point where rays parallel to the principal axis meet, or appear to come from, after reflection", "Principal focus"),
        ("The diameter of the reflecting surface of a spherical mirror", "Aperture"),
        ("The distance between the pole and the principal focus", "Focal length"),
    ], "easy"),

    ("sci-phy-light.mirrors", "forms", [
        ("A convex mirror", "An image that is always virtual, erect and diminished"),
        ("A plane mirror", "An image that is always virtual, erect and of the same size"),
        ("A concave mirror with the object between the pole and the focus", "An image that is virtual, erect and magnified"),
        ("A concave mirror with the object beyond the focus", "An image that is real and inverted"),
        ("A concave mirror with the object at the centre of curvature", "An image at the centre of curvature, the same size as the object"),
    ], "medium"),

    ("sci-phy-light.mirrors", "classified as", [
        ("A concave mirror", "A converging mirror"),
        ("A convex mirror", "A diverging mirror"),
        ("An image that can be obtained on a screen", "A real image"),
        ("An image that cannot be obtained on a screen", "A virtual image"),
    ], "easy"),

    ("sci-phy-light.mirrors", "used for", [
        ("A concave mirror in a torch or vehicle headlight", "Producing a powerful parallel beam of light"),
        ("A convex mirror in a vehicle", "Serving as a rear-view mirror, because it always gives an erect image and a wide field of view"),
        ("A concave mirror used for shaving or make-up", "Producing a magnified erect image of the face"),
        ("A concave mirror used by a dentist", "Producing a magnified image of a tooth"),
        ("A large concave mirror in a solar furnace", "Concentrating sunlight at one point to produce heat"),
        ("A plane mirror", "Producing an image the same size as the object, for everyday viewing"),
    ], "medium"),

    ("sci-phy-light.formulas", "expressed as", [
        ("The mirror formula", "1/v + 1/u = 1/f"),
        ("Magnification produced by a spherical mirror", "m = -v/u, which also equals h'/h"),
        ("The relation between the radius of curvature and the focal length of a spherical mirror", "R = 2f"),
        ("The lens formula", "1/v - 1/u = 1/f"),
        ("Magnification produced by a lens", "m = h'/h = v/u"),
        ("The power of a lens", "P = 1/f, with the focal length expressed in metres"),
    ], "easy"),

    ("sci-phy-light.refraction", "results in", [
        ("Light passing obliquely from air into glass", "Bending towards the normal"),
        ("Light passing obliquely from glass into air", "Bending away from the normal"),
        ("A ray passing through the optical centre of a lens", "Emerging without any deviation"),
        ("A ray passing obliquely through a rectangular glass slab", "An emergent ray parallel to the incident ray but shifted sideways"),
        ("Light entering a denser medium", "Its speed decreasing"),
        ("Light entering a rarer medium", "Its speed increasing"),
    ], "medium"),

    ("sci-phy-light.refraction", "refractive index of", [
        ("Air", "About 1.0003"),
        ("Water", "About 1.33"),
        ("Kerosene", "About 1.44"),
        ("Turpentine", "About 1.47"),
        ("Crown glass", "About 1.52"),
        ("Diamond", "About 2.42"),
    ], "easy"),

    ("sci-phy-light.refraction", "used for", [
        ("A convex lens held close to an object", "Acting as a magnifying glass"),
        ("A concave lens in spectacles", "Correcting myopia"),
        ("A convex lens in spectacles", "Correcting hypermetropia"),
        ("A combination of lenses in a camera", "Focusing a real image onto the film or sensor"),
        ("A rectangular glass slab", "Demonstrating the lateral shift of a light ray"),
        ("A glass prism", "Dispersing white light into its component colours"),
    ], "medium"),

    ("sci-phy-light.images", "forms", [
        ("A concave mirror with the object at infinity", "An image at the focus, highly diminished, real and inverted"),
        ("A concave mirror with the object beyond the centre of curvature", "An image between the focus and the centre, diminished, real and inverted"),
        ("A concave mirror with the object between the focus and the centre of curvature", "An image beyond the centre, magnified, real and inverted"),
        ("A concave mirror with the object at the focus", "An image at infinity, highly magnified, real and inverted"),
        ("A convex mirror with the object at any position in front of it", "An image between the pole and the focus, diminished, virtual and erect"),
        ("A plane mirror with the object at any position in front of it", "An image behind the mirror at the same distance, erect and the same size"),
    ], "hard"),

    ("sci-phy-light.images", "example of", [
        ("Lateral inversion", "The letters on an ambulance appearing reversed in a driver's rear-view mirror"),
        ("A real image", "The image of a candle flame obtained on a screen with a concave mirror"),
        ("A virtual image", "The image of one's own face seen in a plane mirror"),
        ("A diminished image", "The view of the traffic behind a car seen in its convex rear-view mirror"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 10 - The Human Eye and the Colourful World
    # ══════════════════════════════════════════════════════════════════
    ("sci-phy-eye.parts", "function of", [
        ("The cornea", "Providing most of the refraction of the light entering the eye"),
        ("The iris", "Controlling the size of the pupil"),
        ("The pupil", "Regulating the amount of light that enters the eye"),
        ("The ciliary muscles", "Changing the focal length of the eye lens"),
        ("The eye lens", "Focusing a real, inverted image onto the retina"),
        ("The retina", "Acting as the screen on which the image is formed"),
        ("The optic nerve", "Carrying the electrical signal from the retina to the brain"),
        ("Rod cells in the retina", "Responding to the intensity of light"),
        ("Cone cells in the retina", "Responding to colour"),
    ], "easy"),

    ("sci-phy-eye.parts", "value of", [
        ("The least distance of distinct vision for a normal adult eye", "25 cm"),
        ("The far point of a normal eye", "Infinity"),
        ("The range of vision of a normal eye", "From 25 cm to infinity"),
        ("The time for which an image persists on the retina", "About one sixteenth of a second"),
    ], "medium"),

    ("sci-phy-eye.defects", "corrected by", [
        ("Myopia", "A concave lens of suitable power"),
        ("Hypermetropia", "A convex lens of suitable power"),
        ("Presbyopia", "A bifocal lens having both a concave and a convex part"),
        ("Astigmatism", "A cylindrical lens"),
    ], "easy"),

    ("sci-phy-eye.defects", "caused by", [
        ("Myopia", "The eyeball becoming too long, or the lens becoming too curved"),
        ("Hypermetropia", "The eyeball becoming too short, or the focal length of the lens becoming too long"),
        ("Presbyopia", "The gradual weakening of the ciliary muscles and the loss of flexibility of the lens with age"),
        ("A myopic person being unable to see distant objects clearly", "The image of a distant object forming in front of the retina"),
        ("A hypermetropic person being unable to see near objects clearly", "The image of a near object forming behind the retina"),
    ], "medium"),

    ("sci-phy-eye.phenomena", "explained by", [
        ("The twinkling of stars", "Atmospheric refraction, as the optical density of air keeps changing"),
        ("Planets not twinkling", "Being much closer, so they act as extended sources whose fluctuations cancel out"),
        ("The blue colour of the sky", "Scattering of the shorter wavelengths of light by air molecules"),
        ("The reddish appearance of the sun at sunrise and sunset", "Light travelling a longer path through the atmosphere, so most of the blue is scattered away"),
        ("Stars appearing slightly higher in the sky than they really are", "Refraction of starlight as it enters the atmosphere from space"),
        ("The sun becoming visible about two minutes before actual sunrise", "Atmospheric refraction bending sunlight around the horizon"),
        ("Danger signals being red", "Red light being scattered the least, so it travels the farthest through smoke and fog"),
        ("A beam of light becoming visible in a dusty or smoky room", "Scattering of light by the fine particles in its path"),
    ], "medium"),

    ("sci-phy-eye.dispersion", "produced by", [
        ("Dispersion of white light by a prism", "Different colours travelling at different speeds in glass and so bending by different amounts"),
        ("Violet light bending the most on passing through a prism", "Its having the shortest wavelength in the visible spectrum"),
        ("Red light bending the least on passing through a prism", "Its having the longest wavelength in the visible spectrum"),
        ("The formation of a rainbow", "Refraction, dispersion and internal reflection of sunlight in suspended water droplets"),
        ("A rainbow always being seen with the sun behind the observer", "Needing sunlight from behind and water droplets in front"),
    ], "medium"),

    ("sci-phy-eye.dispersion", "term for", [
        ("The band of coloured components of a beam of light", "Spectrum"),
        ("The splitting of white light into its component colours", "Dispersion"),
        ("The bending of light as it passes from one transparent medium into another", "Refraction"),
        ("The scattering of a beam of light by colloidal particles in its path", "The Tyndall effect"),
        ("The ability of the eye lens to adjust its focal length", "Power of accommodation"),
    ], "easy"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 11 - Electricity
    # ══════════════════════════════════════════════════════════════════
    ("sci-phy-electricity.combinations", "property of", [
        ("Resistors connected in series", "The same current flowing through each of them"),
        ("Resistors connected in parallel", "The same potential difference appearing across each of them"),
        ("The equivalent resistance of a series combination", "Being greater than the largest individual resistance in it"),
        ("The equivalent resistance of a parallel combination", "Being less than the smallest individual resistance in it"),
        ("Series wiring being avoided in household circuits", "One appliance failing would stop the current in all the others"),
        ("Parallel wiring being used in household circuits", "Each appliance getting the full supply voltage and its own switch"),
    ], "medium"),

    ("sci-phy-electricity.combinations", "expressed as", [
        ("The equivalent resistance of resistors connected in series", "R = R1 + R2 + R3"),
        ("The equivalent resistance of resistors connected in parallel", "1/R = 1/R1 + 1/R2 + 1/R3"),
        ("The total potential difference across a series combination", "V = V1 + V2 + V3"),
        ("The total current entering a parallel combination", "I = I1 + I2 + I3"),
    ], "medium"),

    ("sci-phy-electricity.ohms-law", "depends on", [
        ("The resistance of a conductor", "Its length, its cross-sectional area, its material and its temperature"),
        ("The resistance of a wire becoming larger", "Its length being increased"),
        ("The resistance of a wire becoming smaller", "Its cross-sectional area being increased"),
        ("The resistivity of a substance", "The material itself, and not on the dimensions of the sample"),
        ("The current through a resistor kept at a constant temperature", "The potential difference applied across its ends"),
    ], "medium"),

    ("sci-phy-electricity.ohms-law", "made of", [
        ("The filament of an electric bulb", "Tungsten"),
        ("The heating element of an electric heater or iron", "Nichrome"),
        ("A fuse wire", "An alloy of lead and tin, which has a low melting point"),
        ("The core placed inside a solenoid to make an electromagnet", "Soft iron"),
        ("The insulating covering of an electric wire", "Rubber or plastic"),
    ], "easy"),

    ("sci-phy-electricity.current", "measured by", [
        ("The electric current flowing in a circuit", "An ammeter, connected in series with the circuit"),
        ("The potential difference across a component", "A voltmeter, connected in parallel with the component"),
        ("The charge that has flowed through a circuit", "Multiplying the current by the time for which it flowed"),
        ("The resistance of a component already carrying current", "Dividing the measured potential difference by the measured current"),
    ], "medium"),

    ("sci-phy-electricity.power", "given by", [
        ("Electric power", "P = VI"),
        ("Power in terms of current and resistance", "P = I²R"),
        ("Power in terms of potential difference and resistance", "P = V²/R"),
        ("Electrical energy consumed", "E = P × t"),
        ("One kilowatt hour expressed in joules", "3.6 × 10⁶ J"),
    ], "hard"),

    ("sci-phy-electricity.power", "used for", [
        ("The heating effect of an electric current", "Working of an electric heater, an iron and a toaster"),
        ("A tungsten filament inside a bulb", "Glowing at a very high temperature without melting"),
        ("A fuse in a domestic circuit", "Protecting appliances by breaking the circuit when the current becomes excessive"),
        ("Filling an electric bulb with argon or nitrogen", "Preventing the hot filament from oxidising and burning away"),
    ], "medium"),

    # ══════════════════════════════════════════════════════════════════
    # Chapter 12 - Magnetic Effects of Electric Current
    # ══════════════════════════════════════════════════════════════════
    ("sci-phy-magnetic.field", "property of", [
        ("Magnetic field lines", "Forming closed and continuous curves"),
        ("Magnetic field lines in the space outside a bar magnet", "Running from the north pole to the south pole"),
        ("Magnetic field lines inside a bar magnet", "Running from the south pole to the north pole"),
        ("Field lines being crowded close together in a region", "The magnetic field being stronger in that region"),
        ("Any two magnetic field lines", "Never intersecting one another"),
        ("The field produced around a straight current-carrying conductor", "Forming concentric circles centred on the wire"),
    ], "medium"),

    ("sci-phy-magnetic.field", "increased by", [
        ("The strength of the magnetic field around a straight wire", "Increasing the current through the wire"),
        ("The strength of the field at the centre of a circular loop", "Increasing the number of turns in the coil"),
        ("The strength of the field inside a solenoid", "Inserting a soft iron core into it"),
        ("The strength of the field near a current-carrying coil", "Moving closer to the conductor"),
    ], "medium"),

    ("sci-phy-magnetic.rules", "named after", [
        ("The rule giving the direction of the magnetic field around a straight current-carrying conductor", "The right-hand thumb rule"),
        ("The rule giving the direction of the force on a current-carrying conductor placed in a magnetic field", "Fleming's left-hand rule"),
        ("The rule giving the direction of the current induced in a moving conductor", "Fleming's right-hand rule"),
        ("The experiment first showing that an electric current produces a magnetic field", "Oersted's experiment"),
    ], "medium"),

    ("sci-phy-magnetic.rules", "used for", [
        ("Fleming's left-hand rule", "Finding the direction of the force on a current-carrying conductor in a magnetic field"),
        ("Fleming's right-hand rule", "Finding the direction of the current induced in a conductor moving in a magnetic field"),
        ("The right-hand thumb rule", "Finding the direction of the magnetic field around a straight current-carrying conductor"),
        ("A compass needle held near a current-carrying wire", "Detecting the presence and direction of the magnetic field"),
    ], "medium"),

    ("sci-phy-magnetic.rules", "function of", [
        ("The thumb in Fleming's left-hand rule", "Giving the direction of the force on the conductor"),
        ("The forefinger in Fleming's left-hand rule", "Giving the direction of the magnetic field"),
        ("The centre finger in Fleming's left-hand rule", "Giving the direction of the current"),
        ("The thumb in Fleming's right-hand rule", "Giving the direction of motion of the conductor"),
        ("The centre finger in Fleming's right-hand rule", "Giving the direction of the induced current"),
        ("The split ring in an electric motor", "Reversing the direction of the current in the coil every half rotation"),
    ], "medium"),

    ("sci-phy-magnetic.motor", "converts", [
        ("An electric motor", "Electrical energy into mechanical energy"),
        ("An electric generator", "Mechanical energy into electrical energy"),
        ("An electric cell", "Chemical energy into electrical energy"),
        ("A loudspeaker", "Electrical energy into sound energy"),
        ("A microphone", "Sound energy into electrical energy"),
        ("An electric bulb", "Electrical energy into light and heat energy"),
    ], "easy"),

    ("sci-phy-magnetic.motor", "based on", [
        ("An electric motor", "The force experienced by a current-carrying conductor placed in a magnetic field"),
        ("An electric generator", "Electromagnetic induction"),
        ("An electromagnet", "The magnetic field produced by a current in a solenoid wound on a soft iron core"),
        ("A galvanometer", "Detecting and measuring a small current flowing in a circuit"),
    ], "medium"),

    ("sci-phy-magnetic.domestic", "function of", [
        ("The live wire in a domestic circuit", "Carrying current from the supply at a potential of 220 V"),
        ("The neutral wire in a domestic circuit", "Completing the circuit at zero potential"),
        ("The earth wire in a domestic circuit", "Carrying any leakage of current safely into the ground"),
        ("A fuse connected in the live wire", "Melting and breaking the circuit when the current exceeds its rating"),
        ("Connecting the metallic body of an appliance to the earth wire", "Preventing a person touching the appliance from receiving a severe shock"),
        ("Wiring the appliances of a house in parallel", "Allowing each appliance to be switched on and off separately at full voltage"),
    ], "medium"),

    ("sci-phy-magnetic.domestic", "value of", [
        ("The potential difference between the live and the neutral wire in India", "220 V"),
        ("The frequency of the alternating current supplied in India", "50 Hz"),
        ("A common fuse rating for a circuit carrying lights and fans", "5 A"),
        ("A common fuse rating for a circuit carrying high-power appliances", "15 A"),
    ], "easy"),

    ("sci-phy-magnetic.domestic", "caused by", [
        ("Overloading of a domestic circuit", "Too many appliances being connected to a single socket"),
        ("A short circuit", "The live wire coming into direct contact with the neutral wire"),
        ("A very large current flowing suddenly through a circuit", "The resistance of the circuit becoming almost zero"),
        ("A fuse wire melting and breaking the circuit", "The current exceeding the rating for which the fuse was designed"),
    ], "medium"),
]

DEFINITIONS = [
    ("sci-phy-light.mirrors", [
        ("Real image", "An image formed where light rays actually meet, and which can be obtained on a screen."),
        ("Virtual image", "An image formed where light rays only appear to meet, and which cannot be obtained on a screen."),
        ("Lateral inversion", "The apparent left-right reversal of an object seen in a plane mirror."),
        ("Centre of curvature", "The centre of the sphere of which a spherical mirror forms a part."),
        ("Principal focus of a spherical mirror", "The point on the principal axis where rays parallel to it meet, or appear to come from, after reflection."),
        ("Aperture", "The diameter of the reflecting surface of a spherical mirror."),
        ("Focal length", "The distance between the pole and the principal focus of a spherical mirror or a lens."),
    ], "easy"),

    ("sci-phy-light.refraction", [
        ("Refractive index", "The ratio of the speed of light in vacuum to its speed in the medium."),
        ("Optical centre", "The central point of a lens through which a ray of light passes without any deviation."),
        ("Power of a lens", "The reciprocal of its focal length in metres, measured in dioptres."),
        ("Dioptre", "The unit of the power of a lens, equal to the power of a lens whose focal length is one metre."),
        ("Lateral displacement", "The perpendicular shift between the incident and the emergent ray passing through a glass slab."),
        ("Converging lens", "A lens that bends parallel rays of light so that they meet at a point."),
        ("Diverging lens", "A lens that bends parallel rays of light so that they appear to spread out from a point."),
    ], "medium"),

    ("sci-phy-eye.parts", [
        ("Power of accommodation", "The ability of the eye lens to adjust its focal length so that objects at different distances can be seen clearly."),
        ("Persistence of vision", "The retention of an image on the retina for about one sixteenth of a second after the object is gone."),
        ("Least distance of distinct vision", "The nearest distance at which a normal eye can see an object clearly without strain, about 25 cm."),
        ("Far point of the eye", "The farthest point up to which the eye can see objects clearly; for a normal eye it is at infinity."),
        ("Retina", "The light-sensitive screen at the back of the eye on which the image is formed."),
        ("Ciliary muscles", "The muscles that hold the eye lens in place and change its focal length."),
        ("Optic nerve", "The nerve that carries the electrical signal produced on the retina to the brain."),
    ], "medium"),

    ("sci-phy-eye.defects", [
        ("Myopia", "The defect of vision in which a person can see nearby objects clearly but not distant ones."),
        ("Hypermetropia", "The defect of vision in which a person can see distant objects clearly but not nearby ones."),
        ("Presbyopia", "The gradual loss of the power of accommodation of the eye with advancing age."),
        ("Astigmatism", "The defect of vision caused by an irregularly curved cornea, blurring vision in some directions."),
        ("Bifocal lens", "A lens having both a concave and a convex part, used to correct presbyopia."),
        ("Cataract", "A condition in which the eye lens becomes milky and cloudy, reducing or destroying vision."),
    ], "medium"),

    ("sci-phy-eye.dispersion", [
        ("Dispersion of light", "The splitting of white light into its component colours."),
        ("Spectrum", "The band of coloured components obtained when a beam of white light is dispersed."),
        ("Tyndall effect", "The scattering of a beam of light by colloidal or suspended particles in its path."),
        ("Scattering of light", "The phenomenon by which light is deflected in many directions by the particles it strikes."),
        ("Atmospheric refraction", "The refraction of light caused by the gradual change in the optical density of the atmosphere."),
    ], "medium"),

    ("sci-phy-electricity.current", [
        ("Electric current", "The rate of flow of electric charge through a conductor."),
        ("Potential difference", "The work done in moving a unit positive charge from one point to another."),
        ("Ampere", "The SI unit of electric current, equal to one coulomb of charge flowing per second."),
        ("Volt", "The SI unit of potential difference, equal to one joule of work per coulomb of charge."),
        ("Coulomb", "The SI unit of electric charge."),
    ], "easy"),

    ("sci-phy-electricity.ohms-law", [
        ("Ohm's law", "The statement that the current through a resistor is directly proportional to the potential difference across it, provided the temperature remains constant."),
        ("Resistance", "The property of a conductor that opposes the flow of current through it."),
        ("Resistivity", "The resistance of a conductor of unit length and unit cross-sectional area, a property of the material itself."),
        ("Variable resistance", "A component used to regulate the current in a circuit without changing the voltage source."),
        ("Rheostat", "A device used to vary the resistance, and therefore the current, in a circuit."),
    ], "medium"),

    ("sci-phy-electricity.combinations", [
        ("Series combination of resistors", "An arrangement in which resistors are joined end to end so that the same current flows through each."),
        ("Parallel combination of resistors", "An arrangement in which resistors are joined between the same two points so that each has the same potential difference."),
        ("Equivalent resistance", "The single resistance that can replace a combination without changing the current drawn from the source."),
    ], "medium"),

    ("sci-phy-electricity.power", [
        ("Electric power", "The rate at which electrical energy is consumed in a circuit."),
        ("Watt", "The SI unit of electric power, equal to one joule per second."),
        ("Kilowatt hour", "The commercial unit of electrical energy, equal to the energy used by a 1 kW device in one hour."),
        ("Heating effect of electric current", "The production of heat in a conductor when a current flows through it, given by H = I²Rt."),
    ], "medium"),

    ("sci-phy-magnetic.field", [
        ("Magnetic field", "The region around a magnet or a current-carrying conductor in which its magnetic influence can be detected."),
        ("Magnetic field line", "A curve along which a free north pole placed in the field would tend to move."),
        ("Solenoid", "A coil of many circular turns of insulated copper wire wrapped in the shape of a cylinder."),
        ("Electromagnet", "A temporary magnet produced by passing a current through a coil wound on a soft iron core."),
        ("Electromagnetic induction", "The production of an induced current in a coil by changing the magnetic field associated with it."),
    ], "medium"),

    ("sci-phy-magnetic.motor", [
        ("Electric motor", "A device that converts electrical energy into mechanical energy."),
        ("Electric generator", "A device that converts mechanical energy into electrical energy."),
        ("Commutator", "A split ring in a motor that reverses the direction of the current in the coil every half rotation."),
        ("Brushes", "The conducting contacts in a motor or generator that carry current between the rotating coil and the external circuit."),
        ("Direct current", "A current that flows in one direction only, as from a cell or a battery."),
        ("Alternating current", "A current that reverses its direction periodically."),
    ], "medium"),

    ("sci-phy-magnetic.domestic", [
        ("Domestic electric circuit", "The wiring of a house that supplies power at 220 V through a live, a neutral and an earth wire."),
        ("Fuse", "A safety device connected in series with the live wire that melts and breaks the circuit when the current exceeds its rating."),
        ("Overloading", "Drawing a current larger than the circuit is designed to carry, usually by connecting too many appliances."),
        ("Short circuit", "A fault in which the live wire comes into direct contact with the neutral wire, making the resistance almost zero."),
        ("Earthing", "Connecting the metallic body of an electrical appliance to the earth through the earth wire."),
    ], "medium"),
]
