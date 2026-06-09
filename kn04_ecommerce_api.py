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
