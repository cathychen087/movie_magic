# Movie Magic Web App

A Django-based web application for movie enthusiasts to browse, review, and interact with movies.

## Deployment on Railway.app

### Prerequisites
- A Railway.app account
- A GitHub account with this repository
- TMDB API key
- Stripe API keys (if using payment features)

### Step 1: Fork and Clone the Repository
1. Fork this repository to your GitHub account
2. Clone your forked repository:
```bash
git clone https://github.com/your-username/movie_magic.git
cd movie_magic
```

### Step 2: Set Up Environment Variables
Create a `.env` file in the project root with the following variables:
```
DEBUG=False
SECRET_KEY=your-secret-key-here
TMDB_API_KEY=your-tmdb-api-key
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
```

### Step 3: Deploy to Railway.app
1. Go to [Railway.app](https://railway.app)
2. Click "New Project" and select "Deploy from GitHub repo"
3. Select your forked repository
4. Add the following environment variables in Railway.app dashboard:
   - `DEBUG=False`
   - `SECRET_KEY` (generate a new secure key)
   - `TMDB_API_KEY`
   - `STRIPE_PUBLIC_KEY`
   - `STRIPE_SECRET_KEY`
   - `DATABASE_URL` (automatically set by Railway)

### Step 4: Configure the Project
1. In Railway.app dashboard, go to your project settings
2. Add a PostgreSQL database service if not already added
3. Configure the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python manage.py migrate && gunicorn movie_magic.wsgi:application --bind 0.0.0.0:$PORT`

### Step 5: Access the Web App
1. After successful deployment, Railway.app will provide a URL (e.g., `https://your-app-name.up.railway.app`)
2. Access the web app through this URL
3. The app should be fully functional with:
   - Movie browsing
   - User authentication
   - Movie reviews
   - Favorites system

## Local Development

### Prerequisites
- Python 3.8 or higher
- pip
- virtualenv

### Setup
1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
source venv/bin/activate     # On Unix/MacOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
TMDB_API_KEY=your-tmdb-api-key
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

6. Access the app at `http://127.0.0.1:8000`

## Features
- Browse movies from TMDB
- User authentication
- Movie reviews and ratings
- Favorite movies system
- Responsive design
- Secure payment integration (if configured)

## Troubleshooting

### Common Issues
1. **Database Connection Issues**
   - Ensure DATABASE_URL is correctly set in Railway.app
   - Check PostgreSQL service status

2. **API Key Issues**
   - Verify TMDB API key is valid
   - Check Stripe API keys if using payment features

3. **Static Files Not Loading**
   - Run `python manage.py collectstatic` locally
   - Check WhiteNoise configuration

4. **Deployment Failures**
   - Check Railway.app logs
   - Verify all environment variables are set
   - Ensure requirements.txt is up to date

### url
https://web-production-fd59a.up.railway.app
