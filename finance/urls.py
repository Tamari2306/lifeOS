from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.dashboard,        name='finance_dashboard'),
    path('set-budget/',                   views.set_budget,       name='finance_set_budget'),
    path('add-expense/',                  views.add_expense,      name='finance_add_expense'),
    path('delete-expense/<int:exp_id>/',  views.delete_expense,   name='finance_delete_expense'),
    path('add-goal/',                     views.add_savings_goal, name='finance_add_goal'),
    path('deposit/<int:goal_id>/',        views.deposit_savings,  name='finance_deposit'),
]