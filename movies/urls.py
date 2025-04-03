from django.urls import path
from . import views
from .views import health_check

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('movie/<int:movie_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('movie/<int:movie_id>/booking/', views.booking_page, name='booking_page'),
    path('booking/<int:booking_id>/payment/', views.payment_page, name='payment_page'),
    path('booking/<int:booking_id>/process-payment/', views.process_payment, name='process_payment'),
    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('api/create-booking/', views.create_booking, name='create_booking'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('movie/<int:movie_id>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('favorites/', views.favorite_movies, name='favorite_movies'),
    path('health/', health_check, name='health_check'),
] 