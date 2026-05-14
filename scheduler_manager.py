import schedule
import threading
import time
import logging
import pytz
from datetime import datetime
from bot import ExnovaBot

logger = logging.getLogger(__name__)

class SchedulerManager:
    def __init__(self):
        self.bot = None
        self.mode = "test"
        self._running = False
        self._thread = None
        self.execution_log = []
        self.executed_count = 0

    def is_running(self):
        return self._running

    def start(self, mode="test"):
        self.mode = mode
        if not self._running:
            self.bot = ExnovaBot(test_mode=(mode == "test"))
            self.bot.start_driver()
            self.bot.login()
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            logger.info(f"✅ Bot iniciado em modo: {mode.upper()}")

    def stop(self):
        self._running = False
        schedule.clear()
        if self.bot:
            self.bot.close()
        logger.info("🔒 Bot encerrado.")

    def _loop(self):
        while self._running:
            schedule.run_pending()
            time.sleep(1)

    def register_signal(self, signal: dict):
        s = signal.copy()
        schedule.every().day.at(s["time"]).do(self._fire, signal=s)

    def reload_signals(self, signals: list):
        schedule.clear()
        for s in signals:
            self.register_signal(s)

    def clear_all(self):
        schedule.clear()

    def _fire(self, signal: dict):
        tz = pytz.timezone("America/Sao_Paulo")
        now = datetime.now(tz).strftime("%H:%M:%S")
        result = {
            "time": now,
            "pair": signal["pair"],
            "direction": signal["direction"],
            "expiration": signal["expiration"],
            "amount": signal["amount"],
            "mode": self.mode,
            "success": False,
        }
        if self.bot:
            ok = self.bot.execute_signal(signal)
            result["success"] = ok
            if ok:
                self.executed_count += 1

        self.execution_log.insert(0, result)
        self.execution_log = self.execution_log[:50]  # mantém últimos 50

    def next_signal_info(self):
        jobs = schedule.get_jobs()
        if not jobs:
            return None
        next_job = min(jobs, key=lambda j: j.next_run)
        return str(next_job.next_run)