# app.py
# Flask app for my part of the WC2026 group project.
# My task is Task 3 - shooting efficiency.
# It loads the data (scraped or from the csv) and runs my analysis.
# Run with:  python app.py   then open http://127.0.0.1:5000

from flask import Flask, jsonify, render_template, request
from scraper import get_data
from tasks import task3_shooting

app = Flask(__name__)


@app.route("/")
def home():
    # the web page
    return render_template("index.html")


@app.route("/api/task")
def api_task():
    """run my shooting analysis and send the results back as json"""
    return jsonify(task3_shooting.run())


@app.route("/api/scrape")
def api_scrape():
    """
    Get the data and show it as a table.
    Pass ?url=... to scrape a site live, otherwise it uses the csv.
    """
    url = request.args.get("url")  # None if not given -> uses the csv
    idx = int(request.args.get("table_index", 0))
    cfg = {
        "url": url,
        "table_index": idx,
        "csv_fallback": "data/team_stats.csv",
    }
    df = get_data(cfg)
    if df.empty:
        return jsonify({"error": "no data could be loaded"}), 500

    # send the columns and the rows so the page can build a table
    return jsonify({
        "source": url if url else "fallback CSV (data/team_stats.csv)",
        "rows": len(df),
        "columns": list(df.columns),
        # only send the first 50 rows so the page doesn't get huge
        "data": df.head(50).fillna("").to_dict(orient="records"),
    })


if __name__ == "__main__":
    app.run(debug=True)
