# scraper.py
# This is the bit that gets the data.
#
# It downloads the FIFA World Cup 2026 data from FIFA's own website and
# saves it to data/fifawcextract.csv. If that file already exists it is
# DELETED first, so the extract always holds the data from the latest
# download and never a mix of old and new.
#
# There is no backup csv. If the download fails there is no data, and the
# task will say so rather than quietly analyse something out of date.
#
# HOW THE FIFA DATA IS DOWNLOADED
# The fifa.com statistics page builds its tables with JavaScript, so there
# is no HTML table to read. The page gets its numbers from FIFA's own data
# service, and that service is what this file calls:
#
#   .../calendar/matches?idCompetition=17&idSeason=285023
#        -> the 104 matches, with the score of each one
#   .../timelines/17/285023/{stage}/{match}
#        -> everything that happened in a match, event by event
#           ("Attempt at Goal", "Corner", "Foul", ...)
#
# Counting each team's events across all 104 matches gives one row per
# team, which is what my analysis needs.

import os
import json
import urllib.request
import pandas as pd

# the folder this file is in, so paths work no matter where you run from
HERE = os.path.dirname(__file__)

# where the downloaded data gets saved
EXTRACT = "data/fifawcextract.csv"

# FIFA's data service, and the ids for the 2026 men's World Cup
FIFA_API = "https://api.fifa.com/api/v3"
COMPETITION = "17"       # FIFA World Cup
SEASON = "285023"        # the 2026 tournament

# Most sites refuse a request that doesn't look like a real browser, so we
# tell them we're Chrome.
BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# If a download fails, the reason is stored here so the web page can show
# something more useful than "it didn't work".
LAST_ERROR = ""


def full_path(path):
    """turn 'data/fifawcextract.csv' into a full path off this folder"""
    return path if os.path.isabs(path) else os.path.join(HERE, path)


def get_json(url):
    """download one address and read the JSON that comes back"""
    request = urllib.request.Request(url, headers=BROWSER)
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf8", "ignore"))


def team_name(team):
    """FIFA gives names as a list of translations - take the English one"""
    names = team.get("TeamName") or []
    return names[0]["Description"] if names else str(team.get("IdTeam"))


def event_name(event):
    """same idea for the description of an event"""
    kinds = event.get("TypeLocalized") or []
    return kinds[0]["Description"] if kinds else ""


def download_fifa():
    """
    Download every match of the 2026 World Cup and count up what each team
    did. Returns a DataFrame with one row per team.
    """
    global LAST_ERROR

    print("downloading the match list from FIFA...")
    calendar = get_json("%s/calendar/matches?idCompetition=%s&idSeason=%s&count=200"
                        % (FIFA_API, COMPETITION, SEASON))
    matches = calendar.get("Results", [])
    if not matches:
        LAST_ERROR = "FIFA returned no matches for this tournament"
        return pd.DataFrame()

    # one dictionary per team, built up as we go through the matches
    teams = {}

    def row_for(team_id, name):
        if team_id not in teams:
            teams[team_id] = {
                "Team": name, "Matches": 0, "Goals": 0, "GoalsAgainst": 0,
                "Attempts": 0, "Assists": 0, "Corners": 0, "Offsides": 0,
                "Fouls": 0, "YellowCards": 0, "Saves": 0,
            }
        return teams[team_id]

    print("downloading %d match timelines (takes about half a minute)..."
          % len(matches))

    for match in matches:
        home, away = match.get("Home"), match.get("Away")
        if not home or not away:
            continue  # a fixture with no teams decided yet

        home_row = row_for(home["IdTeam"], team_name(home))
        away_row = row_for(away["IdTeam"], team_name(away))

        # the score is on the match itself, which is the reliable source
        home_goals = match.get("HomeTeamScore") or 0
        away_goals = match.get("AwayTeamScore") or 0

        for row, scored, let_in in ((home_row, home_goals, away_goals),
                                    (away_row, away_goals, home_goals)):
            row["Matches"] += 1
            row["Goals"] += scored
            row["GoalsAgainst"] += let_in

        # now the detail, which only the timeline has
        timeline = get_json("%s/timelines/%s/%s/%s/%s"
                            % (FIFA_API, COMPETITION, SEASON,
                               match["IdStage"], match["IdMatch"]))

        counts = {
            "Attempt at Goal": "Attempts",
            "Assist": "Assists",
            "Corner": "Corners",
            "Offside": "Offsides",
            "Foul": "Fouls",
            "Yellow card": "YellowCards",
            "Goal Prevention": "Saves",
        }
        for event in timeline.get("Event", []):
            column = counts.get(event_name(event))
            team_id = event.get("IdTeam")
            if column and team_id in teams:
                teams[team_id][column] += 1

    df = pd.DataFrame(list(teams.values()))
    print("counted up", len(df), "teams from", len(matches), "matches")
    return df


def scrape_tables(url):
    """
    Read every table on a web page into a list of DataFrames. Used when a
    different website is given instead of FIFA's own data.
    """
    global LAST_ERROR
    try:
        LAST_ERROR = ""
        return pd.read_html(url, storage_options=BROWSER)
    except Exception as e:
        msg = str(e)
        if "No tables found" in msg:
            LAST_ERROR = (
                "that page has no HTML table in it. Sites like fifa.com and "
                "ESPN build their tables with JavaScript after the page "
                "loads, so there is nothing for pandas to read."
            )
        elif "403" in msg:
            LAST_ERROR = ("the site blocked the request (403 Forbidden). "
                          "FBRef does this to stop automated downloads.")
        elif "404" in msg:
            LAST_ERROR = "that page does not exist (404) - check the address."
        else:
            LAST_ERROR = msg
        print("could not download:", LAST_ERROR)
        return []


def clean(df):
    """
    Tidy up a freshly scraped web table: squash two-row headings into
    single names, drop blank separator rows, strip footnote markers, and
    turn number columns that arrived as text into real numbers.
    """
    if isinstance(df.columns, pd.MultiIndex):
        names = []
        for col in df.columns:
            parts = [str(p) for p in col if "Unnamed" not in str(p)]
            names.append(parts[-1] if parts else str(col[-1]))
        df.columns = names

    df = df.dropna(how="all").copy()

    for c in df.columns:
        if df[c].dtype == object:
            df[c] = (df[c].astype(str)
                          .str.replace(r"\[.*?\]", "", regex=True)
                          .str.replace("−", "-", regex=False)
                          .str.strip())
        as_numbers = pd.to_numeric(df[c], errors="coerce")
        if as_numbers.notna().sum() >= len(df) * 0.8:
            df[c] = as_numbers

    return df.reset_index(drop=True)


def save_extract(df, out_csv=EXTRACT):
    """
    Save the data to the extract file, deleting any old one first so the
    file can only ever hold the data from this download.
    """
    path = full_path(out_csv)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        os.remove(path)
        print("deleted the old extract")

    df.to_csv(path, index=False)
    print("saved", len(df), "rows to", out_csv)
    return path


def get_data(source_config):
    """
    The function my task calls. It downloads the data, saves it to the
    extract csv, then loads it back out of that file - so the csv is
    always exactly what the analysis ran on.

    With no "url" it uses FIFA's own data service. Give it a "url" and it
    reads an HTML table off that page instead.
    """
    global LAST_ERROR
    LAST_ERROR = ""
    url = source_config.get("url")
    out = source_config.get("extract_csv", EXTRACT)

    try:
        # A fifa.com address means "get me the FIFA statistics". Those
        # pages build their tables with JavaScript so there is nothing to
        # read off the page itself - but FIFA's own data service has the
        # same numbers, so use that instead of trying to read the page.
        if url and "fifa.com" in url.lower():
            print("that is a FIFA page - downloading from FIFA's data "
                  "service instead of reading the page")
            df = download_fifa()
            if df.empty:
                return df
        elif url:
            idx = source_config.get("table_index", 0)
            print("downloading:", url)
            tables = scrape_tables(url)
            if len(tables) <= idx:
                if tables:
                    LAST_ERROR = ("that page only has {} tables (numbered 0 "
                                  "to {}), so table {} does not exist."
                                  ).format(len(tables), len(tables) - 1, idx)
                print("nothing downloaded:", LAST_ERROR)
                return pd.DataFrame()
            df = clean(tables[idx])
        else:
            df = download_fifa()
            if df.empty:
                return df
    except Exception as e:
        LAST_ERROR = str(e)
        print("download failed:", LAST_ERROR)
        return pd.DataFrame()

    path = save_extract(df, out)
    df = pd.read_csv(path)
    print("loaded", len(df), "rows from", out)
    return df


if __name__ == "__main__":
    # quick test - download from FIFA and show the top of the table
    print(get_data({"extract_csv": EXTRACT}).head(10))
