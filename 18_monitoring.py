"""
LEKCE 18: Monitoring — Prometheus + Grafana
=============================================
Jak vís, ze tvoje aplikace funguje spravne?
Kolik CPU spotrebuje? Jak dlouho trvaji requesty?
Kdy databaze zacinaji byt pomale?

Na to je monitoring stack:
  Prometheus — sbira metriky (casove rady)
  Grafana    — vizualizuje metriky (grafy, dashboardy)
  Alertmanager — posila alertni (Slack, email, PagerDuty)

Naucis se:
  - nainstalovat kube-prometheus-stack pres Helm
  - co jsou metriky a jak je exponovat
  - napsat vlastni PromQL dotazy
  - nastavit alert

Obtiznost: ⭐⭐⭐⭐
"""

import subprocess
import textwrap


def helm_dostupny() -> bool:
    try:
        r = subprocess.run(["helm", "version"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


HELM_OK = helm_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Proc monitoring?
# ══════════════════════════════════════════════════════════════

print("=== Proc monitoring? ===\n")

print(textwrap.dedent("""\
  Bez monitoringu:
    Uzivatel: "Vas web je pomalý!"
    Ty: "Hm, proc? Nevim..."

  S monitoringem:
    Alert: "HTTP latence > 2s uz 5 minut"
    Dashboard: "PostgreSQL CPU 95%, volna RAM 50MB"
    Ty: "Databaze je preticena — scaluji!"

  Zlate signaly (Google SRE):
    1. Latency  — jak dlouho trva request
    2. Traffic  — kolik requestu za sekundu
    3. Errors   — kolik % requestu selhava
    4. Saturation — jak plne jsou zdroje (CPU, RAM, disk)
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Instalace kube-prometheus-stack
# ══════════════════════════════════════════════════════════════

print("=== Instalace kube-prometheus-stack ===\n")

INSTALL_CMDS = """\
# Pridej repozitar
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Nainstaluj stack (Prometheus + Grafana + Alertmanager + node-exporter + kube-state-metrics)
helm install monitoring prometheus-community/kube-prometheus-stack \\
  --namespace monitoring \\
  --create-namespace \\
  --set grafana.adminPassword=admin123 \\
  --set prometheus.prometheusSpec.retention=7d

# Pockej az vsechno nabehne (~2-3 minuty)
kubectl get pods -n monitoring -w

# Pristup ke Grafane:
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# → http://localhost:3000  (admin / admin123)

# Pristup k Prometheus:
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
# → http://localhost:9090
"""
print(INSTALL_CMDS)


# ══════════════════════════════════════════════════════════════
# CAST 3: Jak Prometheus sbira metriky
# ══════════════════════════════════════════════════════════════

print("=== Jak Prometheus sbira metriky ===\n")

print(textwrap.dedent("""\
  Prometheus pouziva PULL model:
    Kazda aplikace exponuje /metrics endpoint
    Prometheus tento endpoint periodicky "scrape" (tahne data)

  Format metrik (OpenMetrics / Prometheus format):
    # HELP http_requests_total Pocet HTTP requestu
    # TYPE http_requests_total counter
    http_requests_total{method="GET",status="200"} 1234
    http_requests_total{method="POST",status="500"} 5

    # HELP request_duration_seconds Trvani requestu
    # TYPE request_duration_seconds histogram
    request_duration_seconds_bucket{le="0.1"} 980
    request_duration_seconds_bucket{le="0.5"} 1200
    request_duration_seconds_bucket{le="+Inf"} 1234

  Typy metrik:
    Counter    — jen roste (pocet requestu, chyb)
    Gauge      — muze rust i klesat (CPU %, pocet Podu)
    Histogram  — distribuce hodnot (latency, velikost response)
    Summary    — jako histogram, ale quantily na strane klienta
"""))


# ══════════════════════════════════════════════════════════════
# CAST 4: Expo metrik v Pythonu
# ══════════════════════════════════════════════════════════════

print("=== Python aplikace s metrikami ===\n")

PYTHON_METRICS = """\
# pip install prometheus-client
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

# Definice metrik
REQUESTS = Counter(
    'http_requests_total',
    'Pocet HTTP requestu',
    ['method', 'path', 'status']
)
LATENCY = Histogram(
    'http_request_duration_seconds',
    'Trvani requestu',
    ['path'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)
ACTIVE = Gauge(
    'http_requests_active',
    'Aktualne zpracovavane requesty'
)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        start = time.time()
        ACTIVE.inc()
        try:
            if self.path == '/':
                REQUESTS.labels('GET', '/', '200').inc()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Ahoj!')
            else:
                REQUESTS.labels('GET', self.path, '404').inc()
                self.send_response(404)
                self.end_headers()
        finally:
            ACTIVE.dec()
            LATENCY.labels(self.path).observe(time.time() - start)
    def log_message(self, *a): pass

# /metrics je automaticky dostupny na portu 8001
start_http_server(8001)
print("Metrics: http://localhost:8001/metrics")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
"""
print(PYTHON_METRICS)


# ══════════════════════════════════════════════════════════════
# CAST 5: ServiceMonitor — rikame Prometheus kde scrape
# ══════════════════════════════════════════════════════════════

print("=== ServiceMonitor — konfigurace Prometheus scrapingu ===\n")

SERVICE_MONITOR = """\
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: moje-app-metrics
  namespace: production
  labels:
    release: monitoring    ← musi sedent s Prometheus selectorom
spec:
  selector:
    matchLabels:
      app: moje-app        ← vybere Service s timto labelem
  endpoints:
    - port: metrics        ← port jmeno v Service
      path: /metrics
      interval: 15s        ← scrape kazdych 15 sekund
"""
print(SERVICE_MONITOR)


# ══════════════════════════════════════════════════════════════
# CAST 6: PromQL — dotazovaci jazyk
# ══════════════════════════════════════════════════════════════

print("=== PromQL — dotazy na metriky ===\n")

promql_priklady = [
    # Zakladni
    ("up",
     "Ktere sluzby jsou dostupne (1=ano, 0=ne)"),
    ("http_requests_total",
     "Celkovy pocet requestu (counter)"),
    # Rate
    ("rate(http_requests_total[5m])",
     "Requesty za sekundu (prumer za 5 minut)"),
    ("rate(http_requests_total{status=~'5..'}[5m])",
     "Chybovost (5xx) za sekundu"),
    # Agregace
    ("sum(rate(http_requests_total[5m])) by (path)",
     "RPS agregované dle URL"),
    # CPU a pamet
    ("100 - (avg by(instance) (rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)",
     "CPU utilizace v %"),
    ("container_memory_working_set_bytes{namespace='production'} / 1024 / 1024",
     "RAM pouzita kontejnery v MB"),
    # Latency percentily
    ("histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
     "99. percentil latence (P99)"),
    ("histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
     "Median latence (P50)"),
    # Kubernetes
    ("kube_deployment_status_replicas_unavailable",
     "Nedostupne repliky Deploymentu"),
    ("kube_pod_container_status_restarts_total",
     "Pocet restartu kontejneru (crashy!)"),
]

for dotaz, popis in promql_priklady:
    print(f"  {popis}:")
    print(f"  {dotaz}\n")


# ══════════════════════════════════════════════════════════════
# CAST 7: Alert pravidla
# ══════════════════════════════════════════════════════════════

print("=== Alert pravidla ===\n")

ALERT_YAML = """\
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: moje-app-alerts
  namespace: production
  labels:
    release: monitoring
spec:
  groups:
    - name: moje-app
      rules:
        # Alert kdyz chybovost > 5%
        - alert: HighErrorRate
          expr: |
            rate(http_requests_total{status=~"5.."}[5m])
            /
            rate(http_requests_total[5m]) > 0.05
          for: 2m          ← stav musi trvat alespon 2 minuty
          labels:
            severity: critical
          annotations:
            summary: "Vysoka chybovost ({{ $value | humanizePercentage }})"
            description: "Aplikace {{ $labels.app }} ma chybovost {{ $value | humanizePercentage }}"

        # Alert kdyz Pod restartoval > 5x za hodinu
        - alert: PodCrashLooping
          expr: |
            increase(kube_pod_container_status_restarts_total[1h]) > 5
          for: 0m
          labels:
            severity: warning
          annotations:
            summary: "Pod crashing: {{ $labels.pod }}"
"""
print(ALERT_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 8: Demo — zobraz stav
# ══════════════════════════════════════════════════════════════

if HELM_OK:
    print("=== Kontrola monitoring stacku ===\n")

    r = subprocess.run(["helm", "list", "-n", "monitoring"],
                      capture_output=True, text=True)
    if r.returncode == 0 and "monitoring" in r.stdout:
        print("  ✓ kube-prometheus-stack je nainstalovan!")
        print(r.stdout.strip())
    else:
        print("  Monitoring stack neni nainstalovan.")
        print("  Nainstaluj ho prikazem vyse (viz INSTALL_CMDS).")
else:
    print("=== Helm neni dostupny ===\n")
    print("  Nainstaluj Helm a spust prikazy z INSTALL_CMDS sekce.")


print("\n=== Hotovo! Dalsi lekce: GitOps s ArgoCD ===")

# TVOJE ULOHA:
# 1. Nainstaluj kube-prometheus-stack pres Helm
# 2. Otevri Grafanu: kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# 3. Prozkoumej dashboard "Kubernetes / Compute Resources / Namespace (Pods)"
# 4. Najdi v Prometheus: kube_pod_container_status_restarts_total a filtruj dle namespace

# RESENI:
# 1. helm repo add prometheus-community https://prometheus-community.github.io/helm-charts && helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
# 2. kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80  →  http://localhost:3000 (admin/prom-operator)
# 3. V Grafane: Dashboards → Browse → Kubernetes → Compute Resources → Namespace (Pods)
# 4. V Prometheus UI: http://localhost:9090 → dotaz: kube_pod_container_status_restarts_total{namespace="default"}
