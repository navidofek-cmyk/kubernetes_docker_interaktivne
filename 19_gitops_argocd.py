"""
LEKCE 19: GitOps a ArgoCD — git jako zdroj pravdy
===================================================
Klasicky deployment: clovek spusti kubectl apply.
Problem: kdo spustil co? Kdyz? Jak se vratit zpet?

GitOps princip:
  Git repozitar = jediny zdroj pravdy pro stav clusteru
  Automaticky agent sleduje git a synchronizuje cluster

ArgoCD je GitOps operator pro Kubernetes:
  - sleduje git repo
  - kdyz se zmeni YAML → automaticky nasadi do K8s
  - kdyz se cluster odlisi od gitu → upozorni nebo opraví

Naucis se:
  - nainstalovat ArgoCD
  - vytvorit Application
  - auto-sync a manual sync
  - rollback pres git revert

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
# CAST 1: Co je GitOps?
# ══════════════════════════════════════════════════════════════

print("=== Co je GitOps? ===\n")

print(textwrap.dedent("""\
  Tradicni CI/CD:
    Kod zmena → CI build → CI pushne do K8s
                           (CI ma kubeconfig s opravnenimi)
    Problem: clovek muze taky rucne zmenit cluster
             cluster a git se rozchazeji (drift)

  GitOps:
    Kod zmena → CI build → push image → uprav YAML v gitu
    ArgoCD: "Git se zmenil → synchronizuj cluster"
    Cluster = co je v gitu, nic vic nic min

  Vyhody:
    ✅ Audit trail: kazda zmena = git commit (kdo, kdy, co)
    ✅ Rollback = git revert (jednoduche!)
    ✅ Drift detection: ArgoCD ti rekne kdyz nekdo zmenil
       cluster rucne bez gitu
    ✅ Pull model: cluster si tahne z gitu (ne push)
       → CI nepotrebuje kubeconfig s write opravnenimi
"""))

schema = """\
Developer                Git repo               ArgoCD              Kubernetes
    │                       │                      │                     │
    │── git push ──────────▶│                      │                     │
    │                       │── webhook/poll ──────▶│                     │
    │                       │                      │── kubectl apply ───▶│
    │                       │                      │                     │
    │                       │             [cluster bezi jako v gitu]      │
"""
print(schema)


# ══════════════════════════════════════════════════════════════
# CAST 2: Instalace ArgoCD
# ══════════════════════════════════════════════════════════════

print("=== Instalace ArgoCD ===\n")

print(textwrap.dedent("""\
  Moznost 1 — Helm (doporuceno):
    helm repo add argo https://argoproj.github.io/argo-helm
    helm repo update
    helm install argocd argo/argo-cd \\
      --namespace argocd \\
      --create-namespace \\
      --set server.extraArgs[0]=--insecure   # pro lokalni vyvoj bez TLS

  Moznost 2 — Official manifest:
    kubectl create namespace argocd
    kubectl apply -n argocd \\
      -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

  Pristup k UI:
    kubectl port-forward svc/argocd-server -n argocd 8080:443
    → https://localhost:8080

  Heslo admina:
    kubectl -n argocd get secret argocd-initial-admin-secret \\
      -o jsonpath='{.data.password}' | base64 -d

  ArgoCD CLI:
    argocd login localhost:8080
    argocd app list
"""))


# ══════════════════════════════════════════════════════════════
# CAST 3: Application — srdce ArgoCD
# ══════════════════════════════════════════════════════════════

print("=== ArgoCD Application ===\n")

APP_YAML = """\
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: moje-app
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/tomas/moje-k8s-repo.git
    targetRevision: main           ← vetev nebo tag
    path: k8s/production           ← slozka s YAML manifesty

  destination:
    server: https://kubernetes.default.svc   ← lokalni cluster
    namespace: production

  syncPolicy:
    automated:                     ← automaticka synchronizace
      prune: true                  ← smaz objekty ktere nejsou v gitu
      selfHeal: true               ← oprav manualni zmeny v clusteru
    syncOptions:
      - CreateNamespace=true       ← vytvor namespace pokud neexistuje
    retry:
      limit: 3
      backoff:
        duration: 5s
        maxDuration: 3m
"""
print(APP_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 4: Sync stavy
# ══════════════════════════════════════════════════════════════

print("=== Sync stavy ===\n")

print(textwrap.dedent("""\
  Synced     — cluster odpovida gitu ✅
  OutOfSync  — cluster se lisi od gitu (nekdo zmenil rucne?)
  Unknown    — ArgoCD nemuze porovnat

  Health stavy:
    Healthy    — vsechno bezi jak ma ✅
    Progressing — update probiha...
    Degraded   — neco selhava (Pody crashuji atd.)
    Missing    — objekt chybi v clusteru

  Prikazy:
    argocd app get moje-app              ← detail aplikace
    argocd app sync moje-app             ← rucni sync
    argocd app diff moje-app             ← co se zmeni pri syncu
    argocd app history moje-app          ← historie deploymentu
    argocd app rollback moje-app 3       ← rollback na revizi 3
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: Typicka struktura repo
# ══════════════════════════════════════════════════════════════

print("=== Typicka struktura GitOps repo ===\n")

print(textwrap.dedent("""\
  Varianta 1 — monorepo (kod + infra dohromady):
    moje-app/
    ├── src/                 ← zdrojovy kod
    ├── Dockerfile
    └── k8s/
        ├── base/            ← zakladni manifesty (Kustomize)
        │   ├── deployment.yaml
        │   ├── service.yaml
        │   └── kustomization.yaml
        └── overlays/
            ├── dev/         ← overrides pro dev
            └── prod/        ← overrides pro produkci

  Varianta 2 — oddelene repo pro infra (doporuceno pro vetsi tymy):
    moje-app-repo/           ← jen kod + CI (build image)
    moje-app-k8s-repo/       ← jen K8s manifesty (ArgoCD sleduje toto)
        ├── apps/
        │   ├── moje-app.yaml   ← ArgoCD Application
        │   └── monitoring.yaml
        └── manifests/
            ├── production/
            └── staging/

  CI/CD flow:
    1. git push → CI build → docker push :sha-abc123
    2. CI automaticky updatuje image tag v k8s repo:
       sed -i 's|image:.*|image: ghcr.io/tomas/app:sha-abc123|' manifests/prod/deploy.yaml
       git commit -m "chore: update image to sha-abc123"
    3. ArgoCD detekuje zmenu → synchronizuje cluster
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Kustomize
# ══════════════════════════════════════════════════════════════

print("=== Kustomize — overrides bez Helmu ===\n")

BASE_KUSTOMIZE = """\
# k8s/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
"""

PROD_KUSTOMIZE = """\
# k8s/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base

patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
    target:
      kind: Deployment
      name: moje-app

images:
  - name: moje-app
    newTag: v1.2.3   ← CI toto automaticky meni
"""

print("base/kustomization.yaml:")
print(BASE_KUSTOMIZE)
print("overlays/prod/kustomization.yaml:")
print(PROD_KUSTOMIZE)
print("Prikaz: kubectl apply -k k8s/overlays/prod/\n")


# ══════════════════════════════════════════════════════════════
# CAST 7: App of Apps pattern
# ══════════════════════════════════════════════════════════════

print("=== App of Apps — spravuj vsechny aplikace z jedne ===\n")

print(textwrap.dedent("""\
  Mas 20 mikrosluzeb. Nechces rucne vytvorit 20 ArgoCD Applications.

  App of Apps: jedna ArgoCD Application sleduje slozku
  kde jsou dalsi ArgoCD Application manifesty.

  apps/
  ├── kustomization.yaml
  ├── web-app.yaml          ← ArgoCD Application
  ├── api-service.yaml      ← ArgoCD Application
  ├── worker.yaml           ← ArgoCD Application
  └── monitoring.yaml       ← ArgoCD Application

  ArgoCD: "sleduj apps/ → nasad vsechny Applications uvnitr"
  Kazda Application sleduje svuj git path.

  Pridani nove sluzby = pridat YAML do apps/ → commit → auto-deploy
"""))

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        print("=== Kontrola ArgoCD ===\n")
        r = subprocess.run(["kubectl", "get", "pods", "-n", "argocd",
                           "--no-headers"],
                          capture_output=True, text=True)
        if r.stdout.strip():
            print("  ✓ ArgoCD bezi!")
            print(r.stdout.strip())
        else:
            print("  ArgoCD neni nainstalovan.")
            print("  Spust: helm install argocd argo/argo-cd -n argocd --create-namespace")
    else:
        print("=== Cluster neni dostupny — spust minikube start ===\n")


print("\n=== Hotovo! Dalsi lekce: Produkční best practices ===")

# TVOJE ULOHA:
# 1. Nainstaluj ArgoCD do minikube
# 2. Vytvor git repo s jednoduchym Deployment YAML
# 3. Vytvor ArgoCD Application ktera sleduje toto repo
# 4. Zmena v gitu → over ze ArgoCD automaticky aktualizuje cluster

# RESENI:
# 1. helm install argocd argo/argo-cd -n argocd --create-namespace --set server.extraArgs[0]=--insecure
# 2. git repo s k8s/deployment.yaml  (viz deploy YAML z lekce 10)
# 3. kubectl apply -f argocd-app.yaml (viz APP_YAML vyse, zmen repoURL)
# 4. git commit zmenu replicas: 3 → git push  →  argocd app get moje-app  →  Synced + 3 Pody bezici
