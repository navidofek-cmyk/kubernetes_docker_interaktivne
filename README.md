# Docker & Kubernetes — interaktivní kurz

Interaktivní kurz pro úplné začátečníky. Od prvního `docker run` po produkční Kubernetes cluster.

**Web kurzu: https://navidofek-cmyk.github.io/kubernetes_docker_interaktivne/**

---

## Co te ceka?

### Docker (lekce 01–07)
| Lekce | Téma |
|-------|------|
| 01 | Co je Docker? Kontejnery a základní pojmy |
| 02 | Tvůj první kontejner |
| 03 | Dockerfile — napiš vlastní recept |
| 04 | Images a vrstvy — jak Docker šetří místo |
| 05 | Volumes — trvalá data |
| 06 | Docker Compose — více kontejnerů najednou |
| 07 | Docker Hub — sdílení images |

### Kubernetes (lekce 08–15)
| Lekce | Téma |
|-------|------|
| 08 | Co je Kubernetes? |
| 09 | První Pod |
| 10 | Deployment — Kubernetes hlídá tvoje aplikace |
| 11 | Service — stabilní adresa pro Pody |
| 12 | ConfigMap a Secret — konfigurace bez hesel v kódu |
| 13 | Ingress — brána z internetu |
| 14 | Helm — balíčky pro Kubernetes |
| 15 | Kompletní projekt — od kódu po Kubernetes |

---

## Jak spustit lokálně

```bash
python3 generator_webu.py
cd web && python3 -m http.server 8080
# → http://localhost:8080
```

## Co potřebuješ mít nainstalováno

- Docker: https://docs.docker.com/get-docker/
- kubectl: https://kubernetes.io/docs/tasks/tools/
- minikube: https://minikube.sigs.k8s.io/docs/start/
