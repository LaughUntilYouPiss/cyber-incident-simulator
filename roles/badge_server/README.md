# Rôle `badge_server`

Serveur de droits d'accès par badges d'AeroCentre : petite API HTTP et base SQLite locale.

- **Machine** : `badge-server` (zone Sûreté, VLAN 50), 10.100.50.11
- **Système** : Debian 13 (trixie), modules `ansible.builtin` uniquement
- **Port** : TCP 8080 (HTTP)
- **Dépendances** : `python3` et `sqlite3` (paquets Debian, aucun paquet `pip`)

## Ce que fait le rôle

1. Installe `python3` et `sqlite3`.
2. Crée l'utilisateur système `badge` (sans shell) et les dossiers `/opt/badge` et `/var/lib/badge`.
3. Déploie l'application `badge_app.py` (serveur HTTP de la bibliothèque standard).
4. Initialise la base `/var/lib/badge/badges.db` avec 5 badges de labo (script SQL rejouable).
5. Installe l'unité systemd `badge.service` (démarrage automatique, logs dans `journalctl`).

Le rôle est idempotent : les badges existants ne sont pas dupliqués.

## Flux réseau

- Flux sortants du serveur : E (vers `ad-dc`) et F (vers `pki`), à utiliser plus tard si l'appli est étendue.
- Aucun flux entrant n'est prévu vers le port 8080 : le service n'est joignable que depuis la zone Sûreté (par exemple `pki`) et en SSH depuis l'hôte Proxmox (flux I).
  Pour l'ouvrir à d'autres zones, ajouter un flux dans le routeur.

## Variables (`defaults/main.yml`)

| Variable | Défaut | Rôle |
|---|---|---|
| `badge_listen` | `0.0.0.0` | Adresse d'écoute |
| `badge_port` | `8080` | Port d'écoute |
| `badge_dir` | `/opt/badge` | Dossier de l'application |
| `badge_db_dir` | `/var/lib/badge` | Dossier de la base SQLite |

## Données de labo

| Badge | Titulaire | Zones autorisées | Actif |
|---|---|---|---|
| B001 | agent.martin | operations | oui |
| B002 | admin.durand | administration, operations | oui |
| B003 | douane.leroy | douane | oui |
| B004 | surete.petit | surete, operations, douane, administration | oui |
| B005 | ancien.employe | operations | non (badge désactivé) |

Les titulaires correspondent aux utilisateurs de l'AD (`ad_dc`). Il n'y a **pas de mot de passe** : l'API n'a pas d'authentification (labo).

## API

| Requête | Réponse |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /badges` | liste JSON des badges |
| `GET /access?badge=B001&zone=operations` | `granted: true` (HTTP 200) ou `granted: false` (HTTP 403) |

## Comment tester

Sur la VM (en root) :

```bash
tail -n 5 /var/log/cyo-ansible.log             # PLAY RECAP avec failed=0
systemctl status badge --no-pager | head -5    # active (running)
ss -tlnp | grep 8080                           # 0.0.0.0:8080 ... python3

curl -s localhost:8080/health
# {"status": "ok"}
curl -s "localhost:8080/access?badge=B001&zone=operations"
# {"badge": "B001", "zone": "operations", "granted": true}
curl -s -w ' -> %{http_code}\n' "localhost:8080/access?badge=B001&zone=douane"
# {"badge": "B001", "zone": "douane", "granted": false} -> 403
curl -s "localhost:8080/access?badge=B005&zone=operations"
# granted: false (badge désactivé)

sqlite3 /var/lib/badge/badges.db "select * from badges;"
journalctl -u badge -n 5 --no-pager            # une ligne par requête
```

Test depuis une autre VM de la zone Sûreté :

```bash
timeout 3 bash -c '</dev/tcp/10.100.50.11/8080'; echo $?
# 0 = ouvert, "connexion refusée" = rien n'écoute, 124 = bloqué par le routeur
```

Idempotence : rejouer le rôle doit donner `changed=0`.

## Dépannage

| Symptôme | Cause / solution |
|---|---|
| `unable to open database file` | `/var/lib/badge` n'appartient pas à `badge` : `chown -R badge:badge /var/lib/badge` |
| Address already in use | Ancien processus : `systemctl restart badge` |
| `/badges` renvoie une liste vide | SQL non appliqué : `sqlite3 /var/lib/badge/badges.db ".read /opt/badge/init_badges.sql"` |
| Injoignable depuis une autre zone | Normal : aucun flux autorisé vers le port 8080 |
