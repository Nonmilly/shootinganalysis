# task3_shooting.py
# Author: Mildred
# Focal point: SCORING EFFICIENCY - how many goals a team scores per match
#
# This is my analytic task. It covers the six required skills, and it
# follows the 4-Step Process for a hypothesis test from the unit notes:
#
#   Skill 1. Analytic question formulation ....... STEP 1: STATE
#   Skill 2. Data wrangling ...................... STEP 3: SOLVE
#   Skill 3. Data preparation and sampling ....... STEP 3: SOLVE
#   Skill 4. Descriptive statistics .............. STEP 3: SOLVE
#   Skill 5. Confidence interval ................. STEP 3: SOLVE
#   Skill 6. Two-sample t-test ................... STEP 2 + 3 + 4

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scraper import get_data
from stats_helpers import (
    describe,
    check_normality,
    confidence_interval,
    two_sample_ttest,
)

# Where the data is downloaded from. The scraper saves it to the extract
# csv and then loads it back, so the csv always matches this run.
SOURCE = {
    "url": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup",
    "table_index": 68,          # the final ranking table of all 48 teams
    "extract_csv": "data/fifawcextract.csv",
}


def run():
    df = get_data(SOURCE)
    if df.empty:
        return {"error": "the download failed, so there is no data to analyse"}

    # ===============================================================
    # SKILL 1 - ANALYTIC QUESTION        (STEP 1: STATE)
    # ===============================================================
    # How many goals per match does a team score at the 2026 World Cup,
    # and do teams that reached the knockout stage score at a different
    # rate to teams that were eliminated in the group stage?
    question = ("How many goals per match does a team score at the 2026 "
                "World Cup, and do teams that reached the knockout stage "
                "score at a different rate from teams eliminated in the "
                "group stage?")

    # ===============================================================
    # STEP 2: PLAN - the parameters and the two competing hypotheses
    # ===============================================================
    # The parameter is mu, the mean goals per match of a group of teams.
    # I am not claiming which group is higher, only asking whether they
    # differ, so this is a two-sided test.
    #
    #   H0: mu_knockout  =  mu_group
    #   Ha: mu_knockout !=  mu_group
    hypotheses = {
        "H0": "mu_knockout = mu_group  (teams that reached the knockout "
              "stage score at the same rate as teams that went out in the "
              "group stage)",
        "Ha": "mu_knockout != mu_group  (the two groups score at different "
              "rates)",
        "tail": "two-sided",
        "test": "two-sample (independent) t-test",
        "alpha": 0.05,
    }

    # ===============================================================
    # SKILL 2 - DATA WRANGLING           (STEP 3: SOLVE)
    # ===============================================================
    # keep only the columns I need: the team, matches played, goals for
    # and goals against
    df = df[["Team", "Pld", "GF", "GA"]].copy()

    # make sure the numbers are numbers and not text
    for c in ["Pld", "GF", "GA"]:
        df[c] = df[c].astype(float)

    # Missing values: I used LISTWISE (CASE) DELETION from the notes - if a
    # row is missing any value I need, the whole row goes. I did not use
    # mean substitution because inventing a goals total for a real team
    # would pull every result towards the average and hide the real spread.
    rows_before = len(df)
    df = df.dropna(subset=["Pld", "GF", "GA"])

    # drop any team with 0 matches played - goals per match divides by
    # Pld, and you cannot divide by zero
    df = df[df["Pld"] > 0]
    rows_dropped = rows_before - len(df)

    # ===============================================================
    # SKILL 3 - DATA PREPARATION AND SAMPLING     (STEP 3: SOLVE)
    # ===============================================================
    # FEATURE CONSTRUCTION (Week 5): I build a new variable out of two
    # existing ones, the same way the notes build BMI out of weight and
    # height. This is my response variable.
    df["GoalsPerMatch"] = df["GF"] / df["Pld"]

    # POPULATION = all the teams in the tournament.
    # SAMPLE     = 30 of them, chosen by SIMPLE RANDOM SAMPLING.
    #
    # Why 30? The Central Limit Theorem needs a sample of 30 or more before
    # the sampling distribution of the mean is close enough to normal for
    # the confidence interval to be valid.
    #
    # random_state=3 keeps the same 30 teams on every run so my results
    # don't change between testing and submitting.
    population_size = len(df)
    sample = df["GoalsPerMatch"].sample(n=min(30, population_size),
                                        random_state=3)

    # ===============================================================
    # STEP 3: SOLVE - check the conditions for inference first
    # ===============================================================
    # Condition 1: was the sample produced by simple random sampling?
    #              Yes - pandas .sample() draws at random.
    # Condition 2: is the sample roughly normally distributed?
    normality = check_normality(sample)

    # ===============================================================
    # SKILL 4 - DESCRIPTIVE STATISTICS   (STEP 3: SOLVE)
    # ===============================================================
    # central tendency (mean, median) and dispersion (range, IQR,
    # variance, standard deviation)
    desc = describe(sample)

    # ===============================================================
    # SKILL 5 - CONFIDENCE INTERVAL      (STEP 3: SOLVE)
    # ===============================================================
    # 95% confidence interval estimating the mean goals per match of the
    # whole population, using CI = x-bar +/- z* . (s / sqrt(n))
    ci = confidence_interval(sample, 0.95)

    # ===============================================================
    # SKILL 6 - TWO-SAMPLE t-TEST        (STEP 3: SOLVE)
    # ===============================================================
    # Split the teams into the two groups being compared. The group stage
    # is 3 matches, so any team with more than 3 matches played reached
    # the knockout stage.
    # (This is DISCRETISATION - turning a continuous variable, matches
    # played, into two categories.)
    knockout = df[df["Pld"] > 3]["GoalsPerMatch"]
    group_only = df[df["Pld"] <= 3]["GoalsPerMatch"]

    ttest = two_sample_ttest(knockout, group_only, alpha=hypotheses["alpha"])

    # ===============================================================
    # STEP 4: CONCLUDE - answer the question from Step 1
    # ===============================================================
    p_text = ttest["p_value_text"]
    # how to word "how often this would happen by chance"
    if ttest["p_value"] < 0.0001:
        chance = "fewer than 1 time in 10,000"
    else:
        chance = "about {:.2f}% of the time".format(ttest["p_value"] * 100)

    if ttest["reject_null"]:
        conclusion = (
            "The p-value is {p}, which is at or below 0.05. If H0 were "
            "true, a difference this big between the two group means would "
            "happen by chance {chance}, which makes it very unusual. So we "
            "REJECT the null hypothesis: there is enough evidence that "
            "teams reaching the knockout stage score at a different rate "
            "from teams eliminated in the group stage."
        ).format(p=p_text, chance=chance)
    else:
        conclusion = (
            "The p-value is {p}, which is above 0.05. If H0 were true, a "
            "difference this big between the two group means could still "
            "happen by chance {chance}, so it is not unusual. So we DO NOT "
            "REJECT the null hypothesis: there is not enough evidence that "
            "teams reaching the knockout stage score at a different rate "
            "from teams eliminated in the group stage."
        ).format(p=p_text, chance=chance)

    # answer to the first half of the question, from the confidence interval
    estimate = (
        "Teams score on average {mean} goals per match. We are {conf:.0f}% "
        "confident the true mean for all teams is between {lo} and {hi}."
    ).format(mean=ci["mean"], conf=ci["conf_level"] * 100,
             lo=ci["lower"], hi=ci["upper"])

    return {
        "title": "Task 3 - Scoring efficiency (Mildred)",
        "question": question,
        "variable": "GoalsPerMatch = GF / Pld (goals scored per match)",
        "measurement_level": "ratio, continuous",
        "data_source": SOURCE["url"],
        "wrangling": {
            "columns_kept": ["Team", "Pld", "GF", "GA"],
            "missing_data_method": "listwise (case) deletion",
            "rows_dropped": int(rows_dropped),
        },
        "sampling": {
            "population": int(population_size),
            "sample": int(len(sample)),
            "method": "simple random sampling",
            "why_30": "Central Limit Theorem needs n >= 30",
        },
        "conditions": normality,
        "hypotheses": hypotheses,
        "descriptive": desc,
        "confidence_interval": ci,
        "ttest": {
            "group_a": "Reached knockout stage",
            "group_b": "Eliminated in group stage",
            **ttest,
        },
        "estimate": estimate,
        "conclusion": conclusion,
    }


if __name__ == "__main__":
    # lets me run just this file on its own to check it works
    import json
    print(json.dumps(run(), indent=2))
