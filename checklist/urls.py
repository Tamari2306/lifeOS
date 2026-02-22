from django.urls import path
from . import views

app_name = 'checklist'

urlpatterns = [
    # ── Main dashboard ────────────────────────────────────────────────────────
    path('', views.dashboard, name='dashboard'),

    # ── Personal daily checklist ──────────────────────────────────────────────
    path('add/',                      views.add_item,    name='add'),
    path('toggle/<int:item_id>/',     views.toggle_item, name='toggle'),
    path('delete/<int:item_id>/',     views.delete_item, name='delete'),
    path('reflect/',                  views.save_reflection, name='reflect'),

    # ── Routine tasks (predefined / repeating every day) ──────────────────────
    path('routine/add/',                          views.add_routine_task,    name='routine_add'),
    path('routine/delete/<int:task_id>/',         views.delete_routine_task, name='routine_delete'),
    path('routine/toggle-active/<int:task_id>/',  views.toggle_routine_task, name='routine_toggle_active'),
    path('routine/log/<int:log_id>/',             views.toggle_routine_log,  name='routine_log'),

    # ── Work daily ────────────────────────────────────────────────────────────
    path('work/add/',                    views.add_work_item,    name='work_add'),
    path('work/toggle/<int:item_id>/',   views.toggle_work_item, name='work_toggle'),
    path('work/delete/<int:item_id>/',   views.delete_work_item, name='work_delete'),

    # ── Week tasks ────────────────────────────────────────────────────────────
    path('week/add/',                          views.add_week_task,          name='week_add'),
    path('week/status/<int:task_id>/',         views.update_week_task_status, name='week_status'),
    path('week/delete/<int:task_id>/',         views.delete_week_task,       name='week_delete'),

    # ── Month goals ───────────────────────────────────────────────────────────
    path('month/add/',                    views.add_month_goal,          name='month_add'),
    path('month/status/<int:goal_id>/',   views.update_month_goal_status, name='month_status'),
    path('month/delete/<int:goal_id>/',   views.delete_month_goal,       name='month_delete'),
]