CREATE TABLE IF NOT EXISTS "players"
(
    name           TEXT not null,
    ffa_rating     REAL,
    teamers_rating REAL,
    ffa_sigma      REAL,
    teamers_sigma  REAL
);
CREATE TABLE IF NOT EXISTS "game_civ_bans"
(
    game_id     text    not null,
    civ_name    TEXT    not null,
    player_name integer not null
);
CREATE TABLE IF NOT EXISTS "game_civ_picks"
(
    game_id     text    not null,
    civ_name    TEXT    not null,
    player_name integer not null
);
CREATE TABLE IF NOT EXISTS "game_players"
(
    game_id     text not null,
    player_name TEXT not null,
    placement   integer
);
CREATE TABLE IF NOT EXISTS "game_teams"
(
    game_id     text,
    player_name text    not null,
    team_number integer not null
, placement integer);
CREATE TABLE IF NOT EXISTS "games"
(
    id     text    not null,
    date   text    not null,
    map    TEXT,
    bbg    integer not null,
    league text
);
