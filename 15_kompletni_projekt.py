"""
LEKCE 15: Kompletni projekt — od kodu po Kubernetes
======================================================
Nasli jsme vsechno co potrebujeme.
Ted to dal dohromady do jednoho projektu.

Postavime kompletni Python API:
  1. Napisme aplikaci
  2. Dockerizujeme
  3. Pushujeme image
  4. Nasadime do Kubernetes
  5. Configurujeme Ingress

Tohle je realny workflow!

Naucis se:
  - kompletni deployment pipeline
  - best practices pro produkci
  - debugovani realnych problemu
  - pouzivat kubectl efektivne

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
# CAST 1: Aplikace
# ══════════════════════════════════════════════════════════════

print("=== CAST 1: Aplikace ===\n")

APP_PY = '''\
"""Jednoduche Python API s pocitadlem."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import time

START_TIME = time.time()
POCITADLO = 0


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global POCITADLO
        if self.path == "/health":
            self._odposli(200, {"status": "ok"})
        elif self.path == "/ready":
            self._odposli(200, {"status": "ready"})
        elif self.path == "/":
            POCITADLO += 1
            self._odposli(200, {
                "zprava": "Ahoj z Kubernetes!",
                "verze": os.getenv("APP_VERSION", "1.0.0"),
                "prostredi": os.getenv("PROSTRED", "unknown"),
                "navstevy": POCITADLO,
                "uptime_s": round(time.time() - START_TIME, 1),
            })
        else:
            self._odposli(404, {"chyba": "nenalezeno"})

    def _odposli(self, kod, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {self.address_string()} - {fmt % args}")


port = int(os.getenv("PORT", "8000"))
print(f"API bezi na http://0.0.0.0:{port}")
HTTPServer(("0.0.0.0", port), Handler).serve_forever()
'''

print("app.py:")
print(APP_PY)


# ══════════════════════════════════════════════════════════════
# CAST 2: Dockerfile
# ══════════════════════════════════════════════════════════════

print("=== CAST 2: Dockerfile (produkce) ===\n")

DOCKERFILE = """\
# Multi-stage: builder + runtime
FROM python:3.12-slim AS builder
WORKDIR /app
# Tady bychom instalovali zavislosti z requirements.txt
# Pouzivame jen stdlib, takze neni treba

FROM python:3.12-slim AS runtime

# Non-root uzivatel
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --chown=appuser:appuser app.py .

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

CMD ["python", "app.py"]
"""

print(DOCKERFILE)


# ══════════════════════════════════════════════════════════════
# CAST 3: Kubernetes manifesty
# ══════════════════════════════════════════════════════════════

print("=== CAST 3: Kubernetes manifesty ===\n")

NAMESPACE_YAML = """\
# 00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: moje-app
  labels:
    environment: production
"""

CONFIGMAP_YAML = """\
# 01-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: moje-app
data:
  PROSTRED: "production"
  LOG_LEVEL: "info"
"""

SECRET_YAML = """\
# 02-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
  namespace: moje-app
stringData:
  APP_VERSION: "1.2.0"
"""

DEPLOYMENT_YAML = """\
# 03-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: moje-api
  namespace: moje-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: moje-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: moje-api
    spec:
      containers:
        - name: api
          image: moje-api:1.0.0     ← tvoje image z Docker Hub
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secret
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "500m"
              memory: "128Mi"
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
"""

SERVICE_YAML = """\
# 04-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: moje-api-svc
  namespace: moje-app
spec:
  selector:
    app: moje-api
  ports:
    - port: 80
      targetPort: 8000
"""

INGRESS_YAML = """\
# 05-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: moje-api-ingress
  namespace: moje-app
spec:
  ingressClassName: nginx
  rules:
    - host: api.moje-app.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: moje-api-svc
                port:
                  number: 80
"""

for nazev, obsah in [
    ("00-namespace.yaml", NAMESPACE_YAML),
    ("01-configmap.yaml", CONFIGMAP_YAML),
    ("02-secret.yaml", SECRET_YAML),
    ("03-deployment.yaml", DEPLOYMENT_YAML),
    ("04-service.yaml", SERVICE_YAML),
    ("05-ingress.yaml", INGRESS_YAML),
]:
    print(f"{'─'*50}")
    print(f"{nazev}")
    print(f"{'─'*50}")
    print(obsah)


# ══════════════════════════════════════════════════════════════
# CAST 4: Deployment pipeline
# ══════════════════════════════════════════════════════════════

print("=== CAST 4: Deployment pipeline ===\n")

PIPELINE = """\
# .github/workflows/deploy.yml
name: Build, Push a Deploy

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}

    steps:
      - uses: actions/checkout@v4

      - name: Login to registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=semver,pattern={{version}}
            type=sha,prefix=sha-
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update image tag in deployment
        run: |
          sed -i 's|image: moje-api:.*|image: ghcr.io/tomas/moje-api:${{ needs.build-and-push.outputs.image_tag }}|' \\
            k8s/03-deployment.yaml

      - name: Deploy to Kubernetes
        env:
          KUBECONFIG: ${{ secrets.KUBECONFIG }}
        run: |
          kubectl apply -f k8s/
          kubectl rollout status deployment/moje-api -n moje-app
"""

print(PIPELINE)


# ══════════════════════════════════════════════════════════════
# CAST 5: Uzitecne kubectl tipy
# ══════════════════════════════════════════════════════════════

print("=== Uzitecne kubectl tipy ===\n")

tipy = [
    ("kubectl get all -n moje-app",
     "Vsechno v namespace (pods, svc, deploy, rs...)"),
    ("kubectl get events --sort-by=.lastTimestamp",
     "Udalosti serazene dle casu (skvele pro debug)"),
    ("kubectl top pods",
     "Spotrebu CPU a RAM Podu (potrebuje metrics-server)"),
    ("kubectl top nodes",
     "Spotrebu CPU a RAM Nodu"),
    ("kubectl port-forward svc/moje-api-svc 8000:80",
     "Preposli port sluzby na lokalni pocitac (debug!)"),
    ("kubectl run tmp --image=busybox --rm -it -- sh",
     "Docasny Pod pro debug uvnitr clusteru"),
    ("kubectl apply -k kustomize/",
     "Kustomize — alternativa Helm pro overrides"),
    ("kubectl diff -f deploy.yaml",
     "Zobraz rozdil bez aplikovani"),
    ("kubectl get pods --field-selector=status.phase=Pending",
     "Jen pending Pody"),
    ("kubectl explain deployment.spec.strategy",
     "Dokumentace primo v terminalu"),
]

for cmd, popis in tipy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo — lokalni deploy
# ══════════════════════════════════════════════════════════════

DEMO_VSECHNO = """\
apiVersion: v1
kind: Namespace
metadata:
  name: demo-projekt
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: moje-api
  namespace: demo-projekt
spec:
  replicas: 2
  selector:
    matchLabels:
      app: moje-api
  template:
    metadata:
      labels:
        app: moje-api
    spec:
      containers:
        - name: api
          image: hashicorp/http-echo:latest
          args: ["-text=Ahoj z Kubernetes!", "-listen=:8000"]
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "50m"
              memory: "32Mi"
            limits:
              cpu: "200m"
              memory: "64Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: moje-api-svc
  namespace: demo-projekt
spec:
  selector:
    app: moje-api
  ports:
    - port: 80
      targetPort: 8000
"""

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("=== Cluster neni dostupny — spust minikube start ===\n")
    else:
        print("=== Demo: Kompletni deploy ===\n")

        manifest = Path("/tmp/demo-projekt.yaml")
        manifest.write_text(DEMO_VSECHNO)

        r = subprocess.run(["kubectl", "apply", "-f", str(manifest)],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        import time; time.sleep(5)

        print("\n$ kubectl get all -n demo-projekt")
        r = subprocess.run(["kubectl", "get", "all", "-n", "demo-projekt"],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        print("\n$ kubectl port-forward svc/moje-api-svc 8001:80 -n demo-projekt (2s)")
        pf = subprocess.Popen(
            ["kubectl", "port-forward", "svc/moje-api-svc", "8001:80",
             "-n", "demo-projekt"],
            capture_output=True
        )
        time.sleep(2)
        try:
            r = subprocess.run(["curl", "-s", "http://localhost:8001"],
                              capture_output=True, text=True, timeout=3)
            if r.returncode == 0:
                print(f"  Odpoved: {r.stdout.strip()}")
        except Exception:
            print("  (curl neni dostupny — zkus sam: curl http://localhost:8001)")
        finally:
            pf.terminate()

        print("\n$ kubectl delete namespace demo-projekt")
        subprocess.run(["kubectl", "delete", "namespace", "demo-projekt"],
                      capture_output=True)
        print("  ✓ Vycisteno — vsechno v namespace bylo smazano")
        manifest.unlink(missing_ok=True)

else:
    print("=== kubectl neni dostupny ===\n")
    print("  Nainstaluj minikube a kubectl, pak zkus tento soubor znova.")


print("\n" + "=" * 60)
print("GRATULACE! Dojel jsi az na konec kurzu!")
print("=" * 60)
print(textwrap.dedent("""
  Co jsi se naucil:

  Docker:
    ✅ Kontejnery a images
    ✅ Dockerfile a build
    ✅ Vrstvy a optimalizace
    ✅ Volumes pro trvalá data
    ✅ Docker Compose
    ✅ Docker Hub a registry

  Kubernetes:
    ✅ Architektura clusteru
    ✅ Pod — zakladni jednotka
    ✅ Deployment — hlida aplikaci
    ✅ Service — stabilni adresa
    ✅ ConfigMap a Secret
    ✅ Ingress — brana z internetu
    ✅ Helm — balicky
    ✅ Kompletni deployment pipeline

  Co dal?
    - Prometheus + Grafana (monitoring)
    - ArgoCD (GitOps)
    - Service Mesh (Istio, Linkerd)
    - Kubernetes operators
    - Multi-cluster
"""))

# TVOJE ULOHA:
# 1. Dockerizuj jednoduchou Python aplikaci (viz app.py v lekci)
# 2. Nasad do minikube pres eval + docker build + kubectl apply
# 3. Pristup k aplikaci pres kubectl port-forward
# 4. Update image na v2 a proved rolling update bez vypadku

# RESENI:
# 1. viz Dockerfile v lekci → docker build -t moje-api:v1 . → docker run -p 8000:8000 moje-api:v1
# 2. eval $(minikube docker-env) → docker build -t moje-api:v1 . → kubectl apply -f k8s/
# 3. kubectl port-forward svc/moje-api-svc 8000:80 -n moje-app   →   curl http://localhost:8000
# 4. docker build -t moje-api:v2 . → kubectl set image deployment/moje-api api=moje-api:v2 -n moje-app → kubectl rollout status deployment/moje-api -n moje-app
