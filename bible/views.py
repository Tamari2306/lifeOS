from datetime import date, timedelta
from calendar import monthrange
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import ReadingPlan, ReadingLog, PrayerRequest, Memorization, DAILY_VERSES


def _get_verse(today):
    idx = (today.timetuple().tm_yday - 1) % len(DAILY_VERSES)
    return DAILY_VERSES[idx]


def _reading_streak(user):
    streak = 0
    day = date.today()
    while True:
        if ReadingLog.objects.filter(user=user, date=day).exists():
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak


def _chapters_this_month(user):
    today = date.today()
    return ReadingLog.objects.filter(
        user=user, date__year=today.year, date__month=today.month
    ).count()


def _days_remaining_in_month(month, year):
    """Days from today (inclusive) to end of given month."""
    today = date.today()
    last_day = monthrange(year, month)[1]
    end = date(year, month, last_day)
    delta = (end - today).days + 1
    return max(1, delta)


@login_required
def dashboard(request):
    today  = date.today()
    verse  = _get_verse(today)
    streak = _reading_streak(request.user)
    chapters_this_month = _chapters_this_month(request.user)

    # Active reading plan for this month
    plan = ReadingPlan.objects.filter(
        user=request.user, month=today.month, year=today.year
    ).first()

    plan_chapters_read = 0
    plan_progress_pct  = 0
    days_remaining     = 0
    chapters_per_day   = 0

    if plan:
        plan_chapters_read = ReadingLog.objects.filter(
            user=request.user, plan=plan
        ).count()
        plan_progress_pct = min(100, int(plan_chapters_read / plan.total_chapters * 100)) if plan.total_chapters else 0
        days_remaining    = _days_remaining_in_month(plan.month, plan.year)
        chapters_left     = max(0, plan.total_chapters - plan_chapters_read)
        chapters_per_day  = round(chapters_left / days_remaining, 1) if days_remaining else chapters_left

    recent_logs  = ReadingLog.objects.filter(user=request.user).order_by('-date', '-chapter')[:15]
    today_logs   = ReadingLog.objects.filter(user=request.user, date=today).order_by('chapter')

    active_prayers   = PrayerRequest.objects.filter(user=request.user, status='active')
    answered_prayers = PrayerRequest.objects.filter(user=request.user, status='answered')[:5]
    memorizations    = Memorization.objects.filter(user=request.user)

    return render(request, 'bible/dashboard.html', {
        'today':               today,
        'verse':               verse,
        'streak':              streak,
        'chapters_this_month': chapters_this_month,
        'plan':                plan,
        'plan_chapters_read':  plan_chapters_read,
        'plan_progress_pct':   plan_progress_pct,
        'days_remaining':      days_remaining,
        'chapters_per_day':    chapters_per_day,
        'recent_logs':         recent_logs,
        'today_logs':          today_logs,
        'active_prayers':      active_prayers,
        'answered_prayers':    answered_prayers,
        'memorizations':       memorizations,
    })


@login_required
@require_POST
def log_reading(request):
    """Log one or more chapters at once (start_chapter to start_chapter + count - 1)."""
    book         = request.POST.get('book', '').strip()
    start_ch_raw = request.POST.get('start_chapter', '1')
    count_raw    = request.POST.get('chapter_count', '1')   # "I read 3 chapters today"
    note         = request.POST.get('note', '').strip()
    plan_id      = request.POST.get('plan_id', '')
    today        = date.today()

    try:
        start_chapter = int(start_ch_raw)
    except ValueError:
        start_chapter = 1

    try:
        chapter_count = max(1, int(count_raw))
    except ValueError:
        chapter_count = 1

    plan = None
    if plan_id:
        try:
            plan = ReadingPlan.objects.get(id=int(plan_id), user=request.user)
        except ReadingPlan.DoesNotExist:
            pass

    if book:
        for i in range(chapter_count):
            ch = start_chapter + i
            ReadingLog.objects.get_or_create(
                user=request.user, book=book, chapter=ch, date=today,
                defaults={'note': note if i == 0 else '', 'plan': plan}
            )

    return redirect('/bible/')


@login_required
@require_POST
def delete_log(request, log_id):
    log = get_object_or_404(ReadingLog, id=log_id, user=request.user)
    log.delete()
    return redirect('/bible/')


@login_required
@require_POST
def edit_log(request, log_id):
    log  = get_object_or_404(ReadingLog, id=log_id, user=request.user)
    note = request.POST.get('note', '').strip()
    ch   = request.POST.get('chapter', '')
    if ch:
        try:
            log.chapter = int(ch)
        except ValueError:
            pass
    log.note = note
    log.save()
    return redirect('/bible/')


@login_required
@require_POST
def set_plan(request):
    today     = date.today()
    book_name = request.POST.get('book_name', '').strip()
    total_ch  = request.POST.get('total_chapters', '1')
    month     = int(request.POST.get('month', today.month))
    year      = int(request.POST.get('year',  today.year))

    try:
        total_ch = int(total_ch)
    except ValueError:
        total_ch = 1

    if book_name:
        ReadingPlan.objects.update_or_create(
            user=request.user, month=month, year=year,
            defaults={'book_name': book_name, 'total_chapters': total_ch}
        )
    return redirect('/bible/')


@login_required
@require_POST
def delete_plan(request, plan_id):
    plan = get_object_or_404(ReadingPlan, id=plan_id, user=request.user)
    plan.delete()
    return redirect('/bible/')


@login_required
@require_POST
def add_prayer(request):
    text = request.POST.get('text', '').strip()
    if text:
        PrayerRequest.objects.create(user=request.user, text=text)
    return redirect('/bible/')


@login_required
@require_POST
def answer_prayer(request, prayer_id):
    prayer = get_object_or_404(PrayerRequest, id=prayer_id, user=request.user)
    prayer.status      = 'answered'
    prayer.answered_at = date.today()
    prayer.save()
    return redirect('/bible/')


@login_required
@require_POST
def delete_prayer(request, prayer_id):
    prayer = get_object_or_404(PrayerRequest, id=prayer_id, user=request.user)
    prayer.delete()
    return redirect('/bible/')


@login_required
@require_POST
def add_memorization(request):
    reference = request.POST.get('reference', '').strip()
    text      = request.POST.get('text', '').strip()
    if reference and text:
        Memorization.objects.create(user=request.user, reference=reference, text=text)
    return redirect('/bible/')


@login_required
@require_POST
def toggle_mastered(request, mem_id):
    mem = get_object_or_404(Memorization, id=mem_id, user=request.user)
    mem.mastered = not mem.mastered
    mem.save()
    return redirect('/bible/')