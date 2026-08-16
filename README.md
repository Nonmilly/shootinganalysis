# FIFA World Cup 2026 — Scoring Efficiency (Assessment 2)

My analytic task for the group project. A Flask app that **downloads** real
2026 World Cup team data from the web, saves it to `data/fifawcextract.csv`,
and analyses **scoring efficiency**.

Task 3 — Scoring efficiency — Mildred (`tasks/task3_shooting.py`)

## The analytic question
How many goals per match does a team score at the 2026 World Cup, and do teams
that reached the knockout stage score at a different rate to teams that were
eliminated in the group stage?

**Focal point:** goals scored per match (`GF / Pld`).

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
H0: mu_knockout  =  mu_group    (both groups score at the same rate)
Ha: mu_knockout !=  mu_group    (two-sided)   alpha = 0.05
```

## Result
```
Sample:  n = 30 of 48 teams, simple random sampling
CI:      mean 1.3053, z* = 1.960, SE 0.13582, MoE 0.2662 -> [1.0391, 1.5715]
t-test:  knockout (n 32, mean 1.6487) vs group stage (n 16, mean 0.6667)
         t(15) = 6.70, p < .0001  ->  reject H0
```

## How to run
```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

- Click **Load data** to download the table and see it.
- Click the task button to run the analysis.

You need an internet connection. There is no backup CSV — if the download
fails, the task reports that instead of analysing stale data.

## Where the data comes from
`scraper.py` downloads the final ranking table of all 48 teams from

```
https://en.wikipedia.org/wiki/2026_FIFA_World_Cup   (table 68)
```

and gives these columns: `Pos, Grp, Team, Pld, W, D, L, GF, GA, GD, Pts,
Final result`.

Every run does the same three things:

1. **download** the table with `pd.read_html()`
2. **delete** any existing `data/fifawcextract.csv`
3. **save** the fresh data to that file, then **load it back** for the analysis

So the extract file always holds exactly the data the analysis ran on — never
a mix of old and new.

The scraper is site-independent: point `SOURCE` in `tasks/task3_shooting.py`
at any page with an HTML table and set `table_index` to pick the table.

**Note:** FBRef blocks automated requests (HTTP 403), so it cannot be used as
a source. See the note on shooting data below.

## Files
```
app.py                    - Flask app, runs the task + the download endpoint
CODE_EXPLAINED.md         - plain-English explanation of the whole project
scraper.py                - downloads the data and writes the extract csv
stats_helpers.py          - describe / confidence interval / t-test functions
tasks/task3_shooting.py   - my analytic task
templates/index.html      - the web page
data/fifawcextract.csv    - the downloaded data (rewritten every run)
```

## Note on shots and xG
The original plan was shot conversion — goals per shot on target — and
comparing teams against their expected goals (xG). Neither shots on target nor
xG is published in any table that can be downloaded: FBRef has them but blocks
automated requests, and ESPN and Understat build their tables with JavaScript
so there is no table in the page to read.

The real data that *can* be downloaded gives goals, matches played and goals
against, so the task measures **goals per match** instead. It is still the
attacking/scoring focal point, and all six required skills are unchanged.

To go back to shot conversion you would need a source for `SoT` and `xG` —
for example an FBRef page saved to CSV by hand and read with `pd.read_csv()`.
