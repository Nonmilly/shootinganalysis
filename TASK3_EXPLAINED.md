# task3.py explained simply

A walk through `task3.py` in everyday language, with the lecture notes it
comes from marked at each step. Run it with `python task3.py`.

---

## The one-sentence version

**Some teams are better at turning shots into goals than others. This program
downloads what every team did at the World Cup, works out how good each one was
at that, and then checks whether teams that shoot a lot are any better at it
than teams that shoot rarely.**

Everything below is just that, in detail.

---

## The idea behind it

Imagine two players on a basketball court.

- **Ana** takes 100 shots and scores 20.
- **Ben** takes 20 shots and scores 8.

Ana scored more goals. But Ben is the better shooter: he scores 8 out of every
20 (**40%**), Ana only 20 out of 100 (**20%**). Ana just shoots more.

That difference — **scoring a lot** versus **being good at scoring** — is what
this whole task is about. The second one is called the **conversion rate**:

```
Conversion = goals ÷ attempts
```

My question has two halves:

1. What is a typical conversion rate at the 2026 World Cup?
2. Are the "Ana" teams (shoot constantly) any better or worse at converting
   than the "Ben" teams (shoot rarely)?

> **Notes link — Week 1.** The notes call the thing you're measuring the
> **response variable** (here: conversion rate) and the thing you think might
> explain it the **explanatory variable** (here: whether a team shoots a lot or
> a little).

---

## Step 1 — Getting the data

```python
response = requests.get(url, headers=BROWSER, timeout=45)
```

`requests` is a tool that fetches a web address, like typing it into a browser
but from inside Python.

**A wrinkle worth understanding.** If you open FIFA's statistics page and use
"View Source", you'll find no table there — just an empty shell. The table you
see on screen is drawn *afterwards* by JavaScript running in your browser.
Python doesn't run that JavaScript, so it sees an empty page.

The fix: the page has to get its numbers from *somewhere*. It asks FIFA's own
data service. So this program asks that same service directly:

```
.../calendar/matches?idCompetition=17&idSeason=285023
        -> the list of all 104 matches and their scores
.../timelines/17/285023/{stage}/{match}
        -> everything that happened in one match, moment by moment
```

The second one is like a **commentary log**. For each match it lists every
event: *"Attempt at Goal"*, *"Corner"*, *"Foul"*, *"Yellow card"*. The program
goes through all 104 matches, and every time it sees "Attempt at Goal" it adds
one to that team's shot count.

That turns 104 match logs into one tidy row per team:

```
Team, Matches, Goals, GoalsAgainst, Attempts, Assists,
Corners, Offsides, Fouls, YellowCards, Saves
```

It then saves that to `data/fifawcextract.csv`, **deleting the old file first**
so it can never be a mix of yesterday's and today's numbers.

> **Notes link — Week 5.** The notes call this stage **data acquisition**, and
> say it comes before data wrangling in the data science lifecycle.

---

## Step 2 — Cleaning it up (data wrangling)

```python
df = df[["Team", "Matches", "Goals", "Attempts"]].copy()
df = df.dropna(subset=["Matches", "Goals", "Attempts"])
df = df[df["Attempts"] > 0]
```

**Wrangling** just means tidying data before you use it — like washing and
chopping vegetables before cooking. Three things happen:

1. **Keep only what I need.** The download has 11 columns; I use 4.
2. **Throw away incomplete rows.** If a team is missing a number I need, the
   whole row goes.
3. **Remove teams with zero attempts.** Conversion divides *by* attempts, and
   dividing by zero breaks the maths.

**Why throw rows away instead of filling them in?** The notes offer three ways
to handle missing values: **listwise deletion** (bin the row), **mean
substitution** (fill it with the average), and **regression imputation**. I used
deletion, for a specific reason: I'm studying how much teams *differ* from each
other. Filling gaps with the average would quietly drag everyone towards the
middle and hide exactly what I'm looking for. As it happens the FIFA data is
complete, so **0 rows are actually dropped**.

> **Notes link — Week 5.** "Listwise or case deletion", and the warning that it
> "may inadvertently introduce bias… when the dataset is not large enough".

---

## Step 3 — Building the number I actually study

```python
df["Conversion"] = df["Goals"] / df["Attempts"]
```

Neither "conversion" nor anything like it exists in the downloaded data. I
build it from two columns that do exist.

> **Notes link — Week 5, feature construction.** The notes' example is BMI:
> you don't measure BMI directly, you build it from weight and height.
> ```
> BMI = Weight ÷ Height²          Conversion = Goals ÷ Attempts
> ```

---

## Step 4 — Taking a sample

```python
sample = df["Conversion"].sample(n=30, random_state=3)
```

- **Population** = all 48 teams. Everyone.
- **Sample** = 30 of them, picked at random.

This is how opinion polls work: nobody rings all 30 million voters, they ring
1,000 and reason about the rest.

**Why exactly 30?** Not arbitrary. There's a rule that once your sample reaches
about 30, the maths behind confidence intervals starts working properly. Below
30 it gets shaky. 30 is the smallest number that qualifies.

**What is `random_state=3`?** Normally "random" means different every time. This
freezes the shuffle so the same 30 teams come out on every run — so my numbers
don't change between testing it and demonstrating it. The 3 is just a label.

> **Notes link — Week 3.** **Simple random sampling**, and the **Central Limit
> Theorem**: the sampling distribution of the mean approaches normal "provided
> that the size of each sample is sufficiently large, which is usually 30 or
> larger". Also **parameter** (describes the population) vs **statistic**
> (computed from the sample).

---

## Step 5 — Checking it's safe to proceed

```
skewness 0.209  ->  yes
mean 0.1113 vs median 0.1124
```

Before trusting any of the later maths, the notes say check two things.

**Was the sample random?** Yes — `.sample()` picks at random. If I'd picked
teams myself I'd have leaned towards ones I recognise, and the answer would be
worthless.

**Is the data reasonably balanced?** A balanced (normal) set of numbers is
symmetric — the mean and median sit in the same place. Ours are 0.1113 and
0.1124, nearly identical, and skewness is 0.21 where 0 is perfect. So yes.

> **Notes link — Week 4, Step 3.** "Check whether the sample data is generated
> by a simple random sampling procedure" and "check whether the sample data is
> normally distributed. If not, the power of p-value may be limited."

---

## Step 6 — Describing what we found

```
mean 0.1113   median 0.1124
range 0.2391  IQR 0.0738
variance 0.00299   standard deviation 0.0547
```

Two kinds of question here: *where is the middle?* and *how spread out is it?*

**Mean** — the average. **11.1%** of attempts became goals: about one in nine.

**Median** — the middle value when you line them all up.

**Why both?** Picture five people in a room each earning £20,000. The mean is
£20,000. Now a billionaire walks in — the mean jumps to millions, but nobody in
that room got richer. The median stays at £20,000 and describes the room
honestly. Means get dragged around by extremes; medians don't. Ours are almost
identical, which tells you no single team is distorting the picture.

**Range** — biggest minus smallest, 0.2391. Simple, but one freak value stretches
it.

**IQR** — the spread of the *middle half*, ignoring the extremes at both ends. At
0.0738 it's much smaller than the range, which tells you most teams are bunched
together and only the outliers are far apart.

**Standard deviation** — roughly, how far a typical team sits from the average.
Two classes both average 70% in a test: in one everybody scored 68–72, in the
other half scored 40 and half scored 100. Same average, completely different
classes. The standard deviation is what tells them apart.

> **Notes link — Week 2.** **Central tendency** (mean, median, mode) and
> **dispersion** (range, IQR, variance, standard deviation).
>
> **No mode** here on purpose: the notes say the mode is for nominal or ordinal
> data, and conversion rates are continuous — almost every team's value is
> unique, so the "most common value" would be meaningless.
>
> Also note `ddof=1` in the code: the notes give two formulas, dividing by
> *n−1* for a **sample** and by *n* for a **population**. We have a sample, so
> *n−1*.

---

## Step 7 — How sure are we? (confidence interval)

```
95% CI = [0.0918 , 0.1309]
```

We measured 30 teams, not all of them. So "11.1%" is a good estimate, not a
certain fact. A confidence interval turns the estimate into a **range**:

> We're 95% confident the true average for all teams is between **9.2% and
> 13.1%**.

It's like guessing someone's age. "Exactly 34" is probably wrong. "Somewhere
between 30 and 40" is probably right. The range is the honest answer.

The formula from the notes, and how the code matches it piece by piece:

```
CI = x̄ ± z* · (s / √n)

  s / √n          ->  standard_error  = 0.00998
  z*              ->  critical        = 1.960
  z* · s / √n     ->  margin_of_error = 0.01956
```

**Standard error** is how much your answer would wobble if you drew a different
30 teams. Note `n` sits under a square root — bigger sample, less wobble.

**Why z\* and not t\*?** The notes give the rule: sample under 30 use **t\***,
30 or over use **z\***. Ours is exactly 30, so the code picks z* = 1.960. It's
written as an `if` statement so it would switch by itself on a smaller sample.

**What "95%" really means:** if we repeated this whole study 100 times, about 95
of our ranges would contain the true answer. It does *not* mean there's a 95%
chance this particular range is right.

> **Notes link — Week 3.** The confidence interval formula, **standard error**,
> **margin of error**, the z* table (1.645 / 1.960 / 2.576), and the z*-vs-t*
> rule.

---

## Step 8 — Is the difference real? (the t-test)

```
High volume (≥ 11.3 shots/match): n 24, mean 0.1210
Low volume  (< 11.3 shots/match): n 24, mean 0.1026
t = 1.1997,  p = 0.2366
```

Split the teams into two groups and compare. High-volume shooters convert
12.1%, low-volume shooters 10.3%. High looks better — but **is that a real
difference, or just luck in who ended up in which group?**

Flip a coin 10 times and get 6 heads: proves nothing, that happens constantly.
Flip it 100 times and get 60 heads: now something's going on. A t-test is that
judgement made properly.

**Why split on shots *per match*?** Teams that went further played more matches,
so they'd pile up more total shots automatically. Dividing by matches played
keeps a group-stage team and a finalist comparable — otherwise I'd secretly be
measuring who survived longest, not who shoots most.

**The p-value: 0.2366.** This is the number that decides it:

> If the two groups really were identical, how often would we see a gap this
> big just from luck?

**About 24% of the time.** Roughly one run in four. That's completely ordinary —
so the gap is not convincing. The cutoff everyone uses is **0.05** (1 in 20);
we're nowhere near it.

> **Notes link — Week 4.** **Two-sample (independent) t-test** using
> `scipy.stats.ttest_ind()`; the p-value definition; the "reject H₀ when
> p ≤ 0.05" rule; and **degrees of freedom**, where the notes take the
> conservative approach of the smaller group's n − 1 (here 23).
>
> `equal_var=False` is **Welch's test** — it keeps the two groups' variances
> separate, which is exactly the formula the notes write out by hand.

---

## Step 9 — The answer

**Question 1: how efficient are teams?**
About **11.1%** of attempts become goals, and we're 95% confident the true
figure for all teams is between **9.2% and 13.1%**.

**Question 2: do high-volume shooters convert differently?**
**No evidence that they do.** p = 0.237, far above 0.05, so we **do not reject
the null hypothesis**.

**Reported properly:** *t*(23) = 1.20, *p* = .237

### Why "no difference" is a good result, not a failure

It's tempting to look at 12.1% vs 10.3%, announce that high-volume teams are
better, and move on. The t-test exists precisely to stop you doing that — the
gap is well within what luck produces.

And the finding is genuinely interesting: shooting **volume** and shooting
**accuracy** appear to be largely independent. Teams that shoot more are not
taking worse chances to do it.

> **Notes link — Week 4, Step 4: Conclude.** The notes' phrasing for this
> outcome is that "there is not enough evidence to go against the null
> hypothesis".

---

## The two hypotheses, in plain words

Every hypothesis test is a contest between two claims:

| | Claim | In symbols |
|---|---|---|
| **H₀** (null) | The boring one: there's no real difference between the groups | `mu_high = mu_low` |
| **Hₐ** (alternative) | The interesting one: there is a difference | `mu_high != mu_low` |

You start by *assuming H₀ is true*, then ask how surprising your data would be
in that world. Not surprising → keep H₀. Very surprising → reject it.

It's `!=` ("different") rather than `>` ("better") because I genuinely didn't
know which way it would go. That's called **two-sided**.

> **Notes link — Week 4.** Stating H₀ and Hₐ is Step 2 (**Plan**) of the
> notes' 4-Step Process.

---

## How the file is laid out

`task3.py` follows the notes' **4-Step Process** from start to finish:

| Step in the notes | In the file | What it does |
|---|---|---|
| **1. State** | `STEP 1: STATE` | the question |
| **2. Plan** | `STEP 2: PLAN` | H₀, Hₐ, which test, α = 0.05 |
| **3. Solve** | `SKILL 2`–`SKILL 6` | wrangle, sample, check, describe, CI, t-test |
| **4. Conclude** | `STEP 4: CONCLUDE` | the answer in plain English |

And the six skills the assignment asks for:

| Skill | Where |
|---|---|
| Analytic question formulation | Step 1 |
| Data wrangling | Skill 2 |
| Data preparation and sampling | Skill 3 |
| Descriptive statistics | Skill 4 |
| Confidence interval | Skill 5 |
| Two-sample t-test | Skill 6 |

---

## Words you might get asked about

| Word | In plain English |
|---|---|
| **Population** | everyone you could measure — all 48 teams |
| **Sample** | the smaller group you actually measured — our 30 |
| **Parameter** | a number describing the population |
| **Statistic** | a number worked out from the sample |
| **Mean** | the average |
| **Median** | the middle value |
| **Range** | biggest minus smallest |
| **IQR** | the spread of the middle half |
| **Standard deviation** | how far a typical value sits from the average |
| **Ratio data** | numbers with a real zero — a conversion rate |
| **Nominal data** | labels, not quantities — "high" and "low" volume |
| **Central Limit Theorem** | why a sample of 30+ makes the maths work |
| **Standard error** | how much your answer would wobble with a different sample |
| **Margin of error** | the ± part of a confidence interval |
| **Confidence interval** | the range the true answer probably sits in |
| **H₀ / Hₐ** | the "no difference" claim and the "there is a difference" claim |
| **p-value** | how often luck alone would produce a result this extreme |
| **Significant** | p is under 0.05 — probably not a coincidence |
| **Welch's test** | a t-test that doesn't assume both groups are equally spread |
| **Feature construction** | building a new column out of existing ones |
| **Discretisation** | turning a number into categories (high / low) |
| **Listwise deletion** | dropping a whole row that has a gap in it |
| **Attempt at Goal** | FIFA's name for a shot |
