from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('',                              views.dashboard,          name='dashboard'),
    path('set-budget/',                   views.set_budget,         name='set_budget'),
    path('add-expense/',                  views.add_expense,        name='add_expense'),
    path('delete-expense/<int:exp_id>/',  views.delete_expense,     name='delete_expense'),
    path('add-goal/',                     views.add_savings_goal,   name='add_goal'),
    path('deposit/<int:goal_id>/',        views.deposit_savings,    name='deposit'),
    path('delete-goal/<int:goal_id>/',    views.delete_savings_goal, name='delete_goal'),  # NEW
    path('edit-goal/<int:goal_id>/',      views.edit_savings_goal,  name='edit_goal'),    # NEW
]