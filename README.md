# Supply Chain Observatory

Observatoire destiné à analyser les risques associés aux dépendances open source des projets Python et JavaScript.

## Auteurs

- Ateef Sangare
- Koudedia Sissoko

## Objectif

Le projet permet d’importer les dépendances d’une application et de rechercher automatiquement leurs vulnérabilités connues grâce à la base de données OSV.

L’observatoire prendra progressivement en compte :

- les vulnérabilités connues ;
- les licences ;
- la maintenabilité des paquets ;
- les signaux de paquets potentiellement malveillants ;
- un score de risque explicable.

## Fonctionnalités disponibles

- API REST développée avec FastAPI ;
- documentation Swagger automatique ;
- analyse d’une dépendance Python ou JavaScript ;
- import d’un fichier Python `requirements.txt` ;
- import d’un fichier JavaScript `package-lock.json` ;
- analyse groupée des dépendances avec OSV ;
- fichiers vulnérables d’exemple pour la démonstration.

## Technologies utilisées

- Python 3.12 ou version supérieure ;
- FastAPI ;
- Pydantic ;
- HTTPX ;
- OSV API ;
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

## Démarrage de l’API

```powershell
python -m uvicorn app.main:app --reload
```

La documentation interactive est ensuite disponible à l’adresse :

```text
http://127.0.0.1:8000/docs
```

## Principaux endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Informations générales sur l’API |
| GET | `/health` | Vérification du fonctionnement de l’API |
| POST | `/dependencies/preview` | Validation d’une dépendance |
| POST | `/dependencies/analyze` | Analyse OSV d’une dépendance |
| POST | `/files/requirements/preview` | Lecture d’un fichier `requirements.txt` |
| POST | `/files/requirements/analyze` | Analyse d’un fichier `requirements.txt` |
| POST | `/files/package-lock/preview` | Lecture d’un fichier `package-lock.json` |
| POST | `/files/package-lock/analyze` | Analyse d’un fichier `package-lock.json` |

## Fichiers de démonstration

Le dossier `samples` contient :

- `requirements-vulnerable.txt` pour Python ;
- `package-lock-vulnerable.json` pour JavaScript.

Ces fichiers utilisent volontairement d’anciennes versions de dépendances afin de produire des vulnérabilités pendant la démonstration.

## Structure actuelle

```text
app/
├── routers/
│   └── npm.py
├── services/
│   ├── osv.py
│   ├── package_lock_parser.py
│   └── requirements_parser.py
├── main.py
└── schemas.py

samples/
├── package-lock-vulnerable.json
└── requirements-vulnerable.txt
```

## État du projet

Le socle de l’API, l’analyse des vulnérabilités Python et JavaScript, l’analyse des licences et le calcul du score de risque sont fonctionnels.

Les prochaines étapes sont :

- ajout des signaux de maintenabilité ;
- détection de comportements suspects ;
- création du tableau de bord ;
- ajout de tests automatisés ;
- conteneurisation avec Docker ;
- préparation de la démonstration et de la soutenance.

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