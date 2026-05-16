import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "email":          os.getenv("EXNOVA_EMAIL", ""),
    "password":       os.getenv("EXNOVA_PASSWORD", ""),
    "base_url":       "https://exnova.com/pt/login",
    "trade_url":      "https://exnova.com/pt/trade",
    "default_amount": 10.0,
    "timezone":       "America/Sao_Paulo",
}