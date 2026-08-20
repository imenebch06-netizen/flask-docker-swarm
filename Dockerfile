FROM python:3.9-alpine

WORKDIR /app

# 1. Copie des dépendances pour profiter du cache Docker
COPY requirements.txt .

# 2. Installation des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copie de l'application
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]