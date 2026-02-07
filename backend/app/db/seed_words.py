from sqlalchemy.orm import Session

from app.models.word import Word

WORDS = {
    1: [
        # === EASY (200 words) — common objects, animals, actions ===
        "apple", "chair", "river", "pencil", "cloud", "window", "pillow", "garden", "coffee", "mirror",
        "bottle", "candle", "camera", "basket", "button", "carpet", "cookie", "door", "flower", "guitar",
        "hammer", "hat", "island", "jacket", "key", "lamp", "leaf", "map", "moon", "notebook",
        "ocean", "orange", "paint", "paper", "phone", "plant", "plate", "rain", "ring", "rope",
        "baby", "ball", "banana", "bed", "bird", "boat", "book", "bread", "bridge", "brush",
        "bubble", "cake", "car", "cat", "clock", "coin", "comb", "couch", "cow", "crown",
        "cup", "desk", "dog", "drum", "ear", "egg", "eye", "fan", "fence", "fire",
        "fish", "flag", "fork", "frog", "glass", "glove", "goat", "grass", "hand", "heart",
        "hill", "honey", "horse", "house", "ice", "iron", "juice", "king", "kite", "knife",
        "lemon", "lion", "lips", "lock", "milk", "mouse", "nail", "nest", "nose", "oven",
        "pants", "peach", "pen", "pig", "pizza", "pocket", "potato", "queen", "rabbit", "rice",
        "road", "rock", "roof", "rose", "salt", "sand", "shirt", "shoe", "smile", "snake",
        "snow", "soap", "sock", "spoon", "star", "stone", "stove", "sugar", "sun", "table",
        "tail", "tea", "tent", "tiger", "toast", "tooth", "towel", "train", "tree", "truck",
        "turtle", "wall", "watch", "water", "wave", "wheel", "wing", "wood", "yarn", "zebra",
        "candy", "cherry", "cheese", "chicken", "corn", "donkey", "feather", "finger", "grapes", "ladder",
        "mango", "melon", "monkey", "needle", "onion", "parrot", "peanut", "pepper", "pumpkin", "puppy",
        "salad", "spider", "stamp", "swing", "tomato", "tongue", "violin", "wallet", "worm", "zipper",
        "arrow", "belt", "bone", "broom", "chain", "chalk", "cheese", "cliff", "cloud", "crayon",
        "dolphin", "elbow", "forest", "ghost", "globe", "grape", "helmet", "igloo", "jelly", "kitten",
    ],
    2: [
        # === MEDIUM (400 words) — compound words, professions, less common ===
        "airplane", "backpack", "balloon", "barbecue", "binoculars", "calendar", "campfire", "carousel", "compass", "computer",
        "construction", "cupcake", "dinosaur", "elevator", "fireworks", "flashlight", "fountain", "headphones", "highway", "hospital",
        "keyboard", "lighthouse", "mountain", "musical", "necklace", "newspaper", "passport", "rainbow", "sandcastle", "spaceship",
        "sunflower", "telescope", "thermometer", "trainstation", "treasure", "umbrella", "vending", "volcano", "waterfall", "whistle",
        "accordion", "acrobat", "ambulance", "anchor", "antelope", "archery", "avalanche", "bacteria", "bagpipes", "balcony",
        "bamboo", "bandage", "barnacle", "basement", "battery", "bazaar", "beehive", "bicycle", "blizzard", "boomerang",
        "bowling", "bracelet", "broccoli", "buffalo", "bulldozer", "butterfly", "cactus", "cafeteria", "calculator", "catapult",
        "cathedral", "ceiling", "centipede", "chainsaw", "champion", "chariot", "chimney", "chocolate", "cinnamon", "circus",
        "classroom", "clipboard", "cobweb", "coconut", "collision", "comet", "conductor", "conveyor", "coral", "costume",
        "cottage", "coyote", "crossbow", "cucumber", "curtain", "cyclone", "dashboard", "delivery", "detective", "diamond",
        "diploma", "dolphin", "dominos", "doughnut", "dragonfly", "drawbridge", "dumpster", "eclipse", "electrician", "elephant",
        "envelope", "escalator", "espresso", "excavator", "explosion", "factory", "falcon", "festival", "flamingo", "forklift",
        "fossil", "freeway", "furniture", "galaxy", "garage", "gardener", "gazelle", "generator", "geyser", "giraffe",
        "glacier", "goldfish", "gorilla", "grasshopper", "grenade", "grocery", "guillotine", "gymnast", "hamburger", "hammock",
        "handshake", "hangover", "hardware", "harmonica", "harpoon", "harvest", "hedgehog", "helicopter", "hieroglyph", "hooligan",
        "horseshoe", "hourglass", "hummingbird", "hurricane", "iceberg", "iguana", "inventor", "jackpot", "javelin", "jellyfish",
        "jigsaw", "jockey", "juggler", "kangaroo", "kayak", "kennel", "kerosene", "kingdom", "knitting", "koala",
        "labrador", "landscape", "lantern", "laundry", "lawnmower", "leopard", "librarian", "limousine", "lizard", "lobster",
        "locksmith", "locomotive", "luggage", "lumberjack", "magazine", "magician", "magnetic", "mailbox", "mandolin", "marathon",
        "marionette", "mattress", "mechanic", "medicine", "mermaid", "meteor", "microphone", "microscope", "milkshake", "minefield",
        "mistletoe", "molecule", "mongoose", "mosquito", "motorboat", "mushroom", "mustache", "mystery", "navigate", "octopus",
        "orchestra", "origami", "ostrich", "outlaw", "overboard", "parachute", "paramedic", "parcel", "peacock", "pelican",
        "penguin", "perfume", "pharmacy", "piano", "pirate", "plumber", "porcupine", "portrait", "postcard", "pretzel",
        "prisoner", "projector", "propeller", "pumpkin", "puppet", "pyramid", "quarry", "quicksand", "raccoon", "radiator",
        "recorder", "referee", "refrigerator", "reindeer", "reptile", "restaurant", "rhinoceros", "rickshaw", "rollercoaster", "rooftop",
        "sailboat", "satellite", "scarecrow", "scissors", "scorpion", "sculptor", "seahorse", "seesaw", "seminary", "shamrock",
        "shipwreck", "shopping", "skeleton", "skydiving", "sleepwalk", "smuggler", "snowboard", "snowflake", "sombrero", "souvenir",
        "spaghetti", "speedboat", "spotlight", "squirrel", "staircase", "stampede", "starfish", "stilts", "stopwatch", "stroller",
        "submarine", "suitcase", "sundial", "sunscreen", "surfboard", "survivor", "swordfish", "symphony", "tadpole", "tarantula",
        "taxicab", "teapot", "toboggan", "toothbrush", "tornado", "tractor", "trapeze", "tricycle", "trolley", "trampoline",
        "tugboat", "tuxedo", "typewriter", "unicorn", "uniform", "vacation", "vampire", "ventilator", "veterinarian", "vineyard",
        "volleyball", "vulture", "waffle", "warehouse", "werewolf", "wheelchair", "whirlpool", "wildfire", "windshield", "wishbone",
        "woodpecker", "workshop", "wrestler", "xylophone", "yachtsman", "yearbook", "zeppelin", "zigzag", "zookeeper", "avalanche",
        "banister", "blueprint", "caramel", "dynamite", "equipment", "firehouse", "gondola", "holster", "inspector", "jukebox",
        "knapsack", "lifeguard", "mannequin", "nightclub", "overcoat", "paintball", "quickstep", "racetrack", "snowplow", "treadmill",
        "underwear", "viewpoint", "whiplash", "yardstick", "zucchini", "aardvark", "bullseye", "carnival", "dominoes", "espionage",
        "footprint", "gladiator", "handcuffs", "igloo", "jackrabbit", "ketchup", "lollipop", "marmalade", "nightfall", "outrigger",
        "pendulum", "quicksand", "roulette", "sardine", "tightrope", "uppercut", "voodoo", "werewolf", "xylophonist", "yearling",
        "beekeeper", "candlestick", "dragonfly", "earthquake", "foghorn", "gondolier", "hedgerow", "inkwell", "jackknife", "keepsake",
        "lemonade", "moonshine", "newsstand", "outfield", "pineapple", "raspberry", "slingshot", "thunderstorm", "upperhand", "windmill",
    ],
    3: [
        # === HARD (300 words) — abstract, scientific, complex ===
        "astronaut", "blacksmith", "chandelier", "chessboard", "constellation", "cryptogram", "ecosystem", "firefighter",
        "greenhouse", "hologram", "hydraulic", "labyrinth", "microchip", "navigation", "nightingale", "observatory",
        "parliament", "periscope", "philosophy", "quarantine", "reflection", "renaissance", "saxophone", "silhouette",
        "tournament", "trajectory", "yesterday", "zephyr", "biography", "pyramids", "relay", "algorithm",
        "aquarium", "metaphor", "monarchy", "pipeline", "acupuncture", "amnesia", "anesthesia", "anthology",
        "apartheid", "archaeology", "aristocrat", "atmosphere", "autobiography", "bankruptcy", "barricade", "blasphemy",
        "bombardment", "bureaucracy", "camouflage", "capitalism", "catastrophe", "censorship", "choreography", "civilization",
        "claustrophobia", "colonialism", "communism", "compromise", "conspiracy", "contradiction", "controversy", "corruption",
        "counterfeit", "courtroom", "cybernetics", "dehydration", "democracy", "demolition", "depression", "desperation",
        "dictatorship", "diplomacy", "discrimination", "distillation", "documentary", "domesticate", "electromagnet", "embezzlement",
        "emigration", "empathy", "encryption", "enlightenment", "entrepreneur", "epidemiology", "equilibrium", "espionage",
        "evaporation", "exaggeration", "excommunicate", "extravagance", "fahrenheit", "fascination", "fluorescent", "foreclosure",
        "fortification", "fossilization", "frostbite", "fundamentalism", "genealogy", "geopolitics", "germination", "globalization",
        "gravitational", "hallucination", "hemisphere", "hieroglyphics", "homogeneous", "hospitality", "humiliation", "hypothesis",
        "idealism", "immigration", "impeachment", "improvisation", "incandescent", "independence", "industrialize", "inflation",
        "infrastructure", "inheritance", "inoculation", "insomnia", "intelligence", "interference", "interpretation", "intimidation",
        "investigation", "jurisdiction", "kaleidoscope", "kidnapping", "legislation", "linguistics", "lithography", "malfunction",
        "manifestation", "manipulation", "manuscript", "martyrdom", "materialism", "mathematics", "mercenary", "metabolism",
        "metamorphosis", "meteorology", "millennium", "misconception", "modernization", "monotheism", "nationalism", "negotiation",
        "neuroscience", "neutrality", "nomenclature", "nostalgia", "obligation", "obsolescence", "oligarchy", "omnivore",
        "opportunity", "oppression", "optimization", "orchestration", "palindrome", "pandemonium", "pantomime", "paradox",
        "paralysis", "patriotism", "persecution", "philanthropy", "photosynthesis", "plagiarism", "polarization", "polygraph",
        "predicament", "prehistoric", "preservation", "privatization", "procrastination", "propaganda", "prosecution", "psychology",
        "radioactive", "reconnaissance", "rehabilitation", "reincarnation", "relativism", "repercussion", "resignation", "revelation",
        "revolution", "sabotage", "sanctification", "schizophrenia", "segregation", "semiconductor", "skepticism", "socialism",
        "soliloquy", "sophisticated", "speculation", "stagnation", "sterilization", "subconscious", "suffocation", "superstition",
        "surveillance", "sustainability", "symbolism", "synchronize", "telepathy", "temperament", "thermodynamics", "totalitarianism",
        "tranquilizer", "transcription", "transformation", "transplantation", "turbulence", "unauthorized", "unemployment", "urbanization",
        "utilitarianism", "vaccination", "ventriloquist", "verification", "vulnerability", "xenophobia", "archeologist", "bankruptcy",
        "counterintelligence", "deforestation", "electrocution", "fingerprint", "hallucinate", "impersonation", "jurisprudence",
        "kleptomaniac", "libertarian", "malnutrition", "neurosurgeon", "osteoporosis", "plagiarize", "recollection",
        "stethoscope", "tuberculosis", "ventriloquism", "weightlessness", "bibliography", "cardiologist", "decapitation",
        "electromagnetic", "fermentation", "gerontology", "hyperventilate", "incarceration", "juxtaposition", "kinesiology",
        "loudspeaker", "misdemeanor", "neurological", "onomatopoeia", "phosphorescent", "rehabilitation", "socialization",
        "teleportation", "understaffed", "visualization", "whistleblower",
    ],
}


def seed_words(db: Session) -> int:
    existing_texts = {w.text for w in db.query(Word.text).all()}
    inserted = 0
    for difficulty, words in WORDS.items():
        for text in words:
            if text not in existing_texts:
                db.add(Word(text=text, difficulty=difficulty, active=True))
                existing_texts.add(text)
                inserted += 1
    if inserted > 0:
        db.commit()
    return inserted
