# Lekce 01 — Co je Docker?

## Predstav si krabici s obedem

Vis, jak mas ve skole krabicku s obedem? Mas tam vse co potrebujes — chlebicek, jablko, pit.
Kdyz ji otevre, vse je uvnitr. Nikoho nezajima jestli je pondeli nebo patek — krabicka ma vzdy to same.

**Docker dela totez s programy.**

Misto obeda dava do krabicky:
- program (treba webova stranka)
- vse co ten program potrebuje ke spusteni (knihovny, nastaveni, soubory)

Tato krabicka se jmenuje **kontejner**.

---

## Proc je to uzitecne?

Predstav si tento problem:

> Tomas napsal hru na svem pocitaci. Poslal ji Anicce.
> Anicce to nejede. "U me to funguje!" rika Tomas.

Znamas tento problem? :)

S Dockerem by Tomas posla cely kontejner — hru **vcetne vseho co potrebuje**.
Anicce by to jelo stejne jako Tomasovi.

---

## Docker vs. Virtualni pocitac

Mozna jsi slyset o virtualnim pocitaci (VM). Je to jako pocitac uvnitr pocitace.
Docker je chytrejsi — **sdili jadro operacniho systemu** s pocitacem, takze je rychlejsi a mensi.

```
Normalni pocitac:
+---------------------------+
|  Operacni system (Linux)  |
|  +--------+  +--------+  |
|  | App A  |  | App B  |  |
|  +--------+  +--------+  |
+---------------------------+

Docker kontejnery:
+------------------------------------------+
|       Operacni system (Linux)            |
|  +-----------+  +-----------+            |
|  | Kontejner |  | Kontejner |            |
|  |  App A    |  |  App B    |            |
|  | +soubory  |  | +soubory  |            |
|  +-----------+  +-----------+            |
+------------------------------------------+
```

Kazdy kontejner si mysli ze je sam — nevidí ostatní. Ale vsechny sdili Linux pod nimi.

---

## Dulezite pojmy

| Pojem | Co to je |
|-------|----------|
| **Image** | Recept na kontejner (jako predpis na dort) |
| **Kontejner** | Bezici instance image (dort upeceny podle receptu) |
| **Docker Hub** | Obchod s ready-made image (jako AppStore) |
| **Dockerfile** | Soubor kde napises vlastni recept |

---

## Zkusme to!

Mas nainstalovany Docker? Otevri terminal a napis:

```bash
docker --version
```

Melo by se zobrazit neco jako:
```
Docker version 24.0.5, build ced0996
```

Pokud ano — jsi pripraveny na lekci 02!

---

> **Shrnutí:** Docker bali programy do krabicek (kontejnery), aby fungovaly vsude stejne.

[Zpet na obsah](../README.md) | [Dalsi lekce — Prvni kontejner](02-prvni-kontejner.md)
