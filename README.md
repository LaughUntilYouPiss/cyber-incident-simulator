====================================================================
  AEROCENTRE - Cyber-range de gestion de crise (ransomware aeroport)
  Projet INSA Centre-Val de Loire (Bourges) - Gestion de crise cyber
====================================================================

1. PRESENTATION DU PROJET
-------------------------
AeroCentre est un aeroport regional fictif (~2,5 millions de passagers
par an) victime d'une attaque par ransomware. Le projet consiste a
construire un cyber-range (environnement simule) permettant de jouer
cette crise de bout en bout : attaque, detection, reponse technique et
gestion de crise (decisions de la direction, communication, juridique).

Le scenario fusionne trois sources reelles :
  - Dynamique d'impact : cas des aeroports de Montpellier et de
    Seattle-Tacoma (bagagerie, ecrans de vols, enregistrement et
    embarquement en mode manuel).
  - Techniques d'attaque : groupe Rhysida, documentees dans l'advisory
    CISA AA23-319A (cartographie MITRE ATT&CK).
  - Dimension multi-acteurs : cas Collins Aerospace / Heathrow
    (plusieurs entites dependent d'un meme prestataire).

IMPORTANT : tout est SIMULE. Aucun vrai malware, aucun vrai chiffrement,
aucune exfiltration de donnees reelles (fichiers factices, injects
OpenAEV et tests atomiques).


2. SCHEMA D'ARCHITECTURE
------------------------
Voir l'image : Architecture_globale_du_cyber-range_AeroCentre.png

  ![Architecture globale](Architecture_globale_du_cyber-range_AeroCentre.png)

Vue simplifiee en texte :

  Admin (distant/local)
        |
   [WireGuard VPN]
        |
        v
  +--------------------------- Serveur physique Proxmox ---------------------------+
  |  Services permanents : OPNsense | Wazuh/ELK | OpenAEV      Environnement Ludus  |
  +----------------------------------------+-------------------------------------+
                                           |
                                  [OPNsense - pare-feu]
                    +----------------------+-----------------------+
                    |                      |                       |
          Zone de Transit Ludus   Zone de Supervision      Zone d'Exercice
          (routeur du range)      (Wazuh / ELK)            (OpenAEV)
                    |                      |                       |
                    +----------------------+-----------------------+
                                           |
              +----------------- CYBER-RANGE AeroCentre -----------------+
              |                                                           |
              |  VLAN 10 - DMZ Operations   10.10.0.0/24   (expose)       |
              |     DCS-Server, FIDS-Web                                  |
              |  VLAN 20 - LAN Operations   10.20.0.0/24   (metier)       |
              |     BHS-DB, Poste Agent (SkyHandle)                       |
              |  VLAN 30 - LAN Admin        10.30.0.0/24   (sensible)     |
              |     AD-DC, Poste Admin (IT), SIEM local                   |
              +-----------------------------------------------------------+
                   ^                                          ^
        Ressources externes                       Supervision & acces
     (partenaires, Internet)                (dashboards, alertes, acces admin)


3. LES ACTEURS FICTIFS
----------------------
  - AeroCentre SA : exploitant de la plateforme (pistes, batiments,
    surete, IT generale).
  - SkyHandle : sous-traitant d'assistance en escale, gere le DCS
    (Departure Control System) et le BHS (Baggage Handling System).
  - FlyCentre : compagnie partenaire, dependante des systemes de
    SkyHandle.

Cellule de crise : Direction generale, RSSI/DSI, responsable
exploitation piste et bagagerie, responsable surete, communication /
relations compagnies.

Dilemme central a jouer : couper par precaution des systemes non
touches (risque de degrader l'exploitation) ou les laisser tourner
(risque de propagation).


4. LES OUTILS ET LEUR ROLE
--------------------------

  PROXMOX (hyperviseur)
    Serveur physique qui heberge tout le projet. Il fait tourner les
    services permanents (pare-feu, SIEM, orchestration) et
    l'environnement Ludus. Interface web pour creer / cloner / gerer
    les VM. Contrainte : disque limite a 500 Go.

  WIREGUARD (VPN)
    Seul point d'entree pour l'administration, a distance comme en
    local. Tout acces admin a Proxmox et a l'infrastructure passe par
    le VPN.

  OPNSENSE (pare-feu de perimetre)
    Passerelle de toute l'infrastructure. Il filtre et controle les
    flux entre les zones (Transit, Supervision, Exercice) et entre les
    VLAN du cyber-range (routage inter-VLAN). Les flux autorises, bloques
    et de logs sont distingues dans la legende du schema.

  LUDUS (deploiement des cyber-ranges)
    Outil qui construit automatiquement le range AeroCentre a partir
    d'un fichier de configuration (range-config.yml) et de templates de
    VM (Debian, Kali, Windows 11, Windows Server 2022). Il gere un
    routeur de range dans la "Zone de Transit" qui relie le range au
    reste de l'infrastructure.

  WAZUH / ELK (SIEM - supervision et detection)
    Collecte et analyse centralisee des logs du cyber-range (Windows
    Event Logs, Sysmon / Winlogbeat, logs reseau). Les alertes et
    dashboards (Kibana) servent a la Blue Team pour detecter l'attaque.
    Il est place hors des segments compromis. Un SIEM local dans le
    VLAN 30 collecte les logs au plus pres des machines.

  OPENAEV (orchestration d'exercices)
    Plateforme de scenarios, injects et playbooks. Elle declenche les
    etapes de l'attaque simulee et les injects de crise (appel de
    FlyCentre, sollicitation presse, question RGPD...). Elle peut
    consommer les donnees d'OpenCTI pour generer un scenario fonde sur
    la menace reelle.

  OPENCTI (renseignement sur la menace)
    Base de connaissances sur les menaces. On y recherche l'intrusion
    set "Rhysida" (techniques MITRE liees, rapport CISA, indicateurs)
    pour construire des injects realistes plutot que de les inventer.


5. DETAIL DES ZONES ET DES VLAN
-------------------------------
  Zone de Transit (Ludus)
    Connectivite des ranges, routeur gere par Ludus.
  Zone de Supervision (SIEM & detection)
    Wazuh / ELK : collecte et analyse des logs.
  Zone d'Exercice (scenarios & injects)
    OpenAEV : scenarios, injects, playbooks.

  Cyber-range AeroCentre (environnement simule) :

  VLAN 10 - DMZ Operations (10.10.0.0/24) - EXPOSE
    - DCS-Server : enregistrement / embarquement
    - FIDS-Web   : ecrans d'affichage des vols
    Expose aux compagnies partenaires.

  VLAN 20 - LAN Operations (10.20.0.0/24) - METIER
    - BHS-DB       : gestion des bagages
    - Poste Agent  : poste SkyHandle (vecteur d'acces initial possible)

  VLAN 30 - LAN Admin (10.30.0.0/24) - SENSIBLE
    - AD-DC        : annuaire Active Directory
    - Poste Admin  : poste IT (acces VPN distant vers le DCS)
    - SIEM Local   : collecte des logs


6. COMMENT TOUT FONCTIONNE ENSEMBLE
-----------------------------------
  1. L'administrateur se connecte via WireGuard au serveur Proxmox.
  2. Proxmox heberge les services permanents (OPNsense, Wazuh/ELK,
     OpenAEV) et Ludus.
  3. Ludus deploie le cyber-range AeroCentre (VM, VLAN, adressage) et
     le relie a l'infrastructure via la zone de transit.
  4. OPNsense filtre tous les flux entre zones et entre VLAN.
  5. OpenAEV (zone d'exercice) pilote le scenario : il injecte les
     etapes de l'attaque et les evenements de crise dans le range.
  6. Les machines du range envoient leurs logs / telemetrie a
     Wazuh / ELK (zone de supervision), ce qui produit les alertes.
  7. L'equipe (Blue Team / cellule de crise) analyse les alertes via
     les dashboards, gere la crise et pilote l'exercice.
  8. Les partenaires (compagnies aeriennes) et Internet accedent
     uniquement a la DMZ (VLAN 10), jamais directement aux VLAN 20/30.

Points cles :
  - Separation par VLAN (10 / 20 / 30)
  - Controle des flux par OPNsense
  - Supervision centralisee (SIEM)
  - Orchestration des exercices (OpenAEV)


7. SCENARIO D'ATTAQUE (RHYSIDA - CISA AA23-319A)
------------------------------------------------
  Etape                     MITRE ATT&CK         Dans AeroCentre
  ------------------------  -------------------  ----------------------------------
  1. Acces initial          T1078, T1133         Compromission du VPN du poste admin
  2. Reconnaissance         T1082, T1033, T1069, Enumeration du domaine AD
                            T1018, T1482
  3. Mouvement lateral      T1021.001 (RDP)      Pivot poste admin -> DCS-Server
  4. Persistance/execution  T1053, T1055         Tache planifiee sur le DCS
  5. Exfiltration           T1071                Exfiltration simulee de la BHS-DB
  6. Inhibition recuperation T1490               Suppression simulee des shadow copies
  7. Impact                 T1486, T1657         Chiffrement simule, FIDS incoherent,
                                                 enregistrement bloque

  Les etapes 5 a 7 sont simulees (fichiers factices).

  Traces de detection a observer dans Kibana (a confirmer avec
  l'advisory CISA) : evenements Windows 4624/4625 (connexions, type 10
  pour RDP), 4688 et Sysmon 1 (creation de processus), 4698 (tache
  planifiee), Sysmon 3 (connexions reseau sortantes), commandes
  vssadmin / wmic (suppression des shadow copies).


8. EVOLUTION DE L'ARCHITECTURE (DECISION APRES ECHANGE AVEC L'ENCADRANT)
-----------------------------------------------------------------------
Suite a la discussion avec notre professeur, nous avons decide
d'AUGMENTER LE NOMBRE DE VM par rapport a la version initiale (8 VM)
afin de COMPLEXIFIER L'ARCHITECTURE et de rendre l'exercice plus
realiste et plus riche pour la Blue Team :

  - Plus de machines a surveiller et a proteger.
  - Plus de chemins possibles pour l'attaquant (mouvement lateral
    plus varie).
  - Plus de volume et de diversite dans les logs a analyser dans le
    SIEM, donc une detection plus difficile.
  - Un scenario de crise plus credible (SI d'aeroport reel plus
    etendu).

Le schema ci-dessus represente la version de base ; il sera mis a jour
une fois la liste definitive des VM supplementaires arretee, en
respectant les contraintes du projet (templates disponibles, plan
d'adressage impose, disque de 500 Go).

  [ ] Definir la liste des VM supplementaires
  [ ] Mettre a jour le schema et le plan d'adressage
  [ ] Mettre a jour les regles OPNsense et la collecte de logs SIEM
  [ ] Adapter le scenario d'attaque et les injects OpenAEV


9. DEMO LUDUS (PRISE EN MAIN)
-----------------------------
Mini-infrastructure de demonstration : 1 serveur Mattermost + 2 clients
Linux sur le VLAN 10 (Debian 12). Les noms de templates et plages d'IP
sont a adapter a l'instance (voir "ludus templates list").

  ludus:
    - vm_name: "{{ range_id }}-mattermost-srv"
      hostname: "{{ range_id }}-mattermost-srv"
      template: debian-12-x64-server-template
      vlan: 10
      ip_last_octet: 10
      ram_gb: 4
      cpus: 2
      linux: true
    - vm_name: "{{ range_id }}-client-1"
      hostname: "{{ range_id }}-client-1"
      template: debian-12-x64-server-template
      vlan: 10
      ip_last_octet: 11
      ram_gb: 2
      cpus: 1
      linux: true
    - vm_name: "{{ range_id }}-client-2"
      hostname: "{{ range_id }}-client-2"
      template: debian-12-x64-server-template
      vlan: 10
      ip_last_octet: 12
      ram_gb: 2
      cpus: 1
      linux: true

Etapes :
  1. Deployer le range puis recuperer l'IP avec "ludus range status".
  2. SSH sur le serveur Mattermost et lancer (usage demo uniquement) :
     docker run --name mattermost-preview -d --publish 8065:8065 mattermost/mattermost-preview
  3. Depuis les 2 clients, ouvrir http://<ip-mattermost>:8065, creer
     un compte, rejoindre la meme equipe et le meme canal.
  4. Poster des messages entre les deux clients.


10. CALENDRIER
--------------
  - Range et scenario operationnels : mi-janvier.
  - Ensuite : tests atomiques, repetition complete, exercice Blue Team
    face a un autre groupe.


11. SOURCES
-----------
  - CISA, FBI, MS-ISAC : #StopRansomware: Rhysida Ransomware,
    advisory AA23-319A (source primaire).
  - Cas reels etudies : aeroports de Montpellier, Seattle-Tacoma,
    Heathrow / Collins Aerospace (a completer par des sources primaires :
    communiques officiels, rapports d'autorites, retours d'experience).
  - Equivalences fictives : DCS ~ MUSE, BHS-DB ~ BRS (analogies
    pedagogiques).


12. STRUCTURE DU DEPOT
----------------------
  /
  |-- README.txt
  |-- Architecture_globale_du_cyber-range_AeroCentre.png
  |-- (range-config.yml, scenarios, docs ... a ajouter)

====================================================================
