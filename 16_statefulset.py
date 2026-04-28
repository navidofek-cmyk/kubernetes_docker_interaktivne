"""
LEKCE 16: StatefulSet — databaze v Kubernetes
===============================================
Deployment je skvely pro bezstavove aplikace (web, API).
Ale databaze jsou jine — kazda instance ma sve vlastni data,
sve jmeno, svuj storage. Nelze je libovolne vyrazit a nahradit.

StatefulSet garantuje:
  - stabilni jmeno Podu (db-0, db-1, db-2 — ne nahodny hash)
  - stabilni storage (kazdy Pod ma svuj PVC)
  - poradi startu a zastavovani

Naucis se:
  - rozdil Deployment vs StatefulSet
  - Persistent Volume a PersistentVolumeClaim
  - StorageClass
  - priklad PostgreSQL a Redis Sentinel

Obtiznost: ⭐⭐⭐⭐
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
# CAST 1: Deployment vs StatefulSet
# ══════════════════════════════════════════════════════════════

print("=== Deployment vs StatefulSet ===\n")

print(textwrap.dedent("""\
  Deployment:
    - Pody jsou zamenitelne (cattle, ne pets)
    - Jmena: web-7d4f9b-xkpqr, web-7d4f9b-mnbvc (nahodna)
    - Sdileji storage nebo nemaji zadnou
    - Mazani v libovolnem poradi

  StatefulSet:
    - Pody maji identitu (db-0, db-1, db-2)
    - Kazdy Pod ma vlastni PersistentVolumeClaim
    - Spousteni: db-0 → db-1 → db-2 (v poradi)
    - Mazani: db-2 → db-1 → db-0 (obracene)
    - db-0 vzdy zustane db-0 (i po restartu)

  Kdy pouzit StatefulSet:
    ✅ Databaze (PostgreSQL, MySQL, MongoDB)
    ✅ Distribuovane systemy (Kafka, ZooKeeper, etcd)
    ✅ Aplikace kde zalezi na identite uzlu
    ✅ Redis Sentinel / Cluster
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: PersistentVolume a PersistentVolumeClaim
# ══════════════════════════════════════════════════════════════

print("=== PersistentVolume (PV) a PersistentVolumeClaim (PVC) ===\n")

print(textwrap.dedent("""\
  PersistentVolume (PV):
    - Kus uloziste v clusteru
    - Pripravuje ho admin nebo StorageClass
    - Existuje nezavisle na Podech

  PersistentVolumeClaim (PVC):
    - Zadost Podu o uloziste ("chci 10Gi SSD")
    - Kubernetes najde vhodny PV a "svaze" je
    - PVC je v namespacu, PV je globalni

  StorageClass:
    - Definuje typ uloziste (SSD, HDD, NFS...)
    - Umoznuje dynamicke provisioning (PVC → PV auto)

  V cloudu:
    AWS EBS, GCP Persistent Disk, Azure Disk
    → StorageClass je automaticky nastavena

  Vizualizace:
    Pod → PVC ("chci 10Gi") → PV (konkretni disk) → fyzicky disk
"""))

PVC_YAML = """\
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce        ← jen jeden Pod muze psat (block storage)
  storageClassName: standard  ← typ storage (standard = minikube default)
  resources:
    requests:
      storage: 10Gi        ← chci 10 GB
"""

print("PVC priklad:")
print(PVC_YAML)

print(textwrap.dedent("""\
  AccessModes:
    ReadWriteOnce (RWO)  — jen jeden Node muze psat (block: EBS, GCP PD)
    ReadWriteMany (RWX)  — vice Nodu muze psat (NFS, CephFS, EFS)
    ReadOnlyMany  (ROX)  — vice Nodu muze cist
"""))


# ══════════════════════════════════════════════════════════════
# CAST 3: PostgreSQL StatefulSet
# ══════════════════════════════════════════════════════════════

print("=== PostgreSQL StatefulSet ===\n")

POSTGRES_SS = """\
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres          ← headless service jmeno (viz nize)
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: data              ← jmeno volume (shoduje se s VCT)
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 10
            periodSeconds: 5

  volumeClaimTemplates:           ← automaticky vytvori PVC pro kazdy Pod
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: standard
        resources:
          requests:
            storage: 5Gi

---
# Headless Service — pro DNS uvnitr clusteru
# postgres-0.postgres.default.svc.cluster.local
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None              ← headless = zadna ClusterIP, jen DNS
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432

---
# ClusterIP Service pro klienty
apiVersion: v1
kind: Service
metadata:
  name: postgres-svc
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
"""

print(POSTGRES_SS)


# ══════════════════════════════════════════════════════════════
# CAST 4: Headless Service a DNS
# ══════════════════════════════════════════════════════════════

print("=== Headless Service — DNS pro StatefulSet ===\n")

print(textwrap.dedent("""\
  Normalni Service → jedna IP (load balancer)
  Headless Service (clusterIP: None) → DNS pro kazdy Pod zvlast

  StatefulSet "postgres" s headless service "postgres":
    postgres-0.postgres.default.svc.cluster.local → IP podu 0
    postgres-1.postgres.default.svc.cluster.local → IP podu 1
    postgres-2.postgres.default.svc.cluster.local → IP podu 2

  Proc to potrebujeme?
    PostgreSQL primary-replica replikace:
      - primary: postgres-0 (cte i pise)
      - replicas: postgres-1, postgres-2 (jen cte)
    Replica se musi pripojit na KONKRETNI primary (postgres-0),
    ne na nahodny load-balanced endpoint.
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: Prikazy
# ══════════════════════════════════════════════════════════════

print("=== Prikazy pro StatefulSet ===\n")

prikazy = [
    ("kubectl get statefulsets",              "Zobraz vsechny StatefulSety"),
    ("kubectl get pvc",                        "Zobraz PersistentVolumeClaims"),
    ("kubectl get pv",                         "Zobraz PersistentVolumes"),
    ("kubectl describe pvc postgres-data-0",   "Detail PVC pro postgres-0"),
    ("kubectl exec -it postgres-0 -- psql -U postgres", "Psql v postgres-0"),
    ("kubectl scale sts postgres --replicas=3","Skaluj StatefulSet"),
    ("kubectl delete pod postgres-0",          "Restart postgres-0 (pricte svuj PVC)"),
    ("kubectl get storageclass",               "Dostupne StorageClassy"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo
# ══════════════════════════════════════════════════════════════

DEMO_SS = """\
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
stringData:
  password: "tajne123"
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: demo-postgres
spec:
  serviceName: demo-postgres
  replicas: 1
  selector:
    matchLabels:
      app: demo-postgres
  template:
    metadata:
      labels:
        app: demo-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: demo-postgres
spec:
  clusterIP: None
  selector:
    app: demo-postgres
  ports:
    - port: 5432
"""

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("=== Cluster neni dostupny — spust minikube start ===\n")
    else:
        print("=== Demo: PostgreSQL StatefulSet ===\n")

        manifest = Path("/tmp/demo-statefulset.yaml")
        manifest.write_text(DEMO_SS)

        r = subprocess.run(["kubectl", "apply", "-f", str(manifest)],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        import time; time.sleep(5)

        print("\n$ kubectl get statefulset,pod,pvc")
        r = subprocess.run(["kubectl", "get", "statefulset,pod,pvc",
                           "--field-selector=metadata.namespace=default",
                           "-l", "app=demo-postgres"],
                          capture_output=True, text=True)
        print(r.stdout.strip() or "(spousti se...)")

        print("\n  ✓ Vsimni si ze PVC ma jmeno 'data-demo-postgres-0'")
        print("  ✓ Po smazani a obnove Podu PVC zustane!")

        print("\n$ kubectl delete -f manifest + PVC")
        subprocess.run(["kubectl", "delete", "-f", str(manifest)],
                      capture_output=True)
        subprocess.run(["kubectl", "delete", "pvc", "data-demo-postgres-0"],
                      capture_output=True)
        print("  ✓ Vycisteno (PVC je treba smazat rucne — ochrana dat!)")
        manifest.unlink(missing_ok=True)
else:
    print("=== kubectl neni dostupny ===\n")


print("\n=== Hotovo! Dalsi lekce: RBAC — kdo smi co delat ===")

# TVOJE ULOHA:
# 1. Nasad PostgreSQL StatefulSet (viz DEMO_SS)
# 2. Zkontroluj ze PVC bylo automaticky vytvoreno
# 3. Smaz Pod postgres-0 — co se stane s PVC?
# 4. Spust novy Pod — pripoji se na stejny PVC s daty?

# RESENI:
# 1. kubectl apply -f statefulset.yaml
# 2. kubectl get pvc   (uvidi data-demo-postgres-0)
# 3. kubectl delete pod demo-postgres-0   →   PVC zustane, K8s spusti novy Pod
# 4. Novy Pod (demo-postgres-0) se pripoji na stejny PVC — data jsou tam!
