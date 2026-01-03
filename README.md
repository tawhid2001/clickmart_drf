# Django Production Deployment (ClickMart)

This repository documents a full path from local development to production for a Django + React app using Docker, PostgreSQL, GitHub Actions, Linode, Nginx, Gunicorn, a custom domain, and SSL.

## Contents
- Overview
- Tech stack
- Prerequisites
- 1. Clone and reinitialize
- 2. Run locally (no Docker)
- 3. Run with Docker (local)
- 4. Deploy to Linode
- 5. CI/CD (GitHub Actions)
- 6. Nginx reverse proxy
- 7. Gunicorn (production WSGI)
- 8. Custom domain + SSL
- 9. Serve media files

## Overview
Flow:
Local -> Docker -> GitHub -> Linode -> Domain -> HTTPS

## Tech stack
- Django
- Docker + Docker Compose
- PostgreSQL
- GitHub Actions (CI/CD)
- Linode VPS
- Nginx
- Gunicorn
- Custom domain + SSL (Let''s Encrypt)

## Prerequisites
Install these locally:
- Git
- Python 3.10+
- pip
- Docker Desktop
- VS Code (optional)

## 1. Clone and reinitialize
Clone the project:
```bash
git clone https://github.com/dev-rathankumar/django_clickmart_
cd django_clickmart_
```

Optional: remove existing git history and push to your own repo:
```bash
rm -rf .git
git init
git add .
git commit -m "Initial project setup"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/<REPOSITORY-NAME>.git
git push -u origin main
```

## 2. Run locally (no Docker)
Backend:
```bash
cd backend-drf
python -m venv env
# Mac / Linux
source env/bin/activate
# Windows
env\Scripts\activate
pip install -r requirements.txt
```

Create `backend-drf/.env`:
```env
DEBUG=True
SECRET_KEY=<YOUR-SECRET-KEY>

DB_NAME=<DATABASE-NAME>
DB_USER=<POSTGRES-USERNAME>
DB_PASSWORD=<YOUR-PASSWORD>
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=<YOUR-EMAIL-ADDRESS>
EMAIL_HOST_PASSWORD=<PASSWORD>
```

Run migrations and server:
```bash
python manage.py migrate
python manage.py runserver
```

Frontend:
Create `frontend/.env`:
```env
VITE_SERVER_BASE_URL=http://127.0.0.1:8000/api/v1
```

Run the frontend:
```bash
cd ../frontend
npm install
npm run dev
```
Open http://localhost:5173/

Optional: create a superuser:
```bash
cd ../backend-drf
python manage.py createsuperuser
```

## 3. Run with Docker (local)
Verify Docker:
```bash
docker --version
docker compose version
```

Create `backend-drf/Dockerfile`:
```dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "clickmart_main.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "180"]
```

Create `frontend/Dockerfile`:
```dockerfile
# Stage 1: Build
FROM node:18 AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ARG VITE_SERVER_BASE_URL
ENV VITE_SERVER_BASE_URL=$VITE_SERVER_BASE_URL

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Create `docker-compose.yml` in the repo root:
```yaml
services:
  db:
    image: postgres:16-alpine
    env_file:
      - .env.production
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend-drf
    ports:
      - "8000:8000"
    env_file:
      - ./backend-drf/.env.docker
    depends_on:
      - db
    volumes:
      - ./backend-drf/static:/app/static
      - ./backend-drf/media:/app/media
    command: >
      sh -c "python manage.py collectstatic --noinput &&
             python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"

  frontend:
    build:
      context: ./frontend
      args:
        VITE_SERVER_BASE_URL: "http://backend:8000/api/v1"
    ports:
      - "5173:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Create `backend-drf/.env.docker`:
```env
SECRET_KEY=<YOUR-DJANGO-SECRETKEY>
DEBUG=True

DB_NAME=<YOUR_DOCKER_DB>
DB_USER=postgres
DB_PASSWORD=<PASSWORD>
DB_HOST=db
DB_PORT=5432

EMAIL_HOST_USER=<YOUR-EMAIL-ADDRESS>
EMAIL_HOST_PASSWORD=<YOUR-PASSWORD>
```

Run Docker:
```bash
docker compose up --build
```

## 4. Deploy to Linode
Create a Linode server and SSH in:
```bash
ssh root@<LINODE_IP>
```

Install dependencies:
```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin git -y
```

Clone the repo:
```bash
cd /opt
mkdir clickmart
cd clickmart
git clone https://github.com/your-repo.git .
```

Update frontend API URL in `docker-compose.yml`:
```yaml
VITE_SERVER_BASE_URL: "http://<LINODE_IP>:8000/api/v1"
```

Create environment files on Linode:
```bash
nano backend-drf/.env.production
nano backend-drf/.env.docker
```

Open firewall ports:
- 22 (SSH)
- 8000 (backend)
- 5173 (frontend)

Build and run:
```bash
docker compose up --build -d
docker compose ps
```

Test:
- Backend: http://<LINODE_IP>:8000/
- Frontend: http://<LINODE_IP>:5173/

## 5. CI/CD (GitHub Actions)
Create `.github/workflows/automate.yml`:
```yaml
name: Auto Deploy to Linode

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.LINODE_HOST }}
          username: ${{ secrets.LINODE_USER }}
          key: ${{ secrets.LINODE_SSH_KEY }}
          script: |
            cd /opt/clickmart
            git pull origin main
            docker compose up --build -d
```

Add GitHub secrets:
- `LINODE_HOST` = `<LINODE_IP>`
- `LINODE_USER` = `root`
- `LINODE_SSH_KEY` = your private key

Commit and push.

## 6. Nginx reverse proxy
Create `nginx/default.conf`:
```nginx
server {
    listen 80;

    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /admin/ {
        proxy_pass http://backend:8000;
    }

    location /static/ {
        proxy_pass http://backend:8000;
    }

    location /media/ {
        proxy_pass http://backend:8000;
    }
}
```

Update `docker-compose.yml`:
- Add an nginx service
- Remove ports from backend and frontend
- Set `VITE_SERVER_BASE_URL` to `/api/v1`

Example nginx service:
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
  depends_on:
    - frontend
    - backend
```

Update firewall:
- Keep 22 and 80
- Remove 8000 and 5173

## 7. Gunicorn (production WSGI)
Ensure `gunicorn` is in `requirements.txt`.

Update `docker-compose.yml` backend command:
```yaml
command: >
  gunicorn clickmart_main.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## 8. Custom domain + SSL
Point your domain to Linode with DNS A records:
- `@` -> `<LINODE_IP>`
- `www` -> `<LINODE_IP>`

Make nginx config server-managed:
```bash
git rm --cached nginx/default.conf
```
Add to `.gitignore`:
```
nginx/default.conf
```

On the server, create `nginx/default.conf` and set:
```
server_name example.com www.example.com;
```

Install Certbot:
```bash
apt update
apt install certbot -y
```

Create cert directories:
```bash
mkdir -p certbot/www
mkdir -p certbot/conf
```

Add to nginx service volumes:
```yaml
- ./certbot/www:/var/www/certbot
- ./certbot/conf:/etc/letsencrypt
```

Add ACME challenge path in nginx:
```nginx
location /.well-known/acme-challenge/ {
    root /var/www/certbot;
}
```

Get SSL certificate:
```bash
certbot certonly \
  --webroot \
  -w /opt/clickmart/certbot/www \
  -d example.com \
  -d www.example.com
```

Final nginx config:
```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://frontend:80;
    }

    location /api/ {
        proxy_pass http://backend:8000;
    }

    location /admin/ {
        proxy_pass http://backend:8000;
    }

    location /static/ {
        alias /static/;
    }
}
```

Restart nginx:
```bash
docker compose restart nginx
```

## 9. Serve media files
On the server, update `nginx/default.conf` in the HTTPS server block:
```nginx
location /media/ {
    alias /media/;
}
```

Update nginx service volume mapping:
```yaml
nginx:
  volumes:
    - ./backend-drf/media:/media
```

If images still do not appear, ensure the serializer returns a relative URL:
```python
class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_image(self, obj):
        return obj.image.url if obj.image else None
```
