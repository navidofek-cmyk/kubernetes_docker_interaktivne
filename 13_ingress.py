"""
LEKCE 13: Ingress — brana z internetu
=======================================
LoadBalancer Service dava kazde aplikaci vlastní IP.
V produkci mas 20 aplikaci = 20 IP = 20 load balanceru.
Draze a neprehledne!

Ingress je JEDEN vstupní bod (jeden load balancer).
Dle pravidel (URL, hostname) posle provoz spravne sluzbe.

Naucis se:
  - co je Ingress a Ingress Controller
  - pravidla pro routovani (path, host)
  - TLS/HTTPS s certifikatem
  - Ingress v minikube

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
# CAST 1: Architektura Ingress
# ══════════════════════════════════════════════════════════════

print("=== Architektura Ingress ===\n")

schema = """\
Internet
   |
   ▼
┌──────────────────────┐
│   Ingress Controller  │  ← nginx, traefik, HAProxy...
│   (1x LoadBalancer)   │
└──────────────────────┘
   |
   ▼ (dle pravidel Ingress)
   |
   ├─ /api/*     → api-service:8000
   ├─ /web/*     → web-service:80
   └─ /static/*  → static-service:8080

Nebo dle hostname:
   ├─ api.firma.cz   → api-service:8000
   ├─ web.firma.cz   → web-service:80
   └─ blog.firma.cz  → blog-service:80
"""
print(schema)


# ══════════════════════════════════════════════════════════════
# CAST 2: Path-based routing
# ══════════════════════════════════════════════════════════════

print("=== Path-based Ingress ===\n")

PATH_INGRESS = """\
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx      ← jaky controller pouzit
  rules:
    - host: moje-app.local     ← pro tento hostname
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-svc
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-svc
                port:
                  number: 80
"""
print(PATH_INGRESS)


# ══════════════════════════════════════════════════════════════
# CAST 3: Host-based routing
# ══════════════════════════════════════════════════════════════

print("=== Host-based Ingress ===\n")

HOST_INGRESS = """\
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-host-ingress
spec:
  ingressClassName: nginx
  rules:
    - host: web.firma.cz
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-svc
                port:
                  number: 80

    - host: api.firma.cz
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-svc
                port:
                  number: 8000

    - host: blog.firma.cz
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: blog-svc
                port:
                  number: 80
"""
print(HOST_INGRESS)


# ══════════════════════════════════════════════════════════════
# CAST 4: TLS/HTTPS
# ══════════════════════════════════════════════════════════════

print("=== TLS/HTTPS — sifrovany provoz ===\n")

TLS_INGRESS = """\
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod   ← cert-manager!
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - web.firma.cz
      secretName: web-tls-cert    ← K8s Secret s certifikatem
  rules:
    - host: web.firma.cz
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-svc
                port:
                  number: 80
"""
print(TLS_INGRESS)

print(textwrap.dedent("""\
  cert-manager automaticky ziska a obnovuje Let's Encrypt certifikat.
  Instalace: helm install cert-manager jetstack/cert-manager
  Dokumentace: https://cert-manager.io
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: Ingress v minikube
# ══════════════════════════════════════════════════════════════

print("=== Ingress v minikube ===\n")

print(textwrap.dedent("""\
  1. Povol Ingress addon:
     minikube addons enable ingress
     minikube addons enable ingress-dns

  2. Zkontroluj ze controller bezi:
     kubectl get pods -n ingress-nginx

  3. Zjisti IP minikube:
     minikube ip
     (napr. 192.168.49.2)

  4. Pridej do /etc/hosts:
     192.168.49.2  moje-app.local

  5. Vytvor Ingress a aplikuj:
     kubectl apply -f ingress.yaml

  6. Otevri: http://moje-app.local
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Alternativy — Gateway API
# ══════════════════════════════════════════════════════════════

print("=== Gateway API — budoucnost Ingressu ===\n")

print(textwrap.dedent("""\
  Ingress je stary a ma limitace.
  Gateway API je novejsi, flexibilnejsi:
    - HTTPRoute, GRPCRoute, TCPRoute...
    - Lepsi RBAC (team muze spravovat jen svuj route)
    - Podporuje vice protokolu

  Jestli zacinás nový projekt, podivej se na Gateway API.
  Pro uceni staci Ingress — koncepty jsou stejne.
"""))


# ══════════════════════════════════════════════════════════════
# CAST 7: Demo
# ══════════════════════════════════════════════════════════════

DEMO_YAML = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: demo-web
  template:
    metadata:
      labels:
        app: demo-web
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
---
apiVersion: v1
kind: Service
metadata:
  name: demo-web-svc
spec:
  selector:
    app: demo-web
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: demo-ingress
spec:
  ingressClassName: nginx
  rules:
    - host: demo.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: demo-web-svc
                port:
                  number: 80
"""

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("=== Cluster neni dostupny — spust minikube start ===\n")
    else:
        print("=== Aplikujeme Ingress ===\n")

        manifest = Path("/tmp/demo-ingress.yaml")
        manifest.write_text(DEMO_YAML)

        r = subprocess.run(["kubectl", "apply", "-f", str(manifest)],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        import time; time.sleep(2)

        print("\n$ kubectl get ingress")
        r = subprocess.run(["kubectl", "get", "ingress"],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        print("\n  Pokud mas Ingress controller (minikube addons enable ingress),")
        print("  pridej do /etc/hosts: <minikube-ip> demo.local")
        print("  Pak otevri http://demo.local")

        print("\n$ kubectl delete -f demo.yaml")
        subprocess.run(["kubectl", "delete", "-f", str(manifest)],
                      capture_output=True)
        print("  ✓ Vycisteno")
        manifest.unlink(missing_ok=True)

else:
    print("=== kubectl neni dostupny — nainstaluj minikube ===\n")


print("\n=== Hotovo! Dalsi lekce: Helm — balicky pro Kubernetes ===")

# TVOJE ULOHA:
# 1. Povol Ingress addon v minikube
# 2. Vytvor Deployment + ClusterIP Service + Ingress (host: moje-app.local)
# 3. Pridej zaznam do /etc/hosts a otevri v prohlizeci
# 4. Pridej druhou sluzbu a routuj /api/ na ni

# RESENI:
# 1. minikube addons enable ingress
# 2. kubectl apply -f deployment.yaml -f service.yaml -f ingress.yaml   (viz DEMO_YAML)
# 3. echo "$(minikube ip) moje-app.local" | sudo tee -a /etc/hosts   →   curl http://moje-app.local
# 4. Vytvor druhy Deployment+Service, pridej do Ingress: {path: /api, backend: {service: {name: api-svc, port: {number: 80}}}}
