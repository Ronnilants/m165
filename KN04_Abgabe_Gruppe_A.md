# KN04 – Prometheus Monitoring: Szenario A – E-Commerce Checkout API

---

## Implementierung: Das vollständige Script

```python
import time
import random
# --- AUFGABE 1: IMPORTIEREN ---
from prometheus_client import start_http_server, Counter

# --- AUFGABE 2: METRIK ERSTELLEN ---
sales_metric = Counter('ecommerce_sales_total', 'Anzahl der Verkaeufe', ['kategorie', 'status'])

def process_checkout():
    categories = ['Elektronik', 'Kleidung', 'Buecher']
    category = random.choice(categories)

    # 80% Erfolgsquote
    if random.random() > 0.2:
        status = 'success'
        print(f"[API] Erfolgreicher Kauf in {category}")
    else:
        status = 'error_payment_declined'
        print(f"[API] KREDITKARTENFEHLER in {category}")

    # --- AUFGABE 3: METRIK ERHÖHEN ---
    sales_metric.labels(kategorie=category, status=status).inc()

if __name__ == '__main__':
    print("Starte E-Commerce API Simulation...")
    # --- AUFGABE 4: METRIK-SERVER AUF PORT 8000 STARTEN ---
    start_http_server(8000)
    print("Prometheus Metrik-Server läuft auf http://localhost:8000")

    # Endlosschleife zur Simulation von Traffic
    while True:
        process_checkout()
        time.sleep(random.uniform(0.5, 2.0))
```

---

## Erklärung

**Aufgabe 1 – Import:**
`from prometheus_client import start_http_server, Counter` lädt die zwei benötigten Komponenten: `Counter` für die Metrik und `start_http_server` um den HTTP-Endpunkt zu starten, den Prometheus später scrapt.

**Aufgabe 2 – Counter erstellen:**
```python
sales_metric = Counter('ecommerce_sales_total', 'Anzahl der Verkaeufe', ['kategorie', 'status'])
```
Ein Counter ist eine Metrik, die nur steigen kann (nie sinken). Die Labels `['kategorie', 'status']` erlauben es, die Counts nach Produktkategorie (Elektronik, Kleidung, Buecher) und Status (success, error_payment_declined) zu filtern und gruppieren.

**Aufgabe 3 – Metrik erhöhen:**
```python
sales_metric.labels(kategorie=category, status=status).inc()
```
`.labels(...)` wählt die spezifische Label-Kombination, `.inc()` erhöht den Counter um 1.

**Aufgabe 4 – Server starten:**
```python
start_http_server(8000)
```
Startet einen HTTP-Server auf Port 8000. Unter `http://localhost:8000/metrics` kann Prometheus die Metriken im Text-Format abrufen (scrapen).

---

## Beweis: Terminal-Output (Script läuft)

```
Starte E-Commerce API Simulation...
Prometheus Metrik-Server laeuft auf http://localhost:8000
[API] KREDITKARTENFEHLER in Buecher
[API] Erfolgreicher Kauf in Buecher
[API] Erfolgreicher Kauf in Buecher
[API] KREDITKARTENFEHLER in Kleidung
[API] Erfolgreicher Kauf in Elektronik
[API] Erfolgreicher Kauf in Buecher
[API] Erfolgreicher Kauf in Kleidung
[API] Erfolgreicher Kauf in Kleidung
[API] KREDITKARTENFEHLER in Kleidung
[API] Erfolgreicher Kauf in Kleidung
```

---

## Beweis: Prometheus Metriken unter `http://localhost:8000/metrics`

```
# HELP ecommerce_sales_total Anzahl der Verkaeufe
# TYPE ecommerce_sales_total counter
ecommerce_sales_total{kategorie="Buecher",status="error_payment_declined"} 4.0
ecommerce_sales_total{kategorie="Buecher",status="success"} 12.0
ecommerce_sales_total{kategorie="Kleidung",status="error_payment_declined"} 5.0
ecommerce_sales_total{kategorie="Elektronik",status="success"} 7.0
ecommerce_sales_total{kategorie="Kleidung",status="success"} 11.0
ecommerce_sales_total{kategorie="Elektronik",status="error_payment_declined"} 2.0
```

Alle 6 Label-Kombinationen (3 Kategorien × 2 Status) werden korrekt gezählt und sind unter dem Metrik-Endpunkt abrufbar.

---

## Zusammenfassung

| Aufgabe | Umsetzung |
|---|---|
| Import | `from prometheus_client import start_http_server, Counter` |
| Counter mit Labels | `Counter('ecommerce_sales_total', '...', ['kategorie', 'status'])` |
| Metrik erhöhen | `.labels(kategorie=category, status=status).inc()` |
| HTTP-Server | `start_http_server(8000)` → Metriken auf Port 8000 |
