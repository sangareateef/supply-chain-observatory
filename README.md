# Supply Chain Observatory

Observatoire destiné à analyser les risques associés aux dépendances open source des projets Python et JavaScript.

## Auteurs

- Ateef Sangare
- Koudedia Sissoko

## Objectif

Supply Chain Observatory analyse les risques associés à une version précise d’une dépendance open source Python ou JavaScript.

L’application prend en compte :

- les vulnérabilités connues ;
- les licences et les métadonnées ;
- la maintenabilité des paquets ;
- les informations OpenSSF Scorecard ;
- les signaux potentiellement suspects ;
- un score de risque explicable compris entre 0 et 100.

Le score représente un niveau de risque à examiner. Il ne correspond ni à une probabilité d’attaque ni à un pourcentage de sécurité.

## Fonctionnalités disponibles

- API REST développée avec FastAPI ;
- documentation interactive Swagger/OpenAPI ;
- tableau de bord web ;
- analyse d’une dépendance Python ou JavaScript ;
- import d’un fichier Python `requirements.txt` ;
- import d’un fichier JavaScript `package-lock.json` ;
- recherche des vulnérabilités connues avec OSV ;
- récupération des licences et des métadonnées avec deps.dev ;
- calcul d’un score de risque explicable ;
- analyse de la maintenabilité du dépôt source ;
- récupération des informations OpenSSF Scorecard ;
- détection de signaux suspects ;
- tests automatisés avec Pytest ;
- lancement local ou avec Docker Compose.

## Technologies utilisées

- Python 3.12 ou version supérieure ;
- FastAPI ;
- Uvicorn ;
- Pydantic ;
- HTTPX ;
- HTML, CSS et JavaScript ;
- Pytest ;
- Docker et Docker Compose ;
- OSV API ;
- deps.dev ;
- OpenSSF Scorecard ;
- Git et GitHub.

## Installation sous Windows

Cloner le dépôt :

```powershell
git clone https://github.com/sangareateef/supply-chain-observatory.git
cd supply-chain-observatory
```

Créer l’environnement virtuel :

```powershell
py -m venv .venv
```

Activer l’environnement :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
python -m pip install -r requirements.txt
```

## Tests automatisés

Pour exécuter les tests :

```powershell
python -m pytest
```

## Démarrage de l’application

```powershell
python -m uvicorn app.main:app --reload
```

L’application est ensuite accessible aux adresses suivantes :

- tableau de bord : <http://127.0.0.1:8000/dashboard>
- documentation Swagger/OpenAPI : <http://127.0.0.1:8000/docs>
- état de l’API : <http://127.0.0.1:8000/health>

Pour arrêter le serveur, utiliser `Ctrl+C`.

## Principaux endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Informations générales sur l’API |
| GET | `/health` | Vérification du fonctionnement de l’API |
| GET | `/dashboard` | Affichage du tableau de bord |
| POST | `/dependencies/preview` | Validation d’une dépendance |
| POST | `/dependencies/analyze` | Analyse générale d’une dépendance |
| POST | `/dependencies/licenses` | Recherche de la licence et des métadonnées |
| POST | `/dependencies/risk` | Calcul du score de risque |
| POST | `/dependencies/maintainability` | Analyse de la maintenabilité |
| POST | `/dependencies/signals` | Recherche de signaux suspects |
| POST | `/files/requirements/preview` | Lecture d’un fichier `requirements.txt` |
| POST | `/files/requirements/analyze` | Analyse d’un fichier `requirements.txt` |
| POST | `/files/package-lock/preview` | Lecture d’un fichier `package-lock.json` |
| POST | `/files/package-lock/analyze` | Analyse d’un fichier `package-lock.json` |

## Fichiers de démonstration

Le dossier `samples` contient :

- `requirements-vulnerable.txt` pour Python ;
- `package-lock-vulnerable.json` pour JavaScript.

Ces fichiers utilisent volontairement d’anciennes versions de dépendances afin de produire des vulnérabilités pendant la démonstration.

## Structure principale

```text
supply-chain-observatory/
├── app/                 Application FastAPI, frontend, routes et services
├── samples/             Fichiers d’exemple
├── tests/               Tests automatisés
├── Dockerfile           Construction de l’image Docker
├── compose.yaml         Démarrage avec Docker Compose
├── requirements.txt     Dépendances Python
└── README.md            Documentation principale
```

## Score de risque

L’endpoint `POST /dependencies/risk` analyse une version précise d’une dépendance en combinant les vulnérabilités connues et les métadonnées du paquet.

Le score va de `0` à `100` :

- `0` indique un risque minimal détecté ;
- `100` indique un risque maximal ;
- ce score n’est ni un pourcentage de santé ni une probabilité d’attaque.

### Signaux analysés

| Signal | Points maximum |
|---|---:|
| Vulnérabilités connues | 55 |
| Licence absente ou contraignante | 15 |
| Version déclarée obsolète | 15 |
| Ancienneté de la version | 10 |
| Métadonnées ou dépôt source manquants | 5 |

La gravité des vulnérabilités est pondérée ainsi :

| Gravité | Points par vulnérabilité |
|---|---:|
| Critique | 50 |
| Élevée | 25 |
| Modérée | 7 |
| Faible | 2 |
| Inconnue | 3 |

La composante liée aux vulnérabilités est plafonnée à `55` points.

### Niveaux de risque

| Score | Niveau |
|---:|---|
| 0 à 24 | Faible |
| 25 à 49 | Modéré |
| 50 à 79 | Élevé |
| 80 à 100 | Critique |

Le champ `age_years` représente l’âge de la version analysée en années. Il ne représente pas son état de santé.

La méthode actuelle est identifiée par `score_version: 1.1`, afin que ses évolutions futures restent traçables.

### Exemple de requête

```json
{
  "ecosystem": "PyPI",
  "name": "requests",
  "version": "2.19.0"
}
```

## Analyse de la maintenabilité

L’endpoint `POST /dependencies/maintainability` analyse les informations de maintenance du dépôt source associé à une dépendance.

L’analyse s’appuie sur les données de deps.dev et d’OpenSSF Scorecard.

Elle retourne notamment :

- les informations du dépôt source ;
- le nombre d’étoiles, de forks et d’issues ouvertes ;
- un score d’activité compris entre 0 et 10 ;
- le niveau d’activité du projet ;
- le score OpenSSF global ;
- plusieurs contrôles disponibles, notamment la maintenance récente et la revue de code.

Le score d’activité mesure l’activité récente du dépôt. Un score élevé indique que des commits ou des activités liées aux issues ont été détectés récemment.

Les étoiles, les forks et les issues ouvertes sont affichés comme informations complémentaires. Ils ne déterminent pas directement le score d’activité.

Si aucun dépôt source n’est associé à la version analysée, l’API retourne le statut `unavailable` sans provoquer d’erreur du serveur.

### Niveaux d’activité

| Score | Niveau |
|---:|---|
| 0 à 1 | Très faible |
| 2 à 4 | Limitée |
| 5 à 7 | Active |
| 8 à 10 | Très active |

### Exemple de requête

```json
{
  "ecosystem": "npm",
  "name": "axios",
  "version": "0.21.1"
}
```
## Analyse des signaux suspects

L’endpoint `POST /dependencies/signals` recherche dans les métadonnées d’une version de paquet des indicateurs nécessitant une vérification humaine.

L’analyse peut notamment signaler :

- une version absente du registre ;
- une version retirée ou déclarée obsolète ;
- des scripts exécutés pendant l’installation ;
- l’absence de dépôt source identifié ;
- l’absence de licence déclarée.

Chaque signal contient un niveau de gravité, les éléments observés et une recommandation. Ces indicateurs ne constituent pas une preuve de malveillance : ils servent à orienter une vérification humaine.

### Niveaux de gravité

| Niveau | Signification |
| --- | --- |
| Aucun | Aucun signal détecté |
| Faible | Information à vérifier |
| Moyen | Vérification recommandée |
| Élevé | Vérification prioritaire |

### Exemple de requête

```json
{
  "ecosystem": "npm",
  "name": "esbuild",
  "version": "0.21.5"
}
```

## État du projet

Le prototype est fonctionnel et validé pour les dépendances Python et JavaScript.

Les éléments suivants sont terminés :

- API FastAPI ;
- analyse des vulnérabilités ;
- analyse des licences et des métadonnées ;
- calcul du score de risque explicable ;
- analyse de la maintenabilité ;
- détection des signaux suspects ;
- import de `requirements.txt` et de `package-lock.json` ;
- tableau de bord final ;
- tests automatisés ;
- conteneurisation Docker ;
- documentation technique ;
- validation des scénarios `httpx 0.28.1`, `requests 2.19.0` et `axios 0.21.1`.

Les résultats peuvent évoluer, car OSV, deps.dev et OpenSSF mettent régulièrement leurs données à jour.

## Démarrage avec Docker

### Prérequis

- Docker Desktop

### Lancer l’application

```powershell
docker compose up --build
```

L’application est ensuite accessible aux adresses suivantes :

- tableau de bord : http://127.0.0.1:8000/dashboard
- documentation de l’API : http://127.0.0.1:8000/docs
- état de l’API : http://127.0.0.1:8000/health

### Arrêter l’application

Appuyer sur `Ctrl+C`, puis exécuter :

```powershell
docker compose down
```

