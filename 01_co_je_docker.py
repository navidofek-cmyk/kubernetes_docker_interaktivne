"""
LEKCE 01: Co je Docker? 🐳
============================
Predstav si krabici s obedem.
Mas tam chlebicek, jablko, pit — vse co potrebujes.
Kdyz ji otevre kdekoli, vzdy najdes to same.

Docker dela totez s programy!
Zabali program + vse co potrebuje do jedne krabicky.
Tato krabicka se jmenuje KONTEJNER.

Naucis se:
  - proc Docker existuje
  - co je image, kontejner, Docker Hub
  - jak funguje izolace
  - zakladni Docker prikazy

Obtiznost: ⭐
"""

# Proc Docker?
# ============
# "U me to funguje!" rika Tomas po skole.
# Anicce to ale nejede...
#
# S Dockerem by Tomas posla cely kontejner.
# Anicce by to jelo STEJNE jako Tomasovi.
# Reseni: vsechno je zabaleno dohromady.

import subprocess
import shutil

def docker_dostupny() -> bool:
    try:
        r = subprocess.run(["docker", "version"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


DOCKER_OK = docker_dostupny()

# ══════════════════════════════════════════════════════════════
# CAST 1: Dulezite pojmy
# ══════════════════════════════════════════════════════════════

print("=== Dulezite pojmy ===\n")

pojmy = {
    "Image":       "Recept na kontejner (jako predpis na dort)",
    "Kontejner":   "Bezici instance image (dort upeceny podle receptu)",
    "Docker Hub":  "Obchod s hotovymi image (jako AppStore)",
    "Dockerfile":  "Soubor kde napises vlastni recept",
    "Registry":    "Misto kde se ukladaji image (Hub je jedna z nich)",
    "Volume":      "Slozka kde kontejner ukada data trvale",
    "Port":        "Okenko pres ktere se dostanes dovnitr kontejneru",
}

for pojem, popis in pojmy.items():
    print(f"  {pojem:<16} — {popis}")


# ══════════════════════════════════════════════════════════════
# CAST 2: Docker vs normalni pocitac
# ══════════════════════════════════════════════════════════════

print("\n=== Docker vs. normalni spusteni ===\n")

schema = """
BEZ DOCKERU:
+---------------------------+
|  Operacni system (Linux)  |
|  App A                    |  ← App A potrebuje Python 3.8
|  App B                    |  ← App B potrebuje Python 3.12
|  KONFLIKT! 💥             |  ← Oba nemuzou byt zaroven
+---------------------------+

S DOCKEREM:
+------------------------------------------+
|       Operacni system (Linux)            |
|  +-----------+  +-----------+            |
|  | Kontejner |  | Kontejner |            |
|  |  App A    |  |  App B    |            |
|  | Python 3.8|  | Python 3.12|           |
|  +-----------+  +-----------+            |
|  Kazdy kontejner je izolovan — zadny     |
|  konflikt!  ✅                            |
+------------------------------------------+
"""
print(schema)


# ══════════════════════════════════════════════════════════════
# CAST 3: Zakladni prikazy
# ══════════════════════════════════════════════════════════════

print("=== Zakladni Docker prikazy ===\n")

prikazy = [
    ("docker pull nginx",                "Stahne image nginx z Docker Hubu"),
    ("docker run nginx",                 "Spusti kontejner z image nginx"),
    ("docker run -d nginx",              "Spusti na pozadi (-d = detached)"),
    ("docker run -p 8080:80 nginx",      "Spusti a pripoji port: 8080 na pocitaci → 80 v kontejneru"),
    ("docker ps",                        "Zobraz bezici kontejnery"),
    ("docker ps -a",                     "Zobraz vsechny kontejnery (i zastavene)"),
    ("docker stop <id>",                 "Zastav kontejner"),
    ("docker rm <id>",                   "Smaz zastaveny kontejner"),
    ("docker images",                    "Zobraz vsechny stazene image"),
    ("docker rmi nginx",                 "Smaz image"),
    ("docker logs <id>",                 "Zobraz logy kontejneru"),
    ("docker exec -it <id> bash",        "Otevri terminal uvnitr kontejneru"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 4: Zkusime spustit nginx
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Docker je dostupny — zkusime nginx ===\n")

    # Stahni image
    print("$ docker pull nginx:alpine")
    r = subprocess.run(["docker", "pull", "nginx:alpine"],
                      capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ Image stazena")
    else:
        print(f"  ✗ Chyba: {r.stderr[:100]}")

    # Zjisti velikost image
    print("\n$ docker images nginx:alpine")
    r = subprocess.run(["docker", "images", "nginx:alpine", "--format",
                       "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"],
                      capture_output=True, text=True)
    print(r.stdout.strip())

    # Spust na pozadi
    print("\n$ docker run -d -p 8080:80 --name test-nginx nginx:alpine")
    r = subprocess.run(
        ["docker", "run", "-d", "-p", "8080:80", "--name", "test-nginx", "nginx:alpine"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        container_id = r.stdout.strip()[:12]
        print(f"  ✓ Kontejner bezi: {container_id}")
        print("  Otevri v prohlizeci: http://localhost:8080")

        # Zastav a smaz
        print("\n$ docker stop test-nginx && docker rm test-nginx")
        subprocess.run(["docker", "stop", "test-nginx"], capture_output=True)
        subprocess.run(["docker", "rm", "test-nginx"], capture_output=True)
        print("  ✓ Kontejner zastayen a smazan")
    else:
        # Mozna uz bezi
        subprocess.run(["docker", "rm", "-f", "test-nginx"], capture_output=True)
        print(f"  Info: {r.stderr[:150]}")
else:
    print("=== Docker neni dostupny ===\n")
    print("  Nainstaluj Docker: https://docs.docker.com/get-docker/")
    print("\n  Pak zkus:")
    print("  $ docker run -d -p 8080:80 nginx:alpine")
    print("  Otevri: http://localhost:8080")


print("\n=== Hotovo! Dalsi lekce: Tvoj prvni kontejner ===")

# TVOJE ULOHA:
# 1. Spust kontejner hello-world: docker run hello-world
# 2. Spust nginx na portu 9090 na pozadi
# 3. Zobraz bezici kontejnery
# 4. Zastav nginx kontejner

# RESENI:
# 1. docker run hello-world
# 2. docker run -d -p 9090:80 nginx
# 3. docker ps
# 4. docker stop $(docker ps -q --filter ancestor=nginx)
