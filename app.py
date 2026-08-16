# app.py
# Flask app for my part of the WC2026 group project.
# My task is Task 3 - scoring efficiency.
# It downloads the data and runs my analysis.
# Run with:  python app.py   then open http://127.0.0.1:5000

from flask import Flask, jsonify, render_template, request
import scraper
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
    Download the data, save it to the extract csv, and show it as a table.
    Pass ?url=... to use a different page. If no url is given it uses the
    same one my task uses.
    """
    url = request.args.get("url") or task3_shooting.SOURCE["url"]
    idx = request.args.get("table_index")
    # if no table number was typed, use the one my task uses
    idx = int(idx) if idx not in (None, "") else task3_shooting.SOURCE["table_index"]

    cfg = {
        "url": url,
        "table_index": idx,
        "extract_csv": task3_shooting.SOURCE["extract_csv"],
    }
    df = scraper.get_data(cfg)
    if df.empty:
        # say WHY it failed, not just that it did
        return jsonify({"error": scraper.LAST_ERROR or "no data could be loaded"}), 500

    # send the columns and the rows so the page can build a table
    return jsonify({
        "source": url,
        "saved_to": cfg["extract_csv"],
        "rows": len(df),
        "columns": list(df.columns),
        # only send the first 50 rows so the page doesn't get huge
        "data": df.head(50).fillna("").to_dict(orient="records"),
    })


if __name__ == "__main__":
    app.run(debug=True)
