from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorite_movies = models.ManyToManyField('Movie', blank=True)
    points = models.IntegerField(default=0)  # 用户积分系统

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie_id')

    def __str__(self):
        return f"{self.user.username}'s favorite movie {self.movie_id}"

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField()
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    backdrop_path = models.CharField(max_length=255, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    vote_average = models.FloatField(default=0.0)
    difficulty_level = models.IntegerField(default=1)  # 临时添加，用于迁移
    challenge_points = models.IntegerField(default=10)  # 添加默认值

    def __str__(self):
        return self.title

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)  # 允许为空

    def __str__(self):
        return f"{self.user.username}'s review for {self.movie.title}"

    class Meta:
        ordering = ['-created_at']

class Challenge(models.Model):
    CHALLENGE_TYPES = [
        ('review', 'Write a Review'),
        ('favorite', 'Add to Favorites'),
        ('rating', 'Rate Movies'),
        ('watch', 'Watch Movies'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie', 'challenge_type')

    def __str__(self):
        return f"{self.user.username}'s {self.challenge_type} challenge for {self.movie.title}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    showtime_date = models.DateField()
    showtime_time = models.TimeField()
    seats = models.JSONField(null=True, blank=True, default=dict)  # 使用 dict 作为默认值
    price_per_seat = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default='pending')
    stripe_payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)  # 允许为空

    def __str__(self):
        return f"{self.user.username}'s booking for {self.movie.title}"
