JAZZ_PROGRESSIONS = {
    # =========================================================================
    # FOUNDATIONAL PROGRESSIONS
    # =========================================================================
    "V-I": {
        "name": "Dominant Resolution",
        "numerals": ["V7", "I"],
        "in_C": ["G7", "Cmaj7"],
        "category": "foundational",
        "description": "The most basic unit of tonal movement. Dominant resolves down a fifth to tonic.",
        "examples": ["Every jazz tune ever"]
    },
    "ii-V-I_major": {
        "name": "Major ii-V-I",
        "numerals": ["ii7", "V7", "Imaj7"],
        "in_C": ["Dm7", "G7", "Cmaj7"],
        "category": "foundational",
        "description": "The backbone of jazz harmony. The most common progression in the genre.",
        "examples": ["Autumn Leaves", "What Is This Thing Called Love", "Tune Up", "Pent Up House"]
    },
    "ii-V-i_minor": {
        "name": "Minor ii-V-i",
        "numerals": ["iiø7", "V7(b9)", "i6"],
        "in_C": ["Dm7b5", "G7b9", "Cm6"],
        "category": "foundational",
        "description": "Minor key version. Half-diminished ii, altered dominant V, minor tonic.",
        "examples": ["Alone Together", "Softly As In A Morning Sunrise", "Beautiful Love"]
    },
    "ii-V_unresolved": {
        "name": "Unresolved ii-V",
        "numerals": ["ii7", "V7"],
        "in_C": ["Dm7", "G7"],
        "category": "foundational",
        "description": "The ii-V without resolution. Creates expectation that gets redirected.",
        "examples": ["Summertime", "Satin Doll"]
    },

    # =========================================================================
    # TURNAROUNDS
    # =========================================================================
    "I-vi-ii-V": {
        "name": "Basic Turnaround",
        "numerals": ["Imaj7", "vi7", "ii7", "V7"],
        "in_C": ["Cmaj7", "Am7", "Dm7", "G7"],
        "category": "turnaround",
        "description": "The standard turnaround. Cycles back to the top of the form.",
        "examples": ["I Got Rhythm", "Anthropology", "Oleo"]
    },
    "iii-VI-ii-V": {
        "name": "Extended Turnaround",
        "numerals": ["iii7", "VI7", "ii7", "V7"],
        "in_C": ["Em7", "A7", "Dm7", "G7"],
        "category": "turnaround",
        "description": "iii substitutes for I, creating a longer chain of falling fifths.",
        "examples": ["Have You Met Miss Jones", "Angel Eyes"]
    },
    "III-VI-II-V": {
        "name": "Dominant Turnaround",
        "numerals": ["III7", "VI7", "II7", "V7"],
        "in_C": ["E7", "A7", "D7", "G7"],
        "category": "turnaround",
        "description": "All dominants. Chain of secondary dominants creating maximum instability.",
        "examples": ["Bebop tunes", "Jazz blues variations"]
    },
    "tritone_sub_turnaround": {
        "name": "Tritone Sub Turnaround",
        "numerals": ["Imaj7", "bIII7", "ii7", "bII7"],
        "in_C": ["Cmaj7", "Eb7", "Dm7", "Db7"],
        "category": "turnaround",
        "description": "Dominant chords replaced with tritone subs. Creates chromatic bass line.",
        "examples": ["Lady Bird (ending)", "Modern jazz arrangements"]
    },
    "I-VI7-ii-V": {
        "name": "Diatonic Turnaround with Secondary Dominant",
        "numerals": ["Imaj7", "VI7", "ii7", "V7"],
        "in_C": ["Cmaj7", "A7", "Dm7", "G7"],
        "category": "turnaround",
        "description": "Basic turnaround but vi becomes VI7 (secondary dominant of ii).",
        "examples": ["Rhythm Changes (A section)", "Ice Cream Changes"]
    },
    "I-bVII-bVI-V": {
        "name": "Chromatic Descending Turnaround",
        "numerals": ["Imaj7", "bVII7", "bVI7", "V7"],
        "in_C": ["Cmaj7", "Bb7", "Ab7", "G7"],
        "category": "turnaround",
        "description": "Chromatic descent from I down to V. Dramatic and bluesy.",
        "examples": ["Blues endings", "Gospel jazz"]
    },
    "tag_ending": {
        "name": "Tag Ending (Repeat Turnaround)",
        "numerals": ["ii7", "V7", "ii7", "V7", "Imaj7"],
        "in_C": ["Dm7", "G7", "Dm7", "G7", "Cmaj7"],
        "category": "turnaround",
        "description": "Repeated ii-V before final resolution. Used to end tunes.",
        "examples": ["Standard jazz endings"]
    },

    # =========================================================================
    # BLUES FORMS
    # =========================================================================
    "basic_jazz_blues": {
        "name": "Basic Jazz Blues (12-bar)",
        "numerals": [
            "I7", "IV7", "I7", "I7",
            "IV7", "IV7", "I7", "vi7 II7",
            "ii7", "V7", "I7 VI7", "ii7 V7"
        ],
        "in_C": [
            "C7", "F7", "C7", "C7",
            "F7", "F7", "C7", "Am7 D7",
            "Dm7", "G7", "C7 A7", "Dm7 G7"
        ],
        "category": "blues",
        "description": "Standard 12-bar blues with jazz ii-V substitutions and turnaround.",
        "examples": ["Billie's Bounce", "Straight No Chaser", "Bag's Groove"]
    },
    "bird_blues": {
        "name": "Bird Blues (Charlie Parker Blues)",
        "numerals": [
            "Imaj7", "ii7/bVII V7/bVII", "ii7/VI V7/VI", "ii7/V V7/V",
            "IV7", "#ivø7", "Imaj7", "ii7/bIII V7/bIII",
            "ii7", "V7", "Imaj7 VI7", "ii7 V7"
        ],
        "in_C": [
            "Cmaj7", "Bm7 E7", "Am7 D7", "Gm7 C7",
            "F7", "F#m7b5", "Cmaj7", "Ebm7 Ab7",
            "Dm7", "G7", "Cmaj7 A7", "Dm7 G7"
        ],
        "category": "blues",
        "description": "Parker's reharmonization of the blues with descending ii-V chains.",
        "examples": ["Blues for Alice", "Chi Chi", "Freight Trane"]
    },
    "minor_blues": {
        "name": "Minor Blues (12-bar)",
        "numerals": [
            "i7", "i7", "i7", "i7",
            "iv7", "iv7", "i7", "i7",
            "bVI7", "V7", "i7", "V7"
        ],
        "in_C": [
            "Cm7", "Cm7", "Cm7", "Cm7",
            "Fm7", "Fm7", "Cm7", "Cm7",
            "Ab7", "G7", "Cm7", "G7"
        ],
        "category": "blues",
        "description": "12-bar blues in a minor key.",
        "examples": ["Mr. P.C.", "Equinox", "Birk's Works"]
    },

    # =========================================================================
    # RHYTHM CHANGES
    # =========================================================================
    "rhythm_changes_A": {
        "name": "Rhythm Changes (A Section)",
        "numerals": ["Imaj7 vi7", "ii7 V7", "iii7 VI7", "ii7 V7"],
        "in_Bb": ["Bbmaj7 Gm7", "Cm7 F7", "Dm7 G7", "Cm7 F7"],
        "category": "rhythm_changes",
        "description": "32-bar AABA form A section. Turnaround pattern from 'I Got Rhythm'.",
        "examples": ["Anthropology", "Oleo", "Moose the Mooche", "Dexterity"]
    },
    "rhythm_changes_bridge": {
        "name": "Rhythm Changes (Bridge)",
        "numerals": ["III7", "III7", "VI7", "VI7", "II7", "II7", "V7", "V7"],
        "in_Bb": ["D7", "D7", "G7", "G7", "C7", "C7", "F7", "F7"],
        "category": "rhythm_changes",
        "description": "Bridge section. Chain of dominants moving through the cycle of fifths.",
        "examples": ["Anthropology", "Oleo", "Rhythm-a-ning"]
    },

    # =========================================================================
    # COMMON HARMONIC MOVEMENTS
    # =========================================================================
    "I-IV": {
        "name": "Tonic to Subdominant",
        "numerals": ["Imaj7", "IVmaj7"],
        "in_C": ["Cmaj7", "Fmaj7"],
        "category": "harmonic_movement",
        "description": "Movement to the IV chord, often set up by its own ii-V.",
        "examples": ["Blues forms", "Misty", "Body and Soul"]
    },
    "IV-IVm": {
        "name": "Major IV to Minor IV",
        "numerals": ["IVmaj7", "IVm6", "Imaj7"],
        "in_C": ["Fmaj7", "Fm6", "Cmaj7"],
        "category": "harmonic_movement",
        "description": "Bittersweet sound. IV goes minor then resolves to I. Borrowed chord from parallel minor.",
        "examples": ["My Funny Valentine", "In A Sentimental Mood", "Bossa nova tunes"]
    },
    "line_cliche": {
        "name": "Line Cliché (Chromatic Inner Voice)",
        "numerals": ["im", "im(maj7)", "im7", "im6"],
        "in_C": ["Cm", "Cm(maj7)", "Cm7", "Cm6"],
        "category": "harmonic_movement",
        "description": "One voice moves chromatically while the chord stays rooted. Creates smooth motion.",
        "examples": ["My Funny Valentine", "Stairway to Heaven", "James Bond Theme"]
    },
    "descending_ii-Vs": {
        "name": "Descending ii-V's",
        "numerals": ["ii7 V7 Imaj7", "(down whole step)", "ii7 V7 Imaj7", "(down whole step)", "ii7 V7 Imaj7"],
        "in_C": ["Em7 A7 Dmaj7", "", "Dm7 G7 Cmaj7", "", "Cm7 F7 Bbmaj7"],
        "category": "harmonic_movement",
        "description": "ii-V-I that modulates down by whole steps (or half steps). Sequential pattern.",
        "examples": ["Tune Up", "How High the Moon"]
    },
    "ascending_ii-Vs": {
        "name": "Ascending ii-V's",
        "numerals": ["ii7 V7", "(up half step)", "ii7 V7"],
        "in_C": ["Dm7 G7", "", "Ebm7 Ab7"],
        "category": "harmonic_movement",
        "description": "ii-V's that climb upward chromatically. Creates rising tension.",
        "examples": ["Moment's Notice", "Giant Steps (partial)"]
    },
    "chromatic_approach": {
        "name": "Chromatic Approach (bII7 to I)",
        "numerals": ["bII7", "Imaj7"],
        "in_C": ["Db7", "Cmaj7"],
        "category": "harmonic_movement",
        "description": "Approaching the tonic from a half step above with a dominant chord.",
        "examples": ["Endings", "Lady Bird"]
    },

    # =========================================================================
    # SUBSTITUTION TECHNIQUES
    # =========================================================================
    "tritone_substitution": {
        "name": "Tritone Substitution",
        "numerals": ["ii7", "bII7", "Imaj7"],
        "in_C": ["Dm7", "Db7", "Cmaj7"],
        "category": "substitution",
        "description": "Replace V7 with dominant a tritone away. Creates chromatic bass: D → Db → C.",
        "examples": ["Lady Bird", "Moment's Notice", "Modern jazz reharmonizations"]
    },
    "secondary_dominant": {
        "name": "Secondary Dominant",
        "numerals": ["V7/ii → ii7", "V7/vi → vi7"],
        "in_C": ["A7 → Dm7", "E7 → Am7"],
        "category": "substitution",
        "description": "Any dominant 7th resolving to a diatonic chord other than I.",
        "examples": ["All The Things You Are", "Stella By Starlight"]
    },
    "diminished_passing": {
        "name": "Diminished Passing Chord",
        "numerals": ["Imaj7", "#Idim7", "ii7"],
        "in_C": ["Cmaj7", "C#dim7", "Dm7"],
        "category": "substitution",
        "description": "Diminished chord fills chromatic gap between diatonic chords.",
        "examples": ["Rhythm Changes variations", "Swing tunes"]
    },
    "backdoor_ii-V": {
        "name": "Backdoor ii-V (bVII7 Resolution)",
        "numerals": ["iv7", "bVII7", "Imaj7"],
        "in_C": ["Fm7", "Bb7", "Cmaj7"],
        "category": "substitution",
        "description": "Arrives at tonic from unexpected direction via the bVII dominant.",
        "examples": ["Joy Spring", "Yardbird Suite", "Days of Wine and Roses"]
    },
    "deceptive_resolution": {
        "name": "Deceptive ii-V (Resolves to Wrong Quality)",
        "numerals": ["iiø7", "V7alt", "Imaj7"],
        "in_C": ["Dm7b5", "G7alt", "Cmaj7"],
        "category": "substitution",
        "description": "Looks like it'll resolve minor (half-dim ii) but lands on major. Or vice versa.",
        "examples": ["Stablemates", "Inner Urge"]
    },
    "sus_dominant": {
        "name": "Suspended Dominant",
        "numerals": ["V7sus4", "V7", "Imaj7"],
        "in_C": ["G7sus4", "G7", "Cmaj7"],
        "category": "substitution",
        "description": "Delays resolution by suspending the 3rd of the dominant. Adds anticipation.",
        "examples": ["Maiden Voyage", "Herbie Hancock tunes"]
    },

    # =========================================================================
    # COLTRANE CHANGES
    # =========================================================================
    "coltrane_changes": {
        "name": "Coltrane Changes (Giant Steps)",
        "numerals": ["Imaj7", "V7/bVI", "bVImaj7", "V7/bIII", "bIIImaj7", "V7/I", "Imaj7"],
        "in_C": ["Cmaj7", "Eb7", "Abmaj7", "B7", "Emaj7", "G7", "Cmaj7"],
        "category": "coltrane",
        "description": "Tonal centers move in major thirds dividing the octave into 3 equal parts.",
        "examples": ["Giant Steps", "Countdown", "26-2", "Central Park West"]
    },
    "coltrane_ii-V-I_sub": {
        "name": "Coltrane Substitution over ii-V-I",
        "numerals": ["ii7", "V7/bVI", "bVImaj7", "V7/bIII", "bIIImaj7", "V7", "Imaj7"],
        "in_C": ["Dm7", "Eb7", "Abmaj7", "B7", "Emaj7", "G7", "Cmaj7"],
        "category": "coltrane",
        "description": "Coltrane changes applied as a reharmonization of a standard ii-V-I.",
        "examples": ["Countdown (reharmonized Tune Up)"]
    },

    # =========================================================================
    # MODAL JAZZ
    # =========================================================================
    "modal_vamp": {
        "name": "Modal Vamp",
        "numerals": ["i7 (extended)"],
        "in_C": ["Cm7 or Dm7 (for D Dorian)"],
        "category": "modal",
        "description": "One or two chords sustained for long sections. Improvisation based on mode, not changes.",
        "examples": ["So What", "Impressions", "Maiden Voyage", "Footprints"]
    },
    "modal_interchange": {
        "name": "Modal Interchange / Borrowed Chords",
        "numerals": ["Imaj7", "bVIImaj7", "bVImaj7", "Imaj7"],
        "in_C": ["Cmaj7", "Bbmaj7", "Abmaj7", "Cmaj7"],
        "category": "modal",
        "description": "Borrowing chords from the parallel minor/other modes. Creates color without functional movement.",
        "examples": ["Wayne Shorter compositions", "Modern jazz"]
    },
    "quartal_voicings": {
        "name": "Quartal Harmony (Fourths-Based)",
        "numerals": ["Stacked 4ths moving in parallel"],
        "in_C": ["D-G-C-F moving to E-A-D-G etc."],
        "category": "modal",
        "description": "Chords built in fourths rather than thirds. Ambiguous, open sound. McCoy Tyner signature.",
        "examples": ["So What", "McCoy Tyner solos", "Herbie Hancock"]
    },

    # =========================================================================
    # COMMON FULL FORMS
    # =========================================================================
    "take_the_a_train": {
        "name": "'Take the A Train' Changes",
        "numerals": ["Imaj7", "II7", "ii7", "V7"],
        "in_C": ["Cmaj7", "D7", "Dm7", "G7"],
        "category": "named_form",
        "description": "Features the II7 (non-diatonic dominant). Bright, lifted quality.",
        "examples": ["Take the A Train", "Girl from Ipanema"]
    },
    "autumn_leaves": {
        "name": "'Autumn Leaves' Changes",
        "numerals": ["ii7", "V7", "Imaj7", "IVmaj7", "viiø7", "III7", "vi"],
        "in_G": ["Am7", "D7", "Gmaj7", "Cmaj7", "F#m7b5", "B7", "Em"],
        "category": "named_form",
        "description": "Cycles through relative major and minor using ii-V-I's in both.",
        "examples": ["Autumn Leaves"]
    },
    "all_the_things": {
        "name": "'All The Things You Are' Changes",
        "numerals": ["vi7", "ii7", "V7", "Imaj7", "IVmaj7", "(modulates through keys)"],
        "in_Ab": ["Fm7", "Bbm7", "Eb7", "Abmaj7", "Dbmaj7", "..."],
        "category": "named_form",
        "description": "Moves through multiple key centers via ii-V-I's. One of the most played standards.",
        "examples": ["All The Things You Are"]
    },
    "stella": {
        "name": "'Stella By Starlight' Changes",
        "numerals": ["iiø7/ii", "V7/ii", "ii7", "V7", "Imaj7", "(complex modulations)"],
        "in_Bb": ["Em7b5", "A7", "Cm7", "F7", "Bbmaj7", "..."],
        "category": "named_form",
        "description": "Chromatic and complex, with ii-V's targeting multiple key centers.",
        "examples": ["Stella By Starlight"]
    },

    # =========================================================================
    # OTHER IMPORTANT PROGRESSIONS
    # =========================================================================
    "cycle_of_fifths": {
        "name": "Cycle of Fifths / Diatonic Cycle",
        "numerals": ["IVmaj7", "viiø7", "iii7", "vi7", "ii7", "V7", "Imaj7"],
        "in_C": ["Fmaj7", "Bm7b5", "Em7", "Am7", "Dm7", "G7", "Cmaj7"],
        "category": "harmonic_movement",
        "description": "All diatonic chords moving in fourths/fifths. The source of many jazz progressions.",
        "examples": ["Fly Me to the Moon", "All The Things You Are (sections)"]
    },
    "pedal_point": {
        "name": "Pedal Point",
        "numerals": ["Imaj7", "ii7/I", "V7/I", "Imaj7"],
        "in_C": ["Cmaj7", "Dm7/C", "G7/C", "Cmaj7"],
        "category": "harmonic_movement",
        "description": "Bass stays on one note while chords move above it. Creates tension and release.",
        "examples": ["Naima", "Song intros/endings"]
    },
    "minor_plagal": {
        "name": "Minor Plagal Cadence",
        "numerals": ["iv7", "Imaj7"],
        "in_C": ["Fm7", "Cmaj7"],
        "category": "harmonic_movement",
        "description": "Minor iv resolving to major I. Softer, more melancholy resolution than V-I.",
        "examples": ["Endings", "Gospel jazz"]
    },
    "glide_progression": {
        "name": "Glide Progression",
        "numerals": ["im7", "bImaj7", "(repeat pattern)"],
        "in_C": ["Cm7", "Bmaj7", "Bbm7", "Amaj7"],
        "category": "modern",
        "description": "Half the notes slide by half step while the other half stay. Creates dreamy motion.",
        "examples": ["Neo-soul", "Modern jazz piano"]
    },
    "side_slipping": {
        "name": "Side-Slipping / Planing",
        "numerals": ["Imaj7", "bImaj7 or #Imaj7", "Imaj7"],
        "in_C": ["Cmaj7", "Bmaj7 or Dbmaj7", "Cmaj7"],
        "category": "modern",
        "description": "Temporarily shifting the entire chord up or down a half step for dissonance.",
        "examples": ["Thelonious Monk tunes", "Modern improvisation"]
    },
    "constant_structure": {
        "name": "Constant Structure",
        "numerals": ["Same chord quality moving in parallel"],
        "in_C": ["Cmaj7", "Dbmaj7", "Dmaj7", "Ebmaj7"],
        "category": "modern",
        "description": "Same voicing moves chromatically or by interval. Non-functional harmony.",
        "examples": ["Wayne Shorter", "Joe Henderson", "Modern jazz"]
    },
}

CURATED_SERIES = [
    ("Autumn Leaves", ["ii7", "V7", "Imaj7", "IVmaj7", "viiø7", "III7", "vi"]),
]
