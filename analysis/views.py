"""
analysis/views.py
─────────────────
Monthly Analysis — aggregates data from all LifeOS apps and renders
a dashboard page. The /analysis/pdf/ endpoint generates a downloadable PDF.
"""
import io
from datetime import date
from calendar import monthrange, month_name

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# ── Import models from all apps ───────────────────────────────────────────────
try:
    from fitness.models import WorkoutLog, Exercise
except ImportError:
    WorkoutLog = Exercise = None

try:
    from meals.models import MealEntry, NutritionGoal
except ImportError:
    MealEntry = NutritionGoal = None

try:
    from finance.models import Expense, MonthlyBudget, SavingsGoal
except ImportError:
    Expense = MonthlyBudget = SavingsGoal = None

try:
    from checklist.models import ChecklistItem, DayReflection, RoutineLog
except ImportError:
    ChecklistItem = DayReflection = RoutineLog = None

try:
    from hydration.models import HydrationLog
except ImportError:
    HydrationLog = None

try:
    from bible.models import BibleReadingLog
except ImportError:
    BibleReadingLog = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _month_range(year, month):
    """Return (first_day, last_day) date objects for the month."""
    days = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, days)


def _pct(part, total):
    return round(part / total * 100) if total else 0


def _safe_avg(values):
    v = [x for x in values if x is not None]
    return round(sum(v) / len(v), 1) if v else 0


def _collect_fitness(user, first, last):
    if not WorkoutLog:
        return {}
    logs = WorkoutLog.objects.filter(user=user, date__gte=first, date__lte=last)
    workout_days = logs.values('date').distinct().count()
    days_in_month = (last - first).days + 1
    total_sets = sum(l.sets for l in logs)
    total_reps = sum(l.reps_per_set * l.sets for l in logs)
    # streak
    streak = 0
    day = date.today()
    while WorkoutLog.objects.filter(user=user, date=day).exists():
        streak += 1
        day = date(day.year, day.month, day.day - 1) if day.day > 1 else date(day.year - 1 if day.month == 1 else day.year, 12 if day.month == 1 else day.month - 1, monthrange(day.year - 1 if day.month == 1 else day.year, 12 if day.month == 1 else day.month - 1)[1])
    return {
        'workout_days':   workout_days,
        'rest_days':      days_in_month - workout_days,
        'consistency_pct': _pct(workout_days, days_in_month),
        'total_sets':     total_sets,
        'total_reps':     total_reps,
        'current_streak': streak,
        'target_days':    22,  # ~5x/week
    }


def _collect_meals(user, first, last):
    if not MealEntry:
        return {}
    entries = MealEntry.objects.filter(user=user, date__gte=first, date__lte=last)
    days_logged = entries.values('date').distinct().count()
    total_cal   = sum(e.calories for e in entries)
    total_prot  = sum(e.protein  for e in entries)
    total_carbs = sum(e.carbs    for e in entries)
    total_fat   = sum(e.fat      for e in entries)
    days_in_month = (last - first).days + 1
    goal = NutritionGoal.objects.filter(user=user).first() if NutritionGoal else None
    avg_cal  = _safe_avg([total_cal / days_logged]) if days_logged else 0
    return {
        'days_logged':    days_logged,
        'logging_pct':    _pct(days_logged, days_in_month),
        'avg_daily_cal':  round(total_cal / max(days_logged, 1)),
        'avg_protein':    round(total_prot / max(days_logged, 1)),
        'avg_carbs':      round(total_carbs / max(days_logged, 1)),
        'avg_fat':        round(total_fat / max(days_logged, 1)),
        'goal_calories':  goal.calories if goal else 0,
        'total_entries':  entries.count(),
    }


def _collect_finance(user, first, last):
    if not Expense:
        return {}
    from calendar import monthrange as mr
    year, month = first.year, first.month
    expenses   = Expense.objects.filter(user=user, date__gte=first, date__lte=last)
    budget_obj = MonthlyBudget.objects.filter(user=user, year=year, month=month).first() if MonthlyBudget else None
    budget     = float(budget_obj.amount) if budget_obj else 0
    total_spent = sum(float(e.amount) for e in expenses)
    by_cat = {}
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + float(e.amount)
    top_cat = max(by_cat, key=by_cat.get) if by_cat else '—'
    goals = SavingsGoal.objects.filter(user=user) if SavingsGoal else []
    total_saved = sum(float(g.saved_amount) for g in goals)
    return {
        'budget':         budget,
        'total_spent':    round(total_spent, 0),
        'balance':        round(budget - total_spent, 0),
        'spent_pct':      _pct(total_spent, budget) if budget else 0,
        'by_cat':         by_cat,
        'top_category':   top_cat,
        'total_saved':    round(total_saved, 0),
        'savings_goals':  len(goals),
        'transactions':   expenses.count(),
    }


def _collect_checklist(user, first, last):
    if not ChecklistItem:
        return {}
    items = ChecklistItem.objects.filter(user=user, date__gte=first, date__lte=last)
    total    = items.count()
    done     = items.filter(completed=True).count()
    days_in_month = (last - first).days + 1
    # Routine completion
    routine_done  = 0
    routine_total = 0
    if RoutineLog:
        rlogs = RoutineLog.objects.filter(user=user, date__gte=first, date__lte=last)
        routine_total = rlogs.count()
        routine_done  = rlogs.filter(completed=True).count()
    # Reflections
    reflections = DayReflection.objects.filter(user=user, date__gte=first, date__lte=last).count() if DayReflection else 0
    avg_mood = 0
    if DayReflection:
        moods = list(DayReflection.objects.filter(user=user, date__gte=first, date__lte=last).values_list('mood_rating', flat=True))
        avg_mood = _safe_avg(moods)
    return {
        'tasks_total':      total,
        'tasks_done':       done,
        'completion_pct':   _pct(done, total),
        'routine_total':    routine_total,
        'routine_done':     routine_done,
        'routine_pct':      _pct(routine_done, routine_total),
        'reflections':      reflections,
        'avg_mood':         avg_mood,
        'reflection_pct':   _pct(reflections, days_in_month),
    }


def _collect_hydration(user, first, last):
    if not HydrationLog:
        return {}
    logs = HydrationLog.objects.filter(user=user, date__gte=first, date__lte=last)
    days_in_month = (last - first).days + 1
    days_logged = logs.values('date').distinct().count()
    # Try to get goal met days
    try:
        goal_met = logs.filter(met_goal=True).values('date').distinct().count()
    except Exception:
        goal_met = 0
    return {
        'days_logged':   days_logged,
        'days_goal_met': goal_met,
        'goal_met_pct':  _pct(goal_met, days_in_month),
        'logging_pct':   _pct(days_logged, days_in_month),
    }


def _collect_bible(user, first, last):
    if not BibleReadingLog:
        return {}
    logs = BibleReadingLog.objects.filter(user=user, date__gte=first, date__lte=last)
    days_in_month = (last - first).days + 1
    days_read = logs.values('date').distinct().count()
    return {
        'days_read':   days_read,
        'reading_pct': _pct(days_read, days_in_month),
        'entries':     logs.count(),
    }


def _score(data):
    """Compute an overall wellness score 0–100 from all categories."""
    scores = []
    if data.get('fitness'):
        scores.append(min(100, data['fitness'].get('consistency_pct', 0)))
    if data.get('meals'):
        scores.append(min(100, data['meals'].get('logging_pct', 0)))
    if data.get('finance'):
        spent = data['finance'].get('spent_pct', 0)
        scores.append(max(0, 100 - max(0, spent - 80)))  # good if under 80%
    if data.get('checklist'):
        scores.append(data['checklist'].get('completion_pct', 0))
        scores.append(data['checklist'].get('routine_pct', 0))
    if data.get('hydration'):
        scores.append(data['hydration'].get('goal_met_pct', 0))
    if data.get('bible'):
        scores.append(data['bible'].get('reading_pct', 0))
    return round(sum(scores) / len(scores)) if scores else 0


# ── Views ─────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = date.today()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))

    # clamp
    if month < 1:  month = 12; year -= 1
    if month > 12: month = 1;  year += 1

    first, last  = _month_range(year, month)
    display_name = f"{month_name[month]} {year}"

    prev_month = month - 1 if month > 1 else 12
    next_month = month + 1 if month < 12 else 1
    prev_year  = year if month > 1 else year - 1
    next_year  = year if month < 12 else year + 1

    data = {
        'fitness':   _collect_fitness(user=request.user,  first=first, last=last),
        'meals':     _collect_meals(user=request.user,    first=first, last=last),
        'finance':   _collect_finance(user=request.user,  first=first, last=last),
        'checklist': _collect_checklist(user=request.user, first=first, last=last),
        'hydration': _collect_hydration(user=request.user, first=first, last=last),
        'bible':     _collect_bible(user=request.user,    first=first, last=last),
    }
    wellness_score = _score(data)

    return render(request, 'analysis/dashboard.html', {
        'today':        today,
        'year':         year,
        'month':        month,
        'display_name': display_name,
        'first':        first,
        'last':         last,
        'data':         data,
        'wellness_score': wellness_score,
        'prev_month':   prev_month,
        'next_month':   next_month,
        'prev_year':    prev_year,
        'next_year':    next_year,
        'is_current':   (year == today.year and month == today.month),
    })


@login_required
def export_pdf(request):
    """Generate and return a styled monthly analysis PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    today = date.today()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))
    first, last = _month_range(year, month)
    display_name = f"{month_name[month]} {year}"

    data = {
        'fitness':   _collect_fitness(user=request.user,   first=first, last=last),
        'meals':     _collect_meals(user=request.user,     first=first, last=last),
        'finance':   _collect_finance(user=request.user,   first=first, last=last),
        'checklist': _collect_checklist(user=request.user, first=first, last=last),
        'hydration': _collect_hydration(user=request.user, first=first, last=last),
        'bible':     _collect_bible(user=request.user,     first=first, last=last),
    }
    wellness_score = _score(data)

    # ── Colour palette ──────────────────────────────────────────────────────
    BG       = colors.HexColor('#0a0a12')
    CARD     = colors.HexColor('#12121e')
    GREEN    = colors.HexColor('#34d399')
    BLUE     = colors.HexColor('#38bdf8')
    VIOLET   = colors.HexColor('#818cf8')
    AMBER    = colors.HexColor('#fbbf24')
    ROSE     = colors.HexColor('#fb7185')
    MUTED    = colors.HexColor('#64748b')
    SOFT     = colors.HexColor('#94a3b8')
    WHITE    = colors.HexColor('#f1f5f9')

    # ── Styles ──────────────────────────────────────────────────────────────
    def S(name, **kw):
        base = {
            'fontName':  'Helvetica',
            'fontSize':  11,
            'textColor': WHITE,
            'leading':   16,
        }
        base.update(kw)
        return ParagraphStyle(name, **base)

    sTitle   = S('title',   fontName='Helvetica-Bold', fontSize=28, textColor=GREEN,  leading=34, alignment=TA_CENTER)
    sSub     = S('sub',     fontName='Helvetica',      fontSize=13, textColor=SOFT,   leading=18, alignment=TA_CENTER)
    sScore   = S('score',   fontName='Helvetica-Bold', fontSize=48, textColor=VIOLET, leading=56, alignment=TA_CENTER)
    sSecHdr  = S('sechdr',  fontName='Helvetica-Bold', fontSize=14, textColor=WHITE,  leading=20, spaceBefore=8)
    sLabel   = S('label',   fontName='Helvetica',      fontSize=9,  textColor=MUTED,  leading=13)
    sVal     = S('val',     fontName='Helvetica-Bold', fontSize=16, textColor=WHITE,  leading=20)
    sValGr   = S('valgr',   fontName='Helvetica-Bold', fontSize=16, textColor=GREEN,  leading=20)
    sValAm   = S('valam',   fontName='Helvetica-Bold', fontSize=16, textColor=AMBER,  leading=20)
    sValRo   = S('valro',   fontName='Helvetica-Bold', fontSize=16, textColor=ROSE,   leading=20)
    sValBl   = S('valbl',   fontName='Helvetica-Bold', fontSize=16, textColor=BLUE,   leading=20)
    sBody    = S('body',    fontName='Helvetica',      fontSize=10, textColor=SOFT,   leading=15)
    sTip     = S('tip',     fontName='Helvetica-Oblique', fontSize=9, textColor=MUTED, leading=14)

    # ── Table style helpers ─────────────────────────────────────────────────
    def card_table_style(hdr_color=VIOLET):
        return TableStyle([
            ('BACKGROUND',  (0,0), (-1,0),  hdr_color),
            ('BACKGROUND',  (0,1), (-1,-1), CARD),
            ('TEXTCOLOR',   (0,0), (-1,0),  colors.HexColor('#0a0a12')),
            ('TEXTCOLOR',   (0,1), (-1,-1), WHITE),
            ('FONTNAME',    (0,0), (-1,0),  'Helvetica-Bold'),
            ('FONTNAME',    (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',    (0,0), (-1,-1), 10),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [CARD, colors.HexColor('#0f0f1a')]),
            ('GRID',        (0,0), (-1,-1), 0.3, colors.HexColor('#1e2030')),
            ('TOPPADDING',  (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING',(0,0), (-1,-1), 10),
            ('ROWHEIGHT',   (0,0), (-1,-1), 22),
        ])

    # ── Build document ──────────────────────────────────────────────────────
    buf = io.BytesIO()
    W, H = A4
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BG)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        # footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(W/2, 12*mm, f"LifeOS Monthly Analysis — {display_name} — {request.user.username}")
        canvas.drawRightString(W - 18*mm, 12*mm, f"Page {doc.page}")
        canvas.restoreState()

    story = []

    # ── Cover ───────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20*mm),
        Paragraph("LifeOS", sTitle),
        Paragraph("Monthly Wellness Report", sSub),
        Spacer(1, 4*mm),
        HRFlowable(width='100%', thickness=0.5, color=VIOLET, spaceAfter=6*mm),
        Paragraph(display_name, S('month', fontName='Helvetica-Bold', fontSize=20, textColor=AMBER, leading=26, alignment=TA_CENTER)),
        Paragraph(f"Prepared for {request.user.username}", sSub),
        Spacer(1, 8*mm),
        Paragraph("Overall Wellness Score", S('scorelbl', fontName='Helvetica', fontSize=12, textColor=SOFT, leading=16, alignment=TA_CENTER)),
        Paragraph(f"{wellness_score}", sScore),
        Paragraph("out of 100", sTip),
        Spacer(1, 6*mm),
    ]

    # Score bar as table
    bar_filled = max(1, int(wellness_score * 1.54))  # scaled to ~154mm
    bar_table  = Table(
        [['', '']],
        colWidths=[bar_filled*mm, (154 - bar_filled)*mm],
        rowHeights=[8*mm],
    )
    bar_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), VIOLET),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#1e2030')),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story += [bar_table, Spacer(1, 12*mm)]

    # ── Section: Fitness ────────────────────────────────────────────────────
    f = data.get('fitness', {})
    if f:
        story.append(Paragraph("💪  Fitness", sSecHdr))
        story.append(HRFlowable(width='100%', thickness=0.3, color=GREEN, spaceAfter=4*mm))
        rows = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Workout Days',    str(f.get('workout_days', 0)),   'Consistency',     f"{f.get('consistency_pct', 0)}%"],
            ['Total Sets',      str(f.get('total_sets', 0)),     'Total Reps',      str(f.get('total_reps', 0))],
            ['Current Streak',  f"{f.get('current_streak', 0)} days", 'Rest Days', str(f.get('rest_days', 0))],
        ]
        t = Table(rows, colWidths=[50*mm, 26*mm, 50*mm, 26*mm])
        t.setStyle(card_table_style(GREEN))
        story.append(KeepTogether([t, Spacer(1, 6*mm)]))

    # ── Section: Nutrition ──────────────────────────────────────────────────
    m = data.get('meals', {})
    if m:
        story.append(Paragraph("🥗  Nutrition", sSecHdr))
        story.append(HRFlowable(width='100%', thickness=0.3, color=AMBER, spaceAfter=4*mm))
        rows = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Days Logged',      str(m.get('days_logged', 0)),      'Logging Rate',   f"{m.get('logging_pct', 0)}%"],
            ['Avg Daily Calories', str(m.get('avg_daily_cal', 0)),  'Goal Calories',  str(m.get('goal_calories', 0))],
            ['Avg Protein',      f"{m.get('avg_protein', 0)}g",     'Avg Carbs',      f"{m.get('avg_carbs', 0)}g"],
            ['Avg Fat',          f"{m.get('avg_fat', 0)}g",         'Total Entries',  str(m.get('total_entries', 0))],
        ]
        t = Table(rows, colWidths=[50*mm, 26*mm, 50*mm, 26*mm])
        t.setStyle(card_table_style(AMBER))
        story.append(KeepTogether([t, Spacer(1, 6*mm)]))

    # ── Section: Finance ───────────────────────────────────────────────────
    fi = data.get('finance', {})
    if fi:
        story.append(Paragraph("💰  Finance", sSecHdr))
        story.append(HRFlowable(width='100%', thickness=0.3, color=BLUE, spaceAfter=4*mm))
        rows = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Monthly Budget',  f"{fi.get('budget', 0):,.0f} TZS",       'Total Spent',    f"{fi.get('total_spent', 0):,.0f} TZS"],
            ['Balance',         f"{fi.get('balance', 0):,.0f} TZS",       'Budget Used',    f"{fi.get('spent_pct', 0)}%"],
            ['Top Category',    str(fi.get('top_category', '—')).title(),  'Transactions',   str(fi.get('transactions', 0))],
            ['Total Saved',     f"{fi.get('total_saved', 0):,.0f} TZS",    'Savings Goals',  str(fi.get('savings_goals', 0))],
        ]
        t = Table(rows, colWidths=[50*mm, 36*mm, 50*mm, 16*mm])
        t.setStyle(card_table_style(BLUE))
        story.append(KeepTogether([t, Spacer(1, 6*mm)]))

    # ── Section: Planner ──────────────────────────────────────────────────
    c = data.get('checklist', {})
    if c:
        story.append(Paragraph("📋  Planner & Routines", sSecHdr))
        story.append(HRFlowable(width='100%', thickness=0.3, color=VIOLET, spaceAfter=4*mm))
        rows = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Tasks Created',   str(c.get('tasks_total', 0)),      'Tasks Completed',    str(c.get('tasks_done', 0))],
            ['Completion Rate', f"{c.get('completion_pct', 0)}%",  'Routine Rate',       f"{c.get('routine_pct', 0)}%"],
            ['Reflections',     str(c.get('reflections', 0)),      'Avg Mood',           f"{c.get('avg_mood', 0)} / 5"],
        ]
        t = Table(rows, colWidths=[50*mm, 26*mm, 50*mm, 26*mm])
        t.setStyle(card_table_style(VIOLET))
        story.append(KeepTogether([t, Spacer(1, 6*mm)]))

    # ── Section: Hydration ────────────────────────────────────────────────
    h = data.get('hydration', {})
    if h and h.get('days_logged', 0) > 0:
        story.append(Paragraph("💧  Hydration", sSecHdr))
        story.append(HRFlowable(width='100%', thickness=0.3, color=BLUE, spaceAfter=4*mm))
        rows = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Days Logged',  str(h.get('days_logged', 0)),   'Goal Met Days',  str(h.get('days_goal_met', 0))],
            ['Logging Rate', f"{h.get('logging_pct', 0)}%",  'Goal Met Rate',  f"{h.get('goal_met_pct', 0)}%"],
        ]
        t = Table(rows, colWidths=[50*mm, 26*mm, 50*mm, 26*mm])
        t.setStyle(card_table_style(BLUE))
        story.append(KeepTogether([t, Spacer(1, 6*mm)]))

    # ── Section: Bible ────────────────────────────────────────────────────
    b = data.get('bible', {})
    if b and b.get('days_read', 0) > 0:
        story.append(Paragraph("✝️  Bible Reading", sSecHdr))
        story.append(HRFlowable(width='100%', thickness=0.3, color=AMBER, spaceAfter=4*mm))
        rows = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Days Read',    str(b.get('days_read', 0)),  'Entries',      str(b.get('entries', 0))],
            ['Reading Rate', f"{b.get('reading_pct', 0)}%", '', ''],
        ]
        t = Table(rows, colWidths=[50*mm, 26*mm, 50*mm, 26*mm])
        t.setStyle(card_table_style(AMBER))
        story.append(KeepTogether([t, Spacer(1, 6*mm)]))

    # ── Summary insights ──────────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("📊  Key Insights", sSecHdr))
    story.append(HRFlowable(width='100%', thickness=0.3, color=SOFT, spaceAfter=4*mm))

    insights = []
    if f:
        if f.get('consistency_pct', 0) >= 70:
            insights.append(f"✅ Excellent workout consistency at {f['consistency_pct']}% of days.")
        else:
            insights.append(f"💡 Workout consistency was {f.get('consistency_pct', 0)}% — aim for 5x/week.")
    if m:
        cal = m.get('avg_daily_cal', 0)
        goal_cal = m.get('goal_calories', 0)
        if goal_cal and abs(cal - goal_cal) <= 200:
            insights.append(f"✅ Average daily calories ({cal} kcal) were close to your goal ({goal_cal} kcal).")
        elif goal_cal:
            insights.append(f"💡 Average calories ({cal} kcal) vs goal ({goal_cal} kcal) — adjust your intake.")
    if fi:
        if fi.get('spent_pct', 0) <= 80:
            insights.append(f"✅ Good budget discipline — only {fi['spent_pct']}% of budget used.")
        else:
            insights.append(f"⚠️ Budget overspend warning: {fi.get('spent_pct', 0)}% of budget used.")
    if c:
        if c.get('avg_mood', 0) >= 4:
            insights.append(f"✅ Great mood average this month: {c['avg_mood']} / 5.")
        elif c.get('avg_mood', 0) > 0:
            insights.append(f"💡 Mood average was {c.get('avg_mood', 0)} / 5 — keep reflecting daily.")

    for ins in insights:
        story.append(Paragraph(ins, sBody))
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(f"Generated on {today.strftime('%B %d, %Y')} by LifeOS", sTip))

    # ── Build ─────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)

    filename = f"LifeOS_Report_{display_name.replace(' ', '_')}.pdf"
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response