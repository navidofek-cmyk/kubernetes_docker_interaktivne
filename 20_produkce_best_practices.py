"""
LEKCE 20: Produkce — best practices
=====================================
Tvoje aplikace bezi v Kubernetes. Skvele!
Ale je pripravena na realny provoz?

Tato lekce shrnuje vse co potrebujes
pred nasazenim do produkce:
  - Resource limits a requests
  - Pod Disruption Budget
  - Network Policy
  - Security Context
  - Produkce checklist

Obtiznost: ⭐⭐⭐⭐⭐
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
# CAST 1: Resource Requests a Limits
# ══════════════════════════════════════════════════════════════

print("=== Resource Requests a Limits ===\n")

print(textwrap.dedent("""\
  Requests = garantovane zdroje (Scheduler je potrebuje pro umisteni)
  Limits   = maximalni zdroje (prekazeni = throttling/OOMKill)

  CPU:
    1    = 1 jadro = 1000m (millicores)
    100m = 0.1 jadra = 10% jednoho jadra
    Prekroceni limitu = throttling (zpomaleni, ne kill)

  Pamet:
    128Mi = 128 mebibytes
    1Gi   = 1 gibibyte
    Prekroceni limitu = OOMKill (kontejner je zabit a restartovan!)

  Pravidla:
    - Vzdy nastavuj REQUESTS (Scheduler to potrebuje)
    - Nastavuj LIMITS pro pamet (OOMKill je lepsi nez OOM celeho Nodu)
    - CPU limit je volitelny — throttling je lepsi nez kill
    - Requests <= Limits

  Quality of Service (QoS):
    Guaranteed  — requests == limits (nejlepsi priorita)
    Burstable   — requests < limits
    BestEffort  — bez requests/limits (prvni zabit pri nedostatku RAM)
"""))

RESOURCES_YAML = """\
resources:
  requests:
    cpu: "100m"      ← garantovano 0.1 jadra
    memory: "128Mi"  ← garantovano 128 MB RAM
  limits:
    cpu: "500m"      ← max 0.5 jadra (throttling pri prekazeni)
    memory: "256Mi"  ← max 256 MB RAM (OOMKill pri prekazeni!)
"""
print(RESOURCES_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 2: ResourceQuota a LimitRange
# ══════════════════════════════════════════════════════════════

print("=== ResourceQuota a LimitRange ===\n")

QUOTA_YAML = """\
# ResourceQuota — max zdroje pro cely namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "4"         ← vsechny Pody dohromady max 4 jadra
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"                ← max 50 Podu v namespace
    services: "20"
    persistentvolumeclaims: "10"
"""

LIMITRANGE_YAML = """\
# LimitRange — default a min/max pro kazdy kontejner
apiVersion: v1
kind: LimitRange
metadata:
  name: container-limits
  namespace: production
spec:
  limits:
    - type: Container
      default:              ← pokud kontejner nema limits, pouzij tohle
        cpu: "500m"
        memory: "256Mi"
      defaultRequest:       ← pokud kontejner nema requests, pouzij tohle
        cpu: "100m"
        memory: "128Mi"
      max:                  ← nikdo nesmi chtit vic
        cpu: "2"
        memory: "2Gi"
      min:                  ← nikdo nesmi chtit mene
        cpu: "50m"
        memory: "32Mi"
"""

print(QUOTA_YAML)
print(LIMITRANGE_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 3: Pod Disruption Budget
# ══════════════════════════════════════════════════════════════

print("=== Pod Disruption Budget (PDB) ===\n")

print(textwrap.dedent("""\
  Problem: Kubernetes Node upgrade → Node se vypne → vsechny Pody presunuty.
  Pokud mas 3 Pody a vsechny jsou na jednom Nodu → kratky vypadek.

  PDB garantuje ze vzdy bezi minimalni pocet Podu
  i behem "voluntary disruptions" (upgrade Nodu, drain...).
"""))

PDB_YAML = """\
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: moje-app-pdb
spec:
  minAvailable: 2          ← vzdy musi byt dostupne aspon 2 Pody
  # nebo:
  # maxUnavailable: 1      ← max 1 Pod muze byt nedostupny
  selector:
    matchLabels:
      app: moje-app

# Priklad: mas 3 repliky
# Bez PDB: Node drain muze zastavit vsechny 3 najednou
# S PDB (minAvailable: 2): drain zastavi max 1 Pod najednou
"""
print(PDB_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 4: Network Policy
# ══════════════════════════════════════════════════════════════

print("=== Network Policy — firewall pro Pody ===\n")

print(textwrap.dedent("""\
  Default: vsechny Pody v clusteru mohou komunikovat navzajem.
  To je nebezpecne! Pokud jednu sluzbu hacknou, maji pristup ke vsemu.

  Network Policy = firewall pravidla na urovni Podu.
  Vyzaduje CNI plugin s podporou (Calico, Cilium, Weave...).
"""))

NETPOL_YAML = """\
# Povol jen specificke spojeni: web → api → db
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: postgres          ← tato pravidla plati pro Pody s timto labelem
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api       ← jen Pody s labelem app=api smejí pristoupit
      ports:
        - protocol: TCP
          port: 5432
  egress:
    - {}                     ← povol vesker odchozi provoz (DNS atd.)

---
# Deny-all jako zaklad (whitelist pristup)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  podSelector: {}            ← plati pro vsechny Pody
  policyTypes:
    - Ingress
    - Egress
  # Zadna pravidla = vsechno zakazano
"""
print(NETPOL_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 5: Security Context
# ══════════════════════════════════════════════════════════════

print("=== Security Context — bezpecnost kontejneru ===\n")

SECURITY_YAML = """\
spec:
  securityContext:             ← na urovni Podu
    runAsNonRoot: true         ← nikdy nespoustej jako root!
    runAsUser: 1000            ← UID uzivatele
    runAsGroup: 1000           ← GID skupiny
    fsGroup: 1000              ← GID pro volumes
    seccompProfile:
      type: RuntimeDefault     ← omez systemova volani

  containers:
    - name: app
      securityContext:         ← na urovni kontejneru
        allowPrivilegeEscalation: false  ← zakazat sudo/setuid
        readOnlyRootFilesystem: true     ← filesystem je read-only!
        capabilities:
          drop: ["ALL"]        ← zahoď vsechna Linux capabilities
          add: ["NET_BIND_SERVICE"]  ← pridej jen co opravdu potrebujes
"""
print(SECURITY_YAML)

print(textwrap.dedent("""\
  Proc readOnlyRootFilesystem?
    Pokud utocnik spusti kod v kontejneru, nemuze zapsat
    malware na disk. Legitimni zapis → pouzij Volume.

  Proc drop ALL capabilities?
    Linux capabilities jsou mini-superpravneni.
    Aplikace je nepotrebuje. Zahoď vsechna, pridej jen nutna.
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Produkce checklist
# ══════════════════════════════════════════════════════════════

print("=== Produkce checklist ===\n")

checklist = [
    # Resources
    ("✅ Resources", [
        "Nastaveny requests a limits pro vsechny kontejnery",
        "ResourceQuota a LimitRange pro namespace",
    ]),
    # Dostupnost
    ("✅ Dostupnost", [
        "replicas >= 3 pro kriticke sluzby",
        "Pod Disruption Budget nastaven",
        "Pody rozmisteny na vice nodech (topologySpreadConstraints)",
        "ReadinessProbe a LivenessProbe nakonfigurovany",
        "Rolling update strategie (ne Recreate)",
    ]),
    # Bezpecnost
    ("✅ Bezpecnost", [
        "runAsNonRoot: true",
        "readOnlyRootFilesystem: true",
        "allowPrivilegeEscalation: false",
        "capabilities drop ALL",
        "Network Policy (deny-all + whitelist)",
        "Secrets spravovane mimo git (Vault, Sealed Secrets)",
        "RBAC — kazda app ma vlastni SA s min. opravnenimi",
        "Image scan (Trivy, Snyk) v CI/CD",
    ]),
    # Observabilita
    ("✅ Observabilita", [
        "Aplikace exponuje /metrics endpoint",
        "ServiceMonitor nastaven",
        "Logy jdou na stdout/stderr (ne do souboru)",
        "Alerting nastaven pro kritické metriky",
        "Distributed tracing (OpenTelemetry)",
    ]),
    # Deployment
    ("✅ Deployment", [
        "Image tag je konkretni verze (ne latest)",
        "GitOps — cluster odpovida gitu",
        "Rollback otestovan",
        "Disaster recovery plan",
    ]),
]

for sekce, body in checklist:
    print(f"  {sekce}")
    for bod in body:
        print(f"    □ {bod}")
    print()


# ══════════════════════════════════════════════════════════════
# CAST 7: Kompletni "produkce-ready" Deployment
# ══════════════════════════════════════════════════════════════

print("=== Produkce-ready Deployment ===\n")

PROD_DEPLOYMENT = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: moje-app
  namespace: production
  annotations:
    kubernetes.io/change-cause: "Release v1.2.3"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: moje-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: moje-app
        version: v1.2.3
    spec:
      serviceAccountName: moje-app    ← vlastni SA, ne default
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      topologySpreadConstraints:      ← rozmis Pody na vice nodech
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: moje-app
      containers:
        - name: app
          image: ghcr.io/tomas/moje-app:v1.2.3   ← konkretni tag!
          ports:
            - containerPort: 8000
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secret
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 20
          volumeMounts:
            - name: tmp              ← write-only tmp dir (RO filesystem)
              mountPath: /tmp
            - name: cache
              mountPath: /app/cache
      volumes:
        - name: tmp
          emptyDir: {}
        - name: cache
          emptyDir: {}
      terminationGracePeriodSeconds: 60   ← cas na graceful shutdown
"""
print(PROD_DEPLOYMENT)


print("=" * 60)
print("GRATULACE! Jsi Kubernetes hrdina! ☸️")
print("=" * 60)
print(textwrap.dedent("""
  Zvladl jsi:
  Docker:       kontejnery, Dockerfile, Compose, Hub
  Kubernetes:   Pod, Deployment, Service, Ingress, Helm
  Pokrocile:    StatefulSet, RBAC, Monitoring, GitOps
  Produkce:     Resources, PDB, Network Policy, Security

  Co dal?
    - Service Mesh (Istio, Linkerd) — mTLS, traffic management
    - Kubernetes Operators — vlastni CRD a controller
    - Multi-cluster management (Fleet, Argo ApplicationSet)
    - eBPF networking (Cilium) — kernel-level observabilita
    - Chaos Engineering (Chaos Monkey, Litmus)
"""))

# TVOJE ULOHA:
# 1. Vezmi deployment z lekce 10 a pridej security context (runAsNonRoot, readOnly filesystem)
# 2. Nastav ResourceQuota pro namespace: max 2 CPU, 1Gi RAM
# 3. Vytvor Network Policy ktera dovoli jen port 8000 dovnitr
# 4. Zkontroluj checklist — co ze tveho projektu chybi?

# RESENI:
# 1. pod spec: securityContext: {runAsNonRoot: true, runAsUser: 1000}; container securityContext: {allowPrivilegeEscalation: false, readOnlyRootFilesystem: true, capabilities: {drop: ["ALL"]}}
# 2. kubectl create quota moje-quota --hard=requests.cpu=2,requests.memory=1Gi,limits.cpu=4,limits.memory=2Gi -n default
# 3. viz NETPOL_YAML vyse, zmen port na 8000 a selector na tvuj app label
# 4. Projdi checklist a oznac co mas / nemas — to je tvuj TODO list
