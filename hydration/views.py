import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import WaterLog, HydrationGoal


def _streak(user):
    streak = 0
    day = date.today()
    goal = HydrationGoal.objects.filter(user=user).first()
    target = goal.daily_goal if goal else 2000
    while True:
        total = sum(l.amount for l in WaterLog.objects.filter(user=user, date=day))
        if total >= target:
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak


def _weekly(user):
    labels, data = [], []
    today = date.today()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        total = sum(l.amount for l in WaterLog.objects.filter(user=user, date=d))
        labels.append(d.strftime('%a'))
        data.append(total)
    return labels, data


@login_required
def dashboard(request):
    today      = date.today()
    goal_obj   = HydrationGoal.objects.filter(user=request.user).first()
    daily_goal = goal_obj.daily_goal if goal_obj else 2000
    today_logs = WaterLog.objects.filter(user=request.user, date=today).order_by('-logged_at')
    consumed   = sum(l.amount for l in today_logs)
    remaining  = max(0, daily_goal - consumed)
    pct        = min(100, int(consumed / daily_goal * 100)) if daily_goal else 0
    ring_offset = round(490.09 * (1 - pct / 100), 2)
    streak     = _streak(request.user)
    chart_labels, chart_data = _weekly(request.user)

    return render(request, 'hydration/dashboard.html', {
        'today':        today,
        'daily_goal':   daily_goal,
        'consumed':     consumed,
        'remaining':    remaining,
        'pct':          pct,
        'ring_offset':  ring_offset,
        'log_count':    today_logs.count(),
        'today_logs':   today_logs,
        'streak':       streak,
        'chart_labels': json.dumps(chart_labels),
        'chart_data':   json.dumps(chart_data),
    })


@login_required
@require_POST
def set_goal(request):
    """Let the user set their own daily water goal."""
    try:
        amount = int(request.POST.get('daily_goal', 2000))
        if 500 <= amount <= 6000:
            HydrationGoal.objects.update_or_create(
                user=request.user,
                defaults={'daily_goal': amount}
            )
    except (ValueError, TypeError):
        pass
    return redirect('/hydration/')


@login_required
@require_POST
def add_water(request):
    amount = request.POST.get('amount', '0').strip()
    try:
        amount = int(amount)
        if amount > 0:
            WaterLog.objects.create(user=request.user, amount=amount, date=date.today())
    except (ValueError, TypeError):
        pass
    return redirect('/hydration/')


@login_required
@require_POST
def delete_log(request, log_id):
    log = get_object_or_404(WaterLog, id=log_id, user=request.user)
    log.delete()
    return redirect('/hydration/')