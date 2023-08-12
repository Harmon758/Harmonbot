
import random


ELIZABETHAN_ADJECTIVES = (
    "Artless", "Bawdy", "Beslubbering", "Bootless", "Churlish", "Cockered",
    "Clouted", "Craven", "Currish", "Dankish", "Dissembling", "Droning",
    "Errant", "Fawning", "Fobbing", "Froward", "Frothy", "Gleeking", "Goatish",
    "Gorbellied", "Impertinent", "Infectious", "Jarring", "Loggerheaded",
    "Lumpish", "Mammering", "Mangled", "Mewling", "Paunchy", "Pribbling",
    "Puking", "Puny", "Quailing", "Rank", "Reeky", "Roguish", "Ruttish",
    "Saucy", "Spleeny", "Spongy", "Surly", "Tottering", "Unmuzzled", "Vain",
    "Venomed", "Villainous", "Warped", "Wayward", "Weedy", "Yeasty"
)
ELIZABETHAN_COMPOUND_ADJECTIVES = (
    "Base-court", "Bat-fowling", "Beef-witted", "Beetle-headed",
    "Boil-brained", "Clapper-clawed", "Clay-brained", "Common-kissing",
    "Crook-pated", "Dismal-dreaming", "Dizzy-eyed", "Dog-hearted",
    "Dread-bolted", "Earth-vexing", "Elf-skinned", "Fat-kidneyed",
    "Fen-sucked", "Flap-mouthed", "Fly-bitten", "Folly-fallen", "Fool-born",
    "Full-gorged", "Guts-griping", "Half-faced", "Hasty-witted", "Hedge-born",
    "Hell-hated", "Idle-headed", "Ill-breeding", "Ill-nurtured",
    "Knotty-pated", "Milk-livered", "Motley-minded", "Onion-eyed",
    "Plume-plucked", "Pottle-deep", "Pox-marked", "Reeling-ripe", "Rough-hewn",
    "Rude-growing", "Rump-fed", "Shard-borne", "Sheep-biting", "Spur-galled",
    "Swag-bellied", "Tardy-gaited", "Tickle-brained", "Toad-spotted",
    "Unchin-snouted", "Weather-bitten"
)
ELIZABETHAN_NOUNS = (
    "Apple-john", "Baggage", "Barnacle", "Bladder", "Boar-pig", "Bugbear",
    "Bum-bailey", "Canker-blossom", "Clack-dish", "Clot-pole", "Coxcomb",
    "Codpiece", "Death-token", "Dewberry", "Flap-dragon", "Flax-wench",
    "Flirt-gill", "Foot-licker", "Fustilarian", "Giglet", "Gudgeon", "Haggard",
    "Harpy", "Hedge-pig", "Horn-beast", "Huggermugger", "Jolt-head",
    "Lewdster", "Lout", "Maggot-pie", "Malt-worm", "Mammet", "Measle",
    "Minnow","Miscreant", "Mold-warp", "Mumble-news", "Nut-hook", "Pigeon-egg",
    "Pignut", "Puttock","Pumpion", "Rats-bane", "Scut", "Skains-mate",
    "Strumpet", "Varlot", "Vassal", "Whey-face", "Wagtail"
)


def generate_elizabethan_insult():
    # https://web.archive.org/web/20170717092231/http://www.museangel.net/insult.html
    # https://gist.github.com/quandyfactory/258915
    # https://quandyfactory.com/insult
    # https://quandyfactory.com/insult/json
    adjective = random.choice(ELIZABETHAN_ADJECTIVES)
    article = "an" if adjective.startswith(('A', 'E', 'I', 'O', 'U')) else 'a'
    return (
        f"Thou art {article} {adjective}, "
        f"{random.choice(ELIZABETHAN_COMPOUND_ADJECTIVES)} "
        f"{random.choice(ELIZABETHAN_NOUNS)}."
    )

