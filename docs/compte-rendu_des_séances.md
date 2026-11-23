# Compte-rendu des séances

## Séance du vendredi 13/11

### Consignes du professeur

- Plus de machines dans l'architecture.
- Moins de Windows.
- Ajouter un réplicatif qui communique avec la base de données (une machine de réplication ou de sauvegarde, reliée à la BDD).
- Rendre l'identification de l'attaque plus difficile : plus d'éléments, plus de bruit.
- Nombre de machines cibles entre 6 et 12.
- Vocabulaire du projet : nous sommes la DSI (ceux qui construisent et opèrent le SI simulé), l'autre groupe joue le SOC (l'équipe de défense).
- Préparer une fiche qui décrit ce que nous espérons que le SOC fasse pendant l'exercice.

### Actions à mener suite à cette séance

- [x] Vérifier que l'architecture compte bien entre 6 et 12 machines (actuellement 12 avec le scénario étendu).
- [x] Réduire le nombre de machines Windows dans l'architecture si possible.
- [ ] Ajouter une machine de réplication/sauvegarde connectée à une base de données existante (BHS-DB ou DCS-Server).
- [ ] Rédiger la fiche « ce que nous espérons que le SOC fasse » (liée au dossier joueur du scénario OpenAEV).

## Séance du vendredi 20/11

### Consignes du professeur

- L'attaque doit toucher au moins la moitié des machines déployées.
- Les logs sont le point le plus important pour pouvoir évaluer l'exercice.
- Détailler précisément comment les logs de l'attaque seront visualisés sur l'ELK de supervision.
- Décrire comment les participants doivent réagir en tant qu'équipe SOC.
- Définir les règles de détection à mettre dans ELK pour gérer tout ça.

### Actions à mener suite à cette séance

- [x] Vérifier que le scénario touche au moins la moitié des machines (6 sur 12 confirmé, 7 avec l'ajout de PKI-Chiffrement).
- [x] Décrire le circuit des logs entre OpenAEV, les VM, les agents et ELK (fait dans la présentation des attaques, section 4.3).
- [x] Lister les règles de détection par étape (fait, à détailler en syntaxe Kibana).
- [ ] Écrire la syntaxe exacte de chaque règle dans Kibana.
