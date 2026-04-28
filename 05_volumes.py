"""
LEKCE 05: Volumes — trva data
================================
Kontejner je jako piskoviste.
Kdyz ho zastaves a smazes, vsechno co bylo uvnitr je PREC.

Ale co kdyz chces ukladat data trvale?
Databaze, soubory uzivatelu, logy...

Na to jsou VOLUMES — specialni slozky mimo kontejner.
Kontejner se maze, data zustalaji.

Naucis se:
  - co jsou volumes a kdy je pouzit
  - typy mountu: volume, bind mount, tmpfs
  - jak zalohovt a obnovit data

Obtiznost: ⭐⭐
"""

import subprocess
import textwrap
from pathlib import Path


def docker_dostupny() -> bool:
    try:
        r = subprocess.run(["docker", "version"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


DOCKER_OK = docker_dostupny()


# ══════════════════════════════════════════════════════════════
# CAST 1: Problem bez volumes
# ══════════════════════════════════════════════════════════════

print("=== Problem: kontejner ztraci data ===\n")

print(textwrap.dedent("""\
  Spustis databazi v kontejneru:
    docker run postgres

  Pridat data, tabulky, zaznamy...

  Zastav kontejner:
    docker stop <id>

  Smaz kontejner:
    docker rm <id>

  Spusti novy kontejner:
    docker run postgres

  → Vsechna data jsou VIA! 💥

  Reseni: Volume = slozka mimo kontejner
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Typy mountu
# ══════════════════════════════════════════════════════════════

print("=== Typy mountu ===\n")

schema = """\
1. NAMED VOLUME  (Docker spravuje cestu, doporuceno pro data)
   ┌─────────────────────┐     ┌──────────────────────────────┐
   │     Kontejner       │     │  Docker volúme               │
   │  /var/lib/postgres  │────▶│  /var/lib/docker/volumes/    │
   └─────────────────────┘     │  moje-db/_data/              │
                                └──────────────────────────────┘

2. BIND MOUNT  (tvoje vlastni slozka, doporuceno pro vyvoj)
   ┌─────────────────────┐     ┌──────────────────────────────┐
   │     Kontejner       │     │  Tvuj pocitac                │
   │  /app               │────▶│  /home/tomas/moje-app/       │
   └─────────────────────┘     └──────────────────────────────┘
   (zmena souboru na pocitaci se okamzite projevi v kontejneru)

3. TMPFS  (pouze v pameti, zadne IO na disk)
   ┌─────────────────────┐
   │     Kontejner       │
   │  /tmp  (v RAM)      │
   └─────────────────────┘
   (rychle, ztraci se pri restartu kontejneru)
"""
print(schema)


# ══════════════════════════════════════════════════════════════
# CAST 3: Prikazy pro volumes
# ══════════════════════════════════════════════════════════════

print("=== Prikazy pro volumes ===\n")

prikazy = [
    # Named volumes
    ("docker volume create moje-db",
     "Vytvor named volume"),
    ("docker volume ls",
     "Zobraz vsechny volumes"),
    ("docker volume inspect moje-db",
     "Detaily o volume (kde je ulozena atd.)"),
    ("docker volume rm moje-db",
     "Smaz volume (POZOR: vsechna data prec!)"),
    ("docker volume prune",
     "Smaz vsechny nepouzivane volumes"),
    # Pouziti
    ("docker run -v moje-db:/var/lib/postgresql/data postgres",
     "Namountuj volume do kontejneru (named volume)"),
    ("docker run -v /home/tomas/app:/app python:3.12-slim",
     "Namountuj slozku z pocitace (bind mount)"),
    ("docker run -v $(pwd):/app python:3.12-slim",
     "Namountuj aktualni slozku (bind mount - castejsi zkratka)"),
    ("docker run --mount type=volume,src=moje-db,dst=/data alpine",
     "Modernějsi syntax --mount misto -v"),
]

for cmd, popis in prikazy:
    print(f"  $ {cmd}")
    print(f"    → {popis}\n")


# ══════════════════════════════════════════════════════════════
# CAST 4: PostgreSQL s volumes
# ══════════════════════════════════════════════════════════════

print("=== Priklad: PostgreSQL s trvalymi daty ===\n")

COMPOSE_DB = """\
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: tajne_heslo
      POSTGRES_DB: moje_databaze
    volumes:
      - db_data:/var/lib/postgresql/data  ← data preziji restart!
    ports:
      - "5432:5432"

volumes:
  db_data:   ← Docker vytvori a spravuje tuto volume
"""

print("docker-compose.yml:")
print(COMPOSE_DB)

print(textwrap.dedent("""\
  Jak funguje:
    docker compose up -d      ← spust databazi
    ... pouzivej databazi ...
    docker compose down       ← zastav (data zu v db_data!)
    docker compose up -d      ← spust znova — data jsou tam!

  Smazani dat:
    docker compose down -v    ← zastav A smaz volumes
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: Bind mount pro vyvoj
# ══════════════════════════════════════════════════════════════

print("=== Bind mount pro vyvoj — live reload ===\n")

print(textwrap.dedent("""\
  Kdyz vyvijis, chces:
    - zmenit soubor na pocitaci
    - okamzite videt zmenu v kontejneru
    - bez rebuildu image!

  Priklad:
    docker run -d -p 8000:8000 -v $(pwd):/app python:3.12-slim python /app/app.py

  Nyni:
    - Uprav app.py na pocitaci
    - Zmena je hned v /app/app.py v kontejneru
    - Restartni aplikaci nebo pouzij hot-reload (watchdog, uvicorn --reload)

  Pozor na bezpecnost:
    - Bind mount da kontejneru pristup k tvym souborum
    - Nepouzivej -v / pro mount rootu systemu!
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Zaloha a obnova
# ══════════════════════════════════════════════════════════════

print("=== Zaloha a obnova volume ===\n")

ZALOHA_CMD = """\
# Zaloha volume do tar archivu:
docker run --rm \\
  -v moje-db:/data \\
  -v $(pwd):/backup \\
  alpine tar czf /backup/db_zaloha.tar.gz -C /data .

# Obnova ze zalohy:
docker run --rm \\
  -v moje-db:/data \\
  -v $(pwd):/backup \\
  alpine sh -c "tar xzf /backup/db_zaloha.tar.gz -C /data"
"""

print(ZALOHA_CMD)


# ══════════════════════════════════════════════════════════════
# CAST 7: Demo
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Vytvarime a testujeme volume ===\n")

    # Vytvor volume
    print("$ docker volume create test-volume")
    r = subprocess.run(["docker", "volume", "create", "test-volume"],
                      capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ Volume vytvorena")

    # Zapis data
    print("$ docker run --rm -v test-volume:/data alpine sh -c \"echo 'Ahoj volume!' > /data/zprava.txt\"")
    r = subprocess.run(
        ["docker", "run", "--rm", "-v", "test-volume:/data", "alpine",
         "sh", "-c", "echo 'Ahoj volume!' > /data/zprava.txt"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        print("  ✓ Data zapsana")

    # Precteni dat novym kontejnerem
    print("$ docker run --rm -v test-volume:/data alpine cat /data/zprava.txt")
    r = subprocess.run(
        ["docker", "run", "--rm", "-v", "test-volume:/data", "alpine",
         "cat", "/data/zprava.txt"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        print(f"  Data: {r.stdout.strip()}")
        print("  ✓ Data prezila i bez toho kontejneru!")

    # Smaz volume
    print("$ docker volume rm test-volume")
    subprocess.run(["docker", "volume", "rm", "test-volume"], capture_output=True)
    print("  ✓ Volume smazana")

else:
    print("=== Docker neni dostupny ===\n")
    print("  Nainstaluj Docker a zkus:")
    print("  $ docker volume create moje-data")
    print("  $ docker run --rm -v moje-data:/data alpine sh -c \"echo 'Ahoj' > /data/test.txt\"")
    print("  $ docker run --rm -v moje-data:/data alpine cat /data/test.txt")


print("\n=== Hotovo! Dalsi lekce: Sit a porty ===")

# TVOJE ULOHA:
# 1. Vytvor named volume a zapis do nej data
# 2. Smaz kontejner, spust novy se stejnou volume — data tam jsou?
# 3. Spust PostgreSQL s volume, zastav, spust znova
# 4. Smaz volume prikazem

# RESENI:
# 1. docker volume create moje-data && docker run --rm -v moje-data:/data alpine sh -c "echo 'test' > /data/soubor.txt"
# 2. docker run --rm -v moje-data:/data alpine cat /data/soubor.txt   (vypise 'test')
# 3. docker run -d -v pg-data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=heslo postgres:alpine   → docker stop ID → docker run stejny prikaz → data tam jsou!
# 4. docker volume rm moje-data
