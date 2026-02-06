import time
from datetime import datetime, timezone

def record_event(event_name, t0=None):

    mono = time.perf_counter()
    wall = datetime.now(timezone.utc)

    record = {
        "event": event_name,
        "mono_time": mono,
        "wall_time": wall.isoformat(),
    }

    if t0 is not None:
        record["delta_s"] = mono - t0

    return record

def merge_and_sort_events(list1, list2):
    combined = list1 + list2
    return sorted(combined, key=lambda e: e['mono_time'])

def log_events(eventList,startTime):
    for e in eventList:
        print(f"{e["event"]} : {e["mono_time"]-startTime}")