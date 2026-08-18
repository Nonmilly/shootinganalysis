# task3.py
# Author: Mildred
# Task 3 - SHOOTING EFFICIENCY
#
# This is the terminal version of my task. No Flask, no web page - it
# downloads the data with requests, runs the whole analysis, and prints
# everything out so you can read it in the terminal.
#
# Run it with:   python task3.py
#
# It covers the six required skills and follows the 4-Step Process for a
# hypothesis test from the unit notes (State / Plan / Solve / Conclude).

import os
import requests
import pandas as pd

from stats_helpers import (
    describe,
    check_normality,
    confidence_interval,
    two_sample_ttest,
)

# ---------------------------------------------------------------------
# WHERE THE DATA COMES FROM
# ---------------------------------------------------------------------
# The fifa.com statistics page builds its table with JavaScript, so there
# is no table sitting in the page to read. The page gets its numbers from
# FIFA's own data service, so that is what I ask for instead.
PAGE = ("https://www.fifa.com/en/tournaments/mens/worldcup/"
        "canadamexicousa2026/statistics/team-statistics")

FIFA_API = "https://api.fifa.com/api/v3"
COMPETITION = "17"       # FIFA World Cup
SEASON = "285023"        # the 2026 tournament

BROWSER = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept": "application/json",
}

EXTRACT = os.path.join(os.path.dirname(__file__), "data", "fifawcextract.csv")

LINE = "=" * 70


def heading(text):
    """print a title with a line under it so the output is easy to read"""
    print()
    print(LINE)
    print(text)
    print(LINE)


def get_json(url):
    """download one address with requests and read the JSON"""
    response = requests.get(url, headers=BROWSER, timeout=45)
    response.raise_for_status()      # stop here if the site said no
    return response.json()


def first_description(items):
    """FIFA gives text as a list of translations - take the English one"""
    return items[0]["Description"] if items else ""


def download_data():
    """
    Download all 104 matches and count up what each team did.
    Returns a DataFrame with one row per team.
    """
    print("Source page :", PAGE)
    print("Data service:", FIFA_API)
    print()
    print("Downloading the match list...")

    calendar = get_json("%s/calendar/matches?idCompetition=%s&idSeason=%s&count=200"
                        % (FIFA_API, COMPETITION, SEASON))
    matches = calendar.get("Results", [])
    print("  got", len(matches), "matches")

    teams = {}

    def row_for(team):
        team_id = team["IdTeam"]
        if team_id not in teams:
            teams[team_id] = {
                "Team": first_description(team.get("TeamName")),
                "Matches": 0, "Goals": 0, "GoalsAgainst": 0,
                "Attempts": 0, "Assists": 0, "Corners": 0,
                "Offsides": 0, "Fouls": 0, "YellowCards": 0, "Saves": 0,
            }
        return teams[team_id]

    # which timeline event adds to which column
    counts = {
        "Attempt at Goal": "Attempts",
        "Assist": "Assists",
        "Corner": "Corners",
        "Offside": "Offsides",
        "Foul": "Fouls",
        "Yellow card": "YellowCards",
        "Goal Prevention": "Saves",
    }

    print("Downloading each match's events (about half a minute)...")
    for number, match in enumerate(matches, start=1):
        home, away = match.get("Home"), match.get("Away")
        if not home or not away:
            continue

        home_row, away_row = row_for(home), row_for(away)
        home_goals = match.get("HomeTeamScore") or 0
        away_goals = match.get("AwayTeamScore") or 0

        for row, scored, let_in in ((home_row, home_goals, away_goals),
                                    (away_row, away_goals, home_goals)):
            row["Matches"] += 1
            row["Goals"] += scored
            row["GoalsAgainst"] += let_in

        timeline = get_json("%s/timelines/%s/%s/%s/%s"
                            % (FIFA_API, COMPETITION, SEASON,
                               match["IdStage"], match["IdMatch"]))
        for event in timeline.get("Event", []):
            column = counts.get(first_description(event.get("TypeLocalized")))
            team_id = event.get("IdTeam")
            if column and team_id in teams:
                teams[team_id][column] += 1

        if number % 20 == 0:
            print("  ...%d of %d matches" % (number, len(matches)))

    df = pd.DataFrame(list(teams.values()))
    print("  counted up", len(df), "teams")

    # save it, deleting any old extract first
    os.makedirs(os.path.dirname(EXTRACT), exist_ok=True)
    if os.path.exists(EXTRACT):
        os.remove(EXTRACT)
        print("  deleted the old extract")
    df.to_csv(EXTRACT, index=False)
    print("  saved to data/fifawcextract.csv")

    # load it back, so what I analyse is exactly what is in the file
    return pd.read_csv(EXTRACT)


def main():
    heading("TASK 3 - SHOOTING EFFICIENCY (Mildred)")
    print("FIFA World Cup 2026 - how well teams turn attempts into goals")

    heading("GETTING THE DATA")
    try:
        df = download_data()
    except Exception as e:
        print("\nThe download failed:", e)
        print("Check your internet connection and try again.")
        return

    print("\nFirst 10 rows of the downloaded data:")
    print(df.head(10).to_string(index=False))

    # =================================================================
    # SKILL 1 - ANALYTIC QUESTION            (STEP 1: STATE)
    # =================================================================
    heading("STEP 1: STATE - the analytic question")
    print("How efficiently do teams convert their attempts at goal into")
    print("goals at the 2026 World Cup, and do high-volume shooting teams")
    print("convert at a different rate from low-volume shooting teams?")
    print()
    print("Response variable    : Conversion = Goals / Attempts")
    print("Explanatory variable : shooting volume (high or low)")
    print("Level of measurement : ratio, continuous")

    # =================================================================
    # STEP 2: PLAN - the hypotheses
    # =================================================================
    heading("STEP 2: PLAN - the hypotheses")
    print("H0: mu_high  = mu_low    both groups convert at the same rate")
    print("Ha: mu_high != mu_low    the two groups differ  (two-sided)")
    print()
    print("Test  : two-sample (independent) t-test")
    print("alpha : 0.05")

    # =================================================================
    # SKILL 2 - DATA WRANGLING               (STEP 3: SOLVE)
    # =================================================================
    heading("SKILL 2: DATA WRANGLING")
    rows_before = len(df)
    df = df[["Team", "Matches", "Goals", "Attempts"]].copy()
    for c in ["Matches", "Goals", "Attempts"]:
        df[c] = df[c].astype(float)

    # listwise (case) deletion - drop a row that is missing anything I need
    df = df.dropna(subset=["Matches", "Goals", "Attempts"])
    # conversion divides by Attempts, so a team with none would break it
    df = df[df["Attempts"] > 0]

    print("Columns kept        : Team, Matches, Goals, Attempts")
    print("Missing value method: listwise (case) deletion")
    print("Rows before / after : %d / %d  (%d dropped)"
          % (rows_before, len(df), rows_before - len(df)))

    # =================================================================
    # SKILL 3 - DATA PREPARATION AND SAMPLING
    # =================================================================
    heading("SKILL 3: DATA PREPARATION AND SAMPLING")
    # feature construction - build the variable I actually study
    df["Conversion"] = df["Goals"] / df["Attempts"]
    population_size = len(df)
    sample = df["Conversion"].sample(n=min(30, population_size), random_state=3)

    print("Feature construction: Conversion = Goals / Attempts")
    print("Population          : %d teams" % population_size)
    print("Sample              : %d teams" % len(sample))
    print("Sampling method     : simple random sampling (random_state=3)")
    print("Why 30              : the Central Limit Theorem needs n >= 30")

    print("\nThe five best converters in the whole population:")
    best = df.sort_values("Conversion", ascending=False).head(5)
    print(best[["Team", "Goals", "Attempts", "Conversion"]]
          .round(4).to_string(index=False))

    # =================================================================
    # CONDITIONS FOR INFERENCE               (STEP 3: SOLVE)
    # =================================================================
    heading("CONDITIONS FOR INFERENCE")
    conditions = check_normality(sample)
    print("1. Simple random sample : yes, .sample() draws at random")
    print("2. Roughly normal       : skewness %.3f -> %s"
          % (conditions["skewness"],
             "yes" if conditions["roughly_normal"] else "not clearly"))
    print("   (mean %.4f vs median %.4f - close together means symmetric)"
          % (conditions["mean"], conditions["median"]))

    # =================================================================
    # SKILL 4 - DESCRIPTIVE STATISTICS
    # =================================================================
    heading("SKILL 4: DESCRIPTIVE STATISTICS")
    d = describe(sample)
    print("Central tendency")
    print("   n                  %d" % d["n"])
    print("   mean               %.4f   (%.1f%% of attempts score)"
          % (d["mean"], d["mean"] * 100))
    print("   median             %.4f" % d["median"])
    print("Dispersion")
    print("   minimum            %.4f" % d["min"])
    print("   maximum            %.4f" % d["max"])
    print("   range              %.4f" % d["range"])
    print("   Q1 / Q3            %.4f / %.4f" % (d["q1"], d["q3"]))
    print("   IQR                %.4f" % d["iqr"])
    print("   variance           %.5f" % d["variance"])
    print("   standard deviation %.4f" % d["std"])

    # =================================================================
    # SKILL 5 - CONFIDENCE INTERVAL
    # =================================================================
    heading("SKILL 5: CONFIDENCE INTERVAL (95%)")
    ci = confidence_interval(sample, 0.95)
    print("Formula: CI = x-bar +/- z* . (s / sqrt(n))")
    print()
    print("   sample mean        %.4f" % ci["mean"])
    print("   standard error     %.5f" % ci["standard_error"])
    print("   statistic used     %s = %.4f   (n >= 30, so z* by the rule)"
          % (ci["statistic_used"], ci["critical_value"]))
    print("   margin of error    %.5f" % ci["margin_of_error"])
    print()
    print("   95%% CI = [%.4f , %.4f]" % (ci["lower"], ci["upper"]))
    print()
    print("   We are 95% confident the true mean conversion rate of all")
    print("   teams is between %.1f%% and %.1f%%."
          % (ci["lower"] * 100, ci["upper"] * 100))

    # =================================================================
    # SKILL 6 - TWO-SAMPLE t-TEST
    # =================================================================
    heading("SKILL 6: TWO-SAMPLE t-TEST")
    # discretisation - split a continuous variable into two categories.
    # attempts PER MATCH, so teams that played more games aren't favoured.
    df["AttemptsPerMatch"] = df["Attempts"] / df["Matches"]
    median_attempts = df["AttemptsPerMatch"].median()
    high = df[df["AttemptsPerMatch"] >= median_attempts]["Conversion"]
    low = df[df["AttemptsPerMatch"] < median_attempts]["Conversion"]

    print("Split on the median of attempts per match: %.1f" % median_attempts)
    print("(per match, not the total, so teams that played more matches")
    print(" don't automatically land in the high group)")
    print()

    t = two_sample_ttest(high, low, alpha=0.05)
    print("   Group A - high volume : n %2d   mean %.4f   s %.4f"
          % (t["n_a"], t["mean_a"], t["std_a"]))
    print("   Group B - low volume  : n %2d   mean %.4f   s %.4f"
          % (t["n_b"], t["mean_b"], t["std_b"]))
    print()
    print("   t statistic        %.4f" % t["t_stat"])
    print("   p-value            %s" % t["p_value_text"])
    print("   degrees of freedom %d   (smaller group - 1, the conservative"
          % t["df_conservative"])
    print("                          approach from the notes)")
    print("   Welch's test       equal_var=False, variances kept separate")

    # =================================================================
    # STEP 4: CONCLUDE
    # =================================================================
    heading("STEP 4: CONCLUDE")
    if t["p_value"] < 0.0001:
        chance = "fewer than 1 time in 10,000"
    else:
        chance = "about %.2f%% of the time" % (t["p_value"] * 100)

    print("The average team converts %.1f%% of its attempts at goal, and we"
          % (ci["mean"] * 100))
    print("are 95% confident the true average for all teams is between")
    print("%.1f%% and %.1f%%." % (ci["lower"] * 100, ci["upper"] * 100))
    print()
    if t["reject_null"]:
        print("The p-value is %s, at or below 0.05. A difference this big"
              % t["p_value_text"])
        print("between the groups would happen by chance %s," % chance)
        print("which is unusual.")
        print()
        print(">>> REJECT H0. There IS enough evidence that high-volume")
        print(">>> shooting teams convert at a different rate from")
        print(">>> low-volume shooting teams.")
    else:
        print("The p-value is %s, above 0.05. A difference this big between"
              % t["p_value_text"])
        print("the groups could still happen by chance %s," % chance)
        print("so it is not unusual.")
        print()
        print(">>> DO NOT REJECT H0. There is NOT enough evidence that")
        print(">>> high-volume shooting teams convert at a different rate")
        print(">>> from low-volume shooting teams.")
    print()
    print("Reported in APA format: t(%d) = %.2f, p = %s"
          % (t["df_conservative"], t["t_stat"],
             ("< .001" if t["p_value"] < 0.001
              else ("%.3f" % t["p_value"]).lstrip("0"))))
    print()
    print(LINE)
    print("End of Task 3.")
    print(LINE)


if __name__ == "__main__":
    main()
