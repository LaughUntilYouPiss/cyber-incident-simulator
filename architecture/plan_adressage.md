# Plan d'adressage AeroCentre

Référence : architecture cible du laboratoire, 5 VLAN, 12 VM cibles + routeur Ludus.

## Convention d'adressage

Ludus attribue automatiquement les réseaux selon l'identifiant du range, sous la forme :

```
10.<n° du range>.<VLAN>.<hôte>
```

Dans ce document, `<n° du range>` est noté `X` à titre d'exemple. Remplacer par la valeur réelle donnée par Ludus au moment du déploiement, et mettre ce document à jour en conséquence.

## Vue d'ensemble des VLAN

| VLAN | Nom | Plage | Exposition |
| --- | --- | --- | --- |
| 10 | DMZ | 10.X.10.0/24 | Exposée à Internet et aux partenaires |
| 20 | Opérations | 10.X.20.0/24 | Cœur métier, non exposée directement |
| 30 | Administration | 10.X.30.0/24 | Zone sensible, identité et postes IT |
| 40 | Douane | 10.X.40.0/24 | Données passagers |
| 50 | Sûreté | 10.X.50.0/24 | Badges et chiffrement |

Aucun VLAN ne communique directement avec un autre. Tout passe par le routeur du range (Ludus), qui applique les règles de filtrage entre réseaux internes. OPNsense gère l'entrée et la sortie du range (WAN, trunk des zones permanentes).

## Adressage détaillé par machine

### VLAN 10 : DMZ (10.X.10.0/24)

| Machine | IP | Rôle |
| --- | --- | --- |
| FIDS-Web | 10.X.10.10 | Debian, affichage des vols |
| DCS-Server | 10.X.10.20 | Debian, enregistrement des passagers |

### VLAN 20 : Opérations (10.X.20.0/24)

| Machine | IP | Rôle |
| --- | --- | --- |
| BHS-DB | 10.X.20.10 | Debian, base des bagages |
| BHS-PLC | 10.X.20.20 | Debian, automate de tri (API de commande) |
| Poste-Agent | 10.X.20.50 | Windows 11, poste SkyHandle |

### VLAN 30 : Administration (10.X.30.0/24)

| Machine | IP | Rôle |
| --- | --- | --- |
| AD-DC | 10.X.30.10 | Server 2022, annuaire et DNS |
| Poste-Admin | 10.X.30.20 | Windows 11, poste IT |
| Mattermost | 10.X.30.30 | Debian, messagerie interne |

### VLAN 40 : Douane (10.X.40.0/24)

| Machine | IP | Rôle |
| --- | --- | --- |
| Douane-App | 10.X.40.10 | Debian, manifestes passagers |
| Poste-Douane | 10.X.40.20 | Debian XFCE, poste agent douane |

### VLAN 50 : Sûreté (10.X.50.0/24)

| Machine | IP | Rôle |
| --- | --- | --- |
| Badge-Server | 10.X.50.10 | Debian, droits d'accès aux badges |
| PKI-Chiffrement | 10.X.50.20 | Debian, certificats et clés |

## Services permanents (hors range, non supprimés avec lui)

| Service | Rôle | Réseau |
| --- | --- | --- |
| OPNsense | Pare-feu de périmètre, WAN, trunk, VPN | Interconnecte toutes les zones |
| Wazuh ou ELK | Collecte et détection des logs | Zone Supervision |
| OpenAEV | Orchestration des scénarios et injects | Zone OpenAEV |
| Ludus | Déploiement du range | Zone Transit |

## Flux autorisés

Tout le reste est refusé par défaut au niveau du routeur Ludus.

| Repère | Flux | Détail |
| --- | --- | --- |
| A | Internet et partenaires → OPNsense → routeur Ludus → DMZ | Limité à FIDS-Web et DCS-Server |
| B | DCS-Server → BHS-DB | Port de la base de données uniquement |
| C | BHS-DB → BHS-PLC | Commande de tri via l'API dédiée |
| D | Douane-App → DCS-Server | Lecture du manifeste, sens unique, chiffré (TLS) |
| E | Postes, Douane-App, Badge-Server → AD-DC | DNS, Kerberos, LDAP |
| F | PKI-Chiffrement → Badge-Server, Douane-App | Délivrance des certificats TLS |
| G | Toutes les VM → Wazuh ou ELK | Logs uniquement, sens unique |
| H | Agents OpenAEV des VM → OpenAEV | HTTPS, initié par la VM (à vérifier selon la version) |
| I | Administrateurs → OPNsense | Uniquement via WireGuard |

## Flux explicitement bloqués

| Flux | Raison |
| --- | --- |
| DMZ → Administration, Douane, Sûreté | La DMZ est la seule zone exposée ; aucun accès direct aux zones internes |
| Internet → Opérations, Administration, Douane, Sûreté | Seule la DMZ est atteignable depuis l'extérieur |
| Toute connexion vers la gestion Proxmox | Réservée aux administrateurs, hors du plan réseau du range |
