# Rôle `pki`

Autorité de certification interne d'AeroCentre.

- **Machine** : `pki` (zone Sûreté, VLAN 50), 10.100.50.12
- **Système** : Debian 13 (trixie), modules `ansible.builtin` uniquement
- **Flux concerné** : F (badge-server, douane-app, dcs-server, fids-web -> pki, TCP 80 et 443)

## Ce que fait le rôle

1. Installe `openssl` et `nginx`.
2. Crée une **CA racine** (clé RSA 4096, certificat valable 10 ans) dans `/etc/pki-aero/`.
3. Émet à l'avance un **certificat serveur** (RSA 2048, 825 jours) pour chaque machine de la liste `pki_hosts`, avec les noms DNS et l'IP en SAN.
4. Publie avec nginx (ports 80 et 443) :
   - `/ca.crt` : le certificat racine, en accès libre ;
   - `/enroll/<machine>.crt` et `/enroll/<machine>.key` : les certificats émis, protégés par mot de passe (HTTP Basic).
5. Le site HTTPS de la PKI utilise son propre certificat, signé par la CA.

Le rôle est idempotent : les clés et certificats existants ne sont jamais régénérés.

## Variables (`defaults/main.yml`)

| Variable | Défaut | Rôle |
|---|---|---|
| `pki_ca_name` | `AeroCentre Root CA` | Nom (CN) de la CA racine |
| `pki_domain` | `aerocentre.lan` | Domaine des noms DNS dans les certificats |
| `pki_dir` | `/etc/pki-aero` | Dossier privé de la CA (mode 0700) |
| `pki_web_root` | `/var/www/pki` | Dossier publié par nginx |
| `pki_enroll_user` | `enroll` | Utilisateur du dossier `/enroll/` |
| `pki_enroll_password` | `Enroll-Labo-2026` | Mot de passe de labo de `/enroll/` |
| `pki_hosts` | liste (voir ci-dessous) | Machines pour lesquelles un certificat est émis |

`pki_hosts` est une liste (non modifiable depuis le formulaire CYO, à changer dans le rôle) :
`pki` 10.100.50.12, `fids-web` 10.100.10.11, `dcs-server` 10.100.10.12, `douane-app` 10.100.40.11, `badge-server` 10.100.50.11.

## Comptes de labo

| Accès | Identifiant | Mot de passe |
|---|---|---|
| `/enroll/` (certificats et clés) | `enroll` | `Enroll-Labo-2026` |

Mot de passe de **labo uniquement** : il ne doit apparaître que dans `defaults/` et dans ce README.
Les clés privées émises sont téléchargeables avec ce mot de passe : c'est voulu pour le TP (ne pas reproduire en production).

## Comment tester

Sur la VM (en root) :

```bash
tail -n 5 /var/log/cyo-ansible.log          # PLAY RECAP avec failed=0
ss -tlnp | grep -E ':80 |:443 '             # nginx écoute sur 0.0.0.0:80 et 0.0.0.0:443
nginx -t                                    # syntax is ok / test is successful

curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/ca.crt                 # 200
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/enroll/fids-web.crt    # 401
curl -s -o /dev/null -w '%{http_code}\n' -u enroll:Enroll-Labo-2026 http://127.0.0.1/enroll/fids-web.crt   # 200

openssl verify -CAfile /etc/pki-aero/ca.crt /etc/pki-aero/issued/fids-web.crt
# /etc/pki-aero/issued/fids-web.crt: OK

curl -s --cacert /etc/pki-aero/ca.crt --resolve pki.aerocentre.lan:443:127.0.0.1 \
  -o /dev/null -w '%{http_code}\n' https://pki.aerocentre.lan/ca.crt             # 200
```

Test du flux F depuis une autre VM d'AeroCentre :

```bash
timeout 3 bash -c '</dev/tcp/10.100.50.12/443'; echo $?
# 0 = ouvert, "connexion refusée" = rien n'écoute, 124 = bloqué par le routeur
```

Idempotence : rejouer le rôle doit donner `changed=0`.

## Récupérer un certificat depuis un serveur

```bash
curl -fsSL http://10.100.50.12/ca.crt -o /usr/local/share/ca-certificates/aerocentre-ca.crt
update-ca-certificates
curl -fsS -u enroll:Enroll-Labo-2026 -O https://10.100.50.12/enroll/<machine>.crt
curl -fsS -u enroll:Enroll-Labo-2026 -O https://10.100.50.12/enroll/<machine>.key
```

## Dépannage

| Symptôme | Cause / solution |
|---|---|
| `nginx -t` : duplicate default server | Le site `default` est encore actif : `rm /etc/nginx/sites-enabled/default` |
| nginx : Address already in use | Un autre service occupe le port : `ss -tlnp \| grep ':80'` |
| `curl: (60) SSL certificate problem` | Normal sans `--cacert` : la racine n'est pas dans le magasin de confiance |
| Le certificat d'une machine est absent | Machine absente de `pki_hosts` (ajouter, supprimer `/etc/pki-aero/issued/<nom>.*` si besoin, rejouer) |

## Notes

- Dans un premier temps, des certificats auto-signés suffisent aux autres rôles ; la PKI est utilisable quand ils seront prêts.
- Le DNS `pki.aerocentre.lan` est fourni par dnsmasq sur le routeur.
