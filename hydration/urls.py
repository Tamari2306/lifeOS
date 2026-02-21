from django.urls import path
from . import views

app_name = 'hydration'

urlpatterns = [
    path('',                     views.dashboard, name='dashboard'),
    path('set-goal/',            views.set_goal,  name='set_goal'),
    path('add/',                 views.add_water, name='add'),
    path('delete/<int:log_id>/', views.delete_log, name='delete'),
]