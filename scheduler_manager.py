import schedule
import threading
import time
import logging
import pytz
from datetime import datetime
from bot import ExnovaBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class SchedulerManager:
    def __init__(self):
        self.bot            = None
        self.mode           = "test"
        self._running       = False
        self._thread        = None
        self.execution_log  = []
        self.executed_count = 0

    def is_running(self):
        return self._running

    def start(self, mode="test"):
        if self._running:
            self.stop()
        self.mode     = mode
        self._running = True
        self._thread  = threading.Thread(
            target=self._run, args=(mode,), daemon=True
        )
        self._thread.start()
        logger.info(f"🔄 Iniciando bot em modo: {mode.upper()}...")

    def _run(self, mode):
        try:
            self.bot = ExnovaBot(test_mode=(mode == "test"))

            if not self.bot.start_driver():
                logger.error("❌ Falha ao iniciar browser.")
                self._running = False
                return

            if not self.bot.login():
                logger.error("❌ Falha no login.")
                self._running = False
                return

            logger.info(f"✅ Bot iniciado em modo: {mode.upper()}")

            while self._running:
                schedule.run_pending()
                time.sleep(1)

        except Exception as e:
            logger.error(f"❌ Erro fatal na thread do bot: {e}", exc_info=True)
            self._running = False

    def stop(self):
        self._running = False
        schedule.clear()
        if self.bot:
            self.bot.close()
        self.bot = None
        logger.info("🔒 Bot encerrado.")

    def register_signal(self, signal: dict):
        s = signal.copy()
        schedule.every().day.at(s["time"]).do(self._fire, signal=s)
        logger.info(f"📅 Sinal registrado: {s['pair']} às {s['time']}")

    def reload_signals(self, signals: list):
        schedule.clear()
        for s in signals:
            self.register_signal(s)

    def clear_all(self):
        schedule.clear()
        logger.info("🗑 Todos os sinais removidos.")

    def _fire(self, signal: dict):
        tz  = pytz.timezone("America/Sao_Paulo")
        now = datetime.now(tz).strftime("%H:%M:%S")
        mkt = "OTC" if signal.get("market") == "otc" else "Normal"

        result = {
            "time":       now,
            "pair":       signal["pair"],
            "direction":  signal["direction"],
            "expiration": signal["expiration"],
            "amount":     signal["amount"],
            "market":     mkt,
            "mode":       self.mode,
            "success":    False,
        }

        if self.bot:
            ok = self.bot.execute_signal(signal)
            result["success"] = ok
            if ok:
                self.executed_count += 1

        self.execution_log.insert(0, result)
        self.execution_log = self.execution_log[:50]

    def next_signal_info(self):
        jobs = schedule.get_jobs()
        if not jobs:
            return None
        nxt = min(jobs, key=lambda j: j.next_run)
        return str(nxt.next_run)