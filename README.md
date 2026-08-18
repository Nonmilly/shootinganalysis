# FIFA World Cup 2026 — Shooting Efficiency (Assessment 2)

My analytic task for the group project. A Flask app that **downloads** real
2026 World Cup data from **FIFA's official data service**, saves it to
`data/fifawcextract.csv`, and analyses **shooting efficiency**.

Task 3 — Shooting efficiency — Mildred (`tasks/task3_shooting.py`)

## The analytic question
How efficiently do teams convert their attempts at goal into goals at the 2026
World Cup, and do high-volume shooting teams convert at a different rate from
low-volume shooting teams?

**Focal point:** attempt-at-goal conversion rate (`Goals / Attempts`) — FIFA's
own efficiency metric. This is about *efficiency*, not about how many goals a
team scored, so it stays distinct from a goals-count task.

## What the task covers
1. Analytic question formulation
2. Data wrangling
3. Data preparation and sampling
4. Descriptive statistics
5. Inferential statistics — confidence interval
6. Inferential statistics — two-sample t-test

Each is marked with a labelled comment block in `tasks/task3_shooting.py`, laid
out along the unit's 4-Step Process for a hypothesis test (State → Plan →
Solve → Conclude). The hypotheses, the conditions for inference and the written
conclusion are all produced by the code and shown on the page.

## Hypotheses
```
H0: mu_high  =  mu_low    (both groups convert at the same rate)
Ha: mu_high !=  mu_low    (two-sided)   alpha = 0.05
```

## Result
```
Sample:  n = 30 of 48 teams, simple random sampling
CI:      mean 0.1113, z* = 1.960, SE 0.00998 -> [0.0918, 0.1309]
t-test:  high volume (n 24, mean 0.1210) vs low volume (n 24, mean 0.1026)
         t(23) = 1.20, p = .237  ->  do not reject H0
```

## How to run

**Terminal version** (no web page, prints everything out):
```
pip install -r requirements.txt
python task3.py
```

**Web version:**
```
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

- Click **Load data** to download the table and see it.
- Click the task button to run the analysis.

You need an internet connection. There is no backup CSV — if the download
fails, the task reports that instead of analysing stale data.

## Where the data comes from
FIFA's **official data service** — the same one that fills in the statistics
pages on fifa.com. Those pages build their tables with JavaScript, so there is
no HTML table to read off the page itself; the data behind them is public:

```
api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023
    -> the 104 matches and their scores
api.fifa.com/api/v3/timelines/17/285023/{stage}/{match}
    -> every event in a match: "Attempt at Goal", "Corner", "Foul", ...
```

`competition 17` is the FIFA World Cup and `season 285023` is the 2026
tournament (11 Jun – 19 Jul 2026).

Counting each team's events across all 104 matches gives one row per team:

```
Team, Matches, Goals, GoalsAgainst, Attempts, Assists,
Corners, Offsides, Fouls, YellowCards, Saves
```

Every run does the same three things:

1. **download** the 104 matches and their timelines (about 30 seconds)
2. **delete** any existing `data/fifawcextract.csv`
3. **save** the fresh data there, then **load it back** for the analysis

So the extract file always holds exactly the data the analysis ran on — never
a mix of old and new.

**In the app**, a fifa.com address in the URL box (or an empty box) uses this
service. Any other address is read as an ordinary HTML table with
`pd.read_html()`, and the table number picks which table.

**Note:** FBRef blocks automated requests (HTTP 403), so it cannot be used.

## Files
```
task3.py                  - terminal version: downloads + analyses + prints
app.py                    - Flask app, runs the task + the download endpoint
TASK3_EXPLAINED.md        - task3.py explained simply, tied to the notes
CODE_EXPLAINED.md         - plain-English explanation of the whole project
scraper.py                - downloads the data and writes the extract csv
stats_helpers.py          - describe / confidence interval / t-test functions
tasks/task3_shooting.py   - my analytic task
templates/index.html      - the web page
data/fifawcextract.csv    - the downloaded data (rewritten every run)
```

## Note on the data
Both `Goals` and `Attempts` come from FIFA's own records: goals from each
match's official score, attempts from the "Attempt at Goal" events in the
match timeline. `Goals / Attempts` is FIFA's published *Attempt at Goal
Conversion Rate*.

FIFA's data service does not expose expected goals (xG) or a separate
on-target count, so the conversion rate here is goals per *attempt*, not goals
per shot *on target*.
