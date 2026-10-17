"""Autonomous Research Scheduler: Manages recurring research cycles, execution intervals, and recovery."""
from __future__ import annotations
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.agent.controller import AgentController
from backend.app.core.config import settings

class ResearchScheduler:
    def __init__(self, controller: AgentController):
        self.controller = controller
        self.interval_seconds = settings.RESEARCH_INTERVAL_SECONDS
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.cycle_count = 0
        self.last_run_time: Optional[datetime] = None

    def start(self, interval_seconds: Optional[int] = None):
        if self.is_running:
            return
        if interval_seconds:
            self.interval_seconds = max(10, interval_seconds)
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                # Check if there is an active objective with pending tasks
                res = self.controller.run_next_task()
                if res:
                    self.cycle_count += 1
                    self.last_run_time = datetime.now(timezone.utc)
            except Exception as e:
                # Log and wait before retrying to prevent rapid error loops
                time.sleep(2)
                
            # Sleep in 1-second chunks to respond immediately to stop_event
            for _ in range(self.interval_seconds):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "cycle_count": self.cycle_count,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "active_objective_id": self.controller.active_objective_id,
            "paused": self.controller.is_research_paused
        }
