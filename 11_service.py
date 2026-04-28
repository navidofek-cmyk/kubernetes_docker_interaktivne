"""
LEKCE 11: Service — stabilní adresa pro Pody
=============================================
Pody mají nestabilní IP adresy.
Kdyz Pod pada a novy nastartuje, ma JINOU IP.

Service je stabilní adresa která vzdy ukazuje
na spravne bezici Pody (vyber dle labels).
Funguje jako load balancer uvnitr clusteru.

Naucis se:
  - typy Services: ClusterIP, NodePort, LoadBalancer
  - jak Service vybira Pody (selector)
  - pristup k aplikaci z browseru
  - DNS v Kubernetes

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
# CAST 1: Problem bez Service
# ══════════════════════════════════════════════════════════════

print("=== Problem: IP adresy Podu se meni ===\n")

print(textwrap.dedent("""\
  Web Pod: IP 10.0.0.5
  DB Pod:  IP 10.0.0.6

  Web App rika: "Pripojim se na 10.0.0.6"
  DB Pod pada... Kubernetes spusti novy na IP 10.0.0.9
  Web App stale zkusi 10.0.0.6 → CONNECTION REFUSED 💥

  Reseni: Service
  DB Service: vzdy dostupna na "db" nebo "db.default.svc.cluster.local"
  Service vi ktere Pody maji label "app: db" a prepopusli provoz
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Typy Services
# ══════════════════════════════════════════════════════════════

print("=== Typy Services ===\n")

print(textwrap.dedent("""\
  ClusterIP (default)
    - Dostupna jen uvnitr clusteru
    - Pouzij pro: komunikace mezi sluzby (web → db)
    - URL: <service-name>.<namespace>.svc.cluster.local

  NodePort
    - Otevre port na kazdém Node (VM/serveru)
    - Dostupna z externi site na <node-ip>:<node-port>
    - Port rozsah: 30000–32767
    - Pouzij pro: testovani, dev prostredi

  LoadBalancer
    - Vytvori externi load balancer (cloud provider)
    - Dostane verejnou IP adresu
    - Pouzij pro: produkce v AWS/GCP/Azure
    - V minikube: minikube tunnel pro simulaci

  ExternalName
    - Alias na externi DNS jmeno
    - Pouzij pro: external databaze, third-party API
"""))


# ══════════════════════════════════════════════════════════════
# CAST 3: ClusterIP Service YAML
# ══════════════════════════════════════════════════════════════

print("=== ClusterIP Service ===\n")

CLUSTERIP_YAML = """\
apiVersion: v1
kind: Service
metadata:
  name: muj-web-svc    ← toto jmeno je DNS jmeno uvnitr clusteru
spec:
  type: ClusterIP      ← default, vynechat = ClusterIP
  selector:
    app: muj-web       ← posle provoz na Pody s timto labelem
  ports:
    - protocol: TCP
      port: 80         ← port Service (na cem posloucha Service)
      targetPort: 80   ← port Podu (kam se preposi)
"""

print(CLUSTERIP_YAML)
print(textwrap.dedent("""\
  Uvnitr clusteru:
    curl http://muj-web-svc
    curl http://muj-web-svc.default
    curl http://muj-web-svc.default.svc.cluster.local
    → Vsechno funguje diky Kubernetes DNS (CoreDNS)
"""))


# ══════════════════════════════════════════════════════════════
# CAST 4: NodePort Service YAML
# ══════════════════════════════════════════════════════════════

print("=== NodePort Service ===\n")

NODEPORT_YAML = """\
apiVersion: v1
kind: Service
metadata:
  name: muj-web-nodeport
spec:
  type: NodePort
  selector:
    app: muj-web
  ports:
    - protocol: TCP
      port: 80           ← port uvnitr clusteru
      targetPort: 80     ← port v Podu
      nodePort: 30080    ← port na kazdém Nodu (30000-32767)
                           (vynech = K8s priradi nahodny)
"""

print(NODEPORT_YAML)
print(textwrap.dedent("""\
  Pristup:
    curl http://<IP_nodu>:30080
    minikube service muj-web-nodeport --url   ← minikube URL
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: LoadBalancer Service YAML
# ══════════════════════════════════════════════════════════════

print("=== LoadBalancer Service (prod) ===\n")

LB_YAML = """\
apiVersion: v1
kind: Service
metadata:
  name: muj-web-lb
spec:
  type: LoadBalancer
  selector:
    app: muj-web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80

# Cloud provider (AWS/GCP/Azure) automaticky vytvori:
#   - externi load balancer
#   - verejnou IP adresu nebo hostname
#
# kubectl get service muj-web-lb
# NAME         TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)
# muj-web-lb   LoadBalancer   10.0.0.120   52.14.123.456   80:32100/TCP
#                                          ^^^^^^^^^^^^^^
#                                          verejná IP (pristupna z internetu)
"""

print(LB_YAML)


# ══════════════════════════════════════════════════════════════
# CAST 6: Kompletni priklad — Deployment + Service
# ══════════════════════════════════════════════════════════════

print("=== Kompletni priklad: Deployment + Service ===\n")

KOMPLETNI_YAML = """\
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app     ← label Podu
    spec:
      containers:
        - name: web
          image: nginx:alpine
          ports:
            - containerPort: 80

---
# service.yaml (nebo stejny soubor, oddeleny ---)
apiVersion: v1
kind: Service
metadata:
  name: web-app-svc
spec:
  type: NodePort
  selector:
    app: web-app         ← najde Pody s timto labelem
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
"""

print(KOMPLETNI_YAML)


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
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: demo-web-svc
spec:
  type: NodePort
  selector:
    app: demo-web
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30090
"""

if KUBECTL_OK:
    r = subprocess.run(["kubectl", "cluster-info"],
                      capture_output=True, text=True, timeout=10)

    if r.returncode != 0:
        print("=== Cluster neni dostupny — spust minikube start ===\n")
    else:
        print("=== Demo: Deployment + Service ===\n")

        manifest = Path("/tmp/demo-web-svc.yaml")
        manifest.write_text(DEMO_YAML)

        print("$ kubectl apply -f demo.yaml")
        r = subprocess.run(["kubectl", "apply", "-f", str(manifest)],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        import time; time.sleep(3)

        print("\n$ kubectl get service demo-web-svc")
        r = subprocess.run(["kubectl", "get", "service", "demo-web-svc"],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        print("\n$ kubectl get endpoints demo-web-svc")
        r = subprocess.run(["kubectl", "get", "endpoints", "demo-web-svc"],
                          capture_output=True, text=True)
        print(r.stdout.strip())

        print("\n$ kubectl delete -f demo.yaml")
        subprocess.run(["kubectl", "delete", "-f", str(manifest)],
                      capture_output=True)
        print("  ✓ Vycisteno")

        manifest.unlink(missing_ok=True)
else:
    print("=== kubectl neni dostupny ===\n")
    print("  Uloz YAML jako demo.yaml a zkus:")
    print("  $ kubectl apply -f demo.yaml")
    print("  $ kubectl get services")


print("\n=== Hotovo! Dalsi lekce: ConfigMap a Secret ===")

# TVOJE ULOHA:
# 1. Vytvor Deployment + NodePort Service a aplikuj oba
# 2. Ziskej URL v minikube a otevri v prohlizeci
# 3. Zkontroluj endpoints — souhlasi pocet s poctem Podu?
# 4. Skaluj Deployment a znovu zkontroluj endpoints

# RESENI:
# 1. kubectl apply -f deployment.yaml -f service.yaml
# 2. minikube service <service-name> --url   (nebo minikube tunnel)
# 3. kubectl get endpoints <service-name>   (mel by mit 2+ IP:port)
# 4. kubectl scale deployment ... --replicas=4   →   kubectl get endpoints (4 endpointy)
