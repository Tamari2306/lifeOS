from django.urls import path
from . import views

app_name = 'checklist'

urlpatterns = [
    path('',                                    views.dashboard,                name='dashboard'),
    # personal
    path('add/',                                views.add_item,                 name='add'),
    path('toggle/<int:item_id>/',               views.toggle_item,              name='toggle'),
    path('delete/<int:item_id>/',               views.delete_item,              name='delete'),
    path('reflect/',                            views.save_reflection,          name='reflect'),
    # work daily
    path('work/add/',                           views.add_work_item,            name='work_add'),
    path('work/toggle/<int:item_id>/',          views.toggle_work_item,         name='work_toggle'),
    path('work/delete/<int:item_id>/',          views.delete_work_item,         name='work_delete'),
    # week
    path('week/add/',                           views.add_week_task,            name='week_add'),
    path('week/status/<int:task_id>/',          views.update_week_task_status,  name='week_status'),
    path('week/delete/<int:task_id>/',          views.delete_week_task,         name='week_delete'),
    # month
    path('month/add/',                          views.add_month_goal,           name='month_add'),
    path('month/status/<int:goal_id>/',         views.update_month_goal_status, name='month_status'),
    path('month/delete/<int:goal_id>/',         views.delete_month_goal,        name='month_delete'),
]