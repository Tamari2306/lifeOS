import json
import random
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone

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


def _calc_workout_duration(logs):
    """
    FIX: Calculate actual workout duration from real timestamps.
    Uses logged_at timestamps if available, otherwise estimates from sets.
    Each set is ~2.5 min (including rest). Warm-up/cool-down adds ~5 min.
    """
    if not logs:
        return 0

    # Try to use real start/end timestamps from the log entries
    timestamps = [l.logged_at for l in logs if hasattr(l, 'logged_at') and l.logged_at]
    if len(timestamps) >= 2:
        timestamps.sort()
        delta = timestamps[-1] - timestamps[0]
        # Add average time for the last exercise (~5 min) then round up
        total_seconds = delta.total_seconds() + 300
        return max(5, round(total_seconds / 60))

    # Fallback: estimate based on volume
    # Avg 45s per set + 90s rest = ~2.25 min per set, plus 5 min warmup
    total_sets = sum(l.sets for l in logs)
    return max(5, round(total_sets * 2.25 + 5))


@login_required
def dashboard(request):
    today     = date.today()
    exercises = Exercise.objects.all().order_by('category', 'name')

    done_ids   = set(WorkoutLog.objects.filter(user=request.user, date=today).values_list('exercise_id', flat=True))
    today_logs = list(WorkoutLog.objects.filter(user=request.user, date=today).select_related('exercise'))
    total_reps = sum(l.reps_per_set * l.sets for l in today_logs)
    total_sets = sum(l.sets for l in today_logs)
    streak     = _streak(request.user)
    chart_labels, chart_data = _weekly_chart(request.user)

    # FIX: use real duration calculation instead of sets * 2
    workout_minutes = _calc_workout_duration(today_logs)

    # Workout start time — earliest logged_at for today
    workout_start_time = None
    if today_logs:
        times = [l.logged_at for l in today_logs if hasattr(l, 'logged_at') and l.logged_at]
        if times:
            # Convert to local time for display
            earliest = min(times)
            workout_start_time = timezone.localtime(earliest).strftime('%I:%M %p')

    exercise_list = []
    for ex in exercises:
        ex.is_done = ex.id in done_ids
        exercise_list.append(ex)

    completed_count = len(done_ids)
    total_exercises = exercises.count()
    progress_pct    = int(completed_count / total_exercises * 100) if total_exercises else 0

    context = {
        'today':              today,
        'exercises':          exercise_list,
        'completed_count':    completed_count,
        'total_exercises':    total_exercises,
        'progress_pct':       progress_pct,
        'total_reps':         total_reps,
        'total_sets':         total_sets,
        'workout_minutes':    workout_minutes,
        'workout_start_time': workout_start_time,
        'streak':             streak,
        'workout_name':       WORKOUT_NAMES.get(today.weekday(), 'Full Body'),
        'quote':              random.choice(QUOTES),
        'chart_labels':       json.dumps(chart_labels),
        'chart_data':         json.dumps(chart_data),
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
        defaults={
            'reps_per_set': reps_per_set,
            'sets': sets,
            'completed': True,
            'logged_at': timezone.now(),   # FIX: store real timestamp
        },
    )
    if not created:
        log.reps_per_set = reps_per_set
        log.sets = sets
        # Don't overwrite logged_at — keep original time
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

    return render(request, 'fitness/partials/add_exercise_success.html', {'name': name})