"""
LEKCE 09: Prvni Pod — spusti aplikaci v Kubernetes
====================================================
Pod je jako krabicka v Kubernetes.
Muze obsahovat jeden nebo vice kontejneru.
Sdileji spolu sit a uloziste.

Vetsinou jeden kontejner = jeden Pod.
(Vyjimka: init containers, sidecar pattern)

Naucis se:
  - co je Pod a jak ho vytvorit
  - YAML manifest pro Pod
  - kubectl get, describe, logs, exec
  - proc se Pod pouziva malo primo (pouzivame Deployment)

Obtiznost: ⭐⭐
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
# CAST 1: Pod YAML manifest
# ══════════════════════════════════════════════════════════════

print("=== Pod YAML manifest ===\n")

POD_YAML = """\
apiVersion: v1          ← verze API
kind: Pod               ← typ objektu
metadata:
  name: muj-prvni-pod   ← jmeno podu
  labels:
    app: web            ← stitky (dulezite pro selectory!)
spec:
  containers:
    - name: web         ← jmeno kontejneru
      image: nginx:alpine  ← ktera image
      ports:
        - containerPort: 80    ← port kontejneru (info, neotevira!)
      resources:
        requests:              ← minimum CPU a RAM
          cpu: "100m"          ← 100 millicores = 0.1 jadro CPU
          memory: "64Mi"       ← 64 MiB RAM
        limits:                ← maximum CPU a RAM
          cpu: "500m"
          memory: "128Mi"
      readinessProbe:          ← je kontejner pripraveny na provoz?
        httpGet:
          path: /
          port: 80
        initialDelaySeconds: 5
        periodSeconds: 10
"""

print(POD_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 2: Kubectl prikazy pro Pody
# ══════════════════════════════════════════════════════════════

print("=== Kubectl prikazy ===\n")

prikazy = [
    ("kubectl apply -f pod.yaml",        "Vytvor nebo updatuj Pod dle YAML"),
    ("kubectl get pods",                 "Zobraz vsechny Pody"),
    ("kubectl get pods -o wide",         "Zobraz + node a IP adresu"),
    ("kubectl get pod muj-pod -o yaml",  "Zobraz kompletni YAML podu"),
    ("kubectl describe pod muj-pod",     "Detailni info + events (debug!)"),
    ("kubectl logs muj-pod",             "Logy kontejneru"),
    ("kubectl logs muj-pod -f",          "Live logy (follow)"),
    ("kubectl logs muj-pod -c web",      "Logy konkretniho kontejneru"),
    ("kubectl exec -it muj-pod -- bash", "Terminal uvnitr Podu"),
    ("kubectl delete pod muj-pod",       "Smaz Pod"),
    ("kubectl delete -f pod.yaml",       "Smaz Pod dle YAML"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 3: Stavovy automat Podu
# ══════════════════════════════════════════════════════════════

print("=== Stavy Podu ===\n")

print(textwrap.dedent("""\
  Pending    ← Pod ceka na pridani na node (stahuje image, hledá misto)
  Running    ← Pod bezi, kontejnery jsou spusteny
  Succeeded  ← Vsechny kontejnery uspesne skoncily (exit 0)
  Failed     ← Aspon jeden kontejner skoncil s chybou
  Unknown    ← Kubernetes nezna stav (problem se siti)

  Caste problemy:
    CrashLoopBackOff  ← kontejner pada a K8s ho restart opakuje
    ImagePullBackOff  ← nelze stahnou image (spatne jmeno, credentials)
    Pending (dlouho)  ← neni volny node s dostatecnymi zdroji

  Debug:
    kubectl describe pod <jmeno>   ← podivej se na Events sekci
    kubectl logs <jmeno> --previous ← logy pred poslednim crashem
"""))


# ══════════════════════════════════════════════════════════════
# CAST 4: Proc nepouzivat Pod primo
# ══════════════════════════════════════════════════════════════

print("=== Proc nepouzivat holý Pod ===\n")

print(textwrap.dedent("""\
  Holy Pod NE:
    - Kdyz pode pada, Kubernetes ho NESPUSTI znova
    - Nema replikaci
    - Update = manualni mazani + vytvareni

  Deployment ANO:
    - Automaticke restartovani padu
    - Snadna replikace (replicas: 3)
    - Rolling update bez vypadku
    - Rollback na predchozi verzi

  Pody jsou stavebni kameny — Deployment je pouzivame pres ne.
  V dalsi lekci naucime Deployment.

  Prirovnani:
    Pod    = konkretni pracovnik
    Deployment = popis pozice ("chci 3 pokladni")
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: Init containers
# ══════════════════════════════════════════════════════════════

print("=== Init containers — priprava pred startem ===\n")

INIT_YAML = """\
spec:
  initContainers:        ← bezi PRED hlavnimi kontejnery
    - name: cekej-na-db
      image: busybox
      command:
        - sh
        - -c
        - until nc -z db 5432; do echo 'Cekam na databazi...'; sleep 2; done
  containers:
    - name: web
      image: moje-app:v1.0
      # Spusti se az po dokonceni vsech init containers
"""

print("Priklad: cekej az databaze nabezhne:")
print(INIT_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo
# ══════════════════════════════════════════════════════════════

POD_MANIFEST = """\
apiVersion: v1
kind: Pod
metadata:
  name: demo-nginx
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
    print("=== Zkousime vytvorit Pod ===\n")

    # Zjisti jestli bezi cluster
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("  Cluster neni dostupny.")
        print("  Spust: minikube start")
        print("\n  Pak znovu spust tuto lekci.")
    else:
        manifest = Path("/tmp/demo-nginx-pod.yaml")
        manifest.write_text(POD_MANIFEST)

        print("$ kubectl apply -f pod.yaml")
        r = subprocess.run(["kubectl", "apply", "-f", str(manifest)],
                          capture_output=True, text=True)
        print(f"  {r.stdout.strip() or r.stderr.strip()}")

        import time
        print("\n$ kubectl get pods (cekame na Running...)")
        for _ in range(10):
            r = subprocess.run(["kubectl", "get", "pod", "demo-nginx",
                               "--no-headers"],
                              capture_output=True, text=True)
            stav = r.stdout.strip()
            print(f"  {stav}")
            if "Running" in stav:
                break
            time.sleep(3)

        print("\n$ kubectl describe pod demo-nginx (zkracene)")
        r = subprocess.run(["kubectl", "describe", "pod", "demo-nginx"],
                          capture_output=True, text=True)
        radky = r.stdout.splitlines()
        for radek in radky[:20]:
            print(f"  {radek}")

        print("\n$ kubectl delete pod demo-nginx")
        subprocess.run(["kubectl", "delete", "pod", "demo-nginx"],
                      capture_output=True)
        print("  ✓ Pod smazan")

        manifest.unlink(missing_ok=True)

else:
    print("=== kubectl neni dostupny ===\n")
    print("  Uloz nasledujici YAML jako pod.yaml:")
    print(POD_MANIFEST)
    print("  Pak spust:")
    print("  $ kubectl apply -f pod.yaml")
    print("  $ kubectl get pods")
    print("  $ kubectl describe pod demo-nginx")


print("\n=== Hotovo! Dalsi lekce: Deployment — hlida tvoje Pody ===")

# TVOJE ULOHA:
# 1. Vytvor pod.yaml s nginx:alpine a aplikuj ho
# 2. Zobraz stav Podu a pockat az bude Running
# 3. Otevri terminal uvnitr Podu a prozkoumej filesystem
# 4. Smaz Pod a over ze ho K8s neobnovi

# RESENI:
# 1. kubectl apply -f pod.yaml   (viz manifest v lekci)
# 2. kubectl get pods -w   (ctrl+c az bezi)
# 3. kubectl exec -it demo-nginx -- sh   pak: ls /usr/share/nginx/html, exit
# 4. kubectl delete pod demo-nginx   →   kubectl get pods   (Pod zmizi, neobjeví se)
