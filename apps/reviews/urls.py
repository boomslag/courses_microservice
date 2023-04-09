from django.urls import path
from .views import *

app_name = "reviews"

urlpatterns = [
    path('list/<identifier>/', GetCourseReviewsView.as_view()),
    path('create/', CreateReviewView.as_view()),
    path('edit/', UpdateReviewView.as_view()),
    path('get/<id>/', GetReviewView.as_view()),
]
