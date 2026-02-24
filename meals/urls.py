from django.urls import path
from . import views

app_name = 'meals'

urlpatterns = [
    path('',                               views.dashboard,         name='dashboard'),
    path('log/',                           views.log_meal,          name='log'),
    path('delete/<int:entry_id>/',         views.delete_meal,       name='delete'),
    path('set-goals/',                     views.set_goals,         name='set_goals'),
    path('save-recipe/',                   views.save_recipe,       name='save_recipe'),
    path('delete-recipe/<int:recipe_id>/', views.delete_recipe,     name='delete_recipe'),
    path('estimate/',                      views.estimate_meal_api, name='estimate'),

    # ── Meal Plans ──────────────────────────────────────────────────────────
    path('plan/add/',                      views.add_meal_plan,     name='plan_add'),
    path('plan/delete/<int:plan_id>/',     views.delete_meal_plan,  name='plan_delete'),
    path('plan/log/<int:plan_id>/',        views.log_from_plan,     name='plan_log'),
]