# scraper.py
# This is the bit that gets the data.
#
# It downloads the World Cup table off the web and saves it to
# data/fifawcextract.csv. If that file already exists it is DELETED first,
# so the extract always holds the data from the latest download and never
# a mix of old and new.
#
# There is no backup csv. If the download fails there is no data, and the
# task will say so rather than quietly analyse something out of date.
#
# The unit only uses pandas for loading data, so that is all this uses:
#   pd.read_html(url)   - downloads a page and reads its tables
#   df.to_csv(path)     - saves a DataFrame to a csv file
#   pd.read_csv(path)   - reads it back

import os
import pandas as pd

# the folder this file is in, so paths work no matter where you run from
HERE = os.path.dirname(__file__)

# where the downloaded data gets saved
EXTRACT = "data/fifawcextract.csv"

# Most sites refuse a request that doesn't look like a real browser, so we
# tell them we're Chrome. read_html() sends this along for us.
BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def full_path(path):
    """turn 'data/fifawcextract.csv' into a full path off this folder"""
    return path if os.path.isabs(path) else os.path.join(HERE, path)


def scrape_tables(url):
    """
    Read every table on a web page into a list of DataFrames.
    read_html() finds the <table> tags for us, so there is nothing to
    take apart by hand.
    """
    try:
        return pd.read_html(url, storage_options=BROWSER)
    except Exception as e:
        # site blocked us, page has no tables, or no internet
        print("could not scrape:", e)
        return []


def clean(df):
    """
    Tidy up a freshly scraped table. Web tables are messy, so:
      - squash two-row headings into single column names
      - drop the blank rows sites use as separators
      - strip footnote markers like [12] out of the text
      - turn number columns that arrived as text into real numbers
    """
    # two rows of headings become a MultiIndex - squash them to one name
    if isinstance(df.columns, pd.MultiIndex):
        names = []
        for col in df.columns:
            parts = [str(p) for p in col if "Unnamed" not in str(p)]
            names.append(parts[-1] if parts else str(col[-1]))
        df.columns = names

    # blank separator rows (.copy() so pandas knows this is its own table
    # now, not a slice of the original)
    df = df.dropna(how="all").copy()

    for c in df.columns:
        if df[c].dtype == object:
            df[c] = (df[c].astype(str)
                          .str.replace(r"\[.*?\]", "", regex=True)  # footnotes
                          .str.replace("−", "-", regex=False)       # odd minus
                          .str.strip())
        # if a column is really numbers, make it numbers. errors="coerce"
        # turns anything that isn't a number into NaN, so I only keep the
        # conversion when nearly the whole column converted properly.
        as_numbers = pd.to_numeric(df[c], errors="coerce")
        if as_numbers.notna().sum() >= len(df) * 0.8:
            df[c] = as_numbers

    return df.reset_index(drop=True)


def download_to_csv(url, table_index=0, out_csv=EXTRACT):
    """
    Download the table, clean it, and save it to the extract file.
    Any existing extract is deleted first so nothing old is left behind.
    Returns the path it saved to, or None if the download failed.
    """
    print("downloading:", url)
    tables = scrape_tables(url)

    if len(tables) <= table_index:
        print("no table", table_index, "on that page - nothing downloaded")
        return None

    df = clean(tables[table_index])
    path = full_path(out_csv)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # delete the old extract first, so the file can only ever hold the
    # data from this download
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

    source_config is a dictionary like:
        {
          "url": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup",
          "table_index": 68,
          "extract_csv": "data/fifawcextract.csv"
        }
    """
    url = source_config.get("url")
    idx = source_config.get("table_index", 0)
    out = source_config.get("extract_csv", EXTRACT)

    if not url:
        print("no url given - nothing to download")
        return pd.DataFrame()

    path = download_to_csv(url, idx, out)
    if path is None:
        return pd.DataFrame()

    # load it back from the file we just wrote
    df = pd.read_csv(path)
    print("loaded", len(df), "rows from", out)
    return df


if __name__ == "__main__":
    # quick test - download the 2026 World Cup table and show the top of it
    cfg = {
        "url": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup",
        "table_index": 68,
        "extract_csv": EXTRACT,
    }
    print(get_data(cfg).head())
