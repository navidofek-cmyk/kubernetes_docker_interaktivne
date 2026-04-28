"""
LEKCE 02: Tvuj prvni kontejner
================================
Dnes si opravdu zahrajeme s Dockerem.
Spustime kontejner, mrkname dovnitr, a zase ho zastavime.

Je to jako pustit program — ale v bezpecne krabici,
ktera se po zastaveni kompletne uklidí.

Naucis se:
  - stahovat image z Docker Hubu
  - spoustet kontejnery interaktivne
  - prozkoumat souborovy system kontejneru
  - predavat prostredi (environment variables)
  - mapovat porty

Obtiznost: ⭐
"""

import subprocess
import textwrap


def docker_dostupny() -> bool:
    try:
        r = subprocess.run(["docker", "version"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


DOCKER_OK = docker_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Anatomie docker run
# ══════════════════════════════════════════════════════════════

print("=== Anatomie prikazu docker run ===\n")

print(textwrap.dedent("""
  docker run  -d  -p 8080:80  -e ENV=prod  --name muj-web  nginx:alpine
  │           │   │            │            │               │
  │           │   │            │            │               └─ image:tag
  │           │   │            │            └─ jmeno kontejneru
  │           │   │            └─ environment promenna
  │           │   └─ port: localhost:8080 → kontejner:80
  │           └─ detached (bezi na pozadi)
  └─ prikaz
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Zivotni cyklus kontejneru
# ══════════════════════════════════════════════════════════════

print("=== Zivotni cyklus kontejneru ===\n")

cyklus = """
docker pull image       →  stahni image
       ↓
docker create image     →  vytvor kontejner (ale nespoustej)
       ↓
docker start <id>       →  spust kontejner
       ↓
    [bezi]              →  docker exec, docker logs, docker stats
       ↓
docker stop <id>        →  zastav kontejner (gracefully, SIGTERM)
  nebo
docker kill <id>        →  okamzite ukonci (SIGKILL)
       ↓
docker rm <id>          →  smaz kontejner

Zkratka: docker run = pull + create + start (v jednom!)
"""
print(cyklus)


# ══════════════════════════════════════════════════════════════
# CAST 3: Interaktivni mod
# ══════════════════════════════════════════════════════════════

print("=== Interaktivni mod (-it) ===\n")

print(textwrap.dedent("""
  -i  = interactive (drz stdin otevreny)
  -t  = tty (pouzij terminal / pseudoterminal)

  Prikazy pro prochazeni kontejneru:

    docker run -it ubuntu bash          ← bash terminal v Ubuntu
    docker run -it alpine sh            ← sh terminal v Alpine
    docker run -it python:3.12 python   ← Python REPL v kontejneru

  Uvnitr kontejneru zkus:
    ls /           ← vylistuj root filesystem
    cat /etc/os-release  ← zjisti verzi OS
    which python3   ← kde je Python
    exit           ← vyjdi z kontejneru (a zastav ho)

  Pro vice informaci o bezicim kontejneru:
    docker inspect <id>    ← kompletni JSON s info
    docker stats           ← CPU, RAM v realnem case
    docker top <id>        ← procesy uvnitr kontejneru
"""))


# ══════════════════════════════════════════════════════════════
# CAST 4: Environment variables
# ══════════════════════════════════════════════════════════════

print("=== Environment variables ===\n")

env_priklad = """\
# Jedna promenna:
docker run -e JMENO=Tomas ubuntu env

# Vice promennych:
docker run -e JMENO=Tomas -e VECE=pizza ubuntu env

# Ze souboru .env:
docker run --env-file .env ubuntu env

# Priklad .env souboru:
# DATABASE_URL=postgresql://user:pass@localhost/db
# SECRET_KEY=tajne123
# DEBUG=false
"""
print(env_priklad)


# ══════════════════════════════════════════════════════════════
# CAST 5: Porty a sit
# ══════════════════════════════════════════════════════════════

print("=== Porty a sit ===\n")

print(textwrap.dedent("""
  Kontejner je izolovan — zvenku ho nikdo nevidi.
  Pres port 'prorazis okenko' a reknes:

    "Kdyz nekdo pristoupi na port 8080 na mnem pocitaci,
     preposlav to na port 80 uvnitr kontejneru."

  Zapis:  -p <port_na_pocitaci>:<port_v_kontejneru>

  Priklady:
    -p 8080:80      ← localhost:8080 → kontejner:80
    -p 3000:3000    ← localhost:3000 → kontejner:3000
    -p 5432:5432    ← localhost:5432 → kontejner:5432 (PostgreSQL)

  Priklad: nginx webserver
    docker run -d -p 8080:80 nginx
    → Otevri http://localhost:8080
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Zkusime to
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Zkousime docker run ===\n")

    # Spust hello-world
    print("$ docker run hello-world")
    r = subprocess.run(["docker", "run", "--rm", "hello-world"],
                      capture_output=True, text=True)
    if r.returncode == 0:
        # Zobraz prvnich 10 radku
        radky = r.stdout.strip().splitlines()
        for radek in radky[:10]:
            print(f"  {radek}")
        if len(radky) > 10:
            print(f"  ... ({len(radky)-10} dalsich radku)")
        print("\n  ✓ hello-world funguje!")
    else:
        print(f"  ✗ Chyba: {r.stderr[:200]}")

    # Zjisti info o Dockeru
    print("\n$ docker info --format '{{.ServerVersion}}'")
    r = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                      capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  Docker verze: {r.stdout.strip()}")

    # Zobraz stazene image
    print("\n$ docker images")
    r = subprocess.run(["docker", "images", "--format",
                       "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"],
                      capture_output=True, text=True)
    print(r.stdout.strip())

else:
    print("=== Docker neni dostupny — ukazuji co by se stalo ===\n")
    print("  Nainstaluj Docker Desktop: https://docs.docker.com/get-docker/")
    print("\n  Pak zkus tyto prikazy:")
    print("  $ docker run hello-world")
    print("  $ docker run -it alpine sh")
    print("  $ docker run -d -p 8080:80 nginx")


print("\n=== Hotovo! Dalsi lekce: Napises vlastni Dockerfile ===")

# TVOJE ULOHA:
# 1. Spust interaktivni terminal v Alpine Linuxu
# 2. Spust nginx na portu 8888 na pozadi
# 3. Zobraz logy nginx kontejneru
# 4. Zastav a smaz nginx kontejner jednim prikazem

# RESENI:
# 1. docker run -it alpine sh   (pak: ls, cat /etc/alpine-release, exit)
# 2. docker run -d -p 8888:80 --name muj-nginx nginx
# 3. docker logs muj-nginx
# 4. docker rm -f muj-nginx
