import time
import random
import redis
import json

# KONFIGURATION
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("Verbunden mit Redis")
except Exception as e:
    print(f"Konnte nicht mit Redis verbinden: {e}")
    r = None

def fetch_crypto_history(coin_symbol):
    """Simuliert eine API mit starkem Rate-Limit und langsamer Antwortzeit"""
    print(f"... Umgehe Rate-Limit und lade Blockchain-Historie für '{coin_symbol}' (bitte warten) ...")
    time.sleep(3.5) # Künstliche Verzögerung

    # Simulierte historische Daten
    history = {
        "symbol": coin_symbol,
        "current_price": random.uniform(20000, 60000),
        "24h_high": 61000,
        "24h_low": 19500,
        "trend": random.choice(["bullish", "bearish", "neutral"])
    }
    return json.dumps(history)

def get_crypto_data(coin_symbol):
    # --- CACHING-LOGIK ---
    # 1. Prüfen ob 'coin_symbol' als Key in Redis existiert
    cached = r.get(coin_symbol)

    # 2. Cache Hit: Wert direkt aus Redis zurückgeben
    if cached is not None:
        print(f"[CACHE HIT] Daten für '{coin_symbol}' aus Redis geladen.")
        return cached

    # 3. Cache Miss: API aufrufen, Ergebnis in Redis speichern (TTL = 30 Sekunden)
    print(f"[CACHE MISS] Kein Cache-Eintrag für '{coin_symbol}' – rufe API auf...")
    result = fetch_crypto_history(coin_symbol)
    r.setex(coin_symbol, 30, result)
    print(f"[CACHE SET] Daten für '{coin_symbol}' in Redis gespeichert (TTL: 30s).")
    return result

# TEST-ABLAUF
test_coin = "BTC"

print("\n--- Erster Aufruf (Cache Miss - sollte langsam sein) ---")
start = time.time()
print(f"Krypto-Daten: {get_crypto_data(test_coin)}")
print(f"Dauer: {time.time() - start:.4f} Sekunden")

print("\n--- Zweiter Aufruf (Cache Hit - sollte blitzschnell sein) ---")
start = time.time()
print(f"Krypto-Daten: {get_crypto_data(test_coin)}")
print(f"Dauer: {time.time() - start:.4f} Sekunden")
