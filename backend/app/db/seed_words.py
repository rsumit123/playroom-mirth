from sqlalchemy.orm import Session

from app.models.word import Word

CHARADES_WORDS = {
    1: [
        # === EASY (~350 words) — common objects, animals, actions, everyday things ===
        # Original
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
        "arrow", "belt", "bone", "broom", "chain", "chalk", "cliff", "crayon",
        "dolphin", "elbow", "forest", "ghost", "globe", "grape", "helmet", "igloo", "jelly", "kitten",
        # New easy words — animals
        "penguin", "whale", "shark", "eagle", "bear", "deer", "fox", "owl", "seal", "crab",
        "ant", "bee", "snail", "swan", "duck", "goose", "wolf", "bat", "pony", "lamb",
        "camel", "otter", "skunk", "beaver", "raccoon", "hedgehog", "squirrel", "flamingo",
        # New easy words — food & drink
        "burger", "taco", "pie", "soup", "steak", "pasta", "pretzel", "waffle", "popcorn", "bacon",
        "soda", "pancake", "butter", "jam", "yogurt", "cereal", "olive", "garlic", "ginger", "lime",
        # New easy words — objects & household
        "scissors", "blanket", "bucket", "candle", "curtain", "doorbell", "eraser", "flashlight", "garbage",
        "hanger", "ironing", "kettle", "luggage", "mattress", "napkin", "rug", "sponge", "stapler",
        "thermos", "vacuum", "wrench", "zipper", "battery", "plug", "switch", "magnet", "compass",
        # New easy words — clothing & accessories
        "boots", "scarf", "tie", "vest", "apron", "mittens", "sandals", "slippers", "hoodie", "cap",
        # New easy words — nature & weather
        "thunder", "rainbow", "tornado", "puddle", "sunset", "volcano", "cave", "beach", "pond", "creek",
        # New easy words — body & actions
        "sneeze", "yawn", "laugh", "cry", "dance", "jump", "swim", "climb", "crawl", "whistle",
        "clap", "wave", "hug", "kiss", "punch", "kick", "stretch", "sleep", "eat", "drink",
        # Moved from hard (easily actable)
        "relay", "astronaut", "firefighter",
    ],
    2: [
        # === MEDIUM (~600 words) — compound words, professions, activities, places ===
        # Original (deduplicated)
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
        "diploma", "dominos", "doughnut", "dragonfly", "drawbridge", "dumpster", "eclipse", "electrician", "elephant",
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
        "prisoner", "projector", "propeller", "puppet", "pyramid", "quarry", "quicksand", "raccoon", "radiator",
        "recorder", "referee", "refrigerator", "reindeer", "reptile", "restaurant", "rhinoceros", "rickshaw", "rollercoaster", "rooftop",
        "sailboat", "satellite", "scarecrow", "scissors", "scorpion", "sculptor", "seahorse", "seesaw", "seminary", "shamrock",
        "shipwreck", "shopping", "skeleton", "skydiving", "sleepwalk", "smuggler", "snowboard", "snowflake", "sombrero", "souvenir",
        "spaghetti", "speedboat", "spotlight", "squirrel", "staircase", "stampede", "starfish", "stilts", "stopwatch", "stroller",
        "submarine", "suitcase", "sundial", "sunscreen", "surfboard", "survivor", "swordfish", "symphony", "tadpole", "tarantula",
        "taxicab", "teapot", "toboggan", "toothbrush", "tornado", "tractor", "trapeze", "tricycle", "trolley", "trampoline",
        "tugboat", "tuxedo", "typewriter", "unicorn", "uniform", "vacation", "vampire", "ventilator", "veterinarian", "vineyard",
        "volleyball", "vulture", "waffle", "warehouse", "werewolf", "wheelchair", "whirlpool", "wildfire", "windshield", "wishbone",
        "woodpecker", "workshop", "wrestler", "xylophone", "yachtsman", "yearbook", "zeppelin", "zigzag", "zookeeper",
        "banister", "blueprint", "caramel", "dynamite", "equipment", "firehouse", "gondola", "holster", "inspector", "jukebox",
        "knapsack", "lifeguard", "mannequin", "nightclub", "overcoat", "paintball", "quickstep", "racetrack", "snowplow", "treadmill",
        "underwear", "viewpoint", "whiplash", "yardstick", "zucchini", "aardvark", "bullseye", "carnival", "dominoes", "espionage",
        "footprint", "gladiator", "handcuffs", "jackrabbit", "ketchup", "lollipop", "marmalade", "nightfall", "outrigger",
        "pendulum", "roulette", "sardine", "tightrope", "uppercut", "voodoo",
        "beekeeper", "candlestick", "earthquake", "foghorn", "gondolier", "hedgerow", "inkwell", "jackknife", "keepsake",
        "lemonade", "moonshine", "newsstand", "outfield", "pineapple", "raspberry", "slingshot", "thunderstorm", "windmill",
        # Moved from hard (actable with gestures)
        "blacksmith", "chandelier", "chessboard", "saxophone", "silhouette", "biography", "aquarium",
        "quarantine", "periscope", "observatory", "nightingale",
        # New medium words — professions & roles
        "bartender", "butcher", "carpenter", "dentist", "engineer", "farmer", "janitor", "journalist",
        "landlord", "lawyer", "mailman", "nurse", "optician", "photographer", "pilot", "plumber",
        "professor", "scientist", "secretary", "surgeon", "teacher", "waiter", "barber", "cashier",
        "chemist", "coach", "cobbler", "counselor", "firefighter", "florist",
        # New medium words — sports & activities
        "basketball", "baseball", "football", "tennis", "badminton", "gymnastics", "wrestling", "fencing",
        "karate", "boxing", "surfing", "skiing", "snowboarding", "skateboarding", "rollerblading",
        "bungee jumping", "rock climbing", "horseback riding", "ice skating", "scuba diving",
        # New medium words — animals & nature
        "chameleon", "cheetah", "crocodile", "flamingo", "hippopotamus", "hyena", "jaguar", "jellyfish",
        "meerkat", "narwhal", "panther", "platypus", "salamander", "stingray", "toucan", "walrus",
        "wolverine", "armadillo", "chinchilla", "porcupine",
        # New medium words — places & buildings
        "aquarium", "bookstore", "cemetery", "dungeon", "fortress", "gymnasium", "igloo",
        "junkyard", "kindergarten", "laboratory", "monastery", "observatory", "orphanage", "penthouse",
        "plantation", "reservoir", "sanctuary", "skyscraper", "treehouse", "warehouse",
        # New medium words — objects & things
        "accordion", "binoculars", "chandelier", "dreamcatcher", "envelope", "fishbowl",
        "greenhouse", "handkerchief", "icicle", "kaleidoscope", "megaphone", "nutcracker",
        "paperclip", "quicksand", "rocking chair", "scarecrow", "telescope", "umbrella",
        "weathervane", "xylophone",
        # New medium words — food & cooking
        "avocado", "baguette", "burrito", "cannoli", "croissant", "dumpling", "fondue",
        "granola", "jalapeno", "lasagna", "macaroni", "nachos", "omelette", "quesadilla",
        "ravioli", "smoothie", "tiramisu", "tortilla", "wasabi", "bruschetta",
    ],
    3: [
        # === HARD (~450 words) — abstract concepts, complex ideas, challenging to act ===
        # Original (minus words moved to medium/easy, deduplicated)
        "constellation", "cryptogram", "ecosystem",
        "greenhouse", "hologram", "hydraulic", "labyrinth", "microchip", "navigation",
        "parliament", "philosophy", "reflection", "renaissance",
        "tournament", "trajectory", "yesterday", "zephyr", "pyramids", "algorithm",
        "metaphor", "monarchy", "pipeline", "acupuncture", "amnesia", "anesthesia", "anthology",
        "apartheid", "archaeology", "aristocrat", "atmosphere", "autobiography", "bankruptcy", "barricade", "blasphemy",
        "bombardment", "bureaucracy", "camouflage", "capitalism", "catastrophe", "censorship", "choreography", "civilization",
        "claustrophobia", "colonialism", "communism", "compromise", "conspiracy", "contradiction", "controversy", "corruption",
        "counterfeit", "courtroom", "cybernetics", "dehydration", "democracy", "demolition", "depression", "desperation",
        "dictatorship", "diplomacy", "discrimination", "distillation", "documentary", "domesticate", "electromagnet", "embezzlement",
        "emigration", "empathy", "encryption", "enlightenment", "entrepreneur", "epidemiology", "equilibrium",
        "evaporation", "exaggeration", "extravagance", "fahrenheit", "fascination", "fluorescent", "foreclosure",
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
        "utilitarianism", "vaccination", "ventriloquist", "verification", "vulnerability", "xenophobia", "archeologist",
        "counterintelligence", "deforestation", "electrocution", "fingerprint", "hallucinate", "impersonation", "jurisprudence",
        "kleptomaniac", "libertarian", "malnutrition", "neurosurgeon", "osteoporosis", "plagiarize", "recollection",
        "stethoscope", "tuberculosis", "ventriloquism", "weightlessness", "bibliography", "cardiologist", "decapitation",
        "electromagnetic", "fermentation", "gerontology", "hyperventilate", "incarceration", "juxtaposition", "kinesiology",
        "loudspeaker", "misdemeanor", "neurological", "onomatopoeia", "phosphorescent", "socialization",
        "teleportation", "understaffed", "visualization", "whistleblower",
        # New hard words — emotions & states of mind
        "anxiety", "boredom", "confusion", "denial", "embarrassment", "frustration", "guilt", "jealousy",
        "loneliness", "melancholy", "paranoia", "regret", "resentment", "sarcasm", "suspicion", "temptation",
        "vertigo", "wanderlust", "déjà vu", "epiphany",
        # New hard words — abstract concepts
        "addiction", "ambiguity", "arrogance", "betrayal", "chaos", "conscience", "corruption", "destiny",
        "dilemma", "eternity", "evolution", "existence", "faith", "freedom", "gravity", "harmony",
        "illusion", "infinity", "innocence", "irony", "justice", "karma", "liberty", "logic",
        "mercy", "mystery", "nature", "oblivion", "patience", "peace", "poverty", "power",
        "pride", "progress", "reality", "sacrifice", "silence", "time", "truth", "wisdom",
        # New hard words — science & tech
        "artificial intelligence", "blockchain", "clone", "cryogenics", "dark matter", "DNA",
        "entropy", "fossil fuel", "genome", "holography", "isotope",
        "nanotechnology", "nuclear fusion", "parallel universe", "quantum physics", "relativity",
        "stem cell", "supernova", "synthetic biology", "virtual reality",
        # New hard words — social & political
        "abolition", "activism", "amnesty", "anarchy", "austerity", "bipartisan", "boycott",
        "coalition", "constitution", "coup", "embargo", "federalism", "gerrymander",
        "ideology", "imperialism", "insurgency", "lobby", "martial law", "monopoly",
        "populism", "propaganda", "referendum", "sanction", "sovereignty", "suffrage",
        "theocracy", "treaty", "tyranny", "veto",
        # New hard words — cultural & artistic
        "abstract art", "allegory", "baroque", "cubism", "expressionism", "folklore",
        "impressionism", "minimalism", "mythology", "opera", "poetry", "satire",
        "surrealism", "tragedy", "avant-garde", "renaissance",
        # New hard words — philosophical
        "altruism", "determinism", "dualism", "empiricism", "existentialism", "fatalism",
        "hedonism", "humanism", "nihilism", "pacifism", "pragmatism", "rationalism",
        "relativism", "stoicism", "utopia", "virtue",
        # New hard words — complex actions/situations
        "blackmail", "brainwash", "checkmate", "crossfire", "deadlock", "double agent",
        "filibuster", "honeytrap", "inception", "loophole", "mutiny", "overthrow",
        "paradox", "rebellion", "sabotage", "scapegoat", "standoff", "stalemate",
        "undercover", "whistleblower",
    ],
}

# Scribble words — drawable/visual things
SCRIBBLE_WORDS = {
    1: [
        # === EASY (~300 words) — simple drawable objects, single clear visuals ===
        # Original
        "smiley", "rainbow", "pizza slice", "stick figure", "snowman",
        "sunshine", "raindrop", "lollipop", "cupcake", "ice cream",
        "hotdog", "french fries", "donut", "watermelon", "strawberry",
        "pineapple", "mushroom", "cactus", "palm tree", "sunflower",
        "daisy", "tulip", "butterfly", "ladybug", "caterpillar",
        "snail", "bee", "owl", "penguin", "whale",
        "octopus", "starfish", "crab", "seashell", "jellyfish",
        "goldfish", "shark", "bat", "bunny", "bear",
        "panda", "elephant", "giraffe", "kangaroo", "koala",
        "flamingo", "peacock", "swan", "duck", "chick",
        "bicycle", "rocket", "helicopter", "sailboat", "submarine",
        "zip line", "school bus", "fire truck", "ambulance", "tractor",
        "castle", "church", "windmill", "barn", "teepee",
        "volcano", "mountain", "waterfall", "desert", "beach",
        "campfire", "tent", "fishing rod", "kite", "skateboard",
        "basketball", "soccer ball", "baseball bat", "tennis racket", "bowling pin",
        "trophy", "medal", "crown", "diamond ring", "treasure chest",
        "magic wand", "wizard hat", "pirate flag", "anchor", "compass",
        "hourglass", "alarm clock", "television", "laptop", "headphones",
        "microphone", "camera", "binoculars", "magnifying glass", "light bulb",
        # New easy words — animals
        "cat", "dog", "fish", "bird", "frog", "turtle", "horse", "pig", "cow", "chicken",
        "mouse", "rabbit", "snake", "spider", "lion", "tiger", "monkey", "dolphin", "fox", "deer",
        "parrot", "seahorse", "worm", "ant", "dragonfly", "seal", "goat", "sheep", "zebra", "camel",
        # New easy words — food & drink
        "apple", "banana", "cherry", "grapes", "orange", "lemon", "cake", "cookie", "pie", "bread",
        "egg", "cheese", "carrot", "corn", "broccoli", "candy", "popsicle", "milkshake", "juice box", "coffee cup",
        "pizza", "taco", "hamburger", "sandwich", "pancake", "waffle", "sushi roll", "pretzel", "muffin", "popcorn",
        # New easy words — objects
        "candle", "book", "pencil", "scissors", "key", "bell", "umbrella", "balloon", "gift box", "envelope",
        "cup", "plate", "spoon", "fork", "bottle", "bucket", "hammer", "wrench", "paintbrush", "broom",
        "glasses", "hat", "shoe", "sock", "shirt", "dress", "ring", "necklace", "watch", "backpack",
        # New easy words — nature
        "tree", "flower", "leaf", "cloud", "star", "moon", "sun", "river", "hill", "island",
        "snowflake", "lightning bolt", "wave", "rock", "fire", "icicle", "cave", "pond", "garden", "forest",
        # New easy words — buildings & vehicles
        "house", "boat", "car", "train", "airplane", "bus", "bridge", "tower", "igloo", "lighthouse",
        # New easy words — misc simple objects
        "heart", "arrow", "skull", "bone", "footprint", "handprint", "ladder", "flag", "door", "window",
        "fence", "mailbox", "trash can", "street lamp", "stop sign", "clock", "telephone", "guitar", "drum", "piano",
        # New easy words — round 2: toys & play
        "teddy bear", "yo-yo", "rocking horse", "rubber duck", "spinning top",
        "doll", "wagon", "sled", "marbles", "puzzle piece",
        "building blocks", "pinwheel", "frisbee", "bubble wand", "toy soldier",
        "toy box", "dominos", "dice", "paper airplane", "sand pail",
        # New easy words — round 2: musical instruments
        "violin", "trumpet", "flute", "harp", "banjo",
        "tambourine", "maracas", "tuba", "cello", "saxophone",
        "harmonica", "ukulele", "bongo drum", "xylophone", "recorder",
        # New easy words — round 2: kitchen items
        "toaster", "blender", "rolling pin", "whisk", "spatula",
        "teapot", "salt shaker", "cutting board", "oven mitt", "frying pan",
        "mixing bowl", "pot", "apron", "chef hat", "grater",
        "ladle", "tongs", "mug", "pitcher", "thermos",
        # New easy words — round 2: garden & tools
        "watering can", "flower pot", "wheelbarrow", "rake", "shovel",
        "lawn mower", "sprinkler", "bird bath", "garden gnome", "axe",
        "saw", "pliers", "screwdriver", "tape measure", "level",
        # New easy words — round 2: furniture
        "bed", "couch", "lamp", "shelf", "desk",
        "dresser", "stool", "crib", "chandelier", "wardrobe",
        "pillow", "rocking chair", "curtains", "bookcase", "nightstand",
        # New easy words — round 2: bathroom
        "bathtub", "shower", "toilet", "toothbrush", "soap bar",
        "towel", "razor", "hair dryer", "sponge", "bath mat",
        # New easy words — round 2: more food
        "candy cane", "gummy bear", "chocolate bar", "waffle cone", "peanut",
        "olive", "pickle", "celery", "onion", "potato",
        "tomato", "lettuce", "coconut", "pear", "peach",
        "kiwi", "mango", "plum", "hot chocolate", "smoothie",
        # New easy words — round 2: more animals
        "hedgehog", "porcupine", "squirrel", "chipmunk", "hamster",
        "puppy", "kitten", "duckling", "tadpole", "lobster",
        "shrimp", "clam", "eel", "rooster", "turkey",
        # New easy words — round 2: bugs
        "mosquito", "firefly", "grasshopper", "beetle", "cricket",
        "moth", "scorpion", "cockroach", "praying mantis", "hornet",
        # New easy words — round 2: clothing & accessories
        "tie", "bow tie", "belt", "cape", "scarf",
        "earmuffs", "mittens", "overalls", "tutu", "swimsuit",
        # New easy words — round 2: shapes & symbols
        "diamond shape", "spiral", "zigzag", "cross", "checkmark",
        "question mark", "exclamation mark", "hashtag", "infinity sign", "peace sign",
        # New easy words — round 2: everyday objects
        "tissue box", "tape roll", "stapler", "eraser", "ruler",
        "notebook", "calendar", "traffic cone", "shopping cart", "briefcase",
        "lunch box", "paper clip", "rubber band", "safety pin", "thimble",
        "piggy bank", "music note", "tiara", "paw print", "acorn",
        "pinecone", "feather", "seashell", "pearl", "horseshoe",
        # New easy words — round 2: misc objects
        "wind chime", "door knob", "light switch", "coat hanger", "power outlet",
        "ice cube", "tea bag", "candy jar", "cookie jar", "flower crown",
        "paper bag", "shoe lace", "pen cap", "cork", "clothespin",
    ],
    2: [
        # === MEDIUM (~300 words) — multi-part scenes, characters, actions ===
        # Original
        "roller coaster", "ferris wheel", "carousel", "water slide", "trampoline",
        "surfing", "skiing", "snowboarding", "parachute", "scuba diving",
        "fishing", "camping", "hiking", "rock climbing", "horseback riding",
        "juggling", "tightrope walker", "magician", "ballerina", "cheerleader",
        "astronaut", "robot", "alien", "dragon", "mermaid",
        "unicorn", "werewolf", "vampire", "ghost", "zombie",
        "scarecrow", "carved pumpkin", "christmas tree", "snowglobe", "gingerbread house",
        "birthday cake", "wedding cake", "breakfast table", "picnic", "barbecue grill",
        "sushi", "taco", "hamburger", "pancakes", "popcorn",
        "cotton candy", "chocolate fountain", "fruit basket", "salad bowl", "soup pot",
        "stethoscope", "microscope", "telescope", "test tube", "beaker",
        "globe", "bookshelf", "grand piano", "drum set", "electric guitar",
        "film projector", "movie theater", "stage curtain", "spotlight", "disco ball",
        "lighthouse", "bridge", "skyscraper", "igloo", "treehouse",
        "birdhouse", "doghouse", "aquarium", "terrarium", "greenhouse",
        "garden shed", "mailbox", "street lamp", "traffic light", "stop sign",
        "fire hydrant", "park bench", "swing set", "seesaw", "sandbox",
        "pirate ship", "viking ship", "canoe", "jet ski", "cruise ship",
        "space shuttle", "satellite dish", "radio tower", "solar panel", "wind turbine",
        "oil rig", "crane", "bulldozer", "forklift", "steam engine",
        # New medium words — characters & people
        "pirate", "ninja", "knight", "cowboy", "clown", "witch", "fairy", "angel",
        "superhero", "princess", "king", "queen", "wizard", "elf", "caveman",
        "samurai", "pharaoh", "viking", "gladiator", "detective",
        "chef", "scientist", "doctor", "firefighter", "police officer",
        # New medium words — activities & sports
        "bowling", "archery", "boxing", "karate", "wrestling", "gymnastics",
        "ice skating", "skateboarding", "bungee jumping", "hang gliding", "kayaking",
        "arm wrestling", "rope pull", "limbo", "hula hoop", "jump rope",
        "hopscotch", "peekaboo", "tag", "dodgeball", "volleyball",
        # New medium words — scenes & places
        "haunted house", "amusement park", "zoo", "circus tent", "movie set",
        "baseball field", "football stadium", "swimming pool", "ice rink", "bowling alley",
        "library", "museum", "hospital", "airport", "train station",
        "classroom", "playground", "farm", "jungle", "coral reef",
        # New medium words — fantasy & fiction
        "flying carpet", "time machine", "treasure map", "crystal ball", "magic lamp",
        "fairy castle", "enchanted forest", "dragon egg", "phoenix", "centaur",
        "cyclops", "minotaur", "kraken", "pegasus", "griffin",
        # New medium words — vehicles & machines
        "monster truck", "race car", "hot rod", "tank", "submarine",
        "blimp", "hang glider", "catapult", "trebuchet", "battering ram",
        "covered wagon", "stagecoach", "sleigh", "gondola", "hovercraft",
        # New medium words — food scenes
        "birthday party", "tea party", "cooking show", "lemonade stand", "food truck",
        "dessert cart", "bakery", "sushi bar", "pizza oven", "fruit stand",
        # New medium words — nature scenes
        "underwater scene", "bird nest", "ant hill", "beehive", "spider web",
        "tide pool", "rainforest", "arctic scene", "desert oasis", "cave painting",
        "erupting volcano", "meteor shower", "thunderstorm", "tornado", "avalanche",
        # New medium words — holiday & seasonal
        "easter egg", "valentine card", "halloween costume", "thanksgiving turkey", "menorah",
        "fireworks show", "new year", "halloween candy", "easter bunny", "santa claus",
        # New medium words — round 2: landmarks
        "eiffel tower", "stonehenge", "colosseum", "sphinx", "taj mahal",
        "big ben", "parthenon", "great pyramid", "golden gate", "mount rushmore",
        "leaning tower", "great wall", "opera house", "moai statue", "arc triomphe",
        # New medium words — round 2: machines & devices
        "grandfather clock", "cuckoo clock", "jukebox", "pinball machine", "slot machine",
        "gumball machine", "arcade cabinet", "typewriter", "sewing machine", "washing machine",
        "record player", "cash register", "music box", "gramophone", "telegraph",
        # New medium words — round 2: fantasy creatures
        "troll", "ogre", "goblin", "garden gnome", "leprechaun",
        "yeti", "bigfoot", "grim reaper", "tooth fairy", "medusa",
        "hydra", "gargoyle", "jackalope", "banshee", "thunderbird",
        # New medium words — round 2: food items
        "banana split", "boba tea", "cheese fondue", "ramen bowl", "steak dinner",
        "charcuterie board", "buffet table", "midnight snack", "root beer", "fondue pot",
        # New medium words — round 2: outdoor activities
        "bird watching", "star gazing", "kite flying", "dog walking", "ice fishing",
        "berry picking", "apple picking", "pumpkin patch", "hay ride", "bonfire",
        "picnic blanket", "beach volleyball", "snow angel", "leaf pile", "mud wrestling",
        # New medium words — round 2: rooms
        "living room", "dining room", "laundry room", "home office", "game room",
        "wine cellar", "recording studio", "art studio", "music room", "pantry",
        # New medium words — round 2: music
        "rock band", "drum circle", "street musician", "marching band", "karaoke night",
        "concert stage", "choir", "violin solo", "jazz band", "steel drums",
        # New medium words — round 2: water features
        "beaver dam", "canal boat", "whirlpool", "geyser", "hot spring",
        "frozen lake", "river rapids", "tidal wave", "water fountain", "watermill",
        # New medium words — round 2: vehicles
        "motorcycle", "police car", "garbage truck", "cement mixer", "dump truck",
        "tow truck", "delivery van", "paddle boat", "speed boat", "cargo ship",
        "limousine", "pickup truck", "mail truck", "moving truck", "news van",
        # New medium words — round 2: art & craft
        "origami crane", "pottery wheel", "sand sculpture", "ice sculpture", "snow fort",
        "blanket fort", "card house", "domino chain", "marble run", "finger painting",
        "paper snowflake", "tie dye", "bead necklace", "paper mache", "clay pot",
        # New medium words — round 2: school
        "school locker", "chemistry lab", "book report", "school cafeteria", "chalkboard",
        "science volcano", "lab coat", "school bell", "pencil case", "report card",
        # New medium words — round 2: sports
        "slam dunk", "home run", "touchdown", "foam finger", "starting line",
        "finish line", "podium ceremony", "halftime show", "figure skating", "speed skating",
        # New medium words — round 2: space
        "mars rover", "space station", "rocket launch", "asteroid belt", "saturn rings",
        "lunar eclipse", "comet trail", "spacewalk", "alien spaceship", "space helmet",
        # New medium words — round 2: nature scenes
        "wishing well", "hedge maze", "mirror maze", "rooftop garden", "zen garden",
        "butterfly garden", "koi pond", "bird feeder", "tree swing", "tire swing",
        # New medium words — round 2: places & structures
        "wizard tower", "throne room", "dungeon cell", "clock tower", "bell tower",
        "compass rose", "world map", "treasure map", "wanted poster", "totem pole",
        # New medium words — round 2: occupations
        "chimney sweep", "window washer", "crossing guard", "park ranger", "tour guide",
        "street vendor", "toll booth", "zookeeper", "ringmaster", "fortune teller",
        # New medium words — round 2: complex objects
        "dream catcher", "snow globe", "lava lamp", "bean bag", "water bed",
        "bunk bed", "fire escape", "tool belt", "lunch box", "first aid",
        # New medium words — round 2: weather
        "dust devil", "heat wave", "flash flood", "ice storm", "sand storm",
        "sun shower", "fog bank", "thunder cloud", "hail storm", "frost pattern",
        # New medium words — round 2: more vehicles
        "cable car", "ferry boat", "tugboat", "snow plow", "zamboni",
        # New medium words — round 2: games & entertainment
        "photo booth", "phone booth", "bus stop", "chess piece", "dart board",
        "pool table", "ping pong", "ski lift", "water tower", "grain silo",
        "weather vane", "bird cage", "fish tank", "ant farm", "hamster cage",
    ],
    3: [
        # === HARD (~160 words) — abstract concepts, complex scenes, hard to draw ===
        # Original
        "time travel", "black hole", "solar system", "northern lights", "coral reef",
        "food chain", "water cycle", "photosynthesis", "evolution", "gravity",
        "electricity", "magnetism", "ecosystem", "climate change", "recycling",
        "rush hour", "traffic jam", "assembly line", "construction site", "farmers market",
        "flea market", "garage sale", "lemonade stand", "food truck", "drive through",
        "escape room", "haunted house", "corn maze", "obstacle course", "treasure hunt",
        "spelling bee", "science fair", "talent show", "fashion show", "red carpet",
        "graduation ceremony", "wedding reception", "surprise party", "baby shower", "family reunion",
        "pillow fight", "food fight", "snowball fight", "rope pull", "peekaboo",
        "musical chairs", "freeze tag", "flag capture", "relay race", "marathon",
        "opera singer", "orchestra pit", "puppet show", "shadow puppet", "ventriloquist",
        "sword swallower", "fire breather", "snake charmer", "fortune teller", "time capsule",
        # New hard words — abstract concepts to draw
        "dream", "nightmare", "memory", "imagination", "loneliness",
        "happiness", "anger", "fear", "love", "heartbreak",
        "freedom", "peace", "war", "chaos", "silence",
        "time", "infinity", "luck", "karma", "destiny",
        # New hard words — complex scenes
        "earthquake", "shipwreck", "bank robbery", "car chase", "prison break",
        "space walk", "moon landing", "deep dive", "mountain rescue", "jungle expedition",
        "archaeological dig", "crime scene", "courtroom trial", "market crash", "protest march",
        # New hard words — science concepts
        "dna strand", "atom", "molecule", "virus", "bacteria",
        "big bang", "constellation", "galaxy", "supernova", "wormhole",
        "tornado formation", "tectonic plates", "erosion", "fossil formation", "metamorphosis",
        # New hard words — daily life concepts
        "monday morning", "homework", "traffic ticket", "job interview", "first date",
        "moving day", "spring cleaning", "road trip", "lost luggage", "flat tire",
        "power outage", "broken phone", "alarm clock", "bad haircut", "missed bus",
        # New hard words — idioms & expressions (draw the literal meaning)
        "pet rain", "easy cake", "broken leg", "cold shoulder", "stomach butterflies",
        "room elephant", "couch potato", "night owl", "early bird", "brain freeze",
        "tunnel light", "bean spill", "nail hammer", "spilled milk", "eggshell walk",
        # New hard words — round 2: idioms (draw the literal image)
        "flying pig", "spilled beans", "cold shoulder", "hot potato",
        "crying wolf", "burning bridge", "couch potato", "night owl",
        "early bird", "brain freeze", "wild chase", "cat bag",
        "needle haystack", "raining cats", "money tree",
        # New hard words — round 2: battle scenes
        "zombie apocalypse", "alien invasion", "robot uprising", "pirate mutiny", "viking raid",
        "samurai duel", "wizard battle", "dragon slaying", "knight jousting", "gladiator fight",
        "medieval siege", "naval battle", "sword fight", "space battle", "tank battle",
        # New hard words — round 2: sci-fi
        "teleportation", "cryogenics", "force field", "shrink ray", "mind control",
        "invisibility cloak", "laser sword", "cyborg", "android", "warp drive",
        "tractor beam", "death ray", "plasma cannon", "robot army", "clone army",
        # New hard words — round 2: visual puzzles
        "optical illusion", "impossible staircase", "penrose triangle", "mobius strip", "mirror world",
        "domino effect", "chain reaction", "butterfly effect", "forced perspective", "infinity mirror",
        "matryoshka dolls", "ouroboros", "anamorphic art", "vanishing point", "tessellation",
        # New hard words — round 2: historical
        "titanic sinking", "trojan horse", "gold rush", "moon landing", "chariot race",
        "pyramid builders", "viking voyage", "gladiator arena", "silk road", "columbus voyage",
        "wright flyer", "cave painting", "first fire", "roman bath", "medieval market",
        # New hard words — round 2: modern life
        "selfie stick", "video call", "food delivery", "drone delivery", "online shopping",
        "airport security", "moving day", "graduation toss", "office cubicle", "vending machine",
        "parking meter", "speed camera", "self checkout", "road rage", "rush hour",
        # New hard words — round 2: surreal art
        "melting clock", "floating island", "upside city", "flying fish", "walking tree",
        "underground ocean", "cloud house", "sky door", "mirror portal", "book portal",
        "living statue", "frozen motion", "giant miniature", "raining objects", "impossible room",
        # New hard words — round 2: transformations
        "cocoon hatching", "phoenix rising", "werewolf change", "snowman melting", "volcano island",
        "glacier melting", "desert bloom", "aging face", "season change", "metamorphosis",
        "forest regrowth", "fossil forming", "erosion canyon", "river delta", "coral bleaching",
        # New hard words — round 2: complex activities
        "tightrope walk", "bomb defusing", "safe cracking", "lion taming", "maze escape",
        "everest summit", "deep diving", "cave exploring", "storm chasing", "puzzle solving",
        "glass blowing", "sword swallowing", "fire breathing", "knife throwing", "plate spinning",
        # New hard words — round 2: myths & legends
        "pandoras box", "midas touch", "medusa gaze", "minotaur labyrinth", "icarus flight",
        "noahs ark", "rapunzel tower", "pied piper", "frankenstein monster", "dracula coffin",
        "ghost ship", "genie lamp", "excalibur sword", "holy grail", "kraken attack",
        # New hard words — round 2: contrast scenes
        "fire ice", "day night", "land sea", "summer winter", "city nature",
        "past future", "predator prey", "desert ocean", "mountain valley", "feast famine",
        "calm storm", "order chaos", "giant ant", "old new", "fast slow",
        # New hard words — round 2: chain events
        "rube goldberg", "domino fall", "card collapse", "jenga fall", "avalanche start",
        "sandcastle wave", "paper boat", "ant army", "marble race", "balloon chain",
        "mousetrap chain", "waterfall cascade", "snowball rolling", "dam breaking", "lava flow",
        # New hard words — round 2: mysterious & paranormal
        "time loop", "stage fright", "deja vu", "sleep walking", "lucid dream",
        "cabin fever", "witch hunt", "escape artist", "crop circle", "bermuda triangle",
        "urban legend", "lost city", "crystal cave", "mirror dimension", "ghost town",
    ],
}


def seed_words(db: Session) -> int:
    existing = {(w.text, w.game_type) for w in db.query(Word.text, Word.game_type).all()}
    inserted = 0

    # Seed charades words
    for difficulty, words in CHARADES_WORDS.items():
        for text in words:
            key = (text, "charades")
            if key not in existing:
                db.add(Word(text=text, difficulty=difficulty, active=True, game_type="charades"))
                existing.add(key)
                inserted += 1

    # Seed scribble words
    for difficulty, words in SCRIBBLE_WORDS.items():
        for text in words:
            key = (text, "scribble")
            if key not in existing:
                db.add(Word(text=text, difficulty=difficulty, active=True, game_type="scribble"))
                existing.add(key)
                inserted += 1

    if inserted > 0:
        db.commit()
    return inserted
