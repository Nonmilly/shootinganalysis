# How This Project Works — the code, explained against the unit notes

This document explains every part of the code in plain English, using the
terms from the unit. Each section says which week's material it comes from, so
you can point at any line of code and name the concept behind it.

---

## Quick map: notes → code

| Week | Concept from the notes | Where it is in the code |
|---|---|---|
| 1 | Response variable | `Conversion` — the thing being measured |
| 1 | Explanatory variable | high / low shooting volume — the group split |
| 1 | Population vs sample | `population_size` (48) vs `sample` (30) |
| 2 | Levels of measurement | `"measurement_level": "ratio, continuous"` |
| 2 | Central tendency | `statistics.mean()`, `statistics.median()` in `describe()` |
| 2 | Dispersion | range, IQR, variance, std in `describe()` |
| 2 | Sample vs population variance | `ddof=1` in `np.var()` / `np.std()` |
| 3 | Simple random sampling | `.sample(n=30, random_state=3)` |
| 3 | Central Limit Theorem | why `n=30` — see `"why_30"` |
| 3 | Standard error | `sd / math.sqrt(n)` |
| 3 | Margin of error | `critical * standard_error` |
| 3 | z* vs t* rule | the `if n >= 30:` in `confidence_interval()` |
| 3 | Confidence interval | `confidence_interval()` |
| 4 | Null / alternative hypothesis | the `hypotheses` dict — `H0`, `Ha` |
| 4 | Conditions for inference | `check_normality()` + `.sample()` |
| 4 | Two-sample t-test | `stats.ttest_ind(a, b, equal_var=False)` |
| 4 | p-value and the 0.05 rule | `reject_null = p_value <= alpha` |
| 4 | 4-Step Process | the STEP 1–4 comment blocks in the task file |
| 5 | Data acquisition | `scraper.py` (FIFA's official data service) |
| 5 | Listwise (case) deletion | `df.dropna(subset=[...])` |
| 5 | Feature construction | `df["Conversion"] = df["Goals"] / df["Attempts"]` |
| 5 | Discretisation (binning) | splitting teams on median attempts/match |

---

## 1. The big idea

The notes describe data science as solving a real problem using data, and split
the work into stages: **data acquisition → data wrangling → analysis**. That is
exactly the shape of this project.

1. **Get data** — `scraper.py` downloads it from FIFA and saves it to a CSV.
2. **Tidy it** — drop what we don't need, fix types, handle missing values.
3. **Analyse it** — descriptive statistics, a confidence interval, a t-test.
4. **Show it** — a web page with a button.

---

## 2. Step 1 — State: the analytic question

The unit's 4-Step Process for a hypothesis test begins with **State**: what is
the practical question?

> How efficiently do teams convert their attempts at goal into goals at the
> 2026 World Cup, and do high-volume shooting teams convert at a different rate
> from low-volume shooting teams?

The two columns this uses:

**Attempts** — how many times the team tried to score. FIFA records one
"Attempt at Goal" event every time a player has a go, and the scraper counts
them across all 104 matches.

**Goals** — how many went in, taken from each match's official score.

**Conversion rate** — the two divided:

```
Conversion = Goals ÷ Attempts
```

A team with 70 attempts and 10 goals converts 10 ÷ 70 = **0.143**, or about
one in seven. This is FIFA's own published *Attempt at Goal Conversion Rate*.

**Why this is about efficiency, not goals.** A team can score a lot of goals by
shooting constantly without being efficient, and a team can score few goals
very efficiently. Conversion separates the two, which is what keeps this task
distinct from any task that counts goals.

### The variables

The notes distinguish the **response variable** (what we want to explain) from
the **explanatory variable** (what we think explains it).

- **Response:** `Conversion` — continuous, **ratio** data. Ratio because it has
  a true zero: 0 genuinely means nothing went in.
- **Explanatory:** whether a team is a high- or low-volume shooter — **nominal**
  data, because the two labels are just names with no numerical sense.

---

## 3. Step 2 — Plan: the hypotheses

The notes say a hypothesis test is two competing claims, and you must state
both. In `tasks/task3_shooting.py`:

```python
hypotheses = {
    "H0": "mu_high = mu_low",
    "Ha": "mu_high != mu_low",
    "tail": "two-sided",
    "test": "two-sample (independent) t-test",
    "alpha": 0.05,
}
```

**H₀ (null hypothesis)** — the boring claim. There is no difference; both
groups convert at the same rate.

**Hₐ (alternative hypothesis)** — the claim we're looking for evidence of. The
two groups convert at *different* rates.

It is **two-sided** (`!=` rather than `>` or `<`) because, like the community
service example in the notes, I have no direction in mind. There are arguments
both ways — shooting often might mean taking worse chances and converting less,
or it might mean being on top of the game and converting more — so I test only
whether they differ.

**Test chosen:** the two-sample (independent) t-test, because I'm comparing the
means of two separate groups. A one-sample t-test would be for comparing one
group against a fixed number.

---

## 4. Step 3 — Solve, part one: data wrangling

The notes define wrangling as moving data "from their raw formats into
something more suitable for analytics". Four things happen:

```python
df = df[["Team", "Matches", "Goals", "Attempts"]].copy()   # keep what I need
df[c] = df[c].astype(float)                                 # text -> numbers
df = df.dropna(subset=["Matches", "Goals", "Attempts"])     # missing values
df = df[df["Attempts"] > 0]                                 # avoid ÷ by zero
```

### The missing-values decision

The notes give three options: **listwise (case) deletion**, **mean
substitution**, and **regression imputation**. I used listwise deletion —
`.dropna()` — which removes the whole row if any value I need is missing.

The notes warn this "may inadvertently introduce bias in the dataset or
significantly reduce the statistical power when the dataset is not large
enough". Two reasons it's still the right call here:

1. The downloaded data is complete — **0 rows are actually dropped**, so there
   is no bias or lost power to worry about.
2. Mean substitution would invent a shot count for a real team. That drags
   every result towards the average and, as the notes put it, "severely
   underestimates the substitution errors". Since the *spread* of conversion
   rates is exactly what I'm studying, faking values would damage the result.

The `Attempts > 0` line is separate — it isn't about missing data. Conversion
divides by attempts, so a team with zero would break the maths.

---

## 5. Step 3, part two: preparation and sampling

### Feature construction

```python
df["Conversion"] = df["Goals"] / df["Attempts"]
```

The notes call this **feature construction** — manually building a new variable
out of existing ones, exactly like their BMI example:

```
BMI = Weight (kg) ÷ Height (m)²        Conversion = Goals ÷ Attempts
```

### Simple random sampling

```python
sample = df["Conversion"].sample(n=min(30, population_size), random_state=3)
```

- **Population** = all 48 teams — every team we could measure.
- **Sample** = 30 of them, drawn at random.

The notes distinguish a **parameter** (a number describing the population, like
μ) from a **statistic** (a number computed from the sample, like x̄). We compute
statistics from our 30 and use them to infer the parameter for all teams. That
inference is the whole point of Weeks 3 and 4.

**Why exactly 30?** This is the Central Limit Theorem. The notes state that the
sampling distribution of the sample mean approximates a normal distribution
"provided that the size of each sample is sufficiently large, which is usually
30 or larger". Below 30 the confidence interval maths is on shakier ground. 30
is the smallest sample that satisfies the condition.

`random_state=3` locks the randomness so the same 30 teams are drawn every run.
Your numbers won't change between testing and demonstrating.

### Checking the conditions for inference

The notes' Step 3 says to check two things before trusting the result.

**Condition 1 — was this simple random sampling?** Yes. `.sample()` draws at
random, and the notes warn that otherwise "the conclusion of the ensuing
hypothesis test may not be valid".

**Condition 2 — is the sample roughly normal?** `check_normality()` measures
**skewness**. A normal distribution is symmetric, so its mean and median sit
together and skewness is near 0.

```
mean 0.1113   median 0.1124   skewness 0.209
```

The mean and median sit almost on top of each other and skewness is 0.21, well
inside the usual ±0.5 guide — this is about as symmetric as real data gets, so
we can proceed. (If you want the visual check the notes prefer, a histogram via
`matplotlib.pyplot.hist()` would show the same thing.)

---

## 6. Step 3, part three: descriptive statistics

The notes say data is described in two aspects, and `describe()` does both.

### Central tendency

```python
mean   = statistics.mean(s)
median = statistics.median(s)
```

**Mean** — add everything, divide by how many. **0.1113**, so about **11% of
attempts become goals** — roughly one in nine.

**Median** — the middle value once they're lined up in order. **0.1124**.

Why both? Five people earning £20,000 have a mean of £20,000. Elon Musk walks
in and the mean leaps into the millions, though nobody in the room earns that.
The median stays at £20,000. As the notes put it, the median is "a better
measure of central tendency than the mean for data that is asymmetrical or that
contains outliers". Here the two are almost identical, which is itself useful
information: no team is distorting the average.

**No mode.** Deliberately. The notes say the mode is "normally used for
describing nominal or ordinal data". Conversion is continuous ratio data where
almost every value is unique, so a mode would be meaningless.

### Dispersion

```python
data_range = largest - smallest                # range
iqr        = q3 - q1                           # interquartile range
variance   = float(np.var(s, ddof=1))          # sample variance
std        = float(np.std(s, ddof=1))          # sample standard deviation
```

```
range 0.2391      IQR 0.0738
variance 0.00299  standard deviation 0.0547
```

**Range** — biggest minus smallest. The simplest measure of spread, but one
freak value distorts it completely.

**IQR** — the 75th percentile minus the 25th. The spread of the middle half of
the data, which is why outliers can't distort it. Note it is much smaller than
the range: most teams are bunched together, and the range is stretched by the
extremes. (The notes also use IQR for outlier detection: anything more than
1.5 × IQR outside the quartiles.)

**Variance and standard deviation** — how much, on average, values differ from
the mean. The standard deviation is just the square root of the variance, and
it's the more useful of the two because it's back in the original units.

**Why `ddof=1` matters.** The notes give two formulas:

```
sample:      s² = 1/(n-1) · Σ(xᵢ - x̄)²
population:  σ² = 1/n     · Σ(xᵢ - μ)²
```

`ddof=1` means "divide by n−1" — the **sample** formula. We have a sample, not
a population, so this is the correct one. Leaving it out would silently compute
the population variance and give a slightly-too-small answer.

Two classes both average 70%. In class A everyone scored 68–72 — small standard
deviation, uniform class. In class B half scored 40 and half scored 100 — same
mean, huge standard deviation, completely different class. That's why the
central tendency alone is never enough.

---

## 7. Step 3, part four: the confidence interval

We measured 30 teams, not every team, so our mean is an estimate. A confidence
interval turns that estimate into a range. The notes' formula:

```
CI = x̄ ± z* · (s / √n)
```

and the code follows it term by term:

```python
standard_error  = sd / math.sqrt(n)          #  s / √n
critical        = stats.norm.ppf(0.975)      #  z*
margin_of_error = critical * standard_error  #  z* · s / √n
```

**Standard error** — `s / √n`. How much the sample mean itself would wobble if
we drew a different 30 teams. Bigger sample → smaller wobble, which is why n
sits under a square root.

**Margin of error** — the standard error scaled by the critical value. This is
the ± part.

**The critical value.** The notes list z* = 1.645 (90%), **1.960 (95%)**, and
2.576 (99%), and give a rule for choosing between z* and t*:

> if the sample size is "small" (<30), use t* … if the sample size is "large"
> (30 or greater), use z*

The code writes that rule out directly:

```python
if n >= 30:
    critical = float(stats.norm.ppf((1 + conf) / 2))      # z*
else:
    critical = float(stats.t.ppf((1 + conf) / 2, n - 1))  # t*
```

Our n is 30, so it picks **z\* = 1.960**, which is what the unit's convention
asks for. If your sample were smaller it would switch to t* with df = n − 1 on
its own. The notes also point out that at large n the two barely differ.

### Reading the result

```
mean 0.1113   standard error 0.00998   z* 1.960   margin of error 0.01956
CI = 0.0918 to 0.1309
```

We are 95% confident the true mean conversion rate of all teams lies between
**0.092 and 0.131** — roughly **9% to 13% of attempts become goals**.

The 95% means what the notes say it means: if we repeated this study many
times, about 95 intervals in 100 would contain the true mean. It does not mean
there's a 95% chance this particular interval is right.

---

## 8. Step 3, part five: the two-sample t-test

High-volume shooters average 0.121, low-volume shooters 0.103. The high group
looks slightly better — but is that real, or luck in who landed where?

Six heads from ten coin flips proves nothing; sixty from a hundred is harder to
dismiss. The t-test makes that judgement with maths.

### Splitting the groups

```python
df["AttemptsPerMatch"] = df["Attempts"] / df["Matches"]
median_attempts = df["AttemptsPerMatch"].median()
high = df[df["AttemptsPerMatch"] >= median_attempts]["Conversion"]
low  = df[df["AttemptsPerMatch"] <  median_attempts]["Conversion"]
```

**Why per match, not total attempts?** Teams that went further played more
matches and so racked up more attempts automatically. Dividing by matches
played makes a group-stage team and a finalist comparable — otherwise the split
would really be measuring who survived longest.

Splitting a continuous variable at its median like this is **discretisation**
(binning) from the Week 5 notes — the same idea as their age →
child/youth/adult example. Splitting at the median guarantees two groups of
equal size (24 and 24).

### The test

```python
t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
```

`scipy.stats.ttest_ind()` is the exact function the Week 4 practical lists for
performing a two-sample t-test from sample values. The notes' manual formula is:

```
t* = (x̄₁ - x̄₂) / √( s₁²/n₁ + s₂²/n₂ )
```

`equal_var=False` — **Welch's test** — is the version that keeps the two
groups' variances separate, which is precisely the formula above, and is the
safer choice when the two groups aren't identically spread.

**Degrees of freedom.** The notes use df = n − 1, and for a two-sample test take
"a conservative approach" of the smaller group's df. Both groups are 24, so
`df_conservative = 23` — that's the row you'd look up in the t-table. scipy
works out its own more precise df internally, which is why the notes say
software "gives a lot more precise p-value than the one determined using the
manual method".

### The p-value

The notes' definition:

> p-value is the probability, assuming that H₀ is true, that the test statistic
> would take a value as extreme or more extreme than what is actually observed

And the decision rule: reject H₀ when p ≤ 0.05. The code is that rule, written
once:

```python
reject_null = bool(p_value <= alpha)
```

---

## 9. Step 4 — Conclude

```
High-volume shooters (≥ 11.3 attempts/match):  n 24, mean 0.1210
Low-volume shooters  (< 11.3 attempts/match):  n 24, mean 0.1026
t = 1.1997,  p = 0.2366,  df = 23
```

**p = 0.2366, well above 0.05.**

Following the notes' Interpretation 2: if H₀ were true, a difference this large
between the group means could still turn up by chance about 24% of the time.
That is not unusual at all, so the gap is likely "just part of the ordinary
variation".

**We do not reject the null hypothesis. There is not enough evidence that
high-volume shooting teams convert at a different rate from low-volume shooting
teams.**

And the first half of the question, answered from the confidence interval:

**Teams convert about 11.1% of their attempts, and we are 95% confident the
true mean for all teams is between 9.2% and 13.1%.**

A "no significant difference" result is a real finding, not a failed one. Here
it is genuinely interesting: it suggests shooting *volume* and shooting
*efficiency* are largely independent — taking more shots doesn't come at the
cost of taking worse ones. The mistake would be looking at 0.121 versus 0.103,
declaring the high-volume group better, and ignoring the p-value — which is the
exact error the t-test exists to prevent.

**Reporting in APA format** (the notes link a guideline): *t*(23) = 1.20,
*p* = .237.

---

## 10. The supporting files

### `scraper.py` — data acquisition

The notes place wrangling "between the data acquisition and the exploratory
data analysis stages". This file is that acquisition stage.

**The problem it solves.** The fifa.com statistics pages build their tables
with JavaScript after the page loads, so there is no HTML table sitting in the
page for `pandas.read_html()` to read — the page arrives as a 4 KB shell. But
those pages get their numbers from FIFA's own data service, and that service is
public. So the scraper asks it directly:

```
api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023
    -> the 104 matches and their scores
api.fifa.com/api/v3/timelines/17/285023/{stage}/{match}
    -> every event in that match: "Attempt at Goal", "Corner", "Foul", ...
```

`competition 17` is the FIFA World Cup; `season 285023` is the 2026 tournament.

Counting each team's events across all 104 matches turns match-by-match events
into one row per team:

```
Team, Matches, Goals, GoalsAgainst, Attempts, Assists,
Corners, Offsides, Fouls, YellowCards, Saves
```

Goals come from each match's official score rather than from counting "Goal!"
events, because the score is the authoritative record.

Every run does the same three steps, in `get_data()`:

1. **Download** the matches and timelines (about 30 seconds — 105 requests).
2. **Delete** any existing `data/fifawcextract.csv`.
3. **Save** the fresh data there — then load it straight back.

Deleting first matters: it guarantees the file holds this run's data only, and
can never be a half-overwritten mix of old and new. Loading the analysis *from*
the saved file means the CSV is always exactly what the analysis ran on.

**There is no backup CSV.** If the download fails, `get_data()` returns an
empty table and the task reports the failure, rather than quietly analysing
stale numbers.

The file still handles ordinary web tables too: give it a non-FIFA URL and it
uses `pd.read_html()` with `clean()` to squash two-row headings, drop blank
separator rows, strip footnote markers like `[12]`, and convert text to
numbers.

### `stats_helpers.py` — the statistics

`describe()`, `check_normality()`, `confidence_interval()` and
`two_sample_ttest()`. Kept in their own file so the task file reads as the
analysis rather than the arithmetic. Each function names the week it comes from
and the formula it implements.

### `app.py` — Flask

**Flask** turns Python into a website. A **route** is a web address plus the
code that answers it:

| Route | What it does |
|---|---|
| `/` | shows the page |
| `/api/task` | runs the analysis, returns the results |
| `/api/scrape` | downloads the data, returns it as a table |

Results travel as **JSON**, a text format for passing data between programs:
`{"mean": 0.1113, "n": 30}`. The page reads those labels and knows what to
display.

### `templates/index.html`

**HTML** is the structure, **CSS** the appearance, **JavaScript** the
behaviour. On click it fetches `/api/task` and builds the results card. The
folder must be named exactly `templates` — Flask looks nowhere else.

---

## 11. Running it

The notes recommend a dedicated conda environment, which also avoids clashes
with whatever else is installed:

```
conda create -n hit140env python
conda activate hit140env
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000**. `127.0.0.1` means "this computer" — the
site isn't on the internet, only you can see it. `5000` is the port. Ctrl+C
stops it.

You need an internet connection, because the data is downloaded fresh each run.

---

## 12. Terms you might be asked about

| Term | Meaning |
|---|---|
| **Population** | every item you could measure (all 48 teams) |
| **Sample** | a subset drawn from it (our 30) |
| **Parameter** | a number describing the population (μ, σ) |
| **Statistic** | a number computed from the sample (x̄, s) |
| **Ratio data** | numeric with a true zero — conversion rate |
| **Nominal data** | labels with no numerical sense — high / low volume |
| **Central tendency** | mean, median, mode |
| **Dispersion** | range, IQR, variance, standard deviation |
| **Central Limit Theorem** | sample means are normally distributed once n ≥ 30 |
| **Standard error** | s / √n — how much the sample mean wobbles |
| **Margin of error** | z* · s / √n — the ± of a confidence interval |
| **Confidence interval** | a range the population parameter probably sits in |
| **H₀ / Hₐ** | null and alternative hypotheses |
| **p-value** | chance of a result this extreme if H₀ were true |
| **α (alpha)** | the cutoff, 0.05 |
| **Degrees of freedom** | n − 1; the t-distribution's shape depends on it |
| **Welch's test** | two-sample t-test not assuming equal variances |
| **Listwise deletion** | dropping a whole row that has a missing value |
| **Feature construction** | building a new variable from existing ones |
| **Discretisation** | turning a continuous variable into categories |
| **Attempt at Goal** | FIFA's term for a shot; `Attempts` counts them |
| **Conversion rate** | goals ÷ attempts — FIFA's shooting-efficiency metric |
