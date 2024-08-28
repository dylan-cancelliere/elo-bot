from datetime import datetime
from typing import NamedTuple
from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
from openskill.models import PlackettLuce, PlackettLuceRating
from copy import deepcopy
import sqlite3
import time

class PlayerDbType(NamedTuple):
    name: str
    ffa_rating: float
    teamers_rating: float
    ffa_sigma: float
    teamers_sigma: float

class PlayerRecord(NamedTuple):
    player_name: str
    civ_name: str
    placement: int
    bans: list[str]

class PlayerPlacement(NamedTuple):
    player_name: str
    placement: int
    rating: float
    sigma: float

class BanRecord(NamedTuple):
    player_name: str
    # List of civ names
    bans: list[str]

class Game(NamedTuple):
    date: str
    players: list[PlayerRecord]
    # list of teams, each team is a list of player names
    teams: list[list[str]] | None = None
    bans: list[BanRecord] = []
    map: str | None = None
    bbg: bool = False

class PlayerChange(BaseModel):
    name: str
    new_elo: int
    elo_change: int

RATING_MULT = 40
app = FastAPI()
conn = sqlite3.connect("civsix.sqlite")
cursor = conn.cursor()
print("DB Initialized")



def get_player_query(player: str) -> str:
    return """select * from players where name is '{}'""".format(player)

def update_player_query(name: str, ffa_rating: float | None = None, ffa_sigma: float | None = None, teamers_rating: float | None = None, teamers_sigma: float | None = None) -> str:
    params = []
    if ffa_rating is not None:
        params.append("\'ffa_rating\' = {},".format(ffa_rating))
        params.append("\'ffa_sigma\' = {}".format(ffa_sigma))
    else:
        params.append("\'teamers_rating\' = {},".format(teamers_rating))
        params.append("\'teamers_sigma\' = {}".format(teamers_sigma))
    params = " ".join(params)
    test = """update players set {} where name is '{}'""".format(params, name)
    return test

def get_team_num_from_player(teams: list[list[str]], player: str) -> int:
    for i in range(len(teams)):
        for p in teams[i]:
            if p == player: return i

@app.get("/")
async def root():
    return {"message": "Hello World"}

# @app.get("/hello/{name}")
# async def say_hello(name: str):
#     return {"message": f"Hello {name}"}
#

@app.get("/player/{name}")
async def get_player(name: str):
    result = cursor.execute(get_player_query(name)).fetchall()
    if len(result) == 0:
        return None
    return {"name": result[0][0], "ffa_rating": int(result[0][1] * RATING_MULT), "teamers_rating": int(result[0][2] * RATING_MULT),}

@app.get("/players/{players}")
async def get_players(players: str):
    if players == "": return {}
    player_list = players.split(",")
    fetched_list = []
    for player in player_list:
        print(player)
        res = cursor.execute(get_player_query(player)).fetchall()
        print("Test",res)

        fetched_list.append([player, None, None]) if len(res) == 0 else fetched_list.append(res[0])
    return {"players": list(map(lambda x: {"name": x[0], "ffa_rating": None if x[1] is None else int(x[1] * RATING_MULT), "teamers_rating": None if x[2] is None else int(x[2] * RATING_MULT)} , fetched_list))}

@app.post("/game")
async def create_game(game: Game) -> list[PlayerChange]:
    # Generate game
    game_id = uuid4()
    cursor.execute("""insert into games (id, date map, bbg)
       values ('{}', {}, {}, '{}')""".format(
        game_id, game.date, game.map, game.bbg
    ))

    is_teamer_game = game.teams is not None
    player_ratings: list[PlayerPlacement] = []
    # Log picks, bans, and placements
    for player in game.players:
        # Pick
        cursor.execute("""insert into game_civ_picks (game_id, civ_name, player_name) values ('{}', '{}', '{}')""".format(game_id, player[1], player[0]))
        # Bans
        for ban in player[3]:
            cursor.execute("""insert into game_civ_bans (game_id, civ_name, player_name) values ('{}', '{}', '{}')""".format(game_id, ban, player[0]))
        # Placement
        cursor.execute("""insert into game_players (game_id, player_name, placement) values ('{}', '{}', {})""".format(game_id, player[0], player[2]))
        # Get player ratings
        res: list[PlayerDbType] = cursor.execute(get_player_query(player[0])).fetchall()
        if (len(res) == 0 or
            (is_teamer_game and res[0][2] is None) or
            (not is_teamer_game and res[0][1] is None)
        ):
            player_ratings.append(PlayerPlacement(player[0], player[2], 25, 25 / 3))
            if len(res) == 0:
                cursor.execute("""insert into players (name, ffa_rating, teamers_rating, ffa_sigma, teamers_sigma) values ('{}', null, null, null, null)""".format(player[0]))
            if is_teamer_game:
                cursor.execute("""{}""".format(update_player_query(name=player[0], teamers_rating=25, teamers_sigma=25/3, ffa_rating=None, ffa_sigma=None)))
            else:
                cursor.execute("""{}""".format(update_player_query(name=player[0], ffa_rating=25, ffa_sigma=25/3, teamers_rating=None, teamers_sigma=None)))
        else:
            if is_teamer_game:
                player_ratings.append(PlayerPlacement(player[0], player[2], res[0][2], res[0][4]))
            else:
                player_ratings.append(PlayerPlacement(player[0], player[2], res[0][1], res[0][3]))


    # Calculate and log rating changes
    model = PlackettLuce()
    player_ratings.sort(key=lambda x: x[1])
    if is_teamer_game:
        def get_player_plackett(player_name: str) -> PlackettLuceRating:
            p = next((x for x in player_ratings if x[0] == player_name))
            return model.create_rating(name=player_name, rating=[p[2], p[3]])

        plackett_order = list(map(lambda team: list(map(lambda p: get_player_plackett(p), team)), game.teams))
        updated_plackett = model.rate(deepcopy(plackett_order))
        counter = 0
        for t in updated_plackett:
            # Keeps track of placement
            counter+=1
            for p in t:
                # Update rating
                cursor.execute(update_player_query(name=p.name, teamers_rating=p.mu, teamers_sigma=p.sigma))
                # Log teams
                cursor.execute("""insert into game_teams (game_id, player_name, team_number, placement) values ('{}', '{}', {}, {})""".format(
                    game_id,
                    p.name,
                    get_team_num_from_player(game.teams, p.name),
                    counter
                ))
    else:
        plackett_order: list[list[PlackettLuceRating]] = []
        for row in player_ratings:
            plackett_order.append([model.create_rating(rating=[row[2], row[3]], name=row[0])])
        updated_plackett = model.rate(deepcopy(plackett_order))
        for t in updated_plackett:
            for p in t:
                cursor.execute(update_player_query(name=p.name, ffa_rating=p.mu, ffa_sigma=p.sigma))

    conn.commit()
    return_model: list[PlayerChange] = []
    for j in range(len(updated_plackett)):
        for i in range(len(updated_plackett[j])):
            return_model.append(PlayerChange(name=updated_plackett[j][i].name, new_elo=int(updated_plackett[j][i].mu * RATING_MULT), elo_change=int((updated_plackett[j][i].mu - plackett_order[j][i].mu) * RATING_MULT)))
    return return_model

@app.get("/test")
async def test():
    game = Game(players=[PlayerRecord(player_name="test123", civ_name="congo", placement=2, bans=["america", "egypt"]),
                         PlayerRecord(player_name="Dyllon", civ_name="greece", placement=1, bans=["china", "canada"]),],
                # teams=[["Dylan"], ["Dyllon"]],
                bans=[BanRecord("test123", ["america", "egypt"]), BanRecord("Dyllon", ["china", "canada"])],
                date="08-28-2024",
                map="pangea",
                bbg=True
                )
    return await create_game(game)
