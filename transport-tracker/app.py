from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime
from transport.manager_fb_ds import TransportManagerFB

app = Flask(__name__)
app.secret_key = "dev-secret"

tm = TransportManagerFB()

@app.before_request
def load_snapshot():
    tm.refresh_from_db()

@app.template_filter("datetime")
def ts_to_dt(value):
    try:
        return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        route_id = request.form.get("route_id", "").strip()
        stop_name = request.form.get("stop_name", "").strip()
        if route_id and stop_name:
            return redirect(url_for("route_view", route_id=route_id, stop_name=stop_name))
        flash("Please enter both Route ID and Stop name.")
    routes = tm.get_routes()
    return render_template("index.html", routes=routes)

# ---------- APIs ----------
@app.route("/api/arrivals")
def api_arrivals():
    route_id = request.args.get("route_id")
    stop_name = request.args.get("stop_name")
    if not route_id or not stop_name:
        return jsonify({"ok": False, "error": "route_id and stop_name required"}), 400
    data = tm.get_next_arrivals(route_id, stop_name, count=5)
    return jsonify({"ok": True, "arrivals": data})

@app.route("/api/next_arrival")
def api_next_arrival():
    route_id = request.args.get("route_id")
    stop_name = request.args.get("stop_name")
    if not route_id or not stop_name:
        return jsonify({"ok": False, "error": "route_id and stop_name required"}), 400
    res = tm.get_next_arrival_epoch(route_id, stop_name)
    if not res:
        return jsonify({"ok": True, "nextEpoch": None, "vehicleId": None})
    epoch, vid = res
    return jsonify({"ok": True, "nextEpoch": int(epoch), "vehicleId": vid})
