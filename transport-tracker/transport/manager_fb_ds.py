from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional, Dict
from firebase_init import init_firebase, rtdb_ref
from .data_structs import Queue, MinHeap, HashMap, Stack

init_firebase()

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _fmt_hhmm(dt: datetime) -> str:
    return dt.astimezone().strftime("%H:%M")

def _norm_route(r: str) -> str:
    return (r or "").strip().upper()

def _norm_stop(s: str) -> str:
    return (s or "").strip().lower()

class TransportManagerFB:
    def __init__(self):
        self.routes = HashMap()           # rid -> {routeName, stops[]}
        self.vehicles = HashMap()         # rid -> {vid -> vehicle}
        self.stop_heaps = HashMap()       # norm_stop -> MinHeap[(eta_dt, rid, vid)]
        self.recent_searches = Stack(maxlen=20)
        self.route_alias: Dict[str, str] = {}
        self.stop_alias: Dict[str, Dict[str, str]] = {}  # rid -> {norm: Canonical}

    # ---------- Cache refresh from Firebase ----------
    def refresh_from_db(self):
        # routes
        routes = rtdb_ref("/routes").get() or {}
        self.routes = HashMap()
        self.route_alias = {}
        self.stop_alias = {}
        for rid, r in routes.items():
            self.routes.set(rid, r)
            self.route_alias[rid.lower()] = rid
            self.route_alias[rid.upper()] = rid
            stops = (r or {}).get("stops", []) or []
            self.stop_alias[rid] = {_norm_stop(s): s for s in stops}

        # vehicles
        vehicles_tree = rtdb_ref("/vehicles").get() or {}
        self.vehicles = HashMap()
        for rid, vdict in (vehicles_tree or {}).items():
            inner = HashMap()
            for vid, v in (vdict or {}).items():
                inner.set(vid, v)
            self.vehicles.set(rid, inner)

        # min-heaps per stop for fastest lookup
        self.stop_heaps = HashMap()
        now = _now_utc()
        for rid in self.routes.keys():
            vmap: HashMap = self.vehicles.get(rid, HashMap())
            for vid, v in vmap.items():
                delay = int(v.get("delayMinutes", 0))
                idx = int(v.get("currentStopIndex", 0))
                for i, item in enumerate(v.get("schedule", [])):
                    stop = item.get("stop")
                    t = int(item.get("timeEpoch", 0))
                    if stop and i >= idx:
                        eta_dt = datetime.fromtimestamp(t, tz=timezone.utc) + timedelta(minutes=delay)
                        if eta_dt >= now:
                            key = _norm_stop(stop)
                            heap: MinHeap = self.stop_heaps.get(key)
                            if not heap:
                                heap = MinHeap()
                                self.stop_heaps.set(key, heap)
                            heap.push((eta_dt, rid, vid))

    # ---------- Helpers ----------
    def _resolve_route(self, route_id: str) -> Optional[str]:
        if not route_id:
            return None
        rid = self.route_alias.get(route_id.lower()) or self.route_alias.get(route_id.upper())
        return rid or (route_id if self.routes.get(route_id) else None)

    def _resolve_stop(self, route_id: str, stop_name: str) -> Optional[str]:
        if not route_id or not stop_name:
            return None
        rid = self._resolve_route(route_id)
        if not rid:
            return None
        alias_map = self.stop_alias.get(rid, {})
        return alias_map.get(_norm_stop(stop_name))

    def _resolve_stop_any(self, stop_name: str) -> Optional[str]:
        if not stop_name:
            return None
        ns = _norm_stop(stop_name)
        for _, amap in self.stop_alias.items():
            canon = amap.get(ns)
            if canon:
                return canon
        return None

    # ---------- Queries ----------
    def get_routes(self) -> Dict[str, dict]:
        out = {}
        for rid, r in self.routes.items():
            out[rid] = r
        return out

    def get_next_arrivals(self, route_id: str, stop_name: str, count: int = 3) -> List[Tuple[str, str]]:
        rid = self._resolve_route(route_id)
        canon_stop = self._resolve_stop(route_id, stop_name)
        self.recent_searches.push((route_id, stop_name))
        if not rid or not canon_stop:
            return []

        vmap: HashMap = self.vehicles.get(rid, HashMap())
        options = []
        now = _now_utc()
        for vid, v in vmap.items():
            delay = int(v.get("delayMinutes", 0))
            idx = int(v.get("currentStopIndex", 0))
            q = Queue()
            for i, item in enumerate(v.get("schedule", [])):
                if i >= idx:
                    q.push(item)
            while not q.empty():
                item = q.pop()
                if _norm_stop(item.get("stop")) == _norm_stop(canon_stop):
                    eta = datetime.fromtimestamp(int(item["timeEpoch"]), tz=timezone.utc) + timedelta(minutes=delay)
                    if eta >= now:
                        options.append((eta, vid))
                    break
        options.sort(key=lambda x: x[0])
        return [(_fmt_hhmm(dt), vid) for dt, vid in options[:count]]

    def get_next_arrival_epoch(self, route_id: str, stop_name: str) -> Optional[Tuple[int, str]]:
        rid = self._resolve_route(route_id)
        if not rid:
            return None
        canon_stop = self._resolve_stop(route_id, stop_name)
        if not canon_stop:
            return None

        vmap: HashMap = self.vehicles.get(rid, HashMap())
        now = int(datetime.now(timezone.utc).timestamp())
        best_t, best_vid = None, None

        for vid, v in vmap.items():
            delay_sec = int(v.get("delayMinutes", 0)) * 60
            cur_idx = int(v.get("currentStopIndex", 0))
            for idx, s in enumerate(v.get("schedule", [])):
                if idx < cur_idx:
                    continue
                if _norm_stop(s.get("stop", "")) != _norm_stop(canon_stop):
                    continue
                t = int(s.get("timeEpoch", 0)) + delay_sec
                if t >= now and (best_t is None or t < best_t):
                    best_t, best_vid = t, vid

        if best_t is None:
            return None
        return best_t, best_vid

    def get_earliest_arrival_at_stop(self, stop_name: str) -> Optional[Tuple[str, str, str]]:
        key = _norm_stop(stop_name)
        heap: MinHeap = self.stop_heaps.get(key)
        if not heap or heap.empty():
            return None
        eta_dt, rid, vid = heap.peek()
        return (_fmt_hhmm(eta_dt), rid, vid)

    def get_recent_searches(self):
        return list(self.recent_searches._data)

    # ---------- Mutations ----------
    def submit_report(self, route_id: str, vehicle_id: Optional[str], report_type: str,
                      severity: int, message: str, stop_name: Optional[str] = None) -> bool:
        import time as _time
        rid = self._resolve_route(route_id)
        if not rid:
            return False

        pref = rtdb_ref(f"/reports/{rid}").push()
        pref.set({
            "reportId": pref.key,
            "timestampEpoch": int(_time.time()),
            "routeId": rid,
            "vehicleId": vehicle_id,
            "type": report_type,
            "severity": int(severity),
            "message": message,
            "stop": self._resolve_stop(rid, stop_name) if stop_name else None
        })

        vref = rtdb_ref(f"/vehicles/{rid}")
        vdict = vref.get() or {}
        if not vdict:
            self.refresh_from_db()
            return True

        if vehicle_id and vehicle_id not in vdict:
            self.refresh_from_db()
            return False

        targets = [vehicle_id] if vehicle_id else list(vdict.keys())

        if report_type == "delay":
            add = min(5 * max(int(severity), 1), 50)
            for vid in targets:
                cur = int((vdict[vid] or {}).get("delayMinutes", 0))
                vref.child(vid).update({"delayMinutes": cur + add})
        elif report_type == "breakdown":
            for vid in targets:
                cur = int((vdict[vid] or {}).get("delayMinutes", 0))
                vref.child(vid).update({"delayMinutes": cur + 60})

        self.refresh_from_db()
        return True

    def record_departure(self, route_id: str, vehicle_id: str, stop_name: str) -> bool:
        rid = self._resolve_route(route_id)
        if not rid:
            return False
        vref = rtdb_ref(f"/vehicles/{rid}/{vehicle_id}")
        v = vref.get()
        if not v:
            return False
        idx = int(v.get("currentStopIndex", 0))
        sched = v.get("schedule", [])

        target_norm = _norm_stop(stop_name)
        if 0 <= idx < len(sched):
            cur_norm = _norm_stop(sched[idx].get("stop"))
            if cur_norm == target_norm:
                vref.update({"currentStopIndex": idx + 1})
                self.refresh_from_db()
                return True
            if idx + 1 < len(sched) and _norm_stop(sched[idx + 1].get("stop")) == target_norm:
                vref.update({"currentStopIndex": idx + 2})
                self.refresh_from_db()
                return True

        if idx < len(sched):
            vref.update({"currentStopIndex": min(idx + 1, len(sched))})
            self.refresh_from_db()
            return True
        return False

    def get_recent_reports(self, route_id: str, limit: int = 100):
        """Return recent report dicts, defensively handling bad shapes."""
        rid = self._resolve_route(route_id)
        if not rid:
            return []
        data = rtdb_ref(f"/reports/{rid}").get() or {}
        items = []
        if isinstance(data, dict):
            items = [v for v in data.values() if isinstance(v, dict)]
        elif isinstance(data, list):
            items = [v for v in data if isinstance(v, dict)]
        # else: leave empty

        items.sort(key=lambda x: int(x.get("timestampEpoch", 0)), reverse=True)
        try:
            lim = max(0, int(limit or 0))
        except Exception:
            lim = 100
        return items[:lim]

    # (Kept for compatibility; UI no longer calls this)
    def get_stop_geo(self, stop_name: str):
        canon = self._resolve_stop_any(stop_name) or stop_name
        data = rtdb_ref(f"/stopsGeo/{canon}").get()
        if not data:
            data = rtdb_ref("/stopsGeo").get() or {}
            data = data.get(canon) or data.get(stop_name) or data.get(stop_name.strip().title())
        return data
    
