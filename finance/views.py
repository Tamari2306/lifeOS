import json
from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Expense, MonthlyBudget, SavingsGoal, SavingsDeposit


CAT_COLORS = {
    'food':      '#38bdf8',
    'transport': '#818cf8',
    'bills':     '#fb7185',
    'shopping':  '#fbbf24',
    'health':    '#34d399',
    'misc':      '#94a3b8',
}

CAT_EMOJI = {
    'food':      '&#x1F35C;',
    'transport': '&#x1F697;',
    'bills':     '&#x1F4CB;',
    'shopping':  '&#x1F6CD;',
    'health':    '&#x1F3E5;',
    'misc':      '&#x1F4E6;',
}


def _spending_by_cat(expenses):
    cats = {}
    for e in expenses:
        cats[e.category] = cats.get(e.category, 0) + float(e.amount)
    return cats


def _weekly_spending(user, year, month):
    """Break month spending into 4 weeks."""
    labels, data = [], []
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    week_starts = [1, 8, 15, 22]
    week_ends   = [7, 14, 21, days_in_month]
    for i in range(4):
        ws = date(year, month, week_starts[i])
        we = date(year, month, min(week_ends[i], days_in_month))
        total = sum(
            float(e.amount)
            for e in Expense.objects.filter(user=user, date__gte=ws, date__lte=we)
        )
        labels.append('W' + str(i+1))
        data.append(round(total, 2))
    return labels, data


def _monthly_trend(user):
    """Last 6 months spending totals."""
    labels, data = [], []
    today = date.today()
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year - ((today.month - i - 1) // 12)
        total = sum(
            float(e.amount)
            for e in Expense.objects.filter(user=user, date__year=y, date__month=m)
        )
        labels.append(date(y, m, 1).strftime('%b'))
        data.append(round(total, 2))
    return labels, data


def dashboard(request):
    today = date.today()
    year, month = today.year, today.month

    if not request.user.is_authenticated:
        return render(request, 'finance/dashboard.html', _empty_context(today))

    # Monthly budget
    budget_obj    = MonthlyBudget.objects.filter(user=request.user, year=year, month=month).first()
    monthly_budget = float(budget_obj.amount) if budget_obj else 0

    # This month's expenses
    month_expenses = Expense.objects.filter(user=request.user, date__year=year, date__month=month)
    total_spent    = sum(float(e.amount) for e in month_expenses)
    balance        = monthly_budget - total_spent
    spent_pct      = min(100, int(total_spent / monthly_budget * 100)) if monthly_budget else 0
    # Ring offset for SVG r=70, circumference=439.82
    ring_offset    = round(439.82 * (1 - spent_pct / 100), 2)

    # Budget warning level
    if spent_pct >= 90:
        budget_status = 'danger'
    elif spent_pct >= 70:
        budget_status = 'warning'
    else:
        budget_status = 'safe'

    # Category breakdown
    by_cat     = _spending_by_cat(month_expenses)
    cat_chart_labels = [c.title() for c in by_cat.keys()]
    cat_chart_data   = [round(v, 2) for v in by_cat.values()]
    cat_chart_colors = [CAT_COLORS.get(c, '#94a3b8') for c in by_cat.keys()]

    # Recent 10 expenses
    recent = Expense.objects.filter(user=request.user).order_by('-added_at')[:10]

    # Weekly breakdown
    week_labels, week_data = _weekly_spending(request.user, year, month)

    # Monthly trend (last 6 months)
    trend_labels, trend_data = _monthly_trend(request.user)

    # Savings goals
    goals = SavingsGoal.objects.filter(user=request.user)
    total_saved = sum(float(g.saved_amount) for g in goals)

    # Month-end analysis
    days_in_month = 28  # safe default
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    days_passed   = today.day
    days_left     = days_in_month - days_passed
    daily_avg     = round(total_spent / days_passed, 2) if days_passed else 0
    projected_end = round(daily_avg * days_in_month, 2)

    context = {
        'today':             today,
        'month_name':        today.strftime('%B %Y'),
        'monthly_budget':    monthly_budget,
        'total_spent':       round(total_spent, 2),
        'balance':           round(balance, 2),
        'spent_pct':         spent_pct,
        'ring_offset':       ring_offset,
        'budget_status':     budget_status,
        'by_cat':            by_cat,
        'cat_emoji':         CAT_EMOJI,
        'recent':            recent,
        'goals':             goals,
        'total_saved':       round(total_saved, 2),
        'days_left':         days_left,
        'daily_avg':         daily_avg,
        'projected_end':     projected_end,
        'cat_chart_labels':  json.dumps(cat_chart_labels),
        'cat_chart_data':    json.dumps(cat_chart_data),
        'cat_chart_colors':  json.dumps(cat_chart_colors),
        'week_labels':       json.dumps(week_labels),
        'week_data':         json.dumps(week_data),
        'trend_labels':      json.dumps(trend_labels),
        'trend_data':        json.dumps(trend_data),
    }
    return render(request, 'finance/dashboard.html', context)


def _empty_context(today):
    return {
        'today': today, 'month_name': today.strftime('%B %Y'),
        'monthly_budget': 0, 'total_spent': 0, 'balance': 0,
        'spent_pct': 0, 'ring_offset': 439.82, 'budget_status': 'safe',
        'by_cat': {}, 'cat_emoji': CAT_EMOJI, 'recent': [],
        'goals': [], 'total_saved': 0, 'days_left': 0, 'daily_avg': 0,
        'projected_end': 0,
        'cat_chart_labels': '[]', 'cat_chart_data': '[]', 'cat_chart_colors': '[]',
        'week_labels': '["W1","W2","W3","W4"]', 'week_data': '[0,0,0,0]',
        'trend_labels': '[]', 'trend_data': '[]',
    }


@require_POST
def set_budget(request):
    amount = request.POST.get('amount', '0').strip()
    try:
        amount = Decimal(amount)
        if amount > 0 and request.user.is_authenticated:
            today = date.today()
            MonthlyBudget.objects.update_or_create(
                user=request.user, year=today.year, month=today.month,
                defaults={'amount': amount}
            )
    except Exception:
        pass
    return redirect('/finance/')


@require_POST
def add_expense(request):
    try:
        amount   = Decimal(request.POST.get('amount', '0'))
        category = request.POST.get('category', 'misc')
        note     = request.POST.get('note', '').strip()
        exp_date = request.POST.get('date', str(date.today()))
        if amount > 0 and request.user.is_authenticated:
            Expense.objects.create(
                user=request.user, amount=amount,
                category=category, note=note, date=exp_date,
            )
    except Exception:
        pass
    return redirect('/finance/')


@require_POST
def delete_expense(request, exp_id):
    if request.user.is_authenticated:
        exp = get_object_or_404(Expense, id=exp_id, user=request.user)
        exp.delete()
    return redirect('/finance/')


@require_POST
def add_savings_goal(request):
    try:
        name     = request.POST.get('name', '').strip()
        target   = Decimal(request.POST.get('target_amount', '0'))
        contrib  = Decimal(request.POST.get('contribution', '0'))
        freq     = request.POST.get('frequency', 'monthly')
        emoji    = request.POST.get('emoji', '&#127937;')
        t_date   = request.POST.get('target_date', '') or None
        if name and target > 0 and request.user.is_authenticated:
            SavingsGoal.objects.create(
                user=request.user, name=name, target_amount=target,
                contribution=contrib, frequency=freq, emoji=emoji,
                target_date=t_date,
            )
    except Exception:
        pass
    return redirect('/finance/')


@require_POST
def deposit_savings(request, goal_id):
    try:
        goal   = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
        amount = Decimal(request.POST.get('amount', '0'))
        note   = request.POST.get('note', '').strip()
        if amount > 0:
            SavingsDeposit.objects.create(goal=goal, amount=amount, note=note)
            goal.saved_amount = goal.saved_amount + amount
            goal.save()
    except Exception:
        pass
    return redirect('/finance/')


@require_POST
def delete_savings_goal(request, goal_id):
    if request.user.is_authenticated:
        goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
        goal.delete()
    return redirect('/finance/')


@require_POST
def edit_savings_goal(request, goal_id):
    if request.user.is_authenticated:
        goal = get_object_or_404(SavingsGoal, id=goal_id, user=request.user)
        try:
            name   = request.POST.get('name', '').strip()
            target = Decimal(request.POST.get('target_amount', str(goal.target_amount)))
            contrib = Decimal(request.POST.get('contribution', str(goal.contribution)))
            emoji  = request.POST.get('emoji', goal.emoji)
            if name:
                goal.name = name
            goal.target_amount = target
            goal.contribution = contrib
            goal.emoji = emoji
            goal.save()
        except Exception:
            pass
    return redirect('/finance/')