"""
LEKCE 12: ConfigMap a Secret — konfigurace aplikaci
====================================================
Nikdy nesmis dat hesla primo do image nebo YAML!
Proc? Image je verejná, YAML je v gitu.

ConfigMap = konfigurace bez hesla (DB host, debug mode...)
Secret    = konfigurace s heslem (passwords, API keys, certs)

Naucis se:
  - vytvorit ConfigMap a Secret
  - pouzit je jako env variables nebo soubory
  - proc Secret neni opravdu "tajny" (base64)
  - jak spravovat sekrety v produkci (Vault, sealed secrets)

Obtiznost: ⭐⭐⭐
"""

import subprocess
import textwrap
from pathlib import Path
import base64


def kubectl_dostupny() -> bool:
    try:
        r = subprocess.run(["kubectl", "version", "--client"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


KUBECTL_OK = kubectl_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: ConfigMap
# ══════════════════════════════════════════════════════════════

print("=== ConfigMap — nekonfidencialni konfigurace ===\n")

CONFIGMAP_YAML = """\
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Jednoduche klice-hodnoty
  DEBUG: "false"
  LOG_LEVEL: "info"
  APP_PORT: "8000"
  DB_HOST: "postgres-svc"
  DB_PORT: "5432"
  DB_NAME: "moje_app"

  # Cely soubor jako hodnota
  app.properties: |
    max_connections=100
    timeout=30
    feature_flags=auth,notifications

  nginx.conf: |
    server {
      listen 80;
      location / {
        proxy_pass http://app-svc:8000;
      }
    }
"""

print(CONFIGMAP_YAML)

print("Jak pouzit v Deployment:\n")
CONFIGMAP_POUZITI = """\
spec:
  containers:
    - name: app
      image: moje-app:v1.0

      # Vsechny hodnoty z ConfigMap jako env:
      envFrom:
        - configMapRef:
            name: app-config

      # Nebo jen vybrane hodnoty:
      env:
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DB_HOST

      # Soubory z ConfigMap:
      volumeMounts:
        - name: config-volume
          mountPath: /etc/nginx/conf.d

  volumes:
    - name: config-volume
      configMap:
        name: app-config
        items:
          - key: nginx.conf
            path: default.conf
"""
print(CONFIGMAP_POUZITI)


# ══════════════════════════════════════════════════════════════
# CAST 2: Secret
# ══════════════════════════════════════════════════════════════

print("=== Secret — konfidencialni data ===\n")

db_heslo = "super_tajne_heslo"
api_klic = "sk-abc123xyz"

# Secret pouziva base64 encoding
db_heslo_b64 = base64.b64encode(db_heslo.encode()).decode()
api_klic_b64 = base64.b64encode(api_klic.encode()).decode()

print(f"  Heslo: {db_heslo}")
print(f"  base64: {db_heslo_b64}")
print(f"  Zpet:  {base64.b64decode(db_heslo_b64).decode()}")
print()

SECRET_YAML = f"""\
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  # POZOR: base64 neni sifrování! Je to jen encoding!
  # echo -n 'super_tajne_heslo' | base64
  DB_PASSWORD: {db_heslo_b64}
  API_KEY: {api_klic_b64}

# Nebo pouzij stringData (K8s sam prevede na base64):
# stringData:
#   DB_PASSWORD: super_tajne_heslo
#   API_KEY: sk-abc123xyz
"""
print(SECRET_YAML)

print("DULEZITE: base64 neni bezpecne sifrovani!")
print("Kdokoli kdo ma pristup k Secrets muze data precist.")
print("Secret je bezpecnejsi nez ConfigMap jen tim, ze:")
print("  - je ulozen v etcd oddelene")
print("  - muzes nastavit RBAC (kdo smi cist)")
print("  - v pameti kontejneru jen kdyz potrebuje")
print()


# ══════════════════════════════════════════════════════════════
# CAST 3: Pouziti Secret
# ══════════════════════════════════════════════════════════════

print("=== Pouziti Secret v Deployment ===\n")

SECRET_POUZITI = """\
spec:
  containers:
    - name: app
      image: moje-app:v1.0

      # Vsechny hodnoty ze Secret jako env:
      envFrom:
        - secretRef:
            name: app-secret

      # Nebo jen vybrane:
      env:
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secret
              key: DB_PASSWORD

      # Secret jako soubory (napr. TLS certifikat):
      volumeMounts:
        - name: tls-certs
          mountPath: /etc/ssl/certs
          readOnly: true

  volumes:
    - name: tls-certs
      secret:
        secretName: tls-secret
"""
print(SECRET_POUZITI)


# ══════════════════════════════════════════════════════════════
# CAST 4: Spravovani Secrets v produkci
# ══════════════════════════════════════════════════════════════

print("=== Produkce: jak spravovat sekrety spravne ===\n")

print(textwrap.dedent("""\
  Moznosti:

  1. External Secrets Operator + AWS Secrets Manager / Vault
     - Sekrety jsou ulozeny mimo K8s (bezpecne)
     - Operator je synchronizuje jako K8s Secrets automaticky
     - Doporuceno pro produkci

  2. Sealed Secrets (Bitnami)
     - Zasifrujes Secret specialnim klicem
     - Zasifrovany YAML lze bezpecne commitnout do gitu
     - Jen K8s cluster ho muze desifrovat

  3. HashiCorp Vault
     - Dedikované reseni pro spravovani secretu
     - Audit log, rotace, fine-grained access

  4. NIKDY nedavej plaintext hesla do:
     - YAML souboru v gitu
     - Dockerfilu
     - ENV v docker-compose.yml v gitu
     - Logu aplikace
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: Kubectl prikazy
# ══════════════════════════════════════════════════════════════

print("=== Kubectl prikazy pro ConfigMap a Secret ===\n")

prikazy = [
    ("kubectl create configmap app-config --from-literal=KEY=value", "Rychle vytvoreni"),
    ("kubectl create configmap app-config --from-file=config.properties", "Ze souboru"),
    ("kubectl apply -f configmap.yaml",  "Ze YAML souboru"),
    ("kubectl get configmaps",           "Zobraz vsechny ConfigMaps"),
    ("kubectl describe cm app-config",   "Detaily ConfigMap"),
    ("kubectl get cm app-config -o yaml","YAML ConfigMap"),
    ("kubectl create secret generic app-secret --from-literal=PASS=heslo", "Rychle vytvoreni"),
    ("kubectl get secrets",              "Zobraz vsechny Secrets"),
    ("kubectl get secret app-secret -o jsonpath='{.data.PASS}' | base64 -d", "Ziskej hodnotu"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo
# ══════════════════════════════════════════════════════════════

DEMO_CM = """\
apiVersion: v1
kind: ConfigMap
metadata:
  name: demo-config
data:
  POZDRAV: "Ahoj z ConfigMap!"
  BARVA: "modra"
"""

DEMO_SECRET = """\
apiVersion: v1
kind: Secret
metadata:
  name: demo-secret
stringData:
  HESLO: "tajne123"
"""

DEMO_POD = """\
apiVersion: v1
kind: Pod
metadata:
  name: demo-config-pod
spec:
  restartPolicy: Never
  containers:
    - name: demo
      image: alpine
      command: ["sh", "-c", "echo Pozdrav=$POZDRAV, Barva=$BARVA, Heslo=$HESLO && sleep 2"]
      envFrom:
        - configMapRef:
            name: demo-config
        - secretRef:
            name: demo-secret
"""

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("=== Cluster neni dostupny — spust minikube start ===\n")
    else:
        print("=== Demo: ConfigMap + Secret → Pod ===\n")

        for fname, content in [("demo-cm.yaml", DEMO_CM),
                                ("demo-secret.yaml", DEMO_SECRET),
                                ("demo-pod.yaml", DEMO_POD)]:
            Path(f"/tmp/{fname}").write_text(content)
            r = subprocess.run(["kubectl", "apply", "-f", f"/tmp/{fname}"],
                              capture_output=True, text=True)
            print(f"  {r.stdout.strip()}")

        import time; time.sleep(5)

        print("\n$ kubectl logs demo-config-pod")
        r = subprocess.run(["kubectl", "logs", "demo-config-pod"],
                          capture_output=True, text=True)
        print(f"  {r.stdout.strip()}")

        for res in ["pod/demo-config-pod", "configmap/demo-config", "secret/demo-secret"]:
            subprocess.run(["kubectl", "delete", res], capture_output=True)
        print("\n  ✓ Vycisteno")

        for fname in ["demo-cm.yaml", "demo-secret.yaml", "demo-pod.yaml"]:
            Path(f"/tmp/{fname}").unlink(missing_ok=True)

else:
    print("=== kubectl neni dostupny ===\n")
    print("  Spust: minikube start")


print("\n=== Hotovo! Dalsi lekce: Ingress — brana z internetu ===")

# TVOJE ULOHA:
# 1. Vytvor ConfigMap s hodnotami DB_HOST a LOG_LEVEL
# 2. Vytvor Secret se stringData (heslo a api klic)
# 3. Pouzij obe v Deploymentu pres envFrom a aplikuj
# 4. Precti hodnotu ze Secretu pres kubectl

# RESENI:
# 1. kubectl create configmap moje-config --from-literal=DB_HOST=localhost --from-literal=LOG_LEVEL=info
# 2. kubectl create secret generic moje-hesla --from-literal=DB_PASSWORD=tajne --from-literal=API_KEY=abc123
# 3. v spec.containers: envFrom: [{configMapRef: {name: moje-config}}, {secretRef: {name: moje-hesla}}]
# 4. kubectl get secret moje-hesla -o jsonpath='{.data.DB_PASSWORD}' | base64 -d
