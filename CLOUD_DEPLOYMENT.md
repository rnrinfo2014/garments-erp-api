# Cloud deployment configurations

## Heroku Deployment

### 1. Install Heroku CLI
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Login and Create App
```bash
heroku login
heroku create garments-erp-api
```

### 3. Add PostgreSQL
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

### 4. Set Environment Variables
```bash
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set JWT_SECRET_KEY="your-jwt-secret-here"
heroku config:set ENVIRONMENT="production"
```

### 5. Deploy
```bash
git push heroku main
```

---

## Railway Deployment

### 1. Connect GitHub Repository
- Go to https://railway.app
- Connect your GitHub repository
- Select this project

### 2. Add PostgreSQL
- Click "New" → "Database" → "PostgreSQL"

### 3. Set Environment Variables
```
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ENVIRONMENT=production
```

### 4. Deploy
Railway will automatically deploy on git push.

---

## DigitalOcean App Platform

### 1. Create App
- Go to DigitalOcean App Platform
- Connect GitHub repository

### 2. Configure Build
```yaml
name: garments-erp-api
services:
- name: api
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  
databases:
- name: db
  engine: PG
  version: "14"
```

### 3. Set Environment Variables
```
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ENVIRONMENT=production
```

---

## AWS Elastic Beanstalk

### 1. Install EB CLI
```bash
pip install awsebcli
```

### 2. Initialize
```bash
eb init garments-erp-api
```

### 3. Create Environment
```bash
eb create production
```

### 4. Set Environment Variables
```bash
eb setenv SECRET_KEY="your-secret-key-here"
eb setenv JWT_SECRET_KEY="your-jwt-secret-here"
eb setenv ENVIRONMENT="production"
```

### 5. Deploy
```bash
eb deploy
```

---

## Google Cloud Run

### 1. Build Image
```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/garments-erp-api
```

### 2. Deploy
```bash
gcloud run deploy --image gcr.io/PROJECT-ID/garments-erp-api --platform managed
```

---

## Environment Variables for All Platforms

Required:
```
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
ENVIRONMENT=production
```

Optional:
```
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=["https://your-frontend.com"]
```
