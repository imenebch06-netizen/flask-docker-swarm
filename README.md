# Flask Docker Swarm CV

Application de génération asynchrone de CV PDF avec Flask, Celery, Redis et PostgreSQL.

Le diagramme de cas d'utilisation est disponible dans [docs/use-case.puml](docs/use-case.puml). Il reflète les API Swagger, la file Redis, le worker Celery et la persistance PostgreSQL.

## Services

- `api` : API Flask sur le port `5000`
- `worker` : génération PDF Celery
- `metrics` : tableau de métriques sur le port `5001`
- `postgres` : stockage persistant des utilisateurs et des statuts
- `redis` : broker et backend Celery
- `frontend` : interface candidat Nginx sur le port `80` en Swarm

Les PDF sont écrits dans le volume Docker `pdf_data`, monté en lecture seule par l'API.

Interface web : `http://localhost/` avec Swarm, ou `http://localhost:8080/` avec Compose local. Nginx relaie les appels `/api/*` vers le service API, donc le navigateur n'a pas besoin de configuration CORS.

## Tester l'application

Avec les ports par défaut :

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5001/health
```

Si les ports sont occupés par une autre stack, le lancement de développement utilise `5002` pour l'API et `5003` pour les métriques :

```powershell
$env:API_PORT="5002"
$env:METRICS_PORT="5003"
docker compose up --build -d
Invoke-RestMethod http://localhost:5002/health
Invoke-RestMethod http://localhost:5003/health
```

Créer un CV et vérifier son traitement :

```powershell
$body = '{"username":"Alice","email":"alice@example.com","experiences":"Developpeuse Python","theme_color":"#2C3E50"}'
$cv = Invoke-RestMethod http://localhost:5002/api/v1/cv -Method Post -ContentType 'application/json' -Body $body
$id = $cv.user.id
Invoke-RestMethod "http://localhost:5002/api/v1/cv/$id/status"
```

Le payload complet accepte `first_name`, `last_name`, `email`, `phone`, `job_title`, `experiences`, `skills` et `theme_color`. Les anciens payloads avec `username` restent compatibles.

Après quelques secondes, le statut doit être `READY`. Le PDF est disponible ici :

```text
http://localhost:5002/api/v1/cv/{id}/download
```

La documentation Swagger est disponible sur `http://localhost:5002/apidocs/`.

Routes principales : `POST /api/v1/cv`, `GET /api/v1/cv/{id}/status`, `GET /api/v1/cv/{id}/download`, `GET /api/v1/users` et `GET /health`.

## Lancement local

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Si les ports `5000` ou `5001` sont déjà utilisés par une autre stack, définissez `API_PORT=5002` et `METRICS_PORT=5003` dans `.env`.

Créer une demande :

```powershell
Invoke-RestMethod http://localhost:5000/api/v1/cv -Method Post -ContentType 'application/json' -Body '{"username":"Alice","email":"alice@example.com","experiences":"Développeuse Python"}'
```

Consulter le statut avec l'identifiant retourné :

```text
GET http://localhost:5000/api/v1/cv/{id}/status
GET http://localhost:5000/api/v1/cv/{id}/download
```

Documentation Swagger : `http://localhost:5000/apidocs/`

## Déploiement Swarm

Le fichier `docker-stack.yml` décrit le déploiement Swarm, mais `docker compose up` ne crée pas de services Swarm. Il faut d'abord publier les images sur un registre accessible aux nœuds, puis déployer explicitement la stack.

Les images publiées sont `itsimenewhowasborntodie/flask-swarm-api:v4`, `itsimenewhowasborntodie/flask-swarm-worker:v2` et `itsimenewhowasborntodie/flask-metrics-api:v2`.
L'image frontend est `itsimenewhowasborntodie/expresspdf-frontend:v3` et le worker PDF est `itsimenewhowasborntodie/flask-swarm-worker:v3`.

```powershell
docker build -t cv-api:latest .
docker build -t cv-worker:latest ./worker_service
docker build -t cv-metrics:latest ./metrics_app
docker build -t itsimenewhowasborntodie/expresspdf-frontend:v3 ./frontend_app
docker tag cv-api:latest itsimenewhowasborntodie/flask-swarm-api:v4
docker tag cv-worker:latest itsimenewhowasborntodie/flask-swarm-worker:v3
docker tag cv-metrics:latest itsimenewhowasborntodie/flask-metrics-api:v2
docker push itsimenewhowasborntodie/flask-swarm-api:v4
docker push itsimenewhowasborntodie/flask-swarm-worker:v3
docker push itsimenewhowasborntodie/flask-metrics-api:v2
docker push itsimenewhowasborntodie/expresspdf-frontend:v3
docker swarm init
docker stack deploy -c docker-stack.yml cvapp
docker stack services cvapp
```

Pour un vrai environnement, remplacer les identifiants PostgreSQL de démonstration par des secrets Docker et utiliser un stockage partagé compatible Swarm pour `pdf_data`.

## Tests

Avec Python et les dépendances de développement installés :

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```
