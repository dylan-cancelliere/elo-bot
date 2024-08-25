import discord
import os
import requests
from dotenv import load_dotenv

### Constants
API_BASE_URL = "http://localhost:8000"

COMMAND_PREFIX = "$civ-bot"
COMMAND_INFO = "info"

INVALID_COMMAND = "Error: invalid command"
HELP_COMMAND ="""
Available commands:\n
`$civ-bot info @username`: displays stats for player a given player\n
`$civ-bot lobby`: displays rating info for all users in your vc\n
`$civ-bot create`: logs your game. TBD
"""
###

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
        case _:
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