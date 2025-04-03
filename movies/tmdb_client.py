import requests
from django.conf import settings

class TMDBClient:
    BASE_URL = 'https://api.themoviedb.org/3'
    
    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.params = {
            'api_key': self.api_key,
            'language': 'en-US'
        }
    
    def get_movie(self, movie_id):
        """Get movie details from TMDB API"""
        url = f'{self.BASE_URL}/movie/{movie_id}'
        response = requests.get(url, params=self.params)
        response.raise_for_status()
        return response.json()
    
    def get_movie_videos(self, movie_id):
        """Get movie videos (trailers, etc.) from TMDB API"""
        url = f'{self.BASE_URL}/movie/{movie_id}/videos'
        response = requests.get(url, params=self.params)
        response.raise_for_status()
        return response.json()
    
    def get_popular_movies(self, page=1):
        """Get popular movies from TMDB API"""
        url = f'{self.BASE_URL}/movie/popular'
        params = {**self.params, 'page': page}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

# Create a singleton instance
tmdb_client = TMDBClient() 