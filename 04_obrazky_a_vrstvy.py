"""
LEKCE 04: Images a vrstvy — jak Docker seri misto
===================================================
Docker je genialni v ukladani mista.
Neopakuje se — kazdy "kus" image se ulozi jen jednou.

Predstav si to jako knizku se samolepicimi strankami:
kazda vrstva je jedna stranka. Vic aplikaci sdili
stejne stranky (zakladni OS, Python), kazda ma jen
svoje vlastni nahore.

Naucis se:
  - jak vrstveny system funguje
  - proc je poradi instrukci dulezite
  - jak funguje cache
  - multi-stage buildy pro mensi image

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
# CAST 1: Co je vrstva (layer)
# ══════════════════════════════════════════════════════════════

print("=== Vrstvy Docker image ===\n")

schema = """\
Kazda instrukce v Dockerfile vytvorí jednu vrstvu:

  FROM python:3.12-slim     ← vrstva 1: zakladni OS + Python
  WORKDIR /app              ← vrstva 2: nastav adresar
  COPY requirements.txt .   ← vrstva 3: requirements soubor
  RUN pip install -r req..  ← vrstva 4: nainstaluj balicky
  COPY . .                  ← vrstva 5: zkopiruj kod
  CMD ["python", "app.py"]  ← vrstva 6: spousteci prikaz

  +──────────────────────────+
  │  CMD ["python","app.py"] │  ← vrstva 6 (tvoje)
  │  COPY . .                │  ← vrstva 5 (tvoje)
  │  RUN pip install         │  ← vrstva 4 (tvoje)
  │  COPY requirements.txt   │  ← vrstva 3 (tvoje)
  │  WORKDIR /app            │  ← vrstva 2 (sdilena)
  │  python:3.12-slim        │  ← vrstva 1 (sdilena s vsemi Python app)
  +──────────────────────────+

Pokud zmenís vrstvu 5 (kód), vrstvy 1-4 se nerebuildí.
Docker pouzije cache — je to RYCHLE! ⚡
"""
print(schema)


# ══════════════════════════════════════════════════════════════
# CAST 2: Dulezitost poradi instrukci
# ══════════════════════════════════════════════════════════════

print("=== Poradi instrukci je dulezite! ===\n")

SPATNE = """\
# SPATNE — requirements se reinstaluje pri KAZDE zmene kodu
FROM python:3.12-slim
WORKDIR /app
COPY . .                     ← kopiruj VE (kod + requirements)
RUN pip install -r requirements.txt  ← pip install az po kopirovani kodu
CMD ["python", "app.py"]

Zmenis radek v app.py → pip install se spusti ZNOVA (pomale!)
"""

DOBRE = """\
# DOBRE — requirements se reinstaluje jen kdyz se zmeni
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .       ← kopiruj JEN requirements (zmeni se malo)
RUN pip install -r requirements.txt  ← cached! Spusti se jen kdyz zmenís requirements
COPY . .                      ← zkopiruj zbytek (zmeni se casto)
CMD ["python", "app.py"]

Zmenis radek v app.py → pip install se PRESKOCI (rychle!) ⚡
"""

print("❌ Spatne:")
print(SPATNE)
print("✅ Dobre:")
print(DOBRE)


# ══════════════════════════════════════════════════════════════
# CAST 3: Multi-stage build
# ══════════════════════════════════════════════════════════════

print("=== Multi-stage build — mensi a cistejsi image ===\n")

print(textwrap.dedent("""\
  Problem: Abychom zkompilovali Go/Rust/C program, potrebujeme
  compiler — ale ten je velky (stovky MB) a v produkci ho
  nepotrebujeme.

  Reseni: Pouzijeme DVA stages.
    Stage 1 (builder): Kompilujeme. Velky. Docasny.
    Stage 2 (runtime): Jen spousteci prostredi. Maly. Finalni.
"""))

MULTI_STAGE = """\
# Stage 1: Builder — kompilace
FROM golang:1.22 AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -o server .


# Stage 2: Runtime — jen to co potrebujeme
FROM scratch                    ← absolutne prazdny image!

COPY --from=builder /app/server /server
EXPOSE 8080
CMD ["/server"]

# Vysledek: image ma par MB misto stovek MB!
"""

print("Priklad Go aplikace:")
print(MULTI_STAGE)

MULTI_STAGE_PYTHON = """\
# Stage 1: Builder — instalace zavislosti
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# Stage 2: Runtime — cistejsi prostredi
FROM python:3.12-slim AS runtime

# Non-root uzivatel (bezpecnost!)
RUN useradd -r -u 1000 appuser

WORKDIR /app

# Zkopiruj nainstalované zavislosti z builderu
COPY --from=builder /install /usr/local

# Zkopiruj zdrojovy kod
COPY --chown=appuser:appuser app.py .

USER appuser
EXPOSE 8000
CMD ["python", "app.py"]
"""

print("Priklad Python aplikace:")
print(MULTI_STAGE_PYTHON)


# ══════════════════════════════════════════════════════════════
# CAST 4: Jak videt vrstvy
# ══════════════════════════════════════════════════════════════

print("=== Jak videt vrstvy image ===\n")

print(textwrap.dedent("""\
  Nastroje pro prochazeni image:

    docker history nginx:alpine     ← zobraz vsechny vrstvy
    docker inspect nginx:alpine     ← kompletni JSON metadata
    docker image ls --digests       ← hash kazde image

  Externi nastroj dive (nejlepsi pro analyzu):
    dive nginx:alpine               ← interaktivni prohlizec vrstev
    (instalace: https://github.com/wagoodman/dive)
"""))


# ══════════════════════════════════════════════════════════════
# CAST 5: Porovnani velikosti
# ══════════════════════════════════════════════════════════════

print("=== Porovnani velikosti base images ===\n")

print(textwrap.dedent("""\
  Image              Velikost    Pouziti
  ─────────────────────────────────────────────────────────────
  ubuntu:22.04       ~77  MB     Plny Ubuntu (debug, vyvoj)
  debian:bookworm    ~124 MB     Plny Debian
  debian:slim        ~75  MB     Debian bez deb tools
  python:3.12        ~1   GB     Python + Debian + build tools
  python:3.12-slim   ~130 MB    Python + Debian slim
  python:3.12-alpine ~50  MB    Python + Alpine Linux (pozor na glibc!)
  alpine:3.19        ~7   MB    Minimalní OS
  scratch            ~0   MB    Absolutne prazdny (jen pro staticke binarky)

  Pravidlo: Pouzij -slim nebo -alpine kde to jde.
  Mala image = rychlejsi stazeni, mene bezpecnostnich dek.
"""))


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Zobrazuji historii nginx:alpine ===\n")
    r = subprocess.run(
        ["docker", "history", "nginx:alpine", "--format",
         "table {{.CreatedBy}}\t{{.Size}}"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        radky = r.stdout.strip().splitlines()
        for radek in radky[:8]:
            print(f"  {radek[:90]}")
        if len(radky) > 8:
            print(f"  ... ({len(radky)-8} dalsich vrstev)")
    else:
        # Image mozna neni stazena
        print("  (nginx:alpine neni stazena — spust: docker pull nginx:alpine)")

else:
    print("=== Docker neni dostupny ===\n")
    print("  Spust: docker history nginx:alpine")
    print("  A podivej se na vsechny vrstvy!")


print("\n=== Hotovo! Dalsi lekce: Volumes — trvalá data ===")

# TVOJE ULOHA:
# 1. Stahni python:3.12-slim a python:3.12-alpine, porovnej velikost
# 2. Zobraz historii vrstev python:3.12-slim (kolik vrstev?)
# 3. Uprav Dockerfile — dej COPY requirements.txt pred COPY . .
# 4. Proven ze cache funguje: sestav 2x a sleduj rychlost

# RESENI:
# 1. docker pull python:3.12-slim && docker pull python:3.12-alpine && docker images python
# 2. docker history python:3.12-slim   (spocitej radky = pocet vrstev)
# 3. V Dockerfile: FROM python:3.12-slim / WORKDIR /app / COPY requirements.txt . / RUN pip install -r requirements.txt / COPY . .
# 4. docker build -t test . (pomale)  →  znova docker build -t test . (rychle, "Using cache")
