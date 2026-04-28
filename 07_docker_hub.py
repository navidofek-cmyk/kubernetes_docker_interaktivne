"""
LEKCE 07: Docker Hub a registry — sdileni images
==================================================
Postavil jsi svuj image. Skvele!
Jak ho dostanes na server? Na jiny pocitac? Do Kubernetes?

Odpoved: registry — misto kde se ukladaji a sdileji images.
Docker Hub je nejvetsi — jako GitHub pro images.

Naucis se:
  - prihlasit se k Docker Hubu
  - pushovat a pullovat images
  - znacit (tagovat) images
  - pouzivat GitHub Container Registry (ghcr.io)
  - co jsou private vs public images

Obtiznost: ⭐⭐
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
# CAST 1: Anatomy image name
# ══════════════════════════════════════════════════════════════

print("=== Anatomie jmena image ===\n")

print(textwrap.dedent("""\
  ghcr.io / tomas123 / moje-app : v1.2.3
  │          │          │          │
  │          │          │          └─ tag (verze, latest, main...)
  │          │          └─ jmeno image
  │          └─ uzivatelske jmeno / organizace
  └─ registry (docker.io = Docker Hub, ghcr.io = GitHub)

  Prikladik:
    nginx                         → docker.io/library/nginx:latest
    python:3.12-slim              → docker.io/library/python:3.12-slim
    tomas123/moje-app:v1.0        → docker.io/tomas123/moje-app:v1.0
    ghcr.io/tomas123/moje-app:main → GitHub Container Registry
"""))


# ══════════════════════════════════════════════════════════════
# CAST 2: Jak pushnut image na Docker Hub
# ══════════════════════════════════════════════════════════════

print("=== Jak pushnut image na Docker Hub ===\n")

print(textwrap.dedent("""\
  Krok 1: Zaregistruj se na hub.docker.com

  Krok 2: Prihlaseni v terminalu:
    docker login
    (zadej uzivatelske jmeno a heslo / token)

  Krok 3: Otaguj image spravnym jmenem:
    docker tag moje-app:latest TVOJE_JMENO/moje-app:v1.0
    docker tag moje-app:latest TVOJE_JMENO/moje-app:latest

  Krok 4: Push:
    docker push TVOJE_JMENO/moje-app:v1.0
    docker push TVOJE_JMENO/moje-app:latest

  Krok 5: Pull na jinem pocitaci:
    docker pull TVOJE_JMENO/moje-app:v1.0
    docker run TVOJE_JMENO/moje-app:v1.0
"""))


# ══════════════════════════════════════════════════════════════
# CAST 3: Tagovaci strategie
# ══════════════════════════════════════════════════════════════

print("=== Tagovaci strategie ===\n")

print(textwrap.dedent("""\
  latest     — nejnovejsi stabilni verze (pouzivej opatrne!)
  v1.2.3     — semanticke verzovani (SemVer) - doporuceno
  v1.2       — major.minor
  v1         — jen major verze
  main       — z main branche (CI/CD)
  sha-abc123 — presny git commit (nejpresnejsi)

  Doporucena praxe v CI/CD:
    docker tag moje-app:latest user/moje-app:latest
    docker tag moje-app:latest user/moje-app:v1.2.3
    docker tag moje-app:latest user/moje-app:${git_sha}

  Nikdy spolihat na 'latest' v produkci!
  Vzdy specifikuj konkretni verzi: image: user/app:v1.2.3
"""))


# ══════════════════════════════════════════════════════════════
# CAST 4: Alternativni registry
# ══════════════════════════════════════════════════════════════

print("=== Alternativni registry ===\n")

registry = [
    ("Docker Hub",            "docker.io",           "Nejvetsi, public zdarma, private za poplatek"),
    ("GitHub Registry",       "ghcr.io",             "Integrovan s GitHub Actions, zdarma pro public"),
    ("Google Artifact Reg.",  "us-docker.pkg.dev",   "Pro GCP projekty"),
    ("Amazon ECR",            "*.dkr.ecr.*.amazonaws.com", "Pro AWS/EKS projekty"),
    ("Azure Container Reg.",  "*.azurecr.io",        "Pro Azure/AKS projekty"),
    ("GitLab Registry",       "registry.gitlab.com", "Integrovan s GitLab CI"),
    ("Vlastni (Harbor)",      "registry.firma.cz",   "Samo-hostovany, bezpecnost, airgap"),
]

print(f"  {'Nazev':<25} {'URL':<35} {'Poznamka'}")
print(f"  {'─'*25} {'─'*35} {'─'*30}")
for nazev, url, pozn in registry:
    print(f"  {nazev:<25} {url:<35} {pozn}")


# ══════════════════════════════════════════════════════════════
# CAST 5: GitHub Container Registry + Actions
# ══════════════════════════════════════════════════════════════

print("\n=== GitHub Actions — automaticky build a push ===\n")

GITHUB_ACTIONS = """\
# .github/workflows/docker.yml
name: Build a Push Docker image

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
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
"""

print(GITHUB_ACTIONS)


# ══════════════════════════════════════════════════════════════
# CAST 6: Demo — zobraz dostupne image
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Lokalne dostupne images ===\n")
    r = subprocess.run(
        ["docker", "images", "--format",
         "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        radky = r.stdout.strip().splitlines()
        for radek in radky[:15]:
            print(f"  {radek}")
        if len(radky) > 15:
            print(f"  ... ({len(radky)-15} dalsich)")
    else:
        print("  (zadne lokalni images)")

else:
    print("=== Docker neni dostupny ===\n")
    print("  Po instalaci Dockeru zkus:")
    print("  $ docker login")
    print("  $ docker pull hello-world")
    print("  $ docker tag hello-world TVOJE_JMENO/hello-world:v1.0")
    print("  $ docker push TVOJE_JMENO/hello-world:v1.0")


print("\n=== Hotovo! Dalsi lekce: Co je Kubernetes? ===")

# TVOJE ULOHA:
# 1. Zaregistruj se na hub.docker.com a prihlasit se v terminalu
# 2. Otaguj libovolnou local image tvym Docker Hub jmenem
# 3. Pushni image na Docker Hub
# 4. Na hub.docker.com over ze je image viditelna

# RESENI:
# 1. docker login   (zadej uzivatelske jmeno a token/heslo)
# 2. docker tag nginx TVOJE_JMENO/muj-nginx:v1.0
# 3. docker push TVOJE_JMENO/muj-nginx:v1.0
# 4. Jdi na https://hub.docker.com/r/TVOJE_JMENO/muj-nginx
