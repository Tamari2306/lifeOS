import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from calendar import monthrange

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Expense, MonthlyBudget, SavingsGoal, SavingsDeposit


CAT_COLORS = {
    'food':'#38bdf8','transport':'#818cf8','bills':'#fb7185',
    'shopping':'#fbbf24','health':'#34d399','misc':'#94a3b8',
}
CAT_EMOJI = {
    'food':'🍜','transport':'🚗','bills':'📋',
    'shopping':'🛍','health':'🏥','misc':'📦',
}


def _spending_by_cat(expenses):
    cats = {}
    for e in expenses:
        cats[e.category] = cats.get(e.category, 0) + float(e.amount)
    return cats


def _weekly_spending(user, year, month):
    days_in_month = monthrange(year, month)[1]
    week_starts = [1, 8, 15, 22]
    week_ends   = [7, 14, 21, days_in_month]
    labels, data = [], []
    for i in range(4):
        ws = date(year, month, week_starts[i])
        we = date(year, month, min(week_ends[i], days_in_month))
        total = sum(float(e.amount) for e in Expense.objects.filter(user=user, date__gte=ws, date__lte=we))
        labels.append('W' + str(i+1))
        data.append(round(total, 2))
    return labels, data


def _monthly_trend(user):
    labels, data = [], []
    today = date.today()
    for i in range(5, -1, -1):
        month_offset = today.month - i
        year  = today.year + (month_offset - 1) // 12
        month = (month_offset - 1) % 12 + 1
        total = sum(float(e.amount) for e in Expense.objects.filter(user=user, date__year=year, date__month=month))
        labels.append(date(year, month, 1).strftime('%b'))
        data.append(round(total, 2))
    return labels, data


@login_required
def dashboard(request):
    today = date.today()
    year, month = today.year, today.month

    budget_obj     = MonthlyBudget.objects.filter(user=request.user, year=year, month=month).first()
    monthly_budget = float(budget_obj.amount) if budget_obj else 0

    month_expenses = Expense.objects.filter(user=request.user, date__year=year, date__month=month)
    total_spent    = sum(float(e.amount) for e in month_expenses)
    balance        = monthly_budget - total_spent
    spent_pct      = min(100, int(total_spent / monthly_budget * 100)) if monthly_budget else 0
    ring_offset    = round(376.99 * (1 - spent_pct / 100), 2)

    if spent_pct >= 90:
        budget_status = 'danger'
    elif spent_pct >= 70:
        budget_status = 'warning'
    else:
        budget_status = 'safe'

    by_cat           = _spending_by_cat(month_expenses)
    cat_chart_labels = [c.title() for c in by_cat.keys()]
    cat_chart_data   = [round(v, 2) for v in by_cat.values()]
    cat_chart_colors = [CAT_COLORS.get(c, '#94a3b8') for c in by_cat.keys()]

    recent                   = Expense.objects.filter(user=request.user).order_by('-added_at')[:10]
    week_labels, week_data   = _weekly_spending(request.user, year, month)
    trend_labels, trend_data = _monthly_trend(request.user)

    goals        = SavingsGoal.objects.filter(user=request.user)
    total_saved  = sum(float(g.saved_amount) for g in goals)

    days_in_month = monthrange(year, month)[1]
    days_passed   = today.day
    days_left     = days_in_month - days_passed
    daily_avg     = round(total_spent / days_passed, 2) if days_passed else 0
    projected_end = round(daily_avg * days_in_month, 2)
    safe_daily    = round(balance / days_left, 2) if days_left > 0 and balance > 0 else 0

    return render(request, 'finance/dashboard.html', {
        'today':            today,
        'month_name':       today.strftime('%B %Y'),
        'monthly_budget':   monthly_budget,
        'total_spent':      round(total_spent, 2),
        'balance':          round(balance, 2),
        'spent_pct':        spent_pct,
        'ring_offset':      ring_offset,
        'budget_status':    budget_status,
        'by_cat':           by_cat,
        'cat_emoji':        CAT_EMOJI,
        'recent':           recent,
        'goals':            goals,
        'total_saved':      round(total_saved, 2),
        'days_left':        days_left,
        'daily_avg':        daily_avg,
        'projected_end':    projected_end,
        'safe_daily':       safe_daily,
        'cat_chart_labels': json.dumps(cat_chart_labels),
        'cat_chart_data':   json.dumps(cat_chart_data),
        'cat_chart_colors': json.dumps(cat_chart_colors),
        'week_labels':      json.dumps(week_labels),
        'week_data':        json.dumps(week_data),
        'trend_labels':     json.dumps(trend_labels),
        'trend_data':       json.dumps(trend_data),
    })


@login_required
@require_POST
def set_budget(request):
    try:
        amount = Decimal(request.POST.get('amount', '0').strip())
        if amount > 0:
            today = date.today()
            MonthlyBudget.objects.update_or_create(
                user=request.user, year=today.year, month=today.month,
                defaults={'amount': amount}
            )
    except (InvalidOperation, Exception):
        pass
    return redirect('/finance/')


@login_required
@require_POST
def add_expense(request):
    try:
        amount   = Decimal(request.POST.get('amount', '0').strip())
        category = request.POST.get('category', 'misc')
        note     = request.POST.get('note', '').strip()
        exp_date = request.POST.get('date', str(date.today()))
        if amount > 0:
            Expense.objects.create(
                user=request.user, amount=amount,
                category=category, note=note, date=exp_date,
            )
    except (InvalidOperation, Exception):
        pass
    return redirect('/finance/')


@login_required
@require_POST
def delete_expense(request, exp_id):
    exp = get_object_or_404(Expense, id=exp_id, user=request.user)
    exp.delete()
    return redirect('/finance/')


@login_required
@require_POST
def add_savings_goal(request):
    try:
        name    = request.POST.get('name', '').strip()
        target  = Decimal(request.POST.get('target_amount', '0').strip())
        contrib = Decimal(request.POST.get('contribution', '0').strip())
        freq    = request.POST.get('frequency', 'monthly')
        emoji   = request.POST.get('emoji', '🏆').strip()
        t_date  = request.POST.get('target_date', '').strip() or None
        if name and target > 0:
            SavingsGoal.objects.create(
                user=request.user, name=name, target_amount=target,
                contribution=contrib, frequency=freq, emoji=emoji, target_date=t_date,
            )
    except (InvalidOperation, Exception):
        pass
    return redirect('/finance/')


@login_required
@require_POST
def deposit_savings(request, goal_id):
    try:
        goal   = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
        amount = Decimal(request.POST.get('amount', '0').strip())
        note   = request.POST.get('note', '').strip()
        if amount > 0:
            SavingsDeposit.objects.create(goal=goal, amount=amount, note=note)
            goal.saved_amount = goal.saved_amount + amount
            goal.save()
    except (InvalidOperation, Exception):
        pass
    return redirect('/finance/')


@login_required
@require_POST
def delete_goal(request, goal_id):
    goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
    goal.delete()
    return redirect('/finance/')


@login_required
@require_POST
def edit_goal(request, goal_id):
    goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
    try:
        name    = request.POST.get('name', '').strip()
        target  = Decimal(request.POST.get('target_amount', '0').strip())
        contrib = Decimal(request.POST.get('contribution', '0').strip())
        emoji   = request.POST.get('emoji', goal.emoji).strip()
        if name and target > 0:
            goal.name          = name
            goal.target_amount = target
            goal.contribution  = contrib
            goal.emoji         = emoji
            goal.save()
    except (InvalidOperation, Exception):
        pass
    return redirect('/finance/')