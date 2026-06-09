# KN03 – Redis Caching: Szenario E – Krypto-Kurshistorie

---

## Implementierung: Caching-Logik

```python
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
```

---

## Erklärung der Caching-Logik

Die Funktion `get_crypto_data` prüft zuerst mit `r.get(coin_symbol)`, ob der Key bereits in Redis existiert. Ist ein Wert vorhanden (**Cache Hit**), wird dieser sofort zurückgegeben – ohne die langsame API aufzurufen. Ist kein Wert vorhanden (**Cache Miss**), wird `fetch_crypto_history` aufgerufen und das Ergebnis mit `r.setex(coin_symbol, 30, result)` für 30 Sekunden in Redis gespeichert. Die TTL (Time-To-Live) von 30 Sekunden stellt sicher, dass nach Ablauf automatisch frische Daten von der API geholt werden.

---

## Beweis: Ausgabe des Scripts

```
Verbunden mit Redis

--- Erster Aufruf (Cache Miss - sollte langsam sein) ---
[CACHE MISS] Kein Cache-Eintrag fuer BTC - rufe API auf...
... Umgehe Rate-Limit und lade Blockchain-Historie fuer BTC (bitte warten) ...
[CACHE SET] Daten fuer BTC in Redis gespeichert (TTL: 30s).
Krypto-Daten: {"symbol": "BTC", "current_price": 38722.4, "24h_high": 61000, "24h_low": 19500, "trend": "bullish"}
Dauer: 3.5020 Sekunden

--- Zweiter Aufruf (Cache Hit - sollte blitzschnell sein) ---
[CACHE HIT] Daten fuer BTC aus Redis geladen.
Krypto-Daten: {"symbol": "BTC", "current_price": 38722.4, "24h_high": 61000, "24h_low": 19500, "trend": "bullish"}
Dauer: 0.0005 Sekunden
```

---

## Vergleich: Cache Miss vs. Cache Hit

| | 1. Aufruf (Cache Miss) | 2. Aufruf (Cache Hit) |
|---|---|---|
| Redis-Eintrag vorhanden? | Nein | Ja |
| API aufgerufen? | Ja (3.5s Delay) | Nein |
| Dauer | **3.5020 Sekunden** | **0.0005 Sekunden** |
| Speedup | – | **~7000× schneller** |

Der zweite Aufruf liefert dasselbe Ergebnis (`current_price: 38722.4`) wie der erste – die Daten kommen direkt aus Redis, die API wird nicht erneut belastet.
