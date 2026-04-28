"""
LEKCE 10: Deployment — Kubernetes hlida tvoje aplikace
=======================================================
Deployment je srdce Kubernetes.
Rikis mu co chces (3 kopie nginx) a on se stara o zbytek.

Pada kontejner? Spusti novy.
Chces 5 kopii misto 3? Prida dalsi.
Novy update? Postupne vymeni — bez vypadku.

Naucis se:
  - vytvorit Deployment
  - skalovat aplikaci
  - rolling update bez vypadku
  - rollback na predchozi verzi

Obtiznost: ⭐⭐⭐
"""

import subprocess
import textwrap
from pathlib import Path


def kubectl_dostupny() -> bool:
    try:
        r = subprocess.run(["kubectl", "version", "--client"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


KUBECTL_OK = kubectl_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Deployment YAML
# ══════════════════════════════════════════════════════════════

print("=== Deployment YAML ===\n")

DEPLOYMENT_YAML = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: muj-web
  labels:
    app: muj-web

spec:
  replicas: 3                    ← chci 3 kopie (Pody)

  selector:                      ← jake Pody spravuje tento Deployment
    matchLabels:
      app: muj-web

  strategy:
    type: RollingUpdate          ← typ updatu (RollingUpdate nebo Recreate)
    rollingUpdate:
      maxSurge: 1                ← muze byt o 1 Pod vice behem updatu
      maxUnavailable: 0          ← vsechny Pody musi byt dostupne (zero downtime)

  template:                      ← sablona pro kazdy Pod
    metadata:
      labels:
        app: muj-web             ← musi sedent se selector.matchLabels!
    spec:
      containers:
        - name: web
          image: nginx:1.25      ← konkretni verze (ne latest v produkci!)
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "500m"
              memory: "128Mi"
          readinessProbe:        ← K8s vi kdy je Pod pripraveny
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:         ← K8s vi kdy Pod selhal a potrebuje restart
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
"""

print(DEPLOYMENT_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 2: Prikazy pro Deployment
# ══════════════════════════════════════════════════════════════

print("=== Prikazy pro Deployment ===\n")

prikazy = [
    ("kubectl apply -f deployment.yaml",       "Vytvor nebo updatuj Deployment"),
    ("kubectl get deployments",                "Zobraz vsechny Deployments"),
    ("kubectl get deploy muj-web",             "Stav konkretniho Deploymentu"),
    ("kubectl describe deploy muj-web",        "Detailni info + events"),
    ("kubectl get pods -l app=muj-web",        "Pody patrici tomuto Deploymentu"),
    ("kubectl scale deploy muj-web --replicas=5", "Skaluj na 5 kopii"),
    ("kubectl set image deploy/muj-web web=nginx:1.26", "Update image"),
    ("kubectl rollout status deploy/muj-web",  "Sleduj prubeh updatu"),
    ("kubectl rollout history deploy/muj-web", "Historie updatu"),
    ("kubectl rollout undo deploy/muj-web",    "Rollback na predchozi verzi"),
    ("kubectl rollout undo deploy/muj-web --to-revision=2", "Rollback na verzi 2"),
    ("kubectl delete deploy muj-web",          "Smaz Deployment (a vsechny Pody)"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 3: Rolling Update
# ══════════════════════════════════════════════════════════════

print("=== Rolling Update — zero downtime ===\n")

print(textwrap.dedent("""\
  Mas 3 Pody s nginx:1.25.
  Chces updatovat na nginx:1.26.

  BEZ rolling update (Recreate):
    Smaz vsechny 3 stare Pody → [downtime!] → Spusti 3 nove
                                   ^^^^^^
                                   aplikace je offline!

  S Rolling Update (default):
    Spusti novy Pod (nginx:1.26) →
    Kdyz je Ready, smaz jeden stary (nginx:1.25) →
    Spusti dalsi novy →
    Kdyz je Ready, smaz dalsi stary →
    ... az jsou vsechny nove

    Aplikace je STALE dostupna! ✅

  Vizualizace:
    Cas →  [1.25] [1.25] [1.25]         stav pred
           [1.25] [1.25] [1.25] [1.26]  pridal novy
           [1.25] [1.25] [1.26]         smaz stary
           [1.25] [1.26] [1.26]         ...
           [1.26] [1.26] [1.26]         dokonceno
"""))


# ══════════════════════════════════════════════════════════════
# CAST 4: ReadinessProbe vs LivenessProbe
# ══════════════════════════════════════════════════════════════

print("=== ReadinessProbe vs LivenessProbe ===\n")

print(textwrap.dedent("""\
  ReadinessProbe — je kontejner PRIPRAVENY prijimat provoz?
    - Fail → Pod se vyrad ze sluzby (Service ho nebude pouzivat)
    - Pouzij pro: cekani na DB, nacteni cache, inicializace

  LivenessProbe — BEZI kontejner spravne?
    - Fail → Kubernetes RESTARTUJE kontejner
    - Pouzij pro: detekovani deadlocku, zamrzlych procesu

  Typy probes:
    httpGet    ← GET request na cestu, ocekava 200-399
    tcpSocket  ← zkusi navazat TCP spojeni
    exec       ← spusti prikaz, ocekava exit 0
    grpc       ← gRPC health check

  Priklad exec probe:
    livenessProbe:
      exec:
        command:
          - python
          - -c
          - "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
      initialDelaySeconds: 30
      periodSeconds: 30
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: HorizontalPodAutoscaler
# ══════════════════════════════════════════════════════════════

print("=== HPA — automaticke skalovani ===\n")

HPA_YAML = """\
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: muj-web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: muj-web
  minReplicas: 2     ← minimum kopii
  maxReplicas: 10    ← maximum kopii
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70   ← skaluj kdyz CPU > 70%
"""

print("Automaticky skaluj dle zateze:")
print(HPA_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo
# ══════════════════════════════════════════════════════════════

DEPLOY_MANIFEST = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "32Mi"
            limits:
              cpu: "200m"
              memory: "64Mi"
"""

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("=== Cluster neni dostupny ===\n")
        print("  Spust: minikube start")
    else:
        print("=== Demo: Deployment, scale, rollout ===\n")

        manifest = Path("/tmp/demo-deployment.yaml")
        manifest.write_text(DEPLOY_MANIFEST)

        print("$ kubectl apply -f deployment.yaml")
        r = subprocess.run(["kubectl", "apply", "-f", str(manifest)],
                          capture_output=True, text=True)
        print(f"  {r.stdout.strip()}")

        import time; time.sleep(3)

        print("\n$ kubectl get pods -l app=demo")
        r = subprocess.run(["kubectl", "get", "pods", "-l", "app=demo",
                           "--no-headers"],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        print("\n$ kubectl scale deployment demo-deployment --replicas=5")
        r = subprocess.run(["kubectl", "scale", "deployment", "demo-deployment",
                           "--replicas=5"],
                          capture_output=True, text=True)
        print(f"  {r.stdout.strip()}")

        time.sleep(3)

        print("\n$ kubectl get deployment demo-deployment")
        r = subprocess.run(["kubectl", "get", "deployment", "demo-deployment"],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        print("\n$ kubectl delete deployment demo-deployment")
        subprocess.run(["kubectl", "delete", "deployment", "demo-deployment"],
                      capture_output=True)
        print("  ✓ Deployment smazan")

        manifest.unlink(missing_ok=True)

else:
    print("=== kubectl neni dostupny ===\n")
    print("  Uloz YAML jako deployment.yaml a spust:")
    print("  $ kubectl apply -f deployment.yaml")
    print("  $ kubectl get pods")
    print("  $ kubectl scale deployment demo-deployment --replicas=5")


print("\n=== Hotovo! Dalsi lekce: Service — pristup k aplikaci ===")

# TVOJE ULOHA:
# 1. Vytvor Deployment se 2 kopiemi nginx a aplikuj
# 2. Smaz jeden Pod rucne — co Kubernetes udela?
# 3. Skaluj Deployment na 5 kopii
# 4. Rollback Deployment na predchozi verzi

# RESENI:
# 1. kubectl apply -f deployment.yaml   (viz DEPLOY_MANIFEST v lekci)
# 2. kubectl delete pod <jmeno>   →   kubectl get pods -w   (K8s okamzite spusti novy!)
# 3. kubectl scale deployment demo-deployment --replicas=5
# 4. kubectl rollout undo deployment/demo-deployment
