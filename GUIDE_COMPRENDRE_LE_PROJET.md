# Guide de compréhension du projet

Ce document sert de support pour parcourir le code et expliquer les choix techniques du projet. Il ne remplace pas une lecture des fichiers : avant une présentation, ouvrez les modules cités, suivez un exemple dans le code et reformulez les explications avec vos mots.

## 1. Le projet en une phrase

SupplyChain Analytics importe des commandes et leurs expéditions depuis un fichier DataCo, les stocke dans PostgreSQL, expose des indicateurs par une API Django et les présente dans un tableau de bord React. Un assistant analyse les mêmes données pour répondre à des questions logistiques.

## 2. Architecture générale

```text
Fichier DataCo
    │
    ▼
Pipeline ETL Django ───────────────► PostgreSQL
                                        │
                                        ▼
Navigateur React ── requêtes HTTP ──► API Django REST
                                        │
                                        ├── KPI et filtres calculés par Django
                                        └── Agent ──► LLM (pour la rédaction IA)
```

Le navigateur ne se connecte pas directement à PostgreSQL. Il envoie des requêtes HTTP à Django. Django vérifie l’authentification, interroge la base, calcule ou prépare les résultats, puis renvoie du JSON. Pour les explications rédigées, le backend transmet au modèle une synthèse chiffrée calculée par le projet ; le modèle ne reçoit pas une connexion libre à la base.

## 3. Dossiers à connaître

| Dossier ou fichier | Rôle |
| --- | --- |
| `backend_supply-chain/config/` | Configuration Django, variables d’environnement et routes principales |
| `backend_supply-chain/apps/logistics/` | Modèles métier, administration et pipeline ETL |
| `backend_supply-chain/apps/api/` | Endpoints REST, filtres, sérialiseurs et calculs KPI |
| `backend_supply-chain/apps/agent/` | Chat, explication des goulots, outils, appels LLM et garde-fous |
| `frontend_supply-chain/src/api/` | Client HTTP, types TypeScript et hooks de requêtes |
| `frontend_supply-chain/src/pages/` | Pages du tableau de bord et des ressources métier |
| `frontend_supply-chain/src/components/` | Graphiques, tableaux, chargements et interface de l’assistant |
| `data/samples/mini.csv` | Petit fichier de données prévu pour les essais |
| `docker-compose.yml` | Démarrage local de PostgreSQL |

## 4. Le backend, étape par étape

### 4.1 Configuration et démarrage

`backend_supply-chain/config/settings.py` lit le fichier `.env` situé à la racine. On y trouve notamment la connexion PostgreSQL, Django REST Framework, l’authentification JWT et les paramètres LLM :

- `LLM_BASE_URL` : adresse API du fournisseur
- `LLM_API_KEY` : clé privée du compte.
- `LLM_MODEL` : identifiant du modèle choisi chez le fournisseur.
- `RAG_EMBEDDING_MODEL` : identifiant du modèle d'embeddings utilisé par la recherche documentaire.
- `RAG_API_KEY` : clé Gemini AI Studio dédiée à l'API d'embeddings, distincte de `LLM_API_KEY`.
- `LLM_TIMEOUT_S` : durée maximale d’attente de l’appel.

Les paramètres du LLM n’incluent pas la clé dans le code source. Le fichier `.env.example` contient un texte de remplacement ; il faut mettre la vraie clé seulement dans `.env`, qui est ignoré par Git.

### 4.2 Modèle de données

Les modèles sont définis dans `apps/logistics/models.py`.

- **Commande** : numéro d’origine, date, statut, région, marché, client, quantités et montants.
- **Expedition** : une commande associée à son mode d’expédition, son entrepôt, ses délais, son statut de livraison et un coût estimé.
- **Transporteur** : dans les données DataCo utilisées, il représente en pratique le mode d’expédition (Standard Class, First Class, etc.).
- **Entrepôt** : dimension reliée à un marché dans le chargement de données actuel.
- **EtlRun** : historique des imports, avec état, fichier source, lignes lues/rejetées et volumes chargés.

Une commande a une expédition liée en OneToOne. Une expédition pointe vers un transporteur et un entrepôt. Ces relations permettent aux requêtes de filtrer ou regrouper les expéditions selon les dimensions métier.

### 4.3 Pipeline ETL

La commande `run_etl` est dans `apps/logistics/management/commands/run_etl.py`. Son déroulement est :

1. **Extract** — `etl/extract.py` lit le CSV en encodage Latin-1 et ne garde que les colonnes nécessaires.
2. **Transform** — `etl/transform.py` convertit les dates, nombres et chaînes ; vérifie les champs requis, les délais, les modes et la cohérence du statut ; écarte les lignes invalides avec un motif ; regroupe les articles d’une même commande ; calcule l’écart entre délai réel et prévu.
3. **Calcul du coût estimé** — la transformation applique une grille par mode, un coût par article et une pénalité par jour de retard. Ce champ est une estimation définie par le projet, pas un coût réel fourni par DataCo.
4. **Quality report** — `etl/quality.py` produit les volumes, rejets, incohérences, taux de retard et période couverte.
5. **Load** — `etl/load.py` enregistre commandes et expéditions par lots dans une transaction. Les conflits sur les identifiants uniques sont mis à jour, ce qui permet de relancer l’import sans créer une copie de chaque ligne.
6. **Suivi** — `EtlRun` conserve le statut et le résultat de l’exécution. Les rejets sont enregistrés sous `data/processed/`.

Commandes usuelles depuis `backend_supply-chain/` :

```sh
python manage.py run_etl --file /chemin/vers/DataCoSupplyChainDataset.csv
python manage.py run_etl --file ../data/samples/mini.csv --limit 100 --dry-run
```

`--dry-run` exécute l’extraction, la transformation et le rapport, sans écrire les commandes/expéditions transformées dans leurs tables métier.

### 4.4 API REST et authentification

Les routes sont raccordées dans `apps/api/urls.py`, puis incluses sous `/api/v1/` par `config/urls.py`. Les vues sont dans `apps/api/views.py`.

| Endpoint | Ce qu’il renvoie |
| --- | --- |
| `GET /api/v1/kpis/summary/` | Volume, retards, taux de retard, taux à temps et moyennes |
| `GET /api/v1/kpis/timeseries/` | Indicateurs regroupés par jour, semaine ou mois |
| `GET /api/v1/kpis/bottlenecks/` | Classements par région, mode ou couple région-mode |
| `/api/v1/commandes/` | Liste paginée des commandes ; le détail inclut l’expédition |
| `/api/v1/expeditions/` | Expéditions et relations utiles |
| `/api/v1/transporteurs/`, `/entrepots/` | Dimensions affichées par l’interface |
| `/api/v1/etl/runs/` | Historique des imports |
| `POST /api/v1/agent/bottlenecks/explain/` | Analyse des goulots et explication |
| `POST /api/v1/agent/chat/` | Réponse à une question du chat |

`apps/api/filters.py` définit les filtres partagés : dates, région, marché, mode, entrepôt et statut de livraison. `apps/api/kpis.py` construit le queryset de départ puis calcule les agrégats. Les commandes annulées sont exclues des indicateurs de livraison.

Les sérialiseurs de `apps/api/serializers.py` déterminent les champs JSON exposés. La pagination est activée pour les listes de commandes et d’expéditions.

Les permissions globales sont configurées sur `IsAuthenticated` dans Django REST Framework. L’inscription est une exception publique afin de créer un compte ; le reste des endpoints de données et de l’agent demande un jeton JWT.

### 4.5 Calcul et interprétation des goulots

`apps/agent/analysis.py` part des mêmes expéditions filtrées que les KPI. Il compare :

- le nombre de retards observés dans chaque groupe ;
- les retards « en excès » par rapport au taux global, pour ne pas confondre gros volume et taux de retard anormal ;
- les différences par mode et par région ;
- la part de variabilité associée à chaque regroupement.

Ces calculs aident à prioriser l’analyse, mais ils ne prouvent pas une cause. Le coût étant estimé avec une pénalité de retard dans la formule, une relation entre coût et retard ne doit pas être présentée comme une découverte indépendante.

## 5. Comment fonctionne l’agent

Le module `apps/agent/` sépare les responsabilités :

- `views.py` valide la requête HTTP et appelle le service approprié.
- `tools.py` expose une liste limitée de fonctions de calcul autorisées ; il n’y a pas d’outil SQL libre.
- `loop.py` pilote le chat : historique borné, appel du modèle, recherche documentaire, exécution des outils autorisés et vérification des nombres.
- `rag.py` classe les passages documentaires indexés par embeddings et recouvrement lexical ; il renvoie des références que le chat affiche comme sources.
- `embedding_client.py` appelle l'API Gemini native `batchEmbedContents` avec la clé dédiée dans un en-tête HTTP.
- `models.py` conserve les passages et leurs vecteurs dans PostgreSQL ; `index_agent_knowledge` indexe le guide et les fichiers Markdown/TXT du dossier de connaissances.
- `services.py` calcule l’évidence des goulots, demande une explication au modèle et gère le cache.
- `llm_client.py` utilise le client OpenAI compatible avec l’API OpenRouter et transforme les erreurs du fournisseur en erreur contrôlée.
- `guardrails.py` vérifie le format de la réponse, les champs requis, le niveau de confiance et les nombres par rapport aux données calculées.
- `prompts.py` fixe le rôle de l’assistant et les règles de réponse.

### Parcours du bouton « Expliquer »

1. Le frontend transmet les filtres du tableau de bord à `POST /api/v1/agent/bottlenecks/explain/`.
2. Django calcule une structure d’évidence : compteurs globaux, classements, constats et parts de variabilité.
3. Le backend envoie au modèle OpenRouter le prompt et cette évidence, en demandant une réponse JSON.
4. Le backend normalise certaines variations de format, puis contrôle les champs et les nombres.
5. Une réponse valide est affichée comme **IA · données vérifiées** et mise en cache.
6. Si l’utilisateur actualise, le cache est ignoré et une nouvelle génération est demandée. Si OpenRouter refuse cette génération, la dernière réponse IA valide peut être conservée et signalée comme non actualisée ; si aucune réponse valide précédente n’existe, une explication automatique de secours est affichée.

Un code HTTP **402** provenant d’OpenRouter signifie que le fournisseur a refusé la génération, typiquement faute de crédits ou de budget disponible. Ce n’est pas un timeout ni une erreur de permission Django. Le code ne peut pas créer des crédits : il faut régler la facturation/quota OpenRouter ou choisir un modèle accessible avec le quota du compte. L’interface doit afficher le motif précis.

Les trois suggestions prédéfinies du chat sont calculées directement à partir des données par Django ; elles ne nécessitent donc pas de génération LLM. Les questions libres utilisent le modèle lorsqu’il est activé.

Le RAG sert aux questions sur le contexte, les définitions et les procédures documentées. Les KPI restent calculés à la demande par SQL via les outils Django ; ils ne sont pas remplacés par des passages documentaires. Configurer `RAG_EMBEDDING_MODEL=gemini-embedding-2` et `RAG_API_KEY`, puis lancer `python manage.py index_agent_knowledge` depuis `backend_supply-chain/`. Le corpus comprend le guide du projet et les fichiers `.md`/`.txt` de `data/knowledge_base/`.

### Agrégation des lignes de commande

Le CSV source contient une ligne par article commandé, pas nécessairement une ligne par commande. `transform.py` retourne les commandes agrégées et le détail de chaque ligne : quantités, ventes et profits sont additionnés sur toutes les lignes, tandis que chaque `Order Item Id` est conservé séparément. `load.py` charge ces détails dans `LigneCommande`, reliée à `Commande`. Les doublons stricts sont retirés ; un identifiant de ligne répété avec des valeurs différentes est rejeté pour éviter un double comptage. Le détail API/frontend d'une commande affiche maintenant la liste des produits, quantités, remises, ventes et profits.

## 6. Le frontend

Le frontend est une application React avec TypeScript et Vite.

- `src/api/client.ts` configure Axios, le préfixe `/api/v1`, l’ajout du JWT et le renouvellement du jeton.
- `src/api/hooks.ts` définit les requêtes de données avec TanStack Query et réutilise les filtres dans les clés de cache.
- `src/api/agent.ts` contient les contrats TypeScript et les appels chat/explication.
- `src/pages/DataPages.tsx` compose le tableau de bord, les filtres, KPI, graphiques et tableaux.
- `src/components/agent/ExplainBottlenecks.tsx` affiche l’explication, son niveau de confiance, ses preuves et ses éventuels avertissements.
- `src/components/agent/ChatPanel.tsx` affiche le panneau de chat, les suggestions, l’historique et l’état d’attente.
- `src/App.tsx` gère la connexion, la création du compte, la navigation et le shell authentifié.

En développement, Vite transmet `/api` à Django sur `127.0.0.1:8000` (configuration dans `vite.config.ts`). En production, il faut fournir une configuration d’hébergement qui sert le frontend et route l’API vers le backend.

## 7. Lancer le projet et le vérifier

Depuis la racine, préparer `.env` à partir de `.env.example`, puis démarrer PostgreSQL :

```sh
cp .env.example .env
docker compose up -d db
```

Dans un terminal backend :

```sh
cd backend_supply-chain
source venv/bin/activate
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Dans un autre terminal :

```sh
cd frontend_supply-chain
npm install
npm run dev
```

Vérifications automatiques :

```sh
# Depuis backend_supply-chain/
python manage.py check
python -m pytest apps/agent/tests

# Depuis frontend_supply-chain/
npm run build
npm run lint
```

Pour vérifier spécifiquement la génération OpenRouter, il faut une clé fonctionnelle, un modèle accessible et un compte disposant du quota nécessaire. Une réponse automatique de secours confirme les calculs de données, mais ne prouve pas que le modèle a généré l’explication.

 
L’ETL prépare et charge les données ; l’API sert les données déjà organisées au frontend. Cette séparation permet de relancer l’import et d’utiliser les endpoints sans relire le gros CSV à chaque page.

