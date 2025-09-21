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

def make_vehicle_schedule(start_time_local: datetime, stops: list[str], segment_minutes: list[int], cycles: int = 3):
    """
    Build a stop-by-stop schedule for multiple round trips.
    cycles: number of complete round trips to generate
    """
    assert len(segment_minutes) == len(stops) - 1, "segment_minutes must be one less than stops"
    
    schedule = []
    current_time = start_time_local
    
    for cycle in range(cycles):
        # Forward journey
        times_forward = [current_time]
        for seg in segment_minutes:
            current_time = current_time + timedelta(minutes=seg)
            times_forward.append(current_time)
        
        # Add forward stops to schedule
        for stop, time in zip(stops, times_forward):
            schedule.append({"stop": stop, "timeEpoch": epoch(time.astimezone(timezone.utc))})
        
        # Return journey (reverse order, same segments)
        if cycle < cycles - 1:  # Don't do return journey on last cycle
            return_segments = segment_minutes[::-1]  # reverse the segments
            return_stops = stops[::-1][1:]  # reverse stops, skip first (already added)
            
            for i, (stop, seg) in enumerate(zip(return_stops, return_segments)):
                current_time = current_time + timedelta(minutes=seg)
                schedule.append({"stop": stop, "timeEpoch": epoch(current_time.astimezone(timezone.utc))})
            
            # Add turnaround time at terminus
            current_time = current_time + timedelta(minutes=5)
    
    return schedule

# --- Enhanced Seed Data Builders -----------------------------------------------

def build_routes():
    return {
        # Bus Routes
        "B154": {
            "routeName": "Colombo - Mount Lavinia (Bus)",
            "stops": ["Fort", "Slave Island", "Bambalapitiya", "Wellawatte", "Dehiwala", "Mount Lavinia"]
        },
        "B138": {
            "routeName": "Pettah - Nugegoda (Bus)", 
            "stops": ["Pettah", "Fort", "Kollupitiya", "Bambalapitiya", "Havelock Town", "Nugegoda"]
        },
        "B177": {
            "routeName": "Kaduwela - Fort (Bus)",
            "stops": ["Kaduwela", "Malabe", "Kottawa", "Maharagama", "Dehiwala", "Bambalapitiya", "Fort"]
        },
        "B103": {
            "routeName": "Kelaniya - Pettah (Bus)",
            "stops": ["Kelaniya", "Peliyagoda", "Dematagoda", "Maradana", "Pettah"]
        },
        "B201": {
            "routeName": "Gampaha - Fort (Bus)",
            "stops": ["Gampaha", "Ragama", "Kelaniya", "Dematagoda", "Maradana", "Fort"]
        },
        
        # Train Routes
        "T01": {
            "routeName": "Colombo - Ragama (Suburban Train)",
            "stops": ["Fort", "Maradana", "Dematagoda", "Kelaniya", "Ragama"]
        },
        "T02": {
            "routeName": "Colombo - Panadura (Coastal Line)",
            "stops": ["Fort", "Slave Island", "Kollupitiya", "Bambalapitiya", "Wellawatte", "Dehiwala", "Mount Lavinia", "Ratmalana", "Panadura"]
        },
        "T03": {
            "routeName": "Colombo - Avissawella (Kelani Valley Line)", 
            "stops": ["Maradana", "Dematagoda", "Kelaniya", "Waga", "Gampaha", "Avissawella"]
        },
        "T04": {
            "routeName": "Colombo - Kandy (Main Line)",
            "stops": ["Fort", "Ragama", "Gampaha", "Veyangoda", "Kandy"]
        },
        
        # Express Services
        "E101": {
            "routeName": "Airport Express Bus",
            "stops": ["Fort", "Gampaha", "Negombo", "Airport"]
        },
        "E201": {
            "routeName": "Kandy Express Train",
            "stops": ["Fort", "Ragama", "Gampaha", "Veyangoda", "Kandy"]
        },
        
        # Staff Service Vans
        "S001": {
            "routeName": "Hospital Staff Shuttle",
            "stops": ["Fort", "Slave Island", "Kollupitiya", "General Hospital", "Medical Faculty"]
        },
        "S002": {
            "routeName": "University Staff Transport", 
            "stops": ["Nugegoda", "University of Colombo", "Medical Faculty", "Fort"]
        },
        "S003": {
            "routeName": "Port Authority Staff Van",
            "stops": ["Fort", "Port Authority", "Cargo Terminal", "Naval Base"]
        }
    }

def build_stops_geo():
    return {
        # Central Colombo
        "Fort":          {"lat": 6.9339, "lng": 79.8500},
        "Pettah":        {"lat": 6.9344, "lng": 79.8428},
        "Maradana":      {"lat": 6.9273, "lng": 79.8657},
        "Slave Island":  {"lat": 6.9176, "lng": 79.8489},
        "Kollupitiya":   {"lat": 6.9147, "lng": 79.8560},
        
        # Southern Coastal
        "Bambalapitiya": {"lat": 6.8916, "lng": 79.8568},
        "Havelock Town": {"lat": 6.8889, "lng": 79.8792},
        "Wellawatte":    {"lat": 6.8747, "lng": 79.8617},
        "Dehiwala":      {"lat": 6.8437, "lng": 79.8678},
        "Mount Lavinia": {"lat": 6.8390, "lng": 79.8653},
        "Ratmalana":     {"lat": 6.8205, "lng": 79.8836},
        "Panadura":      {"lat": 6.7132, "lng": 79.9074},
        
        # Northern/Eastern
        "Dematagoda":    {"lat": 6.9396, "lng": 79.8777},
        "Peliyagoda":    {"lat": 6.9579, "lng": 79.8889},
        "Kelaniya":      {"lat": 6.9550, "lng": 79.8985},
        "Ragama":        {"lat": 7.0279, "lng": 79.9173},
        "Gampaha":       {"lat": 7.0914, "lng": 79.9999},
        "Veyangoda":     {"lat": 7.1590, "lng": 80.0789},
        
        # Inland/Suburban  
        "Nugegoda":      {"lat": 6.8649, "lng": 79.8977},
        "Maharagama":    {"lat": 6.8482, "lng": 79.9278},
        "Kottawa":       {"lat": 6.8291, "lng": 79.9633},
        "Malabe":        {"lat": 6.9333, "lng": 79.9667},
        "Kaduwela":      {"lat": 6.9333, "lng": 79.9833},
        "Waga":          {"lat": 7.0500, "lng": 80.1000},
        "Avissawella":   {"lat": 6.9519, "lng": 80.2108},
        "Negombo":       {"lat": 7.2084, "lng": 79.8358},
        "Airport":       {"lat": 7.1667, "lng": 79.8833},
        "Kandy":         {"lat": 7.2906, "lng": 80.6337},
        
        # Institutional/Special locations
        "General Hospital": {"lat": 6.9271, "lng": 79.8612},
        "Medical Faculty": {"lat": 6.9275, "lng": 79.8622},
        "University of Colombo": {"lat": 6.9022, "lng": 79.8607},
        "Port Authority": {"lat": 6.9403, "lng": 79.8448},
        "Cargo Terminal": {"lat": 6.9420, "lng": 79.8435},
        "Naval Base": {"lat": 6.9375, "lng": 79.8465}
    }

def build_vehicles(now_local: datetime):
    """Create realistic vehicle schedules with multiple services per route."""
    start_base = round_up_to_next_5(now_local)
    all_vehicles = {}

    # Bus B154: Colombo - Mount Lavinia (every 8-12 minutes, 6 buses)
    b154_stops = ["Fort", "Slave Island", "Bambalapitiya", "Wellawatte", "Dehiwala", "Mount Lavinia"]
    b154_segments = [6, 8, 8, 8, 9]  # Heavy traffic corridor
    b154_vehicles = {}
    for i in range(6):
        v_id = f"B154-{i+1:02d}"
        offset_min = i * 8 + random.randint(-2, 2)  # Slight randomness
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, b154_stops, b154_segments, cycles=2)
        b154_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 5),  # Some initial delays
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["B154"] = b154_vehicles

    # Bus B138: Pettah - Nugegoda (every 10 minutes, 4 buses)
    b138_stops = ["Pettah", "Fort", "Kollupitiya", "Bambalapitiya", "Havelock Town", "Nugegoda"]
    b138_segments = [5, 6, 7, 9, 12]
    b138_vehicles = {}
    for i in range(4):
        v_id = f"B138-{i+1:02d}"
        offset_min = i * 10
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, b138_stops, b138_segments, cycles=2)
        b138_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 8),
            "currentStopIndex": random.randint(0, 2),  # Some vehicles already en-route
            "schedule": schedule
        }
    all_vehicles["B138"] = b138_vehicles

    # Bus B177: Kaduwela - Fort (every 15 minutes, 3 buses)
    b177_stops = ["Kaduwela", "Malabe", "Kottawa", "Maharagama", "Dehiwala", "Bambalapitiya", "Fort"]
    b177_segments = [15, 20, 12, 10, 8, 8]
    b177_vehicles = {}
    for i in range(3):
        v_id = f"B177-{i+1:02d}"
        offset_min = i * 15
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, b177_stops, b177_segments, cycles=1)
        b177_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 15),  # Long route, more delays
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["B177"] = b177_vehicles

    # Bus B103: Kelaniya - Pettah (every 12 minutes, 3 buses)
    b103_stops = ["Kelaniya", "Peliyagoda", "Dematagoda", "Maradana", "Pettah"]
    b103_segments = [8, 10, 7, 5]
    b103_vehicles = {}
    for i in range(3):
        v_id = f"B103-{i+1:02d}"
        offset_min = i * 12
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, b103_stops, b103_segments, cycles=2)
        b103_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 6),
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["B103"] = b103_vehicles

    # Bus B201: Gampaha - Fort (every 18 minutes, 3 buses)
    b201_stops = ["Gampaha", "Ragama", "Kelaniya", "Dematagoda", "Maradana", "Fort"]
    b201_segments = [12, 15, 10, 7, 5]
    b201_vehicles = {}
    for i in range(3):
        v_id = f"B201-{i+1:02d}"
        offset_min = i * 18
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, b201_stops, b201_segments, cycles=2)
        b201_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 8),
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["B201"] = b201_vehicles

    # Train T01: Suburban (every 20 minutes, 3 trains)
    t01_stops = ["Fort", "Maradana", "Dematagoda", "Kelaniya", "Ragama"]
    t01_segments = [5, 6, 10, 13]
    t01_vehicles = {}
    for i in range(3):
        v_id = f"T01-{i+1:02d}"
        offset_min = i * 20
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, t01_stops, t01_segments, cycles=2)
        t01_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 3),  # Trains usually more punctual
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["T01"] = t01_vehicles

    # Train T02: Coastal Line (every 30 minutes, 2 trains)
    t02_stops = ["Fort", "Slave Island", "Kollupitiya", "Bambalapitiya", "Wellawatte", "Dehiwala", "Mount Lavinia", "Ratmalana", "Panadura"]
    t02_segments = [3, 4, 5, 6, 7, 8, 10, 25]
    t02_vehicles = {}
    for i in range(2):
        v_id = f"T02-{i+1:02d}"
        offset_min = i * 30
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, t02_stops, t02_segments, cycles=1)
        t02_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 10),
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["T02"] = t02_vehicles

    # Train T03: Kelani Valley Line (every 40 minutes, 2 trains)  
    t03_stops = ["Maradana", "Dematagoda", "Kelaniya", "Waga", "Gampaha", "Avissawella"]
    t03_segments = [6, 10, 20, 15, 35]
    t03_vehicles = {}
    for i in range(2):
        v_id = f"T03-{i+1:02d}"
        offset_min = i * 40
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, t03_stops, t03_segments, cycles=1)
        t03_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 8),
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["T03"] = t03_vehicles

    # Train T04: Main Line to Kandy (every 60 minutes, 2 trains)
    t04_stops = ["Fort", "Ragama", "Gampaha", "Veyangoda", "Kandy"]
    t04_segments = [25, 15, 20, 90]  # Long distance to Kandy
    t04_vehicles = {}
    for i in range(2):
        v_id = f"T04-{i+1:02d}"
        offset_min = i * 60
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, t04_stops, t04_segments, cycles=1)
        t04_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 15),  # Long distance, more delays possible
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["T04"] = t04_vehicles

    # Express E101: Airport Bus (every 45 minutes, 2 buses)
    e101_stops = ["Fort", "Gampaha", "Negombo", "Airport"]
    e101_segments = [35, 25, 15]
    e101_vehicles = {}
    for i in range(2):
        v_id = f"E101-{i+1:02d}"
        offset_min = i * 45
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, e101_stops, e101_segments, cycles=1)
        e101_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 20),  # Highway traffic varies
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["E101"] = e101_vehicles

    # Express E201: Kandy Express Train (every 90 minutes, 2 trains)
    e201_stops = ["Fort", "Ragama", "Gampaha", "Veyangoda", "Kandy"]
    e201_segments = [25, 15, 20, 90]  # Express timing - fewer stops
    e201_vehicles = {}
    for i in range(2):
        v_id = f"E201-{i+1:02d}"
        offset_min = i * 90
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, e201_stops, e201_segments, cycles=1)
        e201_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 10),
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["E201"] = e201_vehicles

    # Staff Van S001: Hospital Shuttle (every 30 minutes during work hours, 2 vans)
    s001_stops = ["Fort", "Slave Island", "Kollupitiya", "General Hospital", "Medical Faculty"]
    s001_segments = [5, 4, 3, 8]
    s001_vehicles = {}
    for i in range(2):
        v_id = f"S001-{i+1:02d}"
        offset_min = i * 30
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, s001_stops, s001_segments, cycles=3)  # Multiple trips
        s001_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 5),  # Staff service, usually punctual
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["S001"] = s001_vehicles

    # Staff Van S002: University Shuttle (every 25 minutes, 2 vans)
    s002_stops = ["Nugegoda", "University of Colombo", "Medical Faculty", "Fort"]
    s002_segments = [15, 8, 10]
    s002_vehicles = {}
    for i in range(2):
        v_id = f"S002-{i+1:02d}"
        offset_min = i * 25
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, s002_stops, s002_segments, cycles=2)
        s002_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 3),
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["S002"] = s002_vehicles

    # Staff Van S003: Port Authority (every 20 minutes, 3 vans)
    s003_stops = ["Fort", "Port Authority", "Cargo Terminal", "Naval Base"]
    s003_segments = [8, 5, 7]
    s003_vehicles = {}
    for i in range(3):
        v_id = f"S003-{i+1:02d}"
        offset_min = i * 20
        start_time = start_base + timedelta(minutes=offset_min)
        schedule = make_vehicle_schedule(start_time, s003_stops, s003_segments, cycles=3)
        s003_vehicles[v_id] = {
            "delayMinutes": random.randint(0, 8),  # Port traffic can be heavy
            "currentStopIndex": 0,
            "schedule": schedule
        }
    all_vehicles["S003"] = s003_vehicles

    return all_vehicles

def add_realistic_incidents():
    """Add some sample incident reports to make the system look active."""
    import time
    now_epoch = int(time.time())
    
    incidents = {
        "B154": {
            "inc1": {
                "reportId": "inc1",
                "timestampEpoch": now_epoch - 1800,  # 30 min ago
                "routeId": "B154",
                "vehicleId": "B154-03", 
                "type": "delay",
                "severity": 4,
                "message": "Heavy traffic near Bambalapitiya junction",
                "stop": "Bambalapitiya"
            },
            "inc2": {
                "reportId": "inc2", 
                "timestampEpoch": now_epoch - 900,   # 15 min ago
                "routeId": "B154",
                "vehicleId": None,
                "type": "crowding", 
                "severity": 6,
                "message": "Rush hour congestion",
                "stop": None
            }
        },
        "T01": {
            "inc3": {
                "reportId": "inc3",
                "timestampEpoch": now_epoch - 600,   # 10 min ago
                "routeId": "T01", 
                "vehicleId": "T01-02",
                "type": "delay",
                "severity": 3,
                "message": "Signal delay at Dematagoda",
                "stop": "Dematagoda"
            }
        }
    }
    return incidents

# --- Main seeding -------------------------------------------------------------

def run_seed():
    init_firebase()
    now_local = datetime.now(LKT)

    print(f"Seeding data for local time: {now_local.strftime('%Y-%m-%d %H:%M:%S')} LKT")

    # 1) Routes and stops
    routes = build_routes()
    rtdb_ref("/routes").set(routes)
    print(f"✓ Added {len(routes)} routes")

    stops_geo = build_stops_geo()  
    rtdb_ref("/stopsGeo").set(stops_geo)
    print(f"✓ Added {len(stops_geo)} stops with coordinates")

    # 2) Vehicle schedules (this is the time-sensitive part)
    vehicles = build_vehicles(now_local)
    rtdb_ref("/vehicles").set(vehicles)
    total_vehicles = sum(len(route_vehicles) for route_vehicles in vehicles.values())
    print(f"✓ Added {total_vehicles} vehicles across {len(vehicles)} routes")

    # 3) Sample incidents
    incidents = add_realistic_incidents()
    rtdb_ref("/reports").set(incidents)
    total_incidents = sum(len(route_incidents) for route_incidents in incidents.values())
    print(f"✓ Added {total_incidents} sample incident reports")

    print("Seed complete! Data is valid from now until vehicles complete their schedules.")
    print("Tip: Schedules include multiple round trips, so data stays fresh longer.")
    print("Re-run this script when schedules get stale (typically after a few hours).")

if __name__ == "__main__":
    run_seed()