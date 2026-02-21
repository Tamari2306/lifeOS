from django.urls import path
from . import views

app_name = 'bible'

urlpatterns = [
    path('',                                    views.dashboard,       name='dashboard'),
    path('log-reading/',                        views.log_reading,     name='log_reading'),
    path('delete-log/<int:log_id>/',            views.delete_log,      name='delete_log'),
    path('edit-log/<int:log_id>/',              views.edit_log,        name='edit_log'),
    path('set-plan/',                           views.set_plan,        name='set_plan'),
    path('delete-plan/<int:plan_id>/',          views.delete_plan,     name='delete_plan'),
    path('add-prayer/',                         views.add_prayer,      name='add_prayer'),
    path('answer-prayer/<int:prayer_id>/',      views.answer_prayer,   name='answer_prayer'),
    path('delete-prayer/<int:prayer_id>/',      views.delete_prayer,   name='delete_prayer'),
    path('add-memorization/',                   views.add_memorization,name='add_memorization'),
    path('toggle-mastered/<int:mem_id>/',       views.toggle_mastered, name='toggle_mastered'),
]