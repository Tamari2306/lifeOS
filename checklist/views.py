from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import (
    ChecklistItem, DayReflection, MonthGoal, WeekTask, WorkDailyItem,
    RoutineTask, RoutineLog,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _week_range(year, week):
    monday = date.fromisocalendar(year, week, 1)
    sunday = date.fromisocalendar(year, week, 7)
    return monday, sunday


def _parse_date(date_str, fallback=None):
    fallback = fallback or date.today()
    try:
        from datetime import datetime
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return fallback


def _safe_int(val, default=0):
    try:
        return int(val or default)
    except (ValueError, TypeError):
        return default


def _ensure_routine_logs(user, target_date):
    """
    For every active RoutineTask belonging to this user,
    make sure a RoutineLog row exists for target_date.
    Returns the queryset of logs for that date.
    """
    active_tasks = RoutineTask.objects.filter(user=user, is_active=True)
    for task in active_tasks:
        RoutineLog.objects.get_or_create(
            routine_task=task,
            user=user,
            date=target_date,
        )
    # Return logs for active tasks only (exclude logs for deactivated tasks)
    return RoutineLog.objects.filter(
        user=user,
        date=target_date,
        routine_task__is_active=True,
    ).select_related('routine_task')


# ── MAIN DASHBOARD ────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today         = date.today()
    view_date_str = request.GET.get('date', str(today))
    view_date     = _parse_date(view_date_str, today)
    active_tab    = request.GET.get('tab', 'daily')

    # ── daily personal checklist ──
    items = ChecklistItem.objects.filter(user=request.user, date=view_date)
    total = items.count()
    done  = items.filter(completed=True).count()
    pct   = int(done / total * 100) if total else 0

    reflection = DayReflection.objects.filter(user=request.user, date=view_date).first()

    # ── routine tasks for this day ──
    routine_logs = _ensure_routine_logs(request.user, view_date)
    routine_total = routine_logs.count()
    routine_done  = routine_logs.filter(completed=True).count()
    routine_pct   = int(routine_done / routine_total * 100) if routine_total else 0

    # All routine tasks (for manage-routines section)
    all_routines = RoutineTask.objects.filter(user=request.user)

    # week strip
    week_data = []
    for i in range(6, -1, -1):
        d       = today - timedelta(days=i)
        d_items = ChecklistItem.objects.filter(user=request.user, date=d)
        d_total = d_items.count()
        d_done  = d_items.filter(completed=True).count()
        d_pct   = int(d_done / d_total * 100) if d_total else 0
        week_data.append({'date': d, 'label': d.strftime('%a'), 'pct': d_pct, 'done': d_done, 'total': d_total})

    # ── work daily ──
    work_items  = WorkDailyItem.objects.filter(user=request.user, date=view_date)
    work_total  = work_items.count()
    work_done   = work_items.filter(completed=True).count()
    work_pct    = int(work_done / work_total * 100) if work_total else 0

    # ── week planner ──
    iso       = today.isocalendar()
    cur_year  = iso[0]
    cur_week  = iso[1]
    week_num  = _safe_int(request.GET.get('week'), cur_week)
    week_year = _safe_int(request.GET.get('wyear'), cur_year)
    if week_num < 1:  week_num = 1
    if week_num > 53: week_num = 52
    w_monday, w_sunday = _week_range(week_year, week_num)
    week_tasks = WeekTask.objects.filter(user=request.user, year=week_year, week_number=week_num)

    tasks_by_day = {}
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for i, day_name in enumerate(days_of_week):
        day_date = w_monday + timedelta(days=i)
        tasks_by_day[i] = {
            'name':  day_name,
            'short': day_name[:3],
            'date':  day_date,
            'tasks': [t for t in week_tasks if t.planned_day == i],
        }

    prev_week  = week_num - 1 if week_num > 1 else 52
    next_week  = week_num + 1 if week_num < 52 else 1
    prev_wyear = week_year if week_num > 1 else week_year - 1
    next_wyear = week_year if week_num < 52 else week_year + 1

    # ── month planner ──
    cur_month  = _safe_int(request.GET.get('month'), today.month)
    cur_m_year = _safe_int(request.GET.get('myear'), today.year)
    month_goals         = MonthGoal.objects.filter(user=request.user, year=cur_m_year, month=cur_month)
    month_goals_active  = month_goals.filter(status='active')
    month_goals_done    = month_goals.filter(status='done')
    month_goals_dropped = month_goals.filter(status='dropped')

    from calendar import month_name
    month_display = f"{month_name[cur_month]} {cur_m_year}"
    prev_month = cur_month - 1 if cur_month > 1 else 12
    next_month = cur_month + 1 if cur_month < 12 else 1
    prev_myear = cur_m_year if cur_month > 1 else cur_m_year - 1
    next_myear = cur_m_year if cur_month < 12 else cur_m_year + 1

    for goal in month_goals:
        goal.linked_tasks = WeekTask.objects.filter(user=request.user, month_goal=goal)

    all_month_goals = MonthGoal.objects.filter(user=request.user, status='active').order_by('-year', '-month')

    return render(request, 'checklist/dashboard.html', {
        'today':      today,
        'view_date':  view_date,
        'yesterday':  today - timedelta(days=1),
        'tomorrow':   today + timedelta(days=1),
        'active_tab': active_tab,
        'is_today':   view_date == today,

        # daily personal
        'items':       items,
        'total':       total,
        'done':        done,
        'pct':         pct,
        'reflection':  reflection,
        'week_data':   week_data,

        # routines
        'routine_logs':  routine_logs,
        'routine_total': routine_total,
        'routine_done':  routine_done,
        'routine_pct':   routine_pct,
        'all_routines':  all_routines,

        # work daily
        'work_items':  work_items,
        'work_total':  work_total,
        'work_done':   work_done,
        'work_pct':    work_pct,

        # weekly
        'week_num':        week_num,
        'week_year':       week_year,
        'w_monday':        w_monday,
        'w_sunday':        w_sunday,
        'week_tasks':      week_tasks,
        'tasks_by_day':    tasks_by_day,
        'days_of_week':    days_of_week,
        'prev_week':       prev_week,
        'next_week':       next_week,
        'prev_wyear':      prev_wyear,
        'next_wyear':      next_wyear,
        'all_month_goals': all_month_goals,

        # monthly
        'cur_month':           cur_month,
        'cur_m_year':          cur_m_year,
        'month_display':       month_display,
        'month_goals_active':  month_goals_active,
        'month_goals_done':    month_goals_done,
        'month_goals_dropped': month_goals_dropped,
        'prev_month':          prev_month,
        'next_month':          next_month,
        'prev_myear':          prev_myear,
        'next_myear':          next_myear,
    })


# ── PERSONAL CHECKLIST ────────────────────────────────────────────────────────

@login_required
@require_POST
def add_item(request):
    text      = request.POST.get('text', '').strip()
    category  = request.POST.get('category', 'personal')
    priority  = request.POST.get('priority', 'medium')
    item_date = request.POST.get('date', str(date.today()))
    if text:
        ChecklistItem.objects.create(
            user=request.user, text=text,
            category=category, priority=priority, date=item_date,
        )
    return redirect(f'/checklist/?date={item_date}&tab=daily')


@login_required
@require_POST
def toggle_item(request, item_id):
    item = get_object_or_404(ChecklistItem, id=item_id, user=request.user)
    item.completed    = not item.completed
    item.completed_at = timezone.now() if item.completed else None
    item.save()
    return redirect(f'/checklist/?date={item.date}&tab=daily')


@login_required
@require_POST
def delete_item(request, item_id):
    item      = get_object_or_404(ChecklistItem, id=item_id, user=request.user)
    item_date = item.date
    item.delete()
    return redirect(f'/checklist/?date={item_date}&tab=daily')


@login_required
@require_POST
def save_reflection(request):
    ref_date = request.POST.get('date', str(date.today()))
    DayReflection.objects.update_or_create(
        user=request.user, date=ref_date,
        defaults={
            'what_went_well':  request.POST.get('what_went_well', ''),
            'what_to_improve': request.POST.get('what_to_improve', ''),
            'grateful_for':    request.POST.get('grateful_for', ''),
            'mood_rating':     _safe_int(request.POST.get('mood_rating'), 3),
        }
    )
    return redirect(f'/checklist/?date={ref_date}&tab=daily')


# ── ROUTINE TASKS ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_routine_task(request):
    """Create a new predefined routine task."""
    title       = request.POST.get('title', '').strip()
    category    = request.POST.get('category', 'personal')
    time_of_day = request.POST.get('time_of_day', 'anytime')
    if title:
        # Set order to end of list
        last_order = RoutineTask.objects.filter(user=request.user).count()
        RoutineTask.objects.create(
            user=request.user,
            title=title,
            category=category,
            time_of_day=time_of_day,
            order=last_order,
        )
    return_date = request.POST.get('date', str(date.today()))
    return redirect(f'/checklist/?date={return_date}&tab=daily')


@login_required
@require_POST
def delete_routine_task(request, task_id):
    """Permanently remove a routine task (and all its logs)."""
    task = get_object_or_404(RoutineTask, id=task_id, user=request.user)
    task.delete()
    return_date = request.POST.get('date', str(date.today()))
    return redirect(f'/checklist/?date={return_date}&tab=daily')


@login_required
@require_POST
def toggle_routine_task(request, task_id):
    """Deactivate/reactivate a routine task without deleting it."""
    task = get_object_or_404(RoutineTask, id=task_id, user=request.user)
    task.is_active = not task.is_active
    task.save()
    return_date = request.POST.get('date', str(date.today()))
    return redirect(f'/checklist/?date={return_date}&tab=daily')


@login_required
@require_POST
def toggle_routine_log(request, log_id):
    """Mark a routine as done/not-done for a specific day."""
    log = get_object_or_404(RoutineLog, id=log_id, user=request.user)
    log.completed    = not log.completed
    log.completed_at = timezone.now() if log.completed else None
    log.save()
    return redirect(f'/checklist/?date={log.date}&tab=daily')


# ── WORK DAILY ────────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_work_item(request):
    title        = request.POST.get('title', '').strip()
    notes        = request.POST.get('notes', '').strip()
    priority     = request.POST.get('priority', 'medium')
    item_date    = request.POST.get('date', str(date.today()))
    week_task_id = request.POST.get('week_task_id', '')

    week_task = None
    if week_task_id:
        try:
            week_task = WeekTask.objects.get(id=int(week_task_id), user=request.user)
        except (WeekTask.DoesNotExist, ValueError):
            pass

    if title:
        WorkDailyItem.objects.create(
            user=request.user, date=item_date, title=title,
            notes=notes, priority=priority, week_task=week_task,
        )
    return redirect(f'/checklist/?date={item_date}&tab=work')


@login_required
@require_POST
def toggle_work_item(request, item_id):
    item = get_object_or_404(WorkDailyItem, id=item_id, user=request.user)
    item.completed    = not item.completed
    item.completed_at = timezone.now() if item.completed else None
    item.save()
    return redirect(f'/checklist/?date={item.date}&tab=work')


@login_required
@require_POST
def delete_work_item(request, item_id):
    item      = get_object_or_404(WorkDailyItem, id=item_id, user=request.user)
    item_date = item.date
    item.delete()
    return redirect(f'/checklist/?date={item_date}&tab=work')


# ── WEEK TASKS ────────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_week_task(request):
    title       = request.POST.get('title', '').strip()
    notes       = request.POST.get('notes', '').strip()
    priority    = request.POST.get('priority', 'medium')
    week_num    = _safe_int(request.POST.get('week_number'), date.today().isocalendar()[1])
    week_year   = _safe_int(request.POST.get('week_year'), date.today().isocalendar()[0])
    planned_day = request.POST.get('planned_day', '')
    goal_id     = request.POST.get('month_goal_id', '')

    planned_day = int(planned_day) if planned_day != '' else None

    month_goal = None
    if goal_id:
        try:
            month_goal = MonthGoal.objects.get(id=int(goal_id), user=request.user)
        except (MonthGoal.DoesNotExist, ValueError):
            pass

    if title:
        WeekTask.objects.create(
            user=request.user, year=week_year, week_number=week_num,
            title=title, notes=notes, priority=priority,
            planned_day=planned_day, month_goal=month_goal,
        )
    return redirect(f'/checklist/?tab=week&week={week_num}&wyear={week_year}')


@login_required
@require_POST
def update_week_task_status(request, task_id):
    task   = get_object_or_404(WeekTask, id=task_id, user=request.user)
    status = request.POST.get('status', 'todo')
    task.status = status
    task.save()
    return redirect(f'/checklist/?tab=week&week={task.week_number}&wyear={task.year}')


@login_required
@require_POST
def delete_week_task(request, task_id):
    task = get_object_or_404(WeekTask, id=task_id, user=request.user)
    week, wyear = task.week_number, task.year
    task.delete()
    return redirect(f'/checklist/?tab=week&week={week}&wyear={wyear}')


# ── MONTH GOALS ───────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_month_goal(request):
    title    = request.POST.get('title', '').strip()
    desc     = request.POST.get('description', '').strip()
    priority = request.POST.get('priority', 'medium')
    month    = _safe_int(request.POST.get('month'), date.today().month)
    year     = _safe_int(request.POST.get('year'), date.today().year)

    if title:
        MonthGoal.objects.create(
            user=request.user, title=title, description=desc,
            priority=priority, month=month, year=year,
        )
    return redirect(f'/checklist/?tab=month&month={month}&myear={year}')


@login_required
@require_POST
def update_month_goal_status(request, goal_id):
    goal   = get_object_or_404(MonthGoal, id=goal_id, user=request.user)
    status = request.POST.get('status', 'active')
    goal.status = status
    goal.save()
    return redirect(f'/checklist/?tab=month&month={goal.month}&myear={goal.year}')


@login_required
@require_POST
def delete_month_goal(request, goal_id):
    goal = get_object_or_404(MonthGoal, id=goal_id, user=request.user)
    month, year = goal.month, goal.year
    goal.delete()
    return redirect(f'/checklist/?tab=month&month={month}&myear={year}')