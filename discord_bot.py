import discord
import os
import requests
from constants import *
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

async def handleCommand(message, channel):
    tokens = message.content.split(" ")
    if len(tokens) < 2:
        await channel.send(INVALID_COMMAND)
        return
    match tokens[1]:
        case "help":
            await channel.send(HELP_COMMAND)
        case "info":
            if len(tokens) != 3:
                await channel.send(INVALID_COMMAND)
                return
            await handleGetInfo(tokens[2], channel)
        case "lobby":
            await handleGetLobby(message)
        case "list":
            await channel.send("Civ names:\n{}".format(" ".join(list(map(lambda x: "`{}`".format(x), CIV_LIST)))))
        case "create":
            print(message.content)
        case _:
            if tokens[1].startswith("create"):
                await handleCreateGame(message)
                return
            await channel.send(INVALID_COMMAND + "\n\n" + HELP_COMMAND)

async def handleGetInfo(player: str, channel):
    res = requests.get("{}/player/{}".format(API_BASE_URL, player)).json()
    if res is None:
        await channel.send("Error: no player \"{}\" found. Players must log at least one game to appear".format(player))
        return
    await channel.send(
"""```py
{}```""".format(printUserRating(player, res["ffa_rating"], res["teamers_rating"]))
    )

async def handleGetLobby(message):
    if message.author.voice is None:
        await message.channel.send("Error: user is not connected to a voice channel")
        return
    vc_members = ",".join(list(map(lambda x: x.name, client.get_channel(message.author.voice.channel.id).members)))
    users_query = requests.get("{}/players/{}".format(API_BASE_URL, vc_members)).json()
    if users_query is not None and "players" in users_query and len(users_query["players"]) > 0:
        formatted_players = list(map(lambda x: printUserRating(x['name'], x['ffa_rating'], x['teamers_rating']), users_query["players"]))
        print(formatted_players)
        await message.channel.send("""```py
{}
```""".format("\n".join(formatted_players))
        )
    print("USER QUERY", users_query)

async def handleCreateGame(message):
    content = message.content.split("\n")
    index = 1

    # Game params
    # map is reserved
    map_name = ""
    bbg = False
    league = None
    lobby_bans = []
    players = []

    while index < len(content) and content[index] != "":
        line = content[index].split(": ")
        if len(line) < 2:
            return None
        cmd = line[0].lower()
        ops = line[1].strip()
        match cmd:
            case "map":
                map_name = ops
            case "league":
                league = ops
            case "bbg":
                bbg = ops.lower() in ['yes', 'true', 't', 'y', '1']
            case "lobby_bans":
                lobby_bans = ops.split(" ")
                lobby_bans = list(filter(lambda x: x in CIV_LIST, lobby_bans))
                if len(lobby_bans) < len(ops.split(" ")): await message.channel.send("Game logger: Skipping some unknown civs in lobby bans (warning)")
            case _:
                await message.channel.send("Game logger: Skipping unknown option '{}' (warning)".format(cmd))
        index += 1

    while index < len(content) and content[index] == "":
        index += 1

    while index < len(content) and content[index] != "":
        player_line = content[index].strip().split(" ")
        player_line = list(filter(lambda y: y != "", player_line))
        print("PLAYER LINE:", player_line)
        position = player_line[0]
        if '.' in position:
            position = position[:-1]
            if not position.isdigit():
                await message.channel.send("Game logger: Error parsing player list: invalid placement '{}'".format(position))
                return
        # example format: 1. @killer_diller yongle bans peter
        if len(player_line) < 3:
            await message.channel.send("Game logger: Error parsing player list: expected min 2 player arguments, got {}".format(len(player_line)-1))
            return
        name = player_line[1]
        civ = player_line[2].lower()
        if civ not in CIV_LIST:
            await message.channel.send("Game logger: Error parsing player list: unknown civ '{}'".format(civ))

        bans = []
        for x in range(3,len(player_line)):
            ban = player_line[x].lower()
            if ban == "bans": continue
            if ban not in CIV_LIST:
                await message.channel.send("Game logger: Skipping unknown civ ban '{}' (warning)".format(ban))
            bans.append(ban)


        players.append({"player_name": name, "civ_name": civ, "placement": int(position), "bans": bans})
        index += 1

    teams = None
    if players[1]["placement"] == 1:
        teams = []
        counter = 1
        for player in players:
            if player["placement"] == counter:
                teams[counter-1].append(player["player_name"])
            else:
                teams.append([player["player_name"]])

    body = {
        "date": datetime.today().strftime('%d-%m-%Y'),
        "players": players,
        "teams": teams,
        "bans": list(map(lambda x: dict(player_name=x["player_name"], bans=x["bans"]), players)),
        "map": map_name,
        "bbg": bbg
    }

    res = requests.post("{}/game".format(API_BASE_URL), json=body).json()
    print(res)


def printUserRating(name, ffa, teamers):
    return "{}:\n\tFFA:\t\t{}\n\tTeamers:\t{}".format(name, ffa, teamers)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(COMMAND_PREFIX):
        await handleCommand(message, message.channel)

client.run(os.getenv('DISCORD_BOT_TOKEN'))