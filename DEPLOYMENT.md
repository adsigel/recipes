# Recipe App Deployment Guide

This guide will help you deploy your Recipe App to production so you can access it from your phone.

## Quick Start Options

### Option 1: Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://localhost:8000
```

### Option 2: Direct Server Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your settings

# Start production server
./start_production.sh
```

## Deployment Platforms

### 1. Fly.io (Recommended for Mobile Access)
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login to Fly
fly auth login

# Deploy
fly launch
fly deploy

# Your app will be available at https://your-app-name.fly.dev
```

### 2. Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### 3. Heroku
```bash
# Install Heroku CLI
# Create Procfile with: web: gunicorn wsgi:app

# Deploy
heroku create your-recipe-app
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

### 4. DigitalOcean App Platform
- Connect your GitHub repository
- Select Python environment
- Set build command: `pip install -r requirements.txt`
- Set run command: `gunicorn wsgi:app`
- Deploy

## Environment Variables

Create a `.env` file with these settings:

```env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
CHROME_HEADLESS=true
CHROME_NO_SANDBOX=true
DEBUG=false
```

## Security Considerations

1. **Change the SECRET_KEY** - Use a strong, random key
2. **HTTPS** - Always use HTTPS in production
3. **Database** - Consider using PostgreSQL for production
4. **Chrome Profile** - The Chrome profile will be reset on each deployment

## Mobile Access

Once deployed, you can:
1. Access the app from your phone's browser
2. Add it to your home screen for app-like experience
3. Use the recipe extraction feature from your phone

## Troubleshooting

### Chrome/Selenium Issues
- Ensure Chrome and ChromeDriver versions match
- Use headless mode in production
- Increase timeout values if needed

### Database Issues
- Check database permissions
- Ensure database is properly initialized
- Consider using managed database service

### Performance
- Use multiple Gunicorn workers
- Enable caching for static files
- Consider CDN for static assets

## Monitoring

Add these to your deployment for monitoring:
- Health checks (already included in Dockerfile)
- Log aggregation
- Performance monitoring
- Error tracking

## Backup Strategy

1. **Database**: Regular backups of your SQLite/PostgreSQL database
2. **Chrome Profile**: Note that login sessions will be lost on redeployment
3. **Recipe Data**: Export recipes periodically as JSON backup 