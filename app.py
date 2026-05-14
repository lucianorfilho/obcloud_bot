from flask import Flask, render_template, request, jsonify
from scheduler_manager import SchedulerManager
import json, os
from datetime import datetime

app = Flask(__name__)
scheduler = SchedulerManager()

SIGNALS_FILE = "signals_data.json"

def load_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, "r") as f:
            return json.load(f)
    return []

def save_signals(signals):
    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

# ── Página principal ──────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── API: listar sinais ────────────────────────────────────────
@app.route("/api/signals", methods=["GET"])
def get_signals():
    signals = load_signals()
    return jsonify(signals)

# ── API: adicionar sinal ──────────────────────────────────────
@app.route("/api/signals", methods=["POST"])
def add_signal():
    data = request.json
    required = ["time", "pair", "direction", "expiration", "amount"]
    if not all(k in data for k in required):
        return jsonify({"error": "Campos obrigatórios faltando"}), 400

    signals = load_signals()
    data["id"] = datetime.now().timestamp()
    data["status"] = "pending"
    signals.append(data)
    save_signals(signals)
    scheduler.register_signal(data)

    return jsonify({"success": True, "signal": data}), 201

# ── API: remover sinal ────────────────────────────────────────
@app.route("/api/signals/<float:signal_id>", methods=["DELETE"])
def delete_signal(signal_id):
    signals = load_signals()
    signals = [s for s in signals if s["id"] != signal_id]
    save_signals(signals)
    scheduler.reload_signals(signals)
    return jsonify({"success": True})

# ── API: limpar todos os sinais ───────────────────────────────
@app.route("/api/signals/clear", methods=["DELETE"])
def clear_signals():
    save_signals([])
    scheduler.clear_all()
    return jsonify({"success": True})

# ── API: status do bot ────────────────────────────────────────
@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "running": scheduler.is_running(),
        "mode": scheduler.mode,
        "next_signal": scheduler.next_signal_info(),
        "executed_today": scheduler.executed_count,
    })

# ── API: iniciar bot ──────────────────────────────────────────
@app.route("/api/bot/start", methods=["POST"])
def start_bot():
    data = request.json or {}
    mode = data.get("mode", "test")
    scheduler.start(mode=mode)
    return jsonify({"success": True, "mode": mode})

# ── API: parar bot ────────────────────────────────────────────
@app.route("/api/bot/stop", methods=["POST"])
def stop_bot():
    scheduler.stop()
    return jsonify({"success": True})

# ── API: log de execuções ─────────────────────────────────────
@app.route("/api/log", methods=["GET"])
def get_log():
    return jsonify(scheduler.execution_log)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)