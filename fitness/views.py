import json
import random
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Exercise, WorkoutLog


QUOTES = [
    "Strong women lift each other up — and heavy weights too.",
    "Your body can do it. It's your mind you have to convince.",
    "Consistency is what transforms average into excellence.",
    "Every rep is a promise you keep to yourself.",
    "She believed she could, so she did.",
    "Progress, not perfection. Show up today.",
    "The pain you feel today is the strength you'll feel tomorrow.",
    "Small steps every day lead to massive results.",
    "Discipline is choosing what you want most over what you want now.",
    "You didn't come this far to only come this far.",
]

WORKOUT_NAMES = {
    0: "Full Body Monday",
    1: "Abs & Core",
    2: "Lower Body",
    3: "Upper Body",
    4: "Full Body Burn",
    5: "Glutes & Hips",
    6: "Active Recovery",
}


def _streak(user):
    streak = 0
    day = date.today()
    while True:
        if WorkoutLog.objects.filter(user=user, date=day).exists():
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak


def _weekly_chart(user):
    labels, data = [], []
    today = date.today()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        reps = sum(l.reps_per_set * l.sets for l in WorkoutLog.objects.filter(user=user, date=d))
        labels.append(d.strftime('%a'))
        data.append(reps)
    return labels, data


@login_required
def dashboard(request):
    today     = date.today()
    exercises = Exercise.objects.all().order_by('category', 'name')

    done_ids   = set(WorkoutLog.objects.filter(user=request.user, date=today).values_list('exercise_id', flat=True))
    today_logs = WorkoutLog.objects.filter(user=request.user, date=today)
    total_reps = sum(l.reps_per_set * l.sets for l in today_logs)
    total_sets = sum(l.sets for l in today_logs)
    streak     = _streak(request.user)
    chart_labels, chart_data = _weekly_chart(request.user)

    exercise_list = []
    for ex in exercises:
        ex.is_done = ex.id in done_ids
        exercise_list.append(ex)

    completed_count = len(done_ids)
    total_exercises = exercises.count()
    progress_pct    = int(completed_count / total_exercises * 100) if total_exercises else 0
    workout_minutes = total_sets * 2

    context = {
        'today':           today,
        'exercises':       exercise_list,
        'completed_count': completed_count,
        'total_exercises': total_exercises,
        'progress_pct':    progress_pct,
        'total_reps':      total_reps,
        'total_sets':      total_sets,
        'workout_minutes': workout_minutes,
        'streak':          streak,
        'workout_name':    WORKOUT_NAMES.get(today.weekday(), 'Full Body'),
        'quote':           random.choice(QUOTES),
        'chart_labels':    json.dumps(chart_labels),
        'chart_data':      json.dumps(chart_data),
    }
    return render(request, 'fitness/dashboard.html', context)


@login_required
@require_POST
def log_exercise(request):
    exercise_id  = request.POST.get('exercise_id')
    reps_per_set = int(request.POST.get('reps', 10))
    sets         = int(request.POST.get('sets', 3))
    exercise     = get_object_or_404(Exercise, id=exercise_id)

    log, created = WorkoutLog.objects.get_or_create(
        user=request.user, exercise=exercise, date=date.today(),
        defaults={'reps_per_set': reps_per_set, 'sets': sets, 'completed': True},
    )
    if not created:
        log.reps_per_set = reps_per_set
        log.sets = sets
        log.save()

    return render(request, 'fitness/partials/exercise_logged.html', {'exercise': exercise, 'log': log})


@login_required
def add_exercise_form(request):
    return render(request, 'fitness/partials/add_exercise_form.html')


@login_required
@require_POST
def add_exercise(request):
    name         = request.POST.get('name', '').strip()
    category     = request.POST.get('category', 'Core')
    default_reps = int(request.POST.get('default_reps', 10))
    sets         = int(request.POST.get('sets', 3))
    description  = request.POST.get('description', '').strip()

    if name:
        Exercise.objects.create(
            name=name,
            category=category,
            default_reps=default_reps,
            sets=sets,
            description=description,
            created_by=request.user,
        )

    # Return the success partial — HTMX swaps this into #qa-area
    return render(request, 'fitness/partials/add_exercise_success.html', {'name': name})