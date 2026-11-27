# Rôle `mattermost`

Messagerie interne d'AeroCentre (Mattermost, édition Team).

- **Machine** : `mattermost` (zone Admin, VLAN 30), 10.100.30.13
- **Système** : Debian 13 (trixie), modules `ansible.builtin` uniquement
- **Port** : TCP 8065
- **Ressources conseillées** : 2 Go de RAM, disque de 20 Go minimum

## Ce que fait le rôle

1. Installe PostgreSQL et crée le rôle et la base `mattermost`.
2. Télécharge le tarball officiel (`releases.mattermost.com`) dans `/opt/mattermost`.
3. Crée l'utilisateur système `mattermost` (sans shell).
4. Configure le serveur par **variables d'environnement** (`/etc/mattermost.env`) : pas d'édition de `config.json`.
5. Installe l'unité systemd `mattermost.service` (démarrage automatique).
6. Attend que l'API réponde (1 à 3 minutes au premier démarrage).
7. Crée, via `mmctl --local`, le compte administrateur et l'équipe `aerocentre`.

Le rôle est idempotent : base, rôle, administrateur et équipe ne sont créés qu'une fois.

## Flux réseau

Aucun flux inter-zones n'autorise le port 8065. Le service est joignable depuis la zone Admin (par exemple `poste-admin`) et en SSH depuis l'hôte Proxmox (flux I). Pour l'ouvrir aux autres zones, il faut ajouter un flux dans le routeur.
Les téléchargements (`apt`, tarball) passent par la sortie Internet des zones.

## Variables (`defaults/main.yml`)

| Variable | Défaut | Rôle |
|---|---|---|
| `mattermost_version` | `11.7.2` | Version du tarball (ESR au moment de l'écriture) |
| `mattermost_dir` | `/opt/mattermost` | Dossier d'installation |
| `mattermost_listen` | `0.0.0.0:8065` | Adresse et port d'écoute |
| `mattermost_site_url` | `http://10.100.30.13:8065` | URL publique du site |
| `mattermost_db_name` | `mattermost` | Nom de la base PostgreSQL |
| `mattermost_db_user` | `mmuser` | Utilisateur PostgreSQL |
| `mattermost_db_password` | `Mm-Labo-2026` | Mot de passe PostgreSQL (labo) |
| `mattermost_admin_user` | `mmadmin` | Administrateur Mattermost (`admin` est un nom réservé) |
| `mattermost_admin_email` | `mmadmin@aerocentre.lan` | E-mail de l'administrateur |
| `mattermost_admin_password` | `Admin-Labo-2026!` | Mot de passe de l'administrateur (labo) |
| `mattermost_team` | `aerocentre` | Nom technique de l'équipe créée |

Si l'URL de téléchargement ne répond plus (HTTP 403 ou 404), changer `mattermost_version` :

```bash
curl -sI https://releases.mattermost.com/<version>/mattermost-<version>-linux-amd64.tar.gz | head -1
# HTTP/2 200
```

## Comptes de labo

| Accès | Identifiant | Mot de passe |
|---|---|---|
| Interface web (administrateur système) | `mmadmin` | `Admin-Labo-2026!` |
| Base PostgreSQL | `mmuser` | `Mm-Labo-2026` |

Mots de passe de **labo uniquement** : ils ne doivent apparaître que dans `defaults/` et dans ce README.

## Comment tester

Sur la VM (en root) :

```bash
tail -n 5 /var/log/cyo-ansible.log             # PLAY RECAP avec failed=0
systemctl status mattermost --no-pager | head -5   # active (running)
ss -tlnp | grep 8065                           # 0.0.0.0:8065 ... mattermost
curl -s http://127.0.0.1:8065/api/v4/system/ping    # ... "status":"OK"
free -h                                        # vérifier la mémoire disponible
```

Interface web : ouvrir `http://10.100.30.13:8065` depuis `poste-admin` et se connecter avec `mmadmin`.
Depuis un PC, via tunnel SSH vers la VM de test : `ssh -L 8065:127.0.0.1:8065 user@<IP>` puis `http://localhost:8065`.

Idempotence : rejouer le rôle doit donner `changed=0`.

## Dépannage

| Symptôme | Cause / solution |
|---|---|
| Téléchargement en erreur 403/404 | Mauvaise version : tester avec `curl -sI` et changer `mattermost_version` |
| `password authentication failed` dans `journalctl -u mattermost` | Mot de passe PostgreSQL différent de celui de `/etc/mattermost.env` : `runuser -u postgres -- psql -c "ALTER ROLE mmuser PASSWORD '...'"` |
| Service en redémarrage permanent | Droits : `chown -R mattermost:mattermost /opt/mattermost` |
| Démarrage très long | Migrations de base au premier lancement : patienter (jusqu'à plusieurs minutes) |
| `mmctl` : socket introuvable | Vérifier `ls /var/tmp/mattermost_local.socket` et `MM_SERVICESETTINGS_ENABLELOCALMODE=true` dans `/etc/mattermost.env` |
| Mémoire insuffisante | Passer la VM à 2 Go ou plus dans CYO-Infra |
| Journal du service | `journalctl -u mattermost -n 50 --no-pager` |
