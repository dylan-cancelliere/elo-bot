import discord
import os
import requests
from dotenv import load_dotenv

### Constants
API_BASE_URL = "http://localhost:8000"

COMMAND_PREFIX = "$civ-bot"
COMMAND_INFO = "info"

INVALID_COMMAND = "Error: invalid command"
###

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

async def handleCommand(message: str, channel):
    tokens = message.split(" ")
    if len(tokens) < 2:
        await channel.send(INVALID_COMMAND)
        return
    match tokens[1]:
        case "info":
            if len(tokens) != 3:
                await channel.send(INVALID_COMMAND)
                return
            await handleGetInfo(tokens[2], channel)


async def handleGetInfo(player: str, channel):
    res = requests.get("{}/player/{}".format(API_BASE_URL, player)).json()
    if res is None:
        await channel.send("Error: no player \"{}\" found. Players must log at least one game to appear".format(player))
        return
    await channel.send(
        """```py
{}:\nFFA:\t\t{}\nTeamers:\t{}
```""".format(player, res["ffa_rating"], res["teamers_rating"])
    )

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(COMMAND_PREFIX):
        print("MESSAGE CONTENT:", message.content)
        await handleCommand(message.content, message.channel)

client.run(os.getenv('DISCORD_BOT_TOKEN'))