# AeroCentre - Cyber-range de gestion de crise (aéroport)

🚧 **Work in progress**&#32;

## 1. Présentation du projet

AeroCentre est un aéroport régional fictif victime d'une attaque simulée. Le projet construit un cyber-range permettant de jouer cette crise de bout en bout : compromission technique, détection, et réaction d'une équipe SOC face à une équipe DSI (nous).

Le scénario s'appuie sur deux incidents réels documentés : la compromission du logiciel MUSE chez Collins Aerospace (Europe, septembre 2025) et le rançongiciel Rhysida contre le Port de Seattle et l'aéroport Sea-Tac (août 2024).

**Important : tout est simulé.** Aucun vrai malware, aucun vrai chiffrement, aucune donnée réelle. Les injects sont orchestrés par OpenAEV sur des machines et des données entièrement fictives.

## 2. Architecture

L'infrastructure repose sur un hôte Proxmox unique (disque 500 Go). Des services permanents (OPNsense, ELK ou Wazuh, OpenAEV, Ludus) survivent à la suppression du range. Le cyber-range AeroCentre, déployé par Ludus, compte 5 VLAN et 12 VM cibles ; aucun VLAN ne communique directement avec un autre, tout passe par le routeur du range.

Schéma de référence : voir le dossier `architecture/`.

Détail complet de l'adressage et des flux autorisés/bloqués : voir le document `p``l``a``n``_``a``d``re``s``s``a``g``e``.``m``d`.

## 3. Acteurs fictifs

- **AeroCentre SA** : exploitant de la plateforme (enregistrement, bagages, sûreté, IT générale).
- **Prestataires et partenaires** : compagnies aériennes et services externes, connectés uniquement à la DMZ.
- **Équipe DSI** (nous) : conçoit l'architecture, construit le range, écrit le scénario d'attaque et anime l'exercice.
- **Équipe SOC** (groupe adverse) : défend le système, détecte l'attaque et y réagit, à partir du dossier joueur uniquement.

## 4. Outils

Proxmox héberge tout. WireGuard est le seul accès admin. OPNsense filtre les flux. Ludus déploie le range. ELK ou Wazuh supervise. OpenAEV orchestre le scénario. OpenCTI documente les menaces réelles.

## 5. VLAN et machines

| VLAN | Nom | Machines |
| --- | --- | --- |
| 10 | DMZ | FIDS-Web, DCS-Server |
| 20 | Opérations | BHS-DB, BHS-PLC, Poste-Agent |
| 30 | Administration | AD-DC, Poste-Admin, Mattermost |
| 40 | Douane | Douane-App, Poste-Douane |
| 50 | Sûreté | Badge-Server, PKI-Chiffrement |

Adressage complet, IP par machine et flux détaillés : voir le document **Plan d'adressage**.

## 6. Comment tout fonctionne ensemble

1. L'administrateur se connecte via WireGuard au serveur Proxmox.
2. OPNsense filtre tous les flux entre les zones permanentes et le range.
3. Ludus déploie le cyber-range AeroCentre : VM, VLAN, adressage.
4. OpenAEV pilote le scénario : il déclenche les injects sur les bonnes machines, au bon moment.
5. Les VM exécutent les actions et génèrent leurs traces normalement ; un agent les envoie à ELK.
6. L'équipe SOC analyse les alertes dans Kibana et réagit.

## 7. Sources

- Compromission du logiciel MUSE chez Collins Aerospace, Europe, septembre 2025 (perturbation de l'enregistrement et des bagages dans plusieurs grands aéroports). [TechRepublic — confirmation ENISA](https://www.techrepublic.com/article/news-eu-airport-ransomware/) · [Wikipedia — Collins Aerospace cyberattack](https://en.wikipedia.org/wiki/Collins_Aerospace_cyberattack)
- Rançongiciel Rhysida contre le Port de Seattle et l'aéroport Sea-Tac, août 2024 (bagages, enregistrement, écrans de vols, vol de données). [Port of Seattle — archive officielle](https://www.portseattle.org/news/port-cyberattack-archive) · [CSOonline — confirmation Rhysida](https://www.csoonline.com/article/3523601/port-of-seattle-says-august-cyberattack-was-rhysida-ransomware.html)

Sources primaires et détail complet, avec distinction entre faits établis et hypothèses : voir le document `présentation_attaques``.md`.
