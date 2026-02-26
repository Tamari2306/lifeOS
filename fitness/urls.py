from django.urls import path
from . import views

app_name = 'fitness'

urlpatterns = [
    path('',                  views.dashboard,        name='dashboard'),
    path('log-exercise/',     views.log_exercise,     name='log_exercise'),
    path("add-exercise-form/", views.add_exercise_form, name="add_exercise_form"),
    path("add-exercise/", views.add_exercise, name="add_exercise"),
    path('schedule/add/', views.add_schedule_exercise,    name='add_schedule_exercise'),
    path('schedule/delete/<int:pk>/',  views.delete_schedule_exercise, name='delete_schedule_exercise'),
]