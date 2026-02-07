from sqlalchemy.orm import Session

from app.models.word import Word

WORDS = {
    1: [
        "apple", "chair", "river", "pencil", "cloud", "window", "pillow", "garden", "coffee", "mirror",
        "bottle", "candle", "camera", "basket", "button", "carpet", "cookie", "door", "flower", "guitar",
        "hammer", "hat", "island", "jacket", "key", "lamp", "leaf", "map", "moon", "notebook",
        "ocean", "orange", "paint", "paper", "phone", "plant", "plate", "rain", "ring", "rope",
    ],
    2: [
        "airplane", "backpack", "balloon", "barbecue", "binoculars", "calendar", "campfire", "carousel", "compass", "computer",
        "construction", "cupcake", "dinosaur", "elevator", "fireworks", "flashlight", "fountain", "headphones", "highway", "hospital",
        "keyboard", "lighthouse", "mountain", "musical", "necklace", "newspaper", "passport", "rainbow", "sandcastle", "spaceship",
        "sunflower", "telescope", "thermometer", "trainstation", "treasure", "umbrella", "vending", "volcano", "waterfall", "whistle",
    ],
    3: [
        "astronaut", "blacksmith", "blueprint", "chandelier", "chessboard", "constellation", "cryptogram", "earthquake", "ecosystem", "firefighter",
        "greenhouse", "hologram", "hydraulic", "labyrinth", "microchip", "navigation", "nightingale", "observatory", "parliament", "periscope",
        "philosophy", "quarantine", "reflection", "renaissance", "saxophone", "silhouette", "tournament", "trajectory", "windmill", "xylophone",
        "yesterday", "zephyr", "biography", "pyramids", "relay", "algorithm", "aquarium", "metaphor", "monarchy", "pipeline",
    ],
}


def seed_words(db: Session) -> int:
    existing = db.query(Word).count()
    if existing >= 100:
        return 0

    inserted = 0
    for difficulty, words in WORDS.items():
        for text in words:
            if not db.query(Word).filter(Word.text == text).first():
                db.add(Word(text=text, difficulty=difficulty, active=True))
                inserted += 1
    db.commit()
    return inserted
