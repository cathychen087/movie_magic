import requests
import stripe
import qrcode
import base64
from io import BytesIO
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import User, Favorite, Movie, Booking, Review, Challenge
from .forms import CustomUserCreationForm
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from django.urls import reverse
import json
from .tmdb_client import tmdb_client

def movie_list(request):
    try:
        movies_data = tmdb_client.get_popular_movies()
        movies = movies_data['results']
        
        # Get user's favorite movies
        favorite_movies = set()
        if request.user.is_authenticated:
            favorite_movies = set(request.user.favorite_movies.values_list('tmdb_id', flat=True))
        
        # Process each movie's data
        for movie in movies:
            movie['poster_url'] = f'https://image.tmdb.org/t/p/w500{movie["poster_path"]}' if movie.get('poster_path') else None
            movie['is_favorite'] = movie['id'] in favorite_movies
            
        return render(request, 'movies/movie_list.html', {'movies': movies})
    except Exception as e:
        return render(request, 'movies/movie_list.html', {'error': str(e)})

def movie_detail(request, movie_id):
    try:
        # Get movie details from TMDB API
        movie_data = tmdb_client.get_movie(movie_id)
        movie, created = Movie.objects.get_or_create(
            tmdb_id=movie_id,
            defaults={
                'title': movie_data['title'],
                'overview': movie_data['overview'],
                'poster_path': movie_data['poster_path'],
                'backdrop_path': movie_data['backdrop_path'],
                'release_date': movie_data['release_date'],
                'vote_average': movie_data['vote_average']
            }
        )
        
        # Add image URLs
        movie.poster_url = f'https://image.tmdb.org/t/p/w500{movie.poster_path}' if movie.poster_path else None
        movie.backdrop_url = f'https://image.tmdb.org/t/p/original{movie.backdrop_path}' if movie.backdrop_path else None
        
        # Get movie trailer
        videos = tmdb_client.get_movie_videos(movie_id)
        trailer = next((video for video in videos['results'] if video['type'] == 'Trailer'), None)
        
        # Get reviews
        reviews = Review.objects.filter(movie=movie).order_by('-created_at')
        
        # Check if movie is favorited by the user
        is_favorite = False
        if request.user.is_authenticated:
            is_favorite = request.user.favorite_movies.filter(tmdb_id=movie_id).exists()
        
        context = {
            'movie': movie,
            'trailer': trailer,
            'reviews': reviews,
            'is_favorite': is_favorite
        }
        return render(request, 'movies/movie_detail.html', context)
    except Exception as e:
        return render(request, 'movies/movie_detail.html', {'error': str(e)})

@login_required
def booking_page(request, movie_id):
    try:
        # Get movie information
        movie_response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={settings.TMDB_API_KEY}&language=en-US'
        )
        movie_response.raise_for_status()
        movie = movie_response.json()
        
        # Add poster URL
        movie['poster_url'] = f'https://image.tmdb.org/t/p/w500{movie["poster_path"]}' if movie.get('poster_path') else None
        
        # Generate showtimes for today only with 3 options
        showtimes = []
        today = datetime.now()
        # Generate 3 showtimes for today
        for hour in [14, 17, 20]:  # 2 PM, 5 PM, and 8 PM
            showtime = {
                'date': today.strftime('%Y-%m-%d'),
                'time': f'{hour:02d}:00',
                'price': 5.99  # Price in EUR
            }
            showtimes.append(showtime)
        
        context = {
            'movie': movie,
            'showtimes': showtimes
        }
        return render(request, 'movies/booking.html', context)
    except requests.RequestException as e:
        return render(request, 'movies/booking.html', {'error': str(e)})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('movie_list')
        else:
            return render(request, 'movies/login.html', {'error': 'Invalid username or password'})
    return render(request, 'movies/login.html')

def logout_view(request):
    logout(request)
    return redirect('movie_list')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('movie_list')
        else:
            print(form.errors)  # For debugging
    else:
        form = CustomUserCreationForm()
    return render(request, 'movies/register.html', {'form': form})

@login_required
def toggle_favorite(request, movie_id):
    if request.method == 'POST':
        try:
            movie = Movie.objects.get(tmdb_id=movie_id)
            if request.user.favorite_movies.filter(tmdb_id=movie_id).exists():
                request.user.favorite_movies.remove(movie)
                is_favorite = False
            else:
                request.user.favorite_movies.add(movie)
                is_favorite = True
            return JsonResponse({'success': True, 'is_favorite': is_favorite})
        except Movie.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Movie not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@login_required
def favorite_movies(request):
    favorite_movies = request.user.favorite_movies.all()
    return render(request, 'movies/favorite_movies.html', {'movies': favorite_movies})

@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    context = {
        'booking': booking,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'movies/payment.html', context)

@login_required
def process_payment(request, booking_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(booking.total_amount * 100),  # Convert to cents
            currency='eur',  # Change to EUR
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
            return_url=request.build_absolute_uri(
                reverse('booking_confirmation', args=[booking.id])
            ),
        )

        if intent.status == 'succeeded':
            # Update booking status
            booking.payment_status = 'paid'
            booking.stripe_payment_id = intent.id
            booking.save()

            return JsonResponse({
                'success': True,
                'confirmation_url': reverse('booking_confirmation', args=[booking.id])
            })
        else:
            return JsonResponse({
                'error': 'Payment failed. Please try again.'
            }, status=400)

    except stripe.error.CardError as e:
        return JsonResponse({
            'error': e.error.message
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.payment_status != 'paid':
        messages.error(request, 'This booking has not been paid for.')
        return redirect('movie_list')
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"Booking ID: {booking.id}\nMovie: {booking.movie.title}\nDate: {booking.showtime_date}\nTime: {booking.showtime_time}\nSeats: {booking.seats}")
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'booking': booking,
        'qr_code': qr_code,
    }
    return render(request, 'movies/booking_confirmation.html', context)

@login_required
def profile(request):
    # Get user's bookings
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    # Get user's favorite movies with poster URLs
    favorite_movies = request.user.favorite_movies.all()
    for movie in favorite_movies:
        movie.poster_url = f'https://image.tmdb.org/t/p/w500{movie.poster_path}' if movie.poster_path else None
    
    context = {
        'bookings': bookings,
        'favorite_movies': favorite_movies,
    }
    return render(request, 'movies/profile.html', context)

@login_required
def create_booking(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        
        # 尝试获取电影，如果不存在则从 TMDB 获取并创建
        try:
            movie = Movie.objects.get(tmdb_id=data['movie_id'])
        except Movie.DoesNotExist:
            # 从 TMDB 获取电影信息
            tmdb_movie = tmdb_client.get_movie(data['movie_id'])
            if not tmdb_movie:
                return JsonResponse({
                    'success': False,
                    'error': 'Movie not found in TMDB'
                })
            
            # 创建新的电影记录
            movie = Movie.objects.create(
                tmdb_id=data['movie_id'],
                title=tmdb_movie.get('title', ''),
                overview=tmdb_movie.get('overview', ''),
                poster_path=tmdb_movie.get('poster_path', ''),
                backdrop_path=tmdb_movie.get('backdrop_path', ''),
                release_date=datetime.strptime(tmdb_movie.get('release_date', '1900-01-01'), '%Y-%m-%d').date(),
                vote_average=tmdb_movie.get('vote_average', 0.0)
            )
        
        # 创建预订
        booking = Booking.objects.create(
            user=request.user,
            movie=movie,
            showtime_date=datetime.strptime(data['showtime_date'], '%Y-%m-%d').date(),
            showtime_time=datetime.strptime(data['showtime_time'], '%H:%M').time(),
            seats=data['seats'],
            price_per_seat=data['price_per_seat'],
            total_amount=data['total_amount']
        )
        
        return JsonResponse({
            'success': True,
            'booking_id': booking.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            if booking.payment_status == 'paid':
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot cancel a paid booking'
                })
            
            # Delete the booking
            booking.delete()
            
            return JsonResponse({
                'success': True
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
def add_review(request, movie_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 尝试获取电影，如果不存在则从 TMDB 获取并创建
            try:
                movie = Movie.objects.get(tmdb_id=movie_id)
            except Movie.DoesNotExist:
                # 从 TMDB 获取电影信息
                tmdb_movie = tmdb_client.get_movie(movie_id)
                if not tmdb_movie:
                    return JsonResponse({
                        'success': False,
                        'error': 'Movie not found in TMDB'
                    })
                
                # 创建新的电影记录
                movie = Movie.objects.create(
                    tmdb_id=movie_id,
                    title=tmdb_movie.get('title', ''),
                    overview=tmdb_movie.get('overview', ''),
                    poster_path=tmdb_movie.get('poster_path', ''),
                    backdrop_path=tmdb_movie.get('backdrop_path', ''),
                    release_date=datetime.strptime(tmdb_movie.get('release_date', '1900-01-01'), '%Y-%m-%d').date(),
                    vote_average=tmdb_movie.get('vote_average', 0.0)
                )
            
            # 创建评论
            review = Review.objects.create(
                user=request.user,
                movie=movie,
                rating=data.get('rating', 5),
                comment=data.get('comment', '')
            )
            
            return JsonResponse({
                'success': True,
                'review': {
                    'id': review.id,
                    'user': review.user.username,
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%B %d, %Y')
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
def delete_review(request, review_id):
    if request.method == 'POST':
        try:
            review = get_object_or_404(Review, id=review_id, user=request.user)
            review.delete()
            return JsonResponse({
                'success': True
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def health_check(request):
    return HttpResponse("OK", content_type="text/plain")
