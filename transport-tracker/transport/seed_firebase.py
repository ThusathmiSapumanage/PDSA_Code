# transport/seed_firebase.py

import os, sys, random
from datetime import datetime, timedelta, timezone

# Ensure project root on sys.path so we can import firebase_init.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from firebase_init import init_firebase, rtdb_ref

# --- Helpers -----------------------------------------------------------------

LKT = timezone(timedelta(hours=5, minutes=30))  # Asia/Colombo (UTC+5:30)

def round_up_to_next_5(dt: datetime) -> datetime:
    """Round time up to the next 5-minute boundary."""
    minute = (dt.minute // 5) * 5
    rounded = dt.replace(second=0, microsecond=0, minute=minute)
    if rounded < dt.replace(second=0, microsecond=0):
        rounded += timedelta(minutes=5)
    # If already exactly on boundary but with seconds/micros, bump to next
    if dt.second != 0 or dt.microsecond != 0:
        if rounded <= dt:
            rounded += timedelta(minutes=5)
    return rounded

def epoch(dt: datetime) -> int:
    """Return UNIX epoch seconds (UTC) for timezone-aware datetime."""
    return int(dt.timestamp())

def make_vehicle_schedule(start_time_local: datetime, stops: list[str], segment_minutes: list[int]):
    """
    Build a stop-by-stop schedule given a start time at stops[0].
    segment_minutes: minutes between consecutive stops.
    """
    assert len(segment_minutes) == len(stops) - 1, "segment_minutes must be one less than stops"
    times_local = [start_time_local]
    current = start_time_local
    for seg in segment_minutes:
        current = current + timedelta(minutes=seg)
        times_local.append(current)
    # Convert to epochs (server expects epoch seconds)
    schedule = [{"stop": stop, "timeEpoch": epoch(t.astimezone(timezone.utc))} for stop, t in zip(stops, times_local)]
    return schedule

# --- Seed Data Builders -------------------------------------------------------

def build_routes():
    return {
        "B154": {
            "routeName": "Colombo - Mount Lavinia (Bus)",
            "stops": ["Fort", "Slave Island", "Bambalapitiya", "Wellawatte", "Dehiwala", "Mount Lavinia"]
        },
        "R01": {
            "routeName": "Colombo - Ragama (Suburban Train)",
            "stops": ["Fort", "Maradana", "Dematagoda", "Kelaniya", "Ragama"]
        }
    }

def build_stops_geo():
    return {
        "Fort":          {"lat": 6.9339, "lng": 79.8500},
        "Slave Island":  {"lat": 6.9176, "lng": 79.8489},
        "Bambalapitiya": {"lat": 6.8916, "lng": 79.8568},
        "Wellawatte":    {"lat": 6.8747, "lng": 79.8617},
        "Dehiwala":      {"lat": 6.8437, "lng": 79.8678},
        "Mount Lavinia": {"lat": 6.8390, "lng": 79.8653},
        "Maradana":      {"lat": 6.9273, "lng": 79.8657},
        "Dematagoda":    {"lat": 6.9396, "lng": 79.8777},
        "Kelaniya":      {"lat": 6.9550, "lng": 79.8985},
        "Ragama":        {"lat": 7.0279, "lng": 79.9173},
    }

def build_vehicles(now_local: datetime):
    """
    Create multiple vehicles per route with realistic headways and segment timings.
    Start times are aligned to the next 5-minute boundary from 'now_local'.
    """
    start0 = round_up_to_next_5(now_local)

    # --- B154 (Bus) timings ---
    b154_stops = ["Fort", "Slave Island", "Bambalapitiya", "Wellawatte", "Dehiwala", "Mount Lavinia"]
    # Approximate segment durations in minutes (busy urban corridor)
    # Fort→Slave 6, Slave→Bamba 8, Bamba→Wellawatte 8, Wellawatte→Dehiwala 8, Dehiwala→ML 9
    b154_segments = [6, 8, 8, 8, 9]
    b154_headway_min = 10
    b154_vehicles = {}

    # Create 3 buses staggered by 0/10/20 minutes
    for i, offset in enumerate([0, b154_headway_min, 2 * b154_headway_min], start=1):
        v_id = f"B154-V{i}"
        depart = start0 + timedelta(minutes=offset)  # from Fort
        schedule = make_vehicle_schedule(depart, b154_stops, b154_segments)
        b154_vehicles[v_id] = {
            "delayMinutes": 0,                # adjust dynamically elsewhere if needed
            "currentStopIndex": 0,            # your tracker can update this
            "schedule": schedule
        }

    # --- R01 (Train) timings ---
    r01_stops = ["Fort", "Maradana", "Dematagoda", "Kelaniya", "Ragama"]
    # Typical suburban running: Fort→Maradana 5, Maradana→Dematagoda 6, Dematagoda→Kelaniya 10, Kelaniya→Ragama 13
    r01_segments = [5, 6, 10, 13]
    r01_headway_min = 20
    r01_vehicles = {}

    # Create 2 trains staggered by 0/20 minutes
    for i, offset in enumerate([0, r01_headway_min], start=1):
        v_id = f"R01-T{i}"
        depart = start0 + timedelta(minutes=offset)
        schedule = make_vehicle_schedule(depart, r01_stops, r01_segments)
        r01_vehicles[v_id] = {
            "delayMinutes": 0,
            "currentStopIndex": 0,
            "schedule": schedule
        }

    return {
        "B154": b154_vehicles,
        "R01": r01_vehicles
    }

# --- Main seeding -------------------------------------------------------------

def run_seed():
    init_firebase()  # initialize Admin SDK / RTDB

    now_local = datetime.now(LKT)

    # 1) Static metadata
    routes = build_routes()
    rtdb_ref("/routes").set(routes)

    stops_geo = build_stops_geo()
    rtdb_ref("/stopsGeo").set(stops_geo)

    # 2) Rolling vehicle schedules from next 5-minute mark
    vehicles = build_vehicles(now_local)
    rtdb_ref("/vehicles").set(vehicles)

    # 3) Reset reports bucket (optional)
    rtdb_ref("/reports").set({"B154": {}, "R01": {}})

    print("Seed complete.",
          f"Local time (Asia/Colombo): {now_local.strftime('%Y-%m-%d %H:%M:%S')}",
          sep="\n")

if __name__ == "__main__":
    run_seed()
