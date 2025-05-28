from .views import fetch_and_store_question
from django.urls import path
from . import views

urlpatterns = [
    path('fetch-question/', fetch_and_store_question, name='fetch_question'),
    path("", views.home_view, name="home"),
    path("question/<int:pk>/", views.question_detail, name="question_detail"),
    path("solved/", views.all_solved_view, name="all_solved"),
    path("new/", views.new_entry_view, name="new_entry")
]