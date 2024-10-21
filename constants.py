API_BASE_URL = "http://localhost:8000"


COMMAND_PREFIX = "$civ-bot"
COMMAND_INFO = "info"

INVALID_COMMAND = "Error: invalid command"
HELP_COMMAND = """
Available commands:\n
`$civ-bot info @username`: displays stats for player a given player\n
`$civ-bot lobby`: displays rating info for all users in your vc\n
`$civ-bot create`: logs your game. TBD\n
`$civ-bot list`: lists all civ names recognized by the bot\n
`$civ-bot random-civs players @p1 @p2... bans civ1 civ2...`: Assigns each player up to six random civs to choose from, excluding banned civs
"""

CIV_LIST = ["abraham-lincoln", "alexander", "amanitore", "ambiorix", "ba-trieu", "basil",
"catherine-black-queen", "catherine-magnificence", "chandragupta", "cleopatra-egyptian",
"cleopatra-ptolemaic", "cyrus", "dido", "eleanor", "elizabeth", "frederick-barbarossa",
"gandhi", "genghis-khan", "gilgamesh", "gitarja", "gorgo", "hammurabi", "harald-konge",
"harald-varangian", "hojo-tokimune", "jadwiga", "jayavarman", "joao", "john-curtain",
"julius-caesar", "kristina", "kublai-khan", "kupe", "lady-six-sky", "lautaro", "ludwig",
"mansa-musa", "matthias-corvinus", "menelik", "montezuma", "mvemba-a-nzinga", "nader-shah",
"nzinga-mbande", "pachacuti", "pedro", "pericles", "peter", "philip", "poundmaker",
"qin-mandate", "qin-unifier", "ramses", "robert-the-bruce", "saladin-sultan",
"saladin-vizier", "sejong", "seondeok", "shaka", "simon-bolivar", "suleiman-kanuni",
"suleiman-muhtesem", "sundiata-keita", "tamar", "teddy-bull-moose", "teddy-rough-rider",
"theodora", "tokugawa", "tomyris", "trajan", "victoria-empire", "victoria-steam",
"wilfrid-laurier", "wilhelmina", "wu-zeitan", "yongle"]

MAX_RANDOM_CIVS = 6