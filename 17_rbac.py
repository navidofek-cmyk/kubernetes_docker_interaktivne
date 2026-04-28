"""
LEKCE 17: RBAC — kdo smi co delat
====================================
V produkci nechces aby kazdy mohl smazat deployment
nebo cist Secret s hesly.

RBAC (Role-Based Access Control) ridi:
  KDO (ServiceAccount / uzivatel)
  CO SIMI (verbs: get, list, create, delete...)
  NA CEM (resources: pods, secrets, deployments...)

Naucis se:
  - Role a ClusterRole
  - RoleBinding a ClusterRoleBinding
  - ServiceAccount pro aplikace
  - Princip nejmensich opravneni

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
# CAST 1: Koncepty RBAC
# ══════════════════════════════════════════════════════════════

print("=== Koncepty RBAC ===\n")

schema = """\
KDO?                      CO SIMI?              NA CEM?
─────────────────────     ──────────────────    ──────────────────────
ServiceAccount            Role                  v namespace
  - app bezi v Podu       verbs:                  pods, services,
  - ma jmeno + namespace    get, list, watch       deployments,
                             create, update,        secrets, configmaps
User (clovek)              delete, patch
  - kubectl pouzivatel    ClusterRole           globalne
                          verbs: same           + nodes, namespaces,
Group                                             persistentvolumes
  - tym lidi

Propojeni pres Binding:
  RoleBinding        = Role       + Subject → v namespace
  ClusterRoleBinding = ClusterRole + Subject → vsude
"""
print(schema)


# ══════════════════════════════════════════════════════════════
# CAST 2: Role a ClusterRole
# ══════════════════════════════════════════════════════════════

print("=== Role vs ClusterRole ===\n")

ROLE_YAML = """\
# Role — platna jen v jednom namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
  - apiGroups: [""]          ← "" = core API (pods, services, secrets...)
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]

  - apiGroups: ["apps"]      ← apps API (deployments, statefulsets...)
    resources: ["deployments"]
    verbs: ["get", "list"]
"""

CLUSTER_ROLE_YAML = """\
# ClusterRole — platna v celem clusteru
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
  - apiGroups: [""]
    resources: ["nodes", "namespaces"]
    verbs: ["get", "list", "watch"]
"""

print(ROLE_YAML)
print(CLUSTER_ROLE_YAML)

print("Dostupne verbs:")
verbs = [
    ("get",              "Ziskat jeden objekt"),
    ("list",             "Vylistovat vsechny objekty"),
    ("watch",            "Sledovat zmeny v realnem case"),
    ("create",           "Vytvorit novy objekt"),
    ("update",           "Prepsat existujici objekt"),
    ("patch",            "Upravit cast objektu"),
    ("delete",           "Smazat objekt"),
    ("deletecollection", "Smazat vice objektu"),
    ("*",                "Vsechno (jen pro adminy!)"),
]
for verb, popis in verbs:
    print(f"  {verb:<20} — {popis}")
print()


# ══════════════════════════════════════════════════════════════
# CAST 3: RoleBinding
# ══════════════════════════════════════════════════════════════

print("=== RoleBinding — propojeni Role se subjektem ===\n")

ROLEBINDING_YAML = """\
# Dej 'pod-reader' roli ServiceAccountu 'moje-app'
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: moje-app-pod-reader
  namespace: production
subjects:
  - kind: ServiceAccount
    name: moje-app
    namespace: production
  # Nebo uzivatel:
  # - kind: User
  #   name: tomas@firma.cz
  # Nebo skupina:
  # - kind: Group
  #   name: devs
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
"""
print(ROLEBINDING_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 4: ServiceAccount pro aplikaci
# ══════════════════════════════════════════════════════════════

print("=== ServiceAccount — identita pro aplikaci ===\n")

print(textwrap.dedent("""\
  Kazdy Pod automaticky dostane 'default' ServiceAccount.
  Ten ma typicky zadna opravneni — to je dobre!

  Pokud tvoje aplikace potrebuje mluvit s K8s API
  (napr. operator, CI runner, monitoring agent),
  vytvor vlastni ServiceAccount s minimalnimi opravnenimi.
"""))

SA_KOMPLETNI = """\
# 1. ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: moje-app
  namespace: production

---
# 2. Role s potrebnymi opravnenimi
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: moje-app-role
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["moje-app-config"]   ← jen TENTO konkretni Secret!
    verbs: ["get"]

---
# 3. Binding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: moje-app-binding
  namespace: production
subjects:
  - kind: ServiceAccount
    name: moje-app
    namespace: production
roleRef:
  kind: Role
  name: moje-app-role
  apiGroup: rbac.authorization.k8s.io

---
# 4. Deployment pouziva ServiceAccount
apiVersion: apps/v1
kind: Deployment
metadata:
  name: moje-app
  namespace: production
spec:
  template:
    spec:
      serviceAccountName: moje-app    ← pouzij tento SA (ne default)
      automountServiceAccountToken: true
      containers:
        - name: app
          image: moje-app:v1.0
"""
print(SA_KOMPLETNI)


# ══════════════════════════════════════════════════════════════
# CAST 5: Auditovani a debug
# ══════════════════════════════════════════════════════════════

print("=== Debug RBAC — kdo smi co ===\n")

prikazy = [
    ("kubectl auth can-i get pods",
     "Smi aktualni uzivatel cist Pody?"),
    ("kubectl auth can-i delete secrets --as=system:serviceaccount:prod:moje-app",
     "Smi SA 'moje-app' mazat Secrets?"),
    ("kubectl auth can-i '*' '*' --all-namespaces",
     "Je aktualni uzivatel cluster-admin?"),
    ("kubectl get rolebindings,clusterrolebindings -A | grep moje-app",
     "Vsechny bindiny pro moje-app"),
    ("kubectl describe clusterrolebinding cluster-admin",
     "Kdo je cluster-admin?"),
    ("kubectl api-resources --verbs=list --namespaced=true",
     "Vsechny namespacovane resources"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 6: Vychozi ClusterRole
# ══════════════════════════════════════════════════════════════

print("=== Vychozi ClusterRole ===\n")

print(textwrap.dedent("""\
  Kubernetes ma built-in ClusterRole pro bezne pripady:

  cluster-admin    — vsechno (nebezpecne! jen pro adminy)
  admin            — vsechno v namespace (delegovatelne)
  edit             — cte + pise, ale ne RBAC a ResourceQuota
  view             — jen cteni (pody, services, config...)

  Priklad — dej 'edit' prava tymu na namespace 'dev':
    kubectl create rolebinding dev-edit \\
      --clusterrole=edit \\
      --group=devs \\
      --namespace=dev
"""))


# ══════════════════════════════════════════════════════════════
# CAST 7: Demo
# ══════════════════════════════════════════════════════════════

DEMO_RBAC = """\
apiVersion: v1
kind: ServiceAccount
metadata:
  name: demo-reader
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-lister
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: demo-reader-binding
subjects:
  - kind: ServiceAccount
    name: demo-reader
    namespace: default
roleRef:
  kind: Role
  name: pod-lister
  apiGroup: rbac.authorization.k8s.io
"""

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("=== Cluster neni dostupny ===\n")
    else:
        print("=== Demo: ServiceAccount + Role + RoleBinding ===\n")

        manifest = Path("/tmp/demo-rbac.yaml")
        manifest.write_text(DEMO_RBAC)
        r = subprocess.run(["kubectl", "apply", "-f", str(manifest)],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        print("\n$ kubectl auth can-i list pods --as=system:serviceaccount:default:demo-reader")
        r = subprocess.run(
            ["kubectl", "auth", "can-i", "list", "pods",
             "--as=system:serviceaccount:default:demo-reader"],
            capture_output=True, text=True
        )
        print(f"  Muze listovat Pody: {r.stdout.strip()}")

        print("$ kubectl auth can-i delete pods --as=system:serviceaccount:default:demo-reader")
        r = subprocess.run(
            ["kubectl", "auth", "can-i", "delete", "pods",
             "--as=system:serviceaccount:default:demo-reader"],
            capture_output=True, text=True
        )
        print(f"  Muze mazat Pody: {r.stdout.strip()}")

        subprocess.run(["kubectl", "delete", "-f", str(manifest)], capture_output=True)
        print("\n  ✓ Vycisteno")
        manifest.unlink(missing_ok=True)
else:
    print("=== kubectl neni dostupny ===\n")


print("\n=== Hotovo! Dalsi lekce: Monitoring — Prometheus + Grafana ===")

# TVOJE ULOHA:
# 1. Vytvor ServiceAccount 'muj-agent' s Role ktera smi jen 'get' a 'list' Pody
# 2. Over ze agent SIMI cist Pody
# 3. Over ze agent NESMI mazat Pody
# 4. Zkus pridat opravneni na Secrets — co se stane?

# RESENI:
# 1. kubectl apply -f sa.yaml (viz SA_KOMPLETNI vyse, zjednodusene)
# 2. kubectl auth can-i list pods --as=system:serviceaccount:default:muj-agent   → yes
# 3. kubectl auth can-i delete pods --as=system:serviceaccount:default:muj-agent  → no
# 4. Pridej do rules: {apiGroups:[""],resources:["secrets"],verbs:["get"]} → kubectl apply znovu → can-i get secrets → yes
