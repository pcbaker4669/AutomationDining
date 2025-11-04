# logger.py
import csv, os, datetime
from typing import Dict, Any, List, Optional

class RunLogger:
    """
    CSV logger with a stable core schema + room to add fields later.
    Writes two CSVs per run: meals (per-customer visit) and events (shocks/notes).
    """

    CORE_MEAL_FIELDS = [
        "run_id", "row_type",  # 'meal'
        "sim_time_s", "sim_minutes",
        "customer_id",
        "wait_time_min",  # ← keep minutes only
        "price", "quality", "mode",
        "demand",  # wave multiplier at log time
        "n_servers",  # capacity at the time
        "money_cum",  # cumulative money collected
        "labor_cum",  # cumulative labor cost
        "fixed_cum",
        "profit"
    ]

    CORE_EVENT_FIELDS = [
        "run_id", "row_type",          # row_type = 'event'
        "sim_time_s", "sim_minutes",
        "event_type",                  # e.g., 'robot_breakdown', 'missed_shift'
        "severity", "duration_s", "note"
    ]

    def __init__(self, enabled: bool = True, log_dir: str = "logs"):
        self.enabled = enabled
        self.log_dir = log_dir
        self.run_id: Optional[str] = None
        self._meals_fp = None
        self._events_fp = None
        self._meals_writer = None
        self._events_writer = None

    def start_run(self, params: Dict[str, Any]):
        if not self.enabled:
            return
        os.makedirs(self.log_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{ts}"

        meals_path  = os.path.join(self.log_dir, f"{self.run_id}_meals.csv")
        events_path = os.path.join(self.log_dir, f"{self.run_id}_events.csv")

        self._meals_fp  = open(meals_path, "w", newline="", encoding="utf-8")
        self._events_fp = open(events_path, "w", newline="", encoding="utf-8")

        self._meals_writer  = csv.DictWriter(self._meals_fp,  fieldnames=self.CORE_MEAL_FIELDS)
        self._events_writer = csv.DictWriter(self._events_fp, fieldnames=self.CORE_EVENT_FIELDS)

        self._meals_writer.writeheader()
        self._events_writer.writeheader()

        # Log a header event with run params (for provenance)
        self.log_event(sim_time_s=0.0, event_type="run_start", severity="info",
                       duration_s=0.0, note=str(params))

    def log_meal(self, record: Dict[str, Any]):
        if not self.enabled or not self._meals_writer:
            return
        row = {k: record.get(k, "") for k in self.CORE_MEAL_FIELDS}
        row["row_type"] = "meal"
        row["run_id"] = self.run_id or ""
        self._meals_writer.writerow(row)

    def log_event(self, sim_time_s: float, event_type: str,
                  severity: str = "info", duration_s: float = 0.0, note: str = ""):
        if not self.enabled or not self._events_writer:
            return
        row = {
            "run_id": self.run_id or "",
            "row_type": "event",
            "sim_time_s": sim_time_s,
            "sim_minutes": sim_time_s / 60.0,
            "event_type": event_type,
            "severity": severity,
            "duration_s": duration_s,
            "note": note,
        }
        self._events_writer.writerow(row)

    def close(self):
        if self._meals_fp:
            self._meals_fp.close()
            self._meals_fp = None
        if self._events_fp:
            self._events_fp.close()
            self._events_fp = None
