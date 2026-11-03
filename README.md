# SupplyChain Analytics

SupplyChain Analytics transforme des données de commandes et d’expéditions en indicateurs faciles à suivre. Le projet réunit un pipeline ETL, une API Django et une interface web pour explorer les livraisons, repérer les retards et comparer les modes d’expédition.

Le tableau de bord présente les indicateurs globaux, leur évolution dans le temps et les zones où les retards se concentrent. Il comprend aussi une analyse des goulots d’étranglement et un assistant conversationnel qui répond à partir des données chargées dans la base.

Pour comprendre plus en détail l’architecture, le backend, le pipeline ETL et le fonctionnement de l’agent, consultez le [guide de compréhension du projet](./GUIDE_COMPRENDRE_LE_PROJET.md).

## Ce que contient le projet

- **Backend Django et Django REST Framework** : authentification JWT, endpoints de données, indicateurs et analyses.
- **Pipeline ETL** : lecture d’un fichier DataCo, transformation des commandes et expéditions, puis chargement dans PostgreSQL.
- **Frontend React, TypeScript et Vite** : tableau de bord, filtres, graphiques, listes détaillées et assistant.
- **Assistant logistique** : réponses calculées directement pour les questions courantes ; un fournisseur compatible avec l’API OpenAI peut être configuré pour les autres questions et la rédaction des explications.
- **Documentation API** : schéma OpenAPI et interface Swagger générés par Django.

Dans les données utilisées ici, le champ appelé « transporteur » correspond en pratique au mode d’expédition (Standard Class, First Class, etc.). Le coût est une estimation ; il ne permet pas, à lui seul, de conclure que les retards causent une hausse des coûts.

## Prérequis

- Python 3.11 ou une version compatible avec les dépendances du backend.
- Node.js et npm.
- Docker avec le plugin Docker Compose, ou une instance PostgreSQL configurée manuellement.
- Le fichier source DataCo pour exécuter l’import complet. Un petit échantillon est fourni dans `data/samples/mini.csv`.

## Démarrage local

Les commandes ci-dessous sont à lancer depuis la racine du dépôt.

### 1. Configurer l’environnement

Créer un fichier `.env` à partir du modèle, puis renseigner les valeurs adaptées à votre machine :

```sh
cp .env.example .env
```

Le fichier doit notamment définir `SECRET_KEY`, `DATABASE_URL` et `ALLOWED_HOSTS`. L’assistant IA utilise l’API du LLM, compatible avec l’API OpenAI. Configurez les variables suivantes dans `.env` :

```dotenv
LLM_BASE_URL=lien
LLM_API_KEY=cle-du-llm
LLM_MODEL=modele
RAG_EMBEDDING_MODEL=modele-embeddings-compatible
RAG_API_KEY=cle-gemini-secrete
LLM_TIMEOUT_S=30
LLM_EXPLAIN_TIMEOUT_S=120
LLM_EXPLAIN_MAX_TOKENS=2000
```

Vous pouvez choisir un autre modèle disponible sur OpenRouter si nécessaire. Ne partagez jamais votre fichier `.env` et ne commitez pas de clé API dans le dépôt. Le fichier `.env.example` ne contient qu’un texte de remplacement pour la clé.

Les trois questions suggérées dans le chat — taux de retard global, modes ayant le plus de retards et goulots indépendamment du volume — sont calculées directement par Django. Elles ne nécessitent pas de clé LLM.

Le RAG utilise l'API native Gemini `batchEmbedContents` pour `gemini-embedding-2`. Définissez `RAG_EMBEDDING_MODEL=gemini-embedding-2` et `RAG_API_KEY` avec une clé Gemini AI Studio distincte de `LLM_API_KEY`. La clé est transmise dans l'en-tête HTTP et ne doit jamais être ajoutée à Git. Après les migrations, lancez `python manage.py index_agent_knowledge` depuis `backend_supply-chain/` pour indexer le guide du projet. Les documents métier Markdown ou TXT peuvent être ajoutés dans `data/knowledge_base/` ; relancez la commande après leur ajout ou modification. `RAG_DOCUMENTS_DIR` permet de choisir un autre dossier et `RAG_TOP_K` de modifier le nombre de passages retournés.

`LLM_EXPLAIN_TIMEOUT_S` règle le temps maximal laissé à chacun des appels du modèle pour expliquer les goulots (120 secondes par défaut), indépendamment du timeout standard `LLM_TIMEOUT_S`. `LLM_EXPLAIN_MAX_TOKENS` réserve jusqu'à 2 000 tokens à cette réponse structurée ; les autres appels conservent leur limite standard. Le backend peut faire une seconde tentative après validation, et le frontend attend jusqu'à 245 secondes pour laisser les deux appels terminer.

L'ETL regroupe les lignes par commande pour les KPI, mais conserve chaque ligne article dans `LigneCommande`. Les quantités, ventes et profits sont additionnés sur toutes les lignes. Le détail API/frontend d'une commande expose chaque produit, sa remise et ses montants ; la liste des commandes affiche le nombre de lignes et d'unités. L'historique ETL indique aussi le nombre de lignes chargées.

### 2. Démarrer PostgreSQL

Le fichier `docker-compose.yml` lance la base de développement sur le port `5433` :

```sh
docker compose up -d db
```

Vérifier que l’URL PostgreSQL dans `.env` correspond à cette instance. Si vous utilisez une base existante, adaptez `DATABASE_URL` à sa configuration.

### 3. Installer et préparer le backend

```sh
cd backend_supply-chain
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

Pour créer un compte administrateur Django :

```sh
python manage.py createsuperuser
```

Démarrer l’API :

```sh
python manage.py runserver 127.0.0.1:8000
```

Laisser ce terminal ouvert. Le serveur doit être lancé depuis `backend_supply-chain` ; ainsi Django charge bien les routes API et le module agent.

### 4. Charger les données

Le pipeline cherche par défaut le fichier `data/raw/DataCoSupplyChainDataset.csv`. Si votre fichier se trouve ailleurs, indiquez son chemin :

```sh
python manage.py run_etl --file /chemin/vers/DataCoSupplyChainDataset.csv
```

Pour tester l’import sur un nombre limité de lignes, utilisez `--limit` :

```sh
python manage.py run_etl --file ../data/samples/mini.csv --limit 100
```

Pour vérifier le traitement sans écrire les lignes transformées dans les tables métier, ajoutez `--dry-run` :

```sh
python manage.py run_etl --file ../data/samples/mini.csv --limit 100 --dry-run
```

Le pipeline enregistre le résultat de chaque exécution. Les lignes rejetées sont écrites dans `data/processed/`.

Chaque ligne article est identifiée par `Order Item Id`. Les lignes strictement identiques sont dédoublonnées ; un identifiant répété avec des données différentes entraîne le rejet de toutes les occurrences concernées, afin d'éviter le double comptage.

### 5. Démarrer le frontend

Dans un autre terminal :

```sh
cd frontend_supply-chain
npm install
npm run dev
```

Ouvrir l’adresse indiquée par Vite, généralement `http://localhost:5173`. Le serveur de développement transmet les requêtes `/api` à Django sur `127.0.0.1:8000`.

Vous pouvez créer un compte depuis l’écran de connexion. Les routes de données et les deux endpoints agent exigent une authentification.

## API principale

Toutes les routes ci-dessous sont préfixées par `/api/v1/`.

| Méthode | Route | Utilité |
| --- | --- | --- |
| `POST` | `auth/register/` | Créer un compte et recevoir les jetons JWT |
| `POST` | `auth/token/` | Obtenir une paire de jetons |
| `POST` | `auth/token/refresh/` | Renouveler un jeton d’accès |
| `GET` | `kpis/summary/` | Lire les indicateurs globaux |
| `GET` | `kpis/timeseries/` | Lire l’évolution des indicateurs |
| `GET` | `kpis/bottlenecks/` | Classer les points de congestion |
| `POST` | `agent/bottlenecks/explain/` | Générer une explication des goulots d’étranglement |
| `POST` | `agent/chat/` | Poser une question à l’assistant |
| `GET`, `POST`, etc. | `commandes/`, `expeditions/`, `transporteurs/`, `entrepots/`, `etl/runs/` | Consulter et gérer les ressources exposées par l’API |

L’interface Swagger est disponible à `http://127.0.0.1:8000/api/docs/` et le schéma OpenAPI à `http://127.0.0.1:8000/api/schema/`.

## Tests et vérifications

Depuis le dossier `backend_supply-chain` :

```sh
python manage.py check
python -m pytest apps/agent/tests
```

Depuis `frontend_supply-chain` :

```sh
npm run build
npm run lint
```

## Organisation des dossiers

```text
backend_supply-chain/
  apps/
    agent/                 Chat, RAG documentaire, outils de données et garde-fous
    api/                   Routes REST, authentification et calcul des KPI
    logistics/             Modèles, administration et pipeline ETL
  config/                  Paramètres et routes Django
  manage.py
frontend_supply-chain/
  src/
    api/                   Client HTTP, types et appels API
    components/             Graphiques, formulaires et composants d’interface
    pages/                  Tableau de bord et pages métier
data/
  knowledge_base/           Documents Markdown/TXT indexés par le RAG
  samples/                  Petit CSV pour les essais
  raw/                      Emplacement attendu du fichier source complet
```

## Quelques commandes utiles

Arrêter la base de développement :

```sh
docker compose down
```

Lancer l’interface Django d’administration : ouvrir `http://127.0.0.1:8000/admin/` après avoir créé un superutilisateur.
