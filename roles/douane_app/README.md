# Rôle `douane_app`

Application des manifestes passagers de la douane : elle lit le DCS en HTTPS (flux D) et garde une copie locale en SQLite.

- **Machine** : `douane-app` (zone Douane, VLAN 40), 10.100.40.11
- **Système** : Debian 13 (trixie), modules `ansible.builtin` uniquement
- **Port** : TCP 8080 (HTTP, zone Douane)
- **Dépendances** : `python3` et `sqlite3` (paquets Debian, aucun paquet `pip`)
- **Flux D** : douane-app -> dcs-server, TCP 443

## Ce que fait le rôle

1. Installe `python3`, `sqlite3` et `ca-certificates`.
2. Crée l'utilisateur système `douane` (sans shell) et les dossiers `/opt/douane` et `/var/lib/douane`.
3. Déploie l'application `douane_app.py` (serveur HTTP de la bibliothèque standard).
4. Installe l'unité systemd `douane.service` (démarrage automatique, logs dans `journalctl`).

À chaque appel de `/manifestes`, l'application interroge le DCS, enregistre le résultat dans `/var/lib/douane/douane.db` puis le renvoie.
Si le DCS est injoignable, elle renvoie les dernières données reçues (`"source": "cache"`) avec le message d'erreur.

## Contrat d'API avec le DCS (à valider avec mbourric)

`GET https://dcs-server/api/passagers` doit renvoyer une liste JSON d'objets :

```json
[{"id": 1, "nom": "Dupont", "vol": "AF123", "passeport": "12AB34567", "statut": "embarque"}]
```

Champs attendus : `id`, `nom`, `vol`, `passeport`, `statut`. L'URL se règle avec `douane_dcs_url`.

## Variables (`defaults/main.yml`)

| Variable | Défaut | Rôle |
|---|---|---|
| `douane_listen` | `0.0.0.0` | Adresse d'écoute |
| `douane_port` | `8080` | Port d'écoute |
| `douane_dir` | `/opt/douane` | Dossier de l'application |
| `douane_db_dir` | `/var/lib/douane` | Dossier de la base SQLite |
| `douane_dcs_url` | `https://10.100.10.12/api/passagers` | URL de l'API du DCS |
| `douane_dcs_verify` | `false` | `true` : vérifier le certificat du DCS (`false` tant qu'il est auto-signé) |

## Comptes de labo

Aucun compte : l'application n'a pas d'authentification (labo). Les données (passeports, noms) sont **fictives**.

## Flux réseau

- Sortant : flux D vers `dcs-server:443`. Le certificat du DCS est auto-signé au début, d'où `douane_dcs_verify: false`.
- Entrant : aucun flux inter-zones vers le port 8080 : joignable depuis la zone Douane (par exemple `poste-douane`) et en SSH depuis l'hôte Proxmox (flux I).

## Comment tester

### Test autonome avec un faux DCS (VM de test, en root)

```bash
mkdir -p /tmp/fake/api
cat > /tmp/fake/api/passagers <<'JSON'
[{"id":1,"nom":"Dupont","vol":"AF123","passeport":"12AB34567","statut":"embarque"},
 {"id":2,"nom":"Moreau","vol":"AF123","passeport":"98ZX76543","statut":"enregistre"}]
JSON
cd /tmp/fake && nohup python3 -m http.server 8000 >/dev/null 2>&1 &

ANSIBLE_ROLES_PATH=/root/repo/roles ansible-playbook -c local -i localhost, /root/play.yml \
  -e douane_dcs_url=http://127.0.0.1:8000/api/passagers
```

Puis :

```bash
systemctl status douane --no-pager | head -5   # active (running)
ss -tlnp | grep 8080                           # 0.0.0.0:8080 ... python3
curl -s localhost:8080/health                  # {"status": "ok"}
curl -s localhost:8080/manifestes
# {"source": "dcs", "erreur": null, "manifestes": [{"id": "1", "nom": "Dupont", ...}, ...]}
```

Mode dégradé : arrêter le faux DCS (`kill %1`), refaire `curl -s localhost:8080/manifestes` : `"source": "cache"`, avec l'erreur et les données déjà reçues.

### Test dans AeroCentre (flux D)

```bash
timeout 3 bash -c '</dev/tcp/10.100.10.12/443'; echo $?
# 0 = ouvert, "connexion refusée" = le DCS n'écoute pas encore, 124 = bloqué par le routeur
curl -s localhost:8080/manifestes
```

Journaux : `journalctl -u douane -n 20 --no-pager` et `tail -n 5 /var/log/cyo-ansible.log` (`failed=0`).

Idempotence : rejouer le rôle doit donner `changed=0`.

## Dépannage

| Symptôme | Cause / solution |
|---|---|
| `"erreur": "... Connection refused"` | Le DCS n'écoute pas encore (rôle `dcs_server` non déployé) |
| `"erreur": "... timed out"` | Flux D bloqué ou mauvaise IP : tester avec `/dev/tcp` |
| `CERTIFICATE_VERIFY_FAILED` | `douane_dcs_verify` à `true` avec un certificat auto-signé : remettre `false` |
| Erreur de lecture JSON ou `KeyError: 'id'` | Le DCS ne respecte pas le format convenu avec mbourric |
| `unable to open database file` | `chown -R douane:douane /var/lib/douane` |
