# transport/seed_firebase.py

import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime, timedelta, timezone
from firebase_init import init_firebase, rtdb_ref

def epoch(dt): 
    return int(dt.timestamp())

def run_seed():
    init_firebase()  # ensure Firebase is initialized

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    routes = {
        "B154": {
            "routeName": "Colombo - Mount Lavinia",
            "stops": ["Fort","Slave Island","Bambalapitiya","Wellawatte","Dehiwala","Mount Lavinia"]
        },
        "R01":  {
            "routeName": "Colombo - Ragama (Suburban)",
            "stops": ["Fort","Maradana","Dematagoda","Kelaniya","Ragama"]
        }
    }
    rtdb_ref("/routes").set(routes)

    vehicles = {
      "B154": {
        "B154-V1": {
          "delayMinutes": 0, "currentStopIndex": 0,
          "schedule": [
            {"stop":"Fort","timeEpoch":epoch(now + timedelta(minutes=5))},
            {"stop":"Slave Island","timeEpoch":epoch(now + timedelta(minutes=10))},
            {"stop":"Bambalapitiya","timeEpoch":epoch(now + timedelta(minutes=20))},
            {"stop":"Wellawatte","timeEpoch":epoch(now + timedelta(minutes=28))},
            {"stop":"Dehiwala","timeEpoch":epoch(now + timedelta(minutes=36))},
            {"stop":"Mount Lavinia","timeEpoch":epoch(now + timedelta(minutes=45))}
          ]
        },
        "B154-V2": {
          "delayMinutes": 0, "currentStopIndex": 0,
          "schedule": [
            {"stop":"Fort","timeEpoch":epoch(now + timedelta(minutes=12))},
            {"stop":"Slave Island","timeEpoch":epoch(now + timedelta(minutes=17))},
            {"stop":"Bambalapitiya","timeEpoch":epoch(now + timedelta(minutes=27))},
            {"stop":"Wellawatte","timeEpoch":epoch(now + timedelta(minutes=35))},
            {"stop":"Dehiwala","timeEpoch":epoch(now + timedelta(minutes=43))},
            {"stop":"Mount Lavinia","timeEpoch":epoch(now + timedelta(minutes=52))}
          ]
        }
      },
      "R01": {
        "R01-T1": {
          "delayMinutes": 0, "currentStopIndex": 0,
          "schedule": [
            {"stop":"Fort","timeEpoch":epoch(now + timedelta(minutes=7))},
            {"stop":"Maradana","timeEpoch":epoch(now + timedelta(minutes=12))},
            {"stop":"Dematagoda","timeEpoch":epoch(now + timedelta(minutes=18))},
            {"stop":"Kelaniya","timeEpoch":epoch(now + timedelta(minutes=28))},
            {"stop":"Ragama","timeEpoch":epoch(now + timedelta(minutes=40))}
          ]
        }
      }
    }
    rtdb_ref("/vehicles").set(vehicles)

    # optional: seed stop geos for the map (if you're using the map feature)
    stops_geo = {
        "Fort":       {"lat": 6.9339, "lng": 79.8500},
        "Slave Island": {"lat": 6.9176, "lng": 79.8489},
        "Bambalapitiya":{"lat": 6.8916, "lng": 79.8568},
        "Wellawatte": {"lat": 6.8747, "lng": 79.8617},
        "Dehiwala":   {"lat": 6.8437, "lng": 79.8678},
        "Mount Lavinia":{"lat": 6.8390, "lng": 79.8653},
        "Maradana":   {"lat": 6.9273, "lng": 79.8657},
        "Dematagoda": {"lat": 6.9396, "lng": 79.8777},
        "Kelaniya":   {"lat": 6.9550, "lng": 79.8985},
        "Ragama":     {"lat": 7.0279, "lng": 79.9173},
    }
    rtdb_ref("/stopsGeo").set(stops_geo)

    # optional: reset reports
    rtdb_ref("/reports").set({"B154": {}, "R01": {}})

    print("Seed complete.")

if __name__ == "__main__":
    run_seed()