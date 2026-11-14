"""Fast, conservative screening for obvious unsafe requests, jailbreaks, and persona boundary violations."""

import re
import unicodedata

REFUSAL = "I can’t help with that request."
ANIMAL_REFUSAL = "I cannot imitate animal sounds or act as an animal. I am a professional AI voice assistant."

_INJECTION = re.compile(
    r"\b(ignore|disregard|bypass|override)\b.{0,50}\b(previous|prior|system|safety)\b.{0,30}\b(instruction|rule|prompt|boundary)s?\b"
    r"|\b(jailbreak|developer mode|reveal (the )?(system prompt|hidden instructions))\b",
    re.IGNORECASE,
)
_HIGH_RISK = re.compile(
    r"\b(how (do i|to)|help me|write|make|build|create|generate|execute|run|send|steal|break into)\b"
    r".{0,100}\b(kill|hurt|attack|assault|self[- ]?harm|suicide|harass|abuse|exploit|"
    r"fraud|phish|steal|rob|pirate|hack|malware|ransomware|keylogger|ddos|spam|exfiltrat|"
    r"unauthorized access|animal cruelty|hurt (a )?animal)\b",
    re.IGNORECASE,
)

# Animal sound, vocalization, and roleplay patterns
_ANIMAL_WORDS = (
    r"(animal|animals|dog|dogs|cat|cats|puppy|puppies|kitten|kittens|lion|lions|tiger|tigers|"
    r"cow|cows|bull|bulls|wolf|wolves|monkey|monkeys|ape|apes|chimpanzee|bear|bears|sheep|lamb|"
    r"goat|goats|pig|pigs|horse|horses|donkey|donkeys|duck|ducks|bird|birds|crow|crows|rooster|roosters|"
    r"hen|hens|chicken|chickens|frog|frogs|snake|snakes|elephant|elephants|hyena|hyenas|"
    r"janwar|kutte|kutta|billi|sher|gaay)"
)
_SOUND_VERBS = (
    r"(bark|barks|barking|meow|meows|meowing|mew|mews|roar|roars|roaring|quack|quacks|quacking|"
    r"oink|oinks|oinking|moo|moos|mooing|neigh|neighs|neighing|howl|howls|howling|chirp|chirps|chirping|"
    r"bleat|bleats|bleating|hiss|hisses|hissing|growl|growls|growling|purr|purrs|purring|"
    r"cluck|clucks|clucking|bhonk|bhonko|myaun)"
)
_SOUND_NOUNS = r"(sound|sounds|noise|noises|vocalization|vocalizations|impression|impressions|voice|awaaz|awaz)"
_ACTION_VERBS = r"(make|produce|generate|do|give|imitate|mimic|reproduce|nikalo|karo|batao)"

_P_MAKE_SOUND = rf"\b{_ACTION_VERBS}\b.{{0,30}}\b({_ANIMAL_WORDS}\s+{_SOUND_NOUNS}|{_SOUND_NOUNS}\s+of\s+{_ANIMAL_WORDS}|{_SOUND_VERBS})\b"
_P_ACT_LIKE = rf"\b(sound|act|behave|talk|speak|perform)\b.{{0,20}}\b(like|as)\b.{{0,15}}\b(an?|the)?\s*{_ANIMAL_WORDS}\b"
_P_PRETEND = rf"\b(pretend|roleplay|impersonate)\b.{{0,25}}\b(to be|you are|you\'re|being)?\s*(an?|the)?\s*{_ANIMAL_WORDS}\b"
_P_DIRECT_COMMAND = rf"^(can you|could you|would you|will you|please|now)?\s*(just\s+)?(bark|meow|roar|quack|oink|moo|neigh|howl|chirp|bleat|hiss|growl|purr)(\s+(for me|like\s+(a|an|the)?\s*{_ANIMAL_WORDS}|now|please|loudly))?[\s.!?]*$"
_P_HINDI = rf"\b{_ANIMAL_WORDS}\b.{{0,20}}\b(ki tarah|jaise|ki awaaz|ki awaz|bhonko)\b"

_ANIMAL_IMPERATIVES = re.compile(
    "|".join(f"({p})" for p in [_P_MAKE_SOUND, _P_ACT_LIKE, _P_PRETEND, _P_HINDI]),
    re.IGNORECASE,
)
_ANIMAL_DIRECT_COMMAND = re.compile(_P_DIRECT_COMMAND, re.IGNORECASE)

_ANIMAL_ONOMATOPOEIA = re.compile(
    r"\b(woof|meow|mew|quack|oink|moo|neigh|baa|baa+|ribbit|caw|cluck|chirp|rawr|roar|hiss|growl|bhow|bow-wow)\b",
    re.IGNORECASE,
)


def is_animal_request(text: str) -> bool:
    """Return True if the text asks the agent to make animal sounds or act/roleplay as an animal."""
    normalized = unicodedata.normalize("NFKC", text).strip().lower()
    normalized = re.sub(r"[\u200b-\u200f\ufeff]", "", normalized)

    # Exclude purely educational or informational questions
    if re.match(
        r"^(why|what is|what are|explain|tell me about)\b|^(do|does)\s+[a-z]+s?\s+(bark|meow|roar|quack|eat|sleep|live)\b",
        normalized,
    ):
        return False

    return bool(_ANIMAL_IMPERATIVES.search(normalized) or _ANIMAL_DIRECT_COMMAND.match(normalized))


def contains_animal_noises(text: str) -> bool:
    """Detect if generated text contains animal sounds or onomatopoeia."""
    matches = _ANIMAL_ONOMATOPOEIA.findall(text)
    if len(matches) >= 2:
        return True
    if len(matches) == 1 and re.search(
        r"^(woof|meow|quack|moo|roar|oink|neigh|bhow)[\s!.]*$", text.strip(), re.IGNORECASE
    ):
        return True
    return False


def screen_user_text(text: str) -> bool:
    """Return True when text contains an obvious jailbreak, harmful command, or animal sound/roleplay attempt."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"[\u200b-\u200f\ufeff]", "", normalized)
    if _INJECTION.search(normalized) or _HIGH_RISK.search(normalized):
        return True
    return is_animal_request(text)


def get_refusal_for_text(text: str) -> str:
    """Return specific refusal message based on the type of screened violation."""
    if is_animal_request(text):
        return ANIMAL_REFUSAL
    return REFUSAL
