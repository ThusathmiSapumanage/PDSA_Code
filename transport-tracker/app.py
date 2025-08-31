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

@app.route("/route/<route_id>/stop/<stop_name>")
def route_view(route_id, stop_name):
    arrivals = tm.get_next_arrivals(route_id, stop_name, count=5)
    return render_template("route.html", route_id=route_id, stop_name=stop_name, arrivals=arrivals)

@app.route("/stop/<stop_name>/earliest")
def stop_view(stop_name):
    ea = tm.get_earliest_arrival_at_stop(stop_name)
    if not ea:
        flash("No arrivals found for this stop.")
        return redirect(url_for("index"))
    eta, r_id, v_id = ea
    return render_template("stop.html", stop_name=stop_name, eta=eta, route_id=r_id, vehicle_id=v_id)

@app.route("/incidents/<route_id>")
def incidents(route_id):
    items = tm.get_recent_reports(route_id, limit=100)
    return render_template("incidents.html", route_id=route_id, items=items)

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

@app.route("/api/report", methods=["POST"])
def api_report():
    d = request.get_json(force=True)
    ok = tm.submit_report(
        route_id=d.get("route_id"),
        vehicle_id=d.get("vehicle_id"),
        report_type=d.get("report_type"),
        severity=int(d.get("severity", 1)),
        message=d.get("message", ""),
        stop_name=d.get("stop_name")
    )
    return jsonify({"ok": ok})

@app.route("/api/depart", methods=["POST"])
def api_depart():
    d = request.get_json(force=True)
    ok = tm.record_departure(
        route_id=d.get("route_id"),
        vehicle_id=d.get("vehicle_id"),
        stop_name=d.get("stop_name")
    )
    return jsonify({"ok": ok})

@app.route("/api/stops")
def api_stops():
    route_id = request.args.get("route_id")
    if not route_id:
        return jsonify({"ok": False, "error": "route_id required"}), 400
    routes = tm.get_routes()
    route = routes.get(route_id)
    if not route:
        return jsonify({"ok": False, "error": "unknown route"}), 404
    return jsonify({"ok": True, "stops": route.get("stops", [])})

@app.route("/api/vehicle_status")
def api_vehicle_status():
    route_id = request.args.get("route_id")
    if not route_id:
        return jsonify({"ok": False, "error": "route_id required"}), 400
    vmap = tm.vehicles.get(route_id)
    if not vmap:
        return jsonify({"ok": True, "vehicles": {}})
    out = {}
    for vid, v in vmap.items():
        out[vid] = {
            "delayMinutes": int(v.get("delayMinutes", 0)),
            "currentStopIndex": int(v.get("currentStopIndex", 0))
        }
    return jsonify({"ok": True, "vehicles": out})

@app.route("/api/reports")
def api_reports():
    route_id = request.args.get("route_id")
    limit = int(request.args.get("limit", 5))
    if not route_id:
        return jsonify({"ok": False, "error": "route_id required"}), 400
    items = tm.get_recent_reports(route_id, limit=limit)
    return jsonify({"ok": True, "items": items})

@app.route("/api/stop_geo")
def api_stop_geo():
    stop_name = request.args.get("stop_name", "")
    if not stop_name:
        return jsonify({"ok": False, "error": "stop_name required"}), 400
    data = tm.get_stop_geo(stop_name)
    if not data:
        return jsonify({"ok": False, "error": "location not found"}), 404
    return jsonify({"ok": True, "geo": data})

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)