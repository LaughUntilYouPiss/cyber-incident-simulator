# AeroCentre : Présentation des attaques

Projet cyber-range · Secteur simulé : aéroport régional

## 1. Objectif de ce document

Ce document présente deux attaques réelles qui ont touché le secteur aéroportuaire, puis le scénario d'attaque que nous allons construire pour l'exercice. Il explique aussi pourquoi ce scénario est difficile à détecter, et ce qu'il apporte sur le plan pédagogique.

## 2. Deux attaques réelles du secteur aérien

Ces deux cas servent de référence pour construire un scénario réaliste. Les faits ci-dessous sont établis par la presse spécialisée et les communiqués officiels. Le détail technique exact (comment l'attaquant est entré) n'est pas public dans les deux cas.

### 2.1 Collins Aerospace — logiciel MUSE (Europe, septembre 2025)

- **Quoi :** un rançongiciel a touché les systèmes qui font fonctionner MUSE, le logiciel partagé d'enregistrement et d'embarquement utilisé par plusieurs compagnies dans de nombreux aéroports.
- **Conséquence :** plusieurs grands aéroports européens (Londres Heathrow, Bruxelles, Berlin, Dublin) ont dû repasser en enregistrement manuel pendant plusieurs jours. Des vols ont été annulés ou retardés.
- **Point clé :** l'attaque n'a pas visé directement les aéroports ni les compagnies, mais un prestataire partagé par plusieurs d'entre eux. Une seule compromission a donc eu un effet en cascade sur tout un continent.
- **Incertitudes :** le rançongiciel exact et le mode d'entrée initial ne sont pas confirmés publiquement.

### 2.2 Port de Seattle et aéroport Sea-Tac (États-Unis, août 2024)

- **Quoi :** un rançongiciel a touché les systèmes informatiques de l'autorité qui gère à la fois le port et l'aéroport de Seattle.
- **Conséquence :** pannes sur les bagages, les bornes d'enregistrement, la billetterie, les écrans d'affichage des vols, le site web et l'application mobile. Environ 90 000 personnes ont eu leurs données personnelles volées.
- **Point clé :** l'organisation a choisi d'isoler ses systèmes dès la détection, ce qui a limité les dégâts mais a aussi coupé plusieurs services en même temps. Elle a refusé de payer la rançon.
- **Incertitudes :** le vecteur d'accès initial n'est pas documenté publiquement.

### 2.3 Ce qu'on retient pour notre scénario

| Élément commun | Application à AeroCentre |
| --- | --- |
| Un service partagé ou exposé comme point d'entrée | Portail partenaires ou serveur d'enregistrement (DCS-Server) |
| Effet en cascade vers plusieurs services métier | Bagages, écrans de vols, données passagers |
| Vecteur d'entrée initial flou dans les faits réels | Nous le définissons nous-mêmes, de façon réaliste |

## 3. Notre scénario d'attaque

### 3.1 Résumé en une phrase

L'attaquant entre par un service exposé sur Internet, puis enchaîne cinq rebonds jusqu'au tri des bagages et aux badges d'accès, en suivant uniquement les connexions autorisées par l'architecture.

### 3.2 Déroulé étape par étape

| Étape | Machine visée | Ce qui se passe | Log attendu |
| --- | --- | --- | --- |
| 1. Entrée | DCS-Server | Exploitation du service exposé sur Internet | Journal web : erreurs puis requête anormale depuis la même IP |
| 2. Pivot métier | BHS-DB | Connexion à la base depuis DCS-Server | Trafic réseau : première connexion jamais vue entre les deux machines |
| 3. Impact bagages | BHS-PLC | Commande envoyée à l'automate via une API sans authentification | Journal de l'API : requête, source, commande |
| 4. Rebond identité | Poste-Agent | Vol d'identifiants sur le même poste | Journal Windows ou Sysmon : accès au processus LSASS |
| 5. Élévation | AD-DC | Authentification avec l'identifiant volé | Journal Kerberos : authentification atypique |
| 6. Impact sûreté | Badge-Server | Modification d'un droit d'accès | Journal applicatif : changement hors horaires habituels |

Le scénario est volontairement linéaire : chaque étape dépend de la précédente. Il couvre six machines sur douze, soit la moitié exigée par le professeur, et les six étapes sont détectables : aucune zone aveugle n'est laissée dans cette version.

### 3.3 Pourquoi ce chemin et pas un autre

L'architecture du réseau interdit tout accès direct entre les zones. L'attaquant doit donc suivre les connexions légitimes, une par une, exactement comme le ferait un attaquant réel. Ce chemin relie un point d'entrée public à un impact opérationnel (le tri des bagages) puis à un impact de sûreté (les badges d'accès), tout en restant entièrement traçable dans les journaux.

## 4. Niveau de difficulté

### 4.1 Ce qui rend l'exercice difficile pour la blue team

- Un trafic qui ressemble à du fonctionnement normal : chaque étape emprunte une connexion habituellement autorisée.
- Un chemin long à six étapes : la blue team doit relier six machines distinctes pour voir l'attaque dans son ensemble, sinon elle ne voit que des incidents isolés.
- Un double impact à comprendre : un impact opérationnel sur les bagages et un impact de sûreté sur les badges, ce qui demande de prioriser.
- Une trace minimale à chaque étape : rien ne déclenche une alerte évidente à lui seul, c'est la corrélation entre les machines qui révèle l'attaque.

## 4.2 Couverture de détection

Les six étapes sont détectables avec les agents déjà installés sur chaque machine (voir le tableau en 3.2). La difficulté ne vient donc pas d'un manque de données, mais du nombre d'étapes à relier entre elles.

## 4.3 Du log brut à l'alerte Kibana

Chaque VM concernée produit ses traces normalement : journal système, journal applicatif, trafic réseau. Un agent installé sur la machine (Winlogbeat ou Filebeat selon l'OS, Packetbeat pour le réseau) envoie ces traces à ELK, qui les indexe et applique des règles de détection.&#32;

### Règles de détection à préparer dans ELK

| Étape | Donnée source | Règle de détection |
| --- | --- | --- |
| 1 | Journal web | Alerte sur plusieurs erreurs HTTP suivies d'une requête anormale depuis la même IP |
| 2 | Trafic réseau (Packetbeat) | Alerte sur une première connexion jamais vue entre DCS-Server et BHS-DB |
| 3 | Journal de l'API BHS-PLC | Alerte sur une requête sans authentification sur l'API de commande |
| 4 | Journal Windows ou Sysmon | Alerte sur un accès au processus LSASS par un programme inhabituel |
| 5 | Journal Kerberos | Alerte sur une authentification à une heure ou depuis une machine inhabituelle |
| 6 | Journal applicatif Badge-Server | Alerte sur une modification de droit d'accès hors horaires habituels |

### Réaction attendue de l'équipe SOC

1. Surveiller le tableau de bord Kibana en continu.
2. Trier chaque alerte : vrai signal ou bruit.
3. Enquêter dans Discover pour reconstituer la chronologie.
4. Relier les événements entre les six machines.
5. Contenir : couper un flux ou isoler une VM dès qu'une machine est confirmée compromise.
6. Documenter l'horodatage, les machines touchées et les actions prises.

## 4.4 Proposition à l'essai : occuper la blue team sur deux fronts (à valider)

Cette section est une piste à tester, pas une décision prise. Elle vise à évaluer si l'équipe sait prioriser entre un incident visible et un objectif discret, plutôt que de ne tester qu'un seul chemin.

### Principe

L'incident bagages (étapes 1 à 3 du tableau en 3.2) sert de diversion bruyante. Pendant que la blue team le traite, l'attaquant profite du flux déjà autorisé entre Douane-App et DCS-Server pour faire fuiter des données passagers, sans ouvrir de nouveau chemin réseau.

### Chronologie proposée

| Temps | Piste bruyante (bagages) | Piste discrète (données) |
| --- | --- | --- |
| T+0 | Entrée sur DCS-Server | — |
| T+10 min | Pivot vers BHS-DB | La réponse servie à Douane-App est modifiée, sans rien déclencher tout de suite |
| T+20 min | Commande vers BHS-PLC : le tri des bagages se dérègle, l'alerte devient visible | — |
| T+25 min | La blue team commence l'investigation et le confinement sur les bagages | Au prochain cycle de lecture de Douane-App, les données partent vers l'attaquant |
| T+35 à 45 min | Vol d'identifiants sur Poste-Agent, puis AD-DC, puis Badge-Server | — |

### Détection à ajouter si cette piste est retenue

| Donnée source | Règle de détection |
| --- | --- |
| Intégrité du fichier manifeste sur DCS-Server | Alerte si le fichier lu par Douane-App a une empreinte différente de la version attendue |

### Ce qu'il reste à valider avant de l'intégrer au scénario final

- Tester ce minutage pendant la répétition générale : l'équipe a-t-elle le temps de se répartir entre les deux fronts ?
- Ajuster l'écart entre les deux événements si l'équipe de test n'y arrive pas.
- Faire valider le principe par le professeur.

## 5. Intérêt pédagogique

- **Réalisme :** le scénario reproduit la logique de deux attaques réelles du secteur aéroportuaire, plutôt qu'une attaque générique.
- **Lien entre informatique et métier :** l'impact final ne touche pas qu'un serveur, il touche un service physique (le tri des bagages), ce qui donne du sens à la détection et à la remédiation.
- **Travail sur les preuves partielles :** la blue team doit apprendre à enquêter avec une télémétrie incomplète, une situation courante en entreprise.
- **Double objectif :** cela entraîne la blue team à prioriser, car elle doit décider où concentrer son attention avec un temps limité.
