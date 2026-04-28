"""
LEKCE 14: Helm — balicky pro Kubernetes
=========================================
Instalace PostgreSQL v K8s? Manualne 10+ YAML souboru.
S Helm jednim prikazem.

Helm je balickovaci system pro Kubernetes.
Jako apt/homebrew — ale pro K8s aplikace.

Naucis se:
  - instalovat Helm charty
  - vytvorit vlastni Helm chart
  - pouzivat values pro konfiguraci
  - upgrady a rollbacky

Obtiznost: ⭐⭐⭐
"""

import subprocess
import textwrap
from pathlib import Path


def helm_dostupny() -> bool:
    try:
        r = subprocess.run(["helm", "version"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


HELM_OK = helm_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Proc Helm?
# ══════════════════════════════════════════════════════════════

print("=== Proc Helm? ===\n")

print(textwrap.dedent("""\
  Bez Helm — instalace nginx-ingress-controller:
    kubectl apply -f https://...//deploy.yaml
    kubectl apply -f ...namespace.yaml
    kubectl apply -f ...serviceaccount.yaml
    kubectl apply -f ...clusterrole.yaml
    kubectl apply -f ...clusterrolebinding.yaml
    kubectl apply -f ...configmap.yaml
    kubectl apply -f ...service.yaml
    kubectl apply -f ...deployment.yaml
    ... a 10 dalsich souboru

  S Helm:
    helm install ingress-nginx ingress-nginx/ingress-nginx

  Navic:
    - verzovani (upgrade na novou verzi)
    - rollback na predchozi verzi
    - konfigurace pres values.yaml
    - templating (jeden chart, ruzne prostredi)
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Zakladni prikazy
# ══════════════════════════════════════════════════════════════

print("=== Helm prikazy ===\n")

prikazy = [
    # Repozitare
    ("helm repo add bitnami https://charts.bitnami.com/bitnami", "Pridej repozitar"),
    ("helm repo update",                  "Aktualizuj seznam chartu"),
    ("helm search repo postgres",         "Hledej chart v repozitarich"),
    # Instalace
    ("helm install moje-db bitnami/postgresql", "Instaluj chart (nazev + chart)"),
    ("helm install moje-db bitnami/postgresql -f values.yaml", "S vlastnim values"),
    ("helm install moje-db bitnami/postgresql --set auth.password=heslo", "S hodnotou"),
    ("helm install moje-db bitnami/postgresql -n db --create-namespace", "Do namespace"),
    # Sprava
    ("helm list",                         "Zobraz nainstalované releases"),
    ("helm list -A",                      "Vsechny namespaces"),
    ("helm status moje-db",               "Stav release"),
    ("helm upgrade moje-db bitnami/postgresql", "Upgraduj release"),
    ("helm rollback moje-db 1",           "Rollback na revizi 1"),
    ("helm uninstall moje-db",            "Odinstall chart"),
    ("helm get values moje-db",           "Aktualni hodnoty"),
    ("helm template moje-db bitnami/postgresql", "Zobraz generovany YAML"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 3: Struktura Helm chart
# ══════════════════════════════════════════════════════════════

print("=== Struktura Helm chart ===\n")

struktura = """\
muj-chart/
├── Chart.yaml          ← metadata chartu (jmeno, verze, popis)
├── values.yaml         ← defaultni hodnoty
├── templates/          ← Kubernetes YAML sablony
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl    ← sdilene funkce (konvence: zacina _)
│   └── NOTES.txt       ← zprava po instalaci
└── charts/             ← zavislosti (dalsi charty)
"""
print(struktura)


# ══════════════════════════════════════════════════════════════
# CAST 4: Vytvor vlastni chart
# ══════════════════════════════════════════════════════════════

print("=== Vlastni Helm chart ===\n")

CHART_YAML = """\
# Chart.yaml
apiVersion: v2
name: moje-aplikace
description: Moje prvni Helm chart
type: application
version: 0.1.0          ← verze chartu
appVersion: "1.0.0"     ← verze aplikace
"""

VALUES_YAML = """\
# values.yaml — defaultni hodnoty
replicaCount: 2

image:
  repository: nginx
  tag: alpine
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  host: moje-app.local

resources:
  requests:
    cpu: 100m
    memory: 64Mi
  limits:
    cpu: 500m
    memory: 128Mi

env:
  LOG_LEVEL: info
  DEBUG: "false"
"""

DEPLOYMENT_TEMPLATE = """\
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-web
  labels:
    app: {{ .Chart.Name }}
    release: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Chart.Name }}
  template:
    metadata:
      labels:
        app: {{ .Chart.Name }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.port }}
          env:
            {{- range $key, $val := .Values.env }}
            - name: {{ $key }}
              value: "{{ $val }}"
            {{- end }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
"""

print("Chart.yaml:")
print(CHART_YAML)
print("values.yaml:")
print(VALUES_YAML)
print("templates/deployment.yaml:")
print(DEPLOYMENT_TEMPLATE)


# ══════════════════════════════════════════════════════════════
# CAST 5: Overrides pro ruzna prostredi
# ══════════════════════════════════════════════════════════════

print("=== Prostredi — values override ===\n")

print(textwrap.dedent("""\
  Jeden chart, vice prostredi:

  values.yaml          ← default
  values-dev.yaml      ← overrides pro vyvoj
  values-staging.yaml  ← overrides pro staging
  values-prod.yaml     ← overrides pro produkci

  Priklad values-prod.yaml:
    replicaCount: 5
    image:
      tag: v1.2.3
    ingress:
      enabled: true
      host: web.firma.cz
    resources:
      limits:
        cpu: 2000m
        memory: 512Mi

  Instalace pro produkci:
    helm install moje-app ./moje-chart -f values-prod.yaml
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Popularni Helm charty
# ══════════════════════════════════════════════════════════════

print("=== Popularni Helm charty ===\n")

charty = [
    ("bitnami/postgresql",   "PostgreSQL databaze"),
    ("bitnami/redis",        "Redis cache"),
    ("bitnami/mongodb",      "MongoDB databaze"),
    ("ingress-nginx/ingress-nginx", "nginx Ingress Controller"),
    ("cert-manager/cert-manager",   "TLS certifikaty (Let's Encrypt)"),
    ("prometheus/kube-prometheus-stack", "Monitoring (Prometheus + Grafana)"),
    ("grafana/loki-stack",   "Log agregace"),
    ("argo/argo-cd",         "GitOps a CD"),
    ("bitnami/kafka",        "Message broker Kafka"),
    ("bitnami/elasticsearch","Fulltextove vyhledavani"),
]

print(f"  {'Chart':<40} {'Popis'}")
print(f"  {'─'*40} {'─'*30}")
for chart, popis in charty:
    print(f"  {chart:<40} {popis}")


# ══════════════════════════════════════════════════════════════
# CAST 7: Demo
# ══════════════════════════════════════════════════════════════

if HELM_OK:
    print("\n=== Helm je dostupny! ===\n")

    print("$ helm version")
    r = subprocess.run(["helm", "version", "--short"],
                      capture_output=True, text=True)
    print(f"  {r.stdout.strip()}")

    print("\n$ helm repo list")
    r = subprocess.run(["helm", "repo", "list"],
                      capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip())
    else:
        print("  (zadne repozitare — pridej: helm repo add bitnami https://charts.bitnami.com/bitnami)")

    print("\n$ helm create muj-chart (demo)")
    demo_dir = Path("/tmp/helm_demo")
    demo_dir.mkdir(exist_ok=True)
    r = subprocess.run(["helm", "create", "muj-chart"],
                      capture_output=True, text=True, cwd=str(demo_dir))
    if r.returncode == 0:
        print("  ✓ Chart vytvoren!")
        # Zobraz strukturu
        for soubor in sorted((demo_dir / "muj-chart").rglob("*"))[:10]:
            relativni = soubor.relative_to(demo_dir)
            print(f"  {relativni}")

    import shutil; shutil.rmtree(demo_dir, ignore_errors=True)

else:
    print("\n=== Helm neni dostupny ===\n")
    print("  Instalace Helm:")
    print("  Linux/Mac:  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash")
    print("  Mac:        brew install helm")
    print("  Windows:    winget install Helm.Helm")
    print("\n  Pak zkus:")
    print("  $ helm version")
    print("  $ helm repo add bitnami https://charts.bitnami.com/bitnami")
    print("  $ helm search repo postgres")


print("\n=== Hotovo! Dalsi lekce: Kompletni projekt ===")

# TVOJE ULOHA:
# 1. Nainstaluj Helm a pridej bitnami repozitar
# 2. Nainstaluj Redis bez autentizace
# 3. Zobraz co Helm vytvoril v clusteru
# 4. Odinstaluj Redis

# RESENI:
# 1. curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash   →   helm repo add bitnami https://charts.bitnami.com/bitnami && helm repo update
# 2. helm install moje-cache bitnami/redis --set auth.enabled=false
# 3. kubectl get all -l app.kubernetes.io/instance=moje-cache
# 4. helm uninstall moje-cache
