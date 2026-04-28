"""
LEKCE 08: Co je Kubernetes? ☸️
================================
Docker ti dal krabicky (kontejnery).
Ale co kdyz mas 100 krabicek?
Kdo je hlida? Kdo spusti novou kdyz jedna pada?
Kdo rozdeli provoz mezi ne?

Na to je KUBERNETES — sef vsech krabicek.
Zkratka: k8s (k + 8 pismen + s)

Naucis se:
  - proc Kubernetes existuje
  - klicove pojmy: cluster, node, pod, deployment
  - jak Kubernetes mysli (declarativni model)
  - jak nainstalovat minikube pro lokalni vyvoj

Obtiznost: ⭐⭐
"""

import subprocess
import textwrap


def kubectl_dostupny() -> bool:
    try:
        r = subprocess.run(["kubectl", "version", "--client"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


KUBECTL_OK = kubectl_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Problem s jednim kontejnerem
# ══════════════════════════════════════════════════════════════

print("=== Problem: proc nestaci Docker? ===\n")

print(textwrap.dedent("""\
  Docker na jednom serveru je skvely.
  Ale v produkci mas tyhle problemy:

  Problem 1: Co kdyz server pada?
    → Vsechna tvoje aplikace jsou offline

  Problem 2: Co kdyz prilis lidi pristupuje najednou?
    → Jeden kontejner nestaci, potrebujes vic

  Problem 3: Jak updatujes bez vypadku?
    → Potrebujes postupne vymenit stare kontejnery za nove

  Problem 4: 50 aplikaci na 10 serverech?
    → Jak spravovat kde co bezi a kolik pameti pouziva?

  Kubernetes resi VSECHNY tyto problemy.
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Kubernetes = sef krabicek
# ══════════════════════════════════════════════════════════════

print("=== Kubernetes jako sef ===\n")

print(textwrap.dedent("""\
  Ty rikis Kubernetes:
    "Chci mit vzdy 3 kopie me web aplikace bezici."

  Kubernetes se postara o zbytek:
    ✅ Spusti 3 kontejnery
    ✅ Kdyz jeden pada, spusti novy
    ✅ Kdyz server pada, presune kontejnery jinam
    ✅ Rozdeli provoz mezi vsechny 3 kopie
    ✅ Updatuje kontejnery bez vypadku
    ✅ Sleduje zdravi vsech kontejneru

  Ty popis CO chces. Kubernetes vyresi JAK.
  Tohle se nazyva DEKLARATIVNI model.
"""))


# ══════════════════════════════════════════════════════════════
# CAST 3: Architektura clusteru
# ══════════════════════════════════════════════════════════════

print("=== Architektura Kubernetes clusteru ===\n")

schema = """\
KUBERNETES CLUSTER
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  CONTROL PLANE (mozek)                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  API Server  │  │  Scheduler   │  │  Controller Mgr  │  │
│  │  (brana do   │  │  (kdo bezi   │  │  (hlida stav)    │  │
│  │   clusteru)  │  │   kde)       │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────────────────────┐                           │
│  │  etcd  (databaze stavu)      │                           │
│  └──────────────────────────────┘                           │
│                                                             │
│  WORKER NODES (svaly — kde skutecne bezi kontejnery)        │
│  ┌────────────────────┐  ┌────────────────────┐             │
│  │  Node 1            │  │  Node 2            │             │
│  │  ┌────┐ ┌────┐    │  │  ┌────┐            │             │
│  │  │Pod │ │Pod │    │  │  │Pod │            │             │
│  │  └────┘ └────┘    │  │  └────┘            │             │
│  │  kubelet, kube-   │  │  kubelet, kube-    │             │
│  │  proxy            │  │  proxy             │             │
│  └────────────────────┘  └────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
"""
print(schema)


# ══════════════════════════════════════════════════════════════
# CAST 4: Dulezite pojmy
# ══════════════════════════════════════════════════════════════

print("=== Dulezite pojmy ===\n")

pojmy = [
    ("Cluster",     "Skupina serveru (nodu) kterou Kubernetes spravuje"),
    ("Node",        "Jeden server v clusteru (fyzicky nebo virtualni)"),
    ("Pod",         "Nejmensi jednotka v K8s — obal pro kontejnery"),
    ("Deployment",  "Popis jak spustit aplikaci (kolik kopii, ktere image...)"),
    ("Service",     "Stabilni adresa pro pristup k Podum (load balancer)"),
    ("Namespace",   "Logicke oddeleni clusteru (jako slozky)"),
    ("ConfigMap",   "Konfigurace jako klice-hodnoty (bez hesla)"),
    ("Secret",      "Konfigurace s hesly (zakodovano)"),
    ("Ingress",     "Pravidla pro pristup z internetu (reverse proxy)"),
    ("Volume",      "Uloziste dat pro Pody"),
    ("kubectl",     "Prikaz pro ovladani clusteru z terminalu"),
    ("Helm",        "Balickovaci system pro Kubernetes (jako apt pro K8s)"),
]

for pojem, popis in pojmy:
    print(f"  {pojem:<14} — {popis}")


# ══════════════════════════════════════════════════════════════
# CAST 5: Deklarativni model
# ══════════════════════════════════════════════════════════════

print("\n=== Deklarativni model — YAML jako pravda ===\n")

print(textwrap.dedent("""\
  Imperiativni (jak):
    "Spust kontejner, zkopiruj ho 3x, nastav load balancer..."

  Deklarativni (co):
    "Chci 3 kopie teto aplikace bezici."

  Kubernetes YAML = deklarace toho co CHCES:
"""))

YAML_PRIKLAD = """\
# Chci Deployment s 3 kopiemi nginx
apiVersion: apps/v1
kind: Deployment
metadata:
  name: muj-web
spec:
  replicas: 3          ← 3 kopie
  selector:
    matchLabels:
      app: muj-web
  template:
    metadata:
      labels:
        app: muj-web
    spec:
      containers:
        - name: web
          image: nginx:alpine
          ports:
            - containerPort: 80
"""

print(YAML_PRIKLAD)
print(textwrap.dedent("""\
  Aplikujes: kubectl apply -f deployment.yaml

  Kubernetes zjisti co je (0 kopii) a co chces (3 kopie)
  a automaticky nastavi stav na pozadovany.

  Kdyz jedna kopie pada → Kubernetes spusti novou.
  Kdyz zmenís YAML na 5 kopii → Kubernetes prida 2 dalsi.
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Instalace minikube
# ══════════════════════════════════════════════════════════════

print("=== Instalace pro lokalni vyvoj — minikube ===\n")

print(textwrap.dedent("""\
  Moznosti pro lokalni K8s:
    minikube     — nejjednodussi, oficial od Kubernetes
    kind         — K8s in Docker (rychle, bez VM)
    k3s          — lehky K8s pro ARM a edge
    Docker Desktop — integraci K8s (Windows/Mac)

  Instalace minikube:
    Linux:
      curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
      sudo install minikube-linux-amd64 /usr/local/bin/minikube

    Mac:
      brew install minikube

    Windows:
      winget install minikube

  Spusteni:
    minikube start           ← prvni start (stahne K8s ~5 minut)
    minikube status          ← stav clusteru
    minikube dashboard       ← otevre webove UI v prohlizeci

  kubectl:
    minikube kubectl --       ← pouzij kubectl pres minikube
    nebo nainstaluj samostatne:
    https://kubernetes.io/docs/tasks/tools/
"""))


# ══════════════════════════════════════════════════════════════
# CAST 7: Prvni prikazy
# ══════════════════════════════════════════════════════════════

if KUBECTL_OK:
    print("=== kubectl je dostupny! ===\n")

    print("$ kubectl version --client")
    r = subprocess.run(["kubectl", "version", "--client", "--output=json"],
                      capture_output=True, text=True)
    if r.returncode == 0:
        import json
        try:
            data = json.loads(r.stdout)
            verze = data.get("clientVersion", {}).get("gitVersion", "neznama")
            print(f"  kubectl verze: {verze}")
        except Exception:
            print(f"  {r.stdout.strip()[:100]}")

    print("\n$ kubectl cluster-info")
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip())
    else:
        print("  (cluster neni dostupny — spust minikube start)")

else:
    print("=== kubectl neni dostupny ===\n")
    print("  Nainstaluj kubectl: https://kubernetes.io/docs/tasks/tools/")
    print("  Nainstaluj minikube: https://minikube.sigs.k8s.io/docs/start/")
    print("  Pak spust: minikube start")


print("\n=== Hotovo! Dalsi lekce: Tvuj prvni Pod ===")

# TVOJE ULOHA:
# 1. Nainstaluj minikube a kubectl (viz navod v lekci)
# 2. Spust Kubernetes cluster
# 3. Zjisti stav clusteru a kolik nodu ma
# 4. Otevri graficke dashboard

# RESENI:
# 1. viz https://minikube.sigs.k8s.io/docs/start/ a https://kubernetes.io/docs/tasks/tools/
# 2. minikube start
# 3. minikube status   a   kubectl get nodes
# 4. minikube dashboard   (otevre prohlizec automaticky)
