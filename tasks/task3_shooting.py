# task3_shooting.py
# Author: Mildred
# Focal point: SHOOTING EFFICIENCY - how well a team turns its attempts at
# goal into actual goals. This is FIFA's own "Attempt at Goal Conversion
# Rate" metric, and it is about efficiency, not about how many goals a
# team scored.
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

# Where the data comes from. With no "url" the scraper downloads from
# FIFA's own data service, saves it to the extract csv, and loads it back.
SOURCE = {
    "url": None,
    "table_index": 0,
    "extract_csv": "data/fifawcextract.csv",
}


def run():
    df = get_data(SOURCE)
    if df.empty:
        return {"error": "the download failed, so there is no data to analyse"}

    # ===============================================================
    # SKILL 1 - ANALYTIC QUESTION        (STEP 1: STATE)
    # ===============================================================
    # How efficiently does a team convert its attempts at goal into goals
    # at the 2026 World Cup, and do teams that attempt a lot of shots
    # convert at a different rate to teams that attempt few?
    question = ("How efficiently do teams convert their attempts at goal "
                "into goals at the 2026 World Cup, and do high-volume "
                "shooting teams convert at a different rate from "
                "low-volume shooting teams?")

    # ===============================================================
    # STEP 2: PLAN - the parameters and the two competing hypotheses
    # ===============================================================
    # The parameter is mu, the mean conversion rate of a group of teams.
    # I am not claiming which group is higher, only asking whether they
    # differ, so this is a two-sided test.
    #
    #   H0: mu_high  =  mu_low
    #   Ha: mu_high !=  mu_low
    hypotheses = {
        "H0": "mu_high = mu_low  (teams that attempt many shots convert at "
              "the same rate as teams that attempt few)",
        "Ha": "mu_high != mu_low  (the two groups convert at different "
              "rates)",
        "tail": "two-sided",
        "test": "two-sample (independent) t-test",
        "alpha": 0.05,
    }

    # ===============================================================
    # SKILL 2 - DATA WRANGLING           (STEP 3: SOLVE)
    # ===============================================================
    # keep only the columns I need for shooting
    df = df[["Team", "Matches", "Goals", "Attempts"]].copy()

    # make sure the numbers are numbers and not text
    for c in ["Matches", "Goals", "Attempts"]:
        df[c] = df[c].astype(float)

    # Missing values: I used LISTWISE (CASE) DELETION from the notes - if a
    # row is missing any value I need, the whole row goes. I did not use
    # mean substitution because inventing a shot count for a real team
    # would pull every result towards the average and hide the real spread.
    rows_before = len(df)
    df = df.dropna(subset=["Matches", "Goals", "Attempts"])

    # drop any team with no attempts at all - conversion divides by
    # Attempts, and you cannot divide by zero
    df = df[df["Attempts"] > 0]
    rows_dropped = rows_before - len(df)

    # ===============================================================
    # SKILL 3 - DATA PREPARATION AND SAMPLING     (STEP 3: SOLVE)
    # ===============================================================
    # FEATURE CONSTRUCTION (Week 5): I build a new variable out of two
    # existing ones, the same way the notes build BMI out of weight and
    # height. This is my response variable.
    df["Conversion"] = df["Goals"] / df["Attempts"]

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
    sample = df["Conversion"].sample(n=min(30, population_size),
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
    # 95% confidence interval estimating the mean conversion rate of the
    # whole population, using CI = x-bar +/- z* . (s / sqrt(n))
    ci = confidence_interval(sample, 0.95)

    # ===============================================================
    # SKILL 6 - TWO-SAMPLE t-TEST        (STEP 3: SOLVE)
    # ===============================================================
    # Split the teams by how many attempts they had. Teams that played
    # more matches naturally get more attempts, so I compare attempts PER
    # MATCH to keep it fair, and split on the median.
    # (This is DISCRETISATION - turning a continuous variable, attempts
    # per match, into two categories.)
    df["AttemptsPerMatch"] = df["Attempts"] / df["Matches"]
    median_attempts = df["AttemptsPerMatch"].median()
    high = df[df["AttemptsPerMatch"] >= median_attempts]["Conversion"]
    low = df[df["AttemptsPerMatch"] < median_attempts]["Conversion"]

    ttest = two_sample_ttest(high, low, alpha=hypotheses["alpha"])

    # ===============================================================
    # STEP 4: CONCLUDE - answer the question from Step 1
    # ===============================================================
    p_text = ttest["p_value_text"]
    if ttest["p_value"] < 0.0001:
        chance = "fewer than 1 time in 10,000"
    else:
        chance = "about {:.2f}% of the time".format(ttest["p_value"] * 100)

    if ttest["reject_null"]:
        conclusion = (
            "The p-value is {p}, which is at or below 0.05. If H0 were "
            "true, a difference this big between the two group means would "
            "happen by chance {chance}, which makes it unusual. So we "
            "REJECT the null hypothesis: there is enough evidence that "
            "high-volume shooting teams convert at a different rate from "
            "low-volume shooting teams."
        ).format(p=p_text, chance=chance)
    else:
        conclusion = (
            "The p-value is {p}, which is above 0.05. If H0 were true, a "
            "difference this big between the two group means could still "
            "happen by chance {chance}, so it is not unusual. So we DO NOT "
            "REJECT the null hypothesis: there is not enough evidence that "
            "high-volume shooting teams convert at a different rate from "
            "low-volume shooting teams."
        ).format(p=p_text, chance=chance)

    # answer to the first half of the question, from the confidence interval
    estimate = (
        "Teams convert on average {mean} of their attempts at goal (about "
        "{pc:.1f}%). We are {conf:.0f}% confident the true mean for all "
        "teams is between {lo} and {hi}."
    ).format(mean=ci["mean"], pc=ci["mean"] * 100,
             conf=ci["conf_level"] * 100, lo=ci["lower"], hi=ci["upper"])

    return {
        "title": "Task 3 - Shooting efficiency (Mildred)",
        "question": question,
        "variable": "Conversion = Goals / Attempts at Goal",
        "measurement_level": "ratio, continuous",
        "data_source": "FIFA official data service (api.fifa.com), "
                       "competition 17, season 285023",
        "wrangling": {
            "columns_kept": ["Team", "Matches", "Goals", "Attempts"],
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
            "group_a": "High-volume shooters (>= %.1f attempts/match)"
                       % median_attempts,
            "group_b": "Low-volume shooters (< %.1f attempts/match)"
                       % median_attempts,
            **ttest,
        },
        "estimate": estimate,
        "conclusion": conclusion,
    }


if __name__ == "__main__":
    # lets me run just this file on its own to check it works
    import json
    print(json.dumps(run(), indent=2))
