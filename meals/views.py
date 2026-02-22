import json
from datetime import date, timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import MealEntry, NutritionGoal, RecipeIdea

MEAL_ORDER = ['breakfast', 'lunch', 'snack', 'dinner']

MEAL_ICONS = {
    'breakfast': '🍳',
    'lunch':     '🥗',
    'snack':     '🍎',
    'dinner':    '🍛',
}

# ── Nutrition database (per common serving) ──────────────────────────────────
NUTRITION_DB = [
    # STAPLES
    (["rice", "white rice", "brown rice", "fried rice"],
     {"bowl": (320, 6, 70, 1), "cup": (200, 4, 44, 0), "plate": (400, 8, 88, 2), "serving": (200, 4, 44, 0)}),
    (["bread", "white bread", "toast"],
     {"slice": (80, 3, 15, 1), "loaf": (1200, 40, 220, 15), "serving": (160, 6, 30, 2)}),
    (["pasta", "spaghetti", "noodles", "macaroni"],
     {"bowl": (350, 12, 68, 3), "plate": (420, 14, 82, 4), "cup": (220, 8, 43, 2), "serving": (350, 12, 68, 3)}),
    (["ugali", "posho", "fufu", "banku", "eba", "tuwo"],
     {"bowl": (360, 7, 80, 1), "plate": (450, 9, 100, 1), "serving": (360, 7, 80, 1)}),
    (["yam", "boiled yam"],
     {"piece": (180, 2, 42, 0), "bowl": (280, 4, 65, 0), "plate": (350, 5, 80, 0), "serving": (180, 2, 42, 0)}),
    (["sweet potato", "sweet potatoes"],
     {"piece": (130, 2, 30, 0), "medium": (130, 2, 30, 0), "large": (200, 3, 46, 0), "serving": (130, 2, 30, 0)}),
    (["potato", "potatoes", "boiled potato", "mashed potato"],
     {"medium": (160, 4, 37, 0), "large": (250, 6, 58, 0), "cup": (180, 4, 41, 0), "serving": (160, 4, 37, 0)}),

    # PROTEINS
    (["chicken", "grilled chicken", "roast chicken", "chicken breast"],
     {"piece": (165, 31, 0, 4), "breast": (165, 31, 0, 4), "thigh": (200, 26, 0, 10), "leg": (220, 28, 0, 12), "serving": (165, 31, 0, 4)}),
    (["chicken leg", "chicken leg piece", "drumstick"],
     {"piece": (180, 24, 0, 9), "1": (180, 24, 0, 9), "2": (360, 48, 0, 18), "serving": (180, 24, 0, 9)}),
    (["chicken wing", "chicken wings"],
     {"piece": (100, 9, 0, 7), "serving": (200, 18, 0, 14)}),
    (["beef", "steak", "grilled beef", "beef stew"],
     {"piece": (250, 26, 0, 15), "serving": (250, 26, 0, 15), "bowl": (380, 34, 8, 20)}),
    (["fish", "grilled fish", "fried fish", "tilapia", "salmon", "tuna", "mackerel"],
     {"piece": (200, 28, 0, 9), "fillet": (200, 28, 0, 9), "serving": (200, 28, 0, 9)}),
    (["egg", "eggs", "boiled egg", "fried egg", "scrambled egg"],
     {"1": (70, 6, 0, 5), "2": (140, 12, 0, 10), "3": (210, 18, 0, 15), "egg": (70, 6, 0, 5), "serving": (140, 12, 0, 10)}),
    (["beans", "black beans", "kidney beans", "lentils", "chickpeas"],
     {"bowl": (230, 15, 40, 1), "cup": (230, 15, 40, 1), "plate": (300, 20, 52, 2), "serving": (230, 15, 40, 1)}),
    (["groundnut", "groundnuts", "peanuts", "peanut"],
     {"handful": (170, 7, 5, 14), "cup": (580, 24, 20, 50), "serving": (170, 7, 5, 14)}),

    # VEGETABLES
    (["vegetables", "veggies", "salad", "mixed vegetables", "stir fry veg"],
     {"bowl": (80, 4, 15, 1), "plate": (120, 6, 22, 2), "cup": (80, 4, 15, 1), "serving": (80, 4, 15, 1)}),
    (["spinach", "kale", "sukuma", "collard greens", "ugwu", "bitter leaf"],
     {"bowl": (50, 5, 7, 1), "cup": (50, 5, 7, 1), "serving": (50, 5, 7, 1)}),
    (["avocado"],
     {"half": (160, 2, 9, 15), "whole": (320, 4, 18, 30), "slice": (50, 1, 3, 5), "serving": (160, 2, 9, 15)}),
    (["tomato", "tomatoes"],
     {"medium": (25, 1, 5, 0), "large": (35, 2, 7, 0), "serving": (25, 1, 5, 0)}),

    # FRUITS
    (["banana", "bananas"],
     {"1": (90, 1, 23, 0), "medium": (90, 1, 23, 0), "large": (120, 1, 31, 0), "serving": (90, 1, 23, 0)}),
    (["plantain", "plantains", "fried plantain", "dodo", "boli"],
     {"1": (120, 1, 28, 2), "2": (240, 2, 56, 4), "3": (360, 3, 84, 6), "piece": (120, 1, 28, 2), "serving": (240, 2, 56, 4)}),
    (["apple"],
     {"1": (95, 0, 25, 0), "medium": (95, 0, 25, 0), "serving": (95, 0, 25, 0)}),
    (["orange"],
     {"1": (65, 1, 16, 0), "medium": (65, 1, 16, 0), "serving": (65, 1, 16, 0)}),
    (["mango"],
     {"1": (200, 3, 50, 1), "half": (100, 1, 25, 0), "serving": (100, 1, 25, 0)}),
    (["watermelon"],
     {"slice": (85, 2, 22, 0), "cup": (45, 1, 11, 0), "serving": (85, 2, 22, 0)}),

    # DAIRY & DRINKS
    (["milk"],
     {"cup": (150, 8, 12, 8), "glass": (150, 8, 12, 8), "serving": (150, 8, 12, 8)}),
    (["yogurt", "greek yogurt"],
     {"cup": (130, 15, 9, 0), "bowl": (130, 15, 9, 0), "serving": (130, 15, 9, 0)}),
    (["cheese"],
     {"slice": (80, 5, 0, 7), "piece": (80, 5, 0, 7), "serving": (80, 5, 0, 7)}),

    # SNACKS / FAST FOOD
    (["bread roll", "burger", "bun"],
     {"1": (260, 10, 40, 7), "serving": (260, 10, 40, 7)}),
    (["chips", "fries", "french fries"],
     {"serving": (365, 4, 48, 17), "bowl": (365, 4, 48, 17), "small": (230, 3, 29, 11)}),
    (["cake", "doughnut", "donut"],
     {"slice": (350, 4, 50, 15), "piece": (280, 4, 35, 14), "serving": (280, 4, 35, 14)}),
    (["biscuit", "biscuits", "cookies"],
     {"serving": (150, 2, 22, 6), "piece": (50, 1, 7, 2)}),
    (["nuts", "mixed nuts", "cashew", "almond", "walnuts"],
     {"handful": (180, 5, 6, 16), "serving": (180, 5, 6, 16), "cup": (720, 20, 24, 64)}),

    # SOUPS & STEWS
    (["soup", "stew", "vegetable soup", "tomato soup", "pepper soup"],
     {"bowl": (150, 8, 14, 6), "cup": (100, 5, 9, 4), "plate": (200, 10, 18, 8), "serving": (150, 8, 14, 6)}),
    (["egusi soup", "egusi"],
     {"bowl": (350, 18, 12, 24), "serving": (350, 18, 12, 24)}),
    (["jollof rice", "jollof"],
     {"plate": (480, 10, 86, 12), "bowl": (380, 8, 68, 10), "serving": (380, 8, 68, 10)}),
    (["fried rice"],
     {"plate": (500, 12, 80, 16), "bowl": (400, 10, 64, 13), "serving": (400, 10, 64, 13)}),
    (["oats", "oatmeal", "porridge"],
     {"bowl": (300, 10, 54, 6), "cup": (160, 6, 28, 3), "serving": (300, 10, 54, 6)}),
    (["smoothie"],
     {"glass": (200, 5, 38, 3), "cup": (200, 5, 38, 3), "serving": (200, 5, 38, 3)}),
]

NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "half": 0.5, "a": 1, "an": 1}


def _parse_quantity(text):
    words = text.lower().split()
    qty = 1
    for w in words:
        if w in NUM_WORDS:
            qty = NUM_WORDS[w]
            break
        try:
            qty = float(w)
            break
        except ValueError:
            pass
    return qty


def _get_serving_type(text):
    servings = ["bowl", "plate", "cup", "glass", "slice", "piece", "fillet",
                "breast", "thigh", "leg", "half", "whole", "handful",
                "medium", "large", "small", "serving"]
    text_lower = text.lower()
    for s in servings:
        if s in text_lower:
            return s
    return "serving"


def estimate_nutrition(meal_description):
    text = meal_description.lower().strip()
    qty = _parse_quantity(text)
    serving = _get_serving_type(text)

    best_match = None
    best_score = 0

    for keywords, nutrition in NUTRITION_DB:
        for kw in keywords:
            if kw in text:
                score = len(kw)
                if score > best_score:
                    best_score = score
                    nums = nutrition.get(serving) or nutrition.get("serving") or list(nutrition.values())[0]
                    best_match = {
                        "kcal":    round(nums[0] * qty),
                        "protein": round(nums[1] * qty),
                        "carbs":   round(nums[2] * qty),
                        "fat":     round(nums[3] * qty),
                    }

    if best_match:
        return {**best_match, "confidence": "estimated", "found": True}
    else:
        return {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0, "confidence": "unknown", "found": False}


def _safe_int(value, default=0):
    """Safely convert a value to int, returning default on failure."""
    try:
        return int(value or default)
    except (ValueError, TypeError):
        return default


def _parse_date(date_str):
    """Safely parse a date string, returning today on failure."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return date.today()


def _totals_for_day(user, day):
    entries = MealEntry.objects.filter(user=user, date=day)
    return {
        'calories': sum(e.calories for e in entries),
        'protein':  sum(e.protein  for e in entries),
        'carbs':    sum(e.carbs    for e in entries),
        'fat':      sum(e.fat      for e in entries),
        'entries':  entries,
    }


@login_required
def dashboard(request):
    today = date.today()
    view_date_str = request.GET.get('date', str(today))
    view_date = _parse_date(view_date_str)

    goal = NutritionGoal.objects.filter(user=request.user).first()
    if not goal:
        goal = NutritionGoal(calories=1800, protein=120, carbs=180, fat=60)

    day_data = _totals_for_day(request.user, view_date)
    entries  = day_data['entries']

    meals_grouped = {}
    for mt in MEAL_ORDER:
        meals_grouped[mt] = {
            'entries':  [e for e in entries if e.meal_type == mt],
            'icon':     MEAL_ICONS[mt],
            'label':    mt.title(),
            'calories': sum(e.calories for e in entries if e.meal_type == mt),
        }
    meals_list = [meals_grouped[mt] for mt in MEAL_ORDER]

    cal_pct     = min(100, int(day_data['calories'] / goal.calories * 100)) if goal.calories else 0
    protein_pct = min(100, int(day_data['protein']  / goal.protein  * 100)) if goal.protein  else 0
    carbs_pct   = min(100, int(day_data['carbs']    / goal.carbs    * 100)) if goal.carbs    else 0
    fat_pct     = min(100, int(day_data['fat']      / goal.fat      * 100)) if goal.fat      else 0

    week_data = []
    for i in range(6, -1, -1):
        d   = today - timedelta(days=i)
        t   = _totals_for_day(request.user, d)
        pct = min(100, int(t['calories'] / goal.calories * 100)) if goal.calories else 0
        week_data.append({'date': d, 'label': d.strftime('%a'), 'calories': t['calories'], 'pct': pct})

    recipes   = RecipeIdea.objects.filter(user=request.user)
    yesterday = today - timedelta(days=1)
    tomorrow  = today + timedelta(days=1)

    return render(request, 'meals/dashboard.html', {
        'today':       today,
        'view_date':   view_date,
        'yesterday':   yesterday,
        'tomorrow':    tomorrow,
        'goal':        goal,
        'day_data':    day_data,
        'meals_list':  meals_list,
        'cal_pct':     cal_pct,
        'protein_pct': protein_pct,
        'carbs_pct':   carbs_pct,
        'fat_pct':     fat_pct,
        'week_data':   week_data,
        'recipes':     recipes,
        'is_today':    view_date == today,
        'MEAL_ORDER':  MEAL_ORDER,
    })


@login_required
def estimate_meal_api(request):
    """AJAX endpoint — returns estimated nutrition for a meal description."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        body = json.loads(request.body)
        description = body.get('description', '').strip()
    except (json.JSONDecodeError, AttributeError):
        description = request.POST.get('description', '').strip()

    if not description:
        return JsonResponse({'error': 'No description'}, status=400)

    result = estimate_nutrition(description)
    return JsonResponse(result)


@login_required
@require_POST
def log_meal(request):
    meal_date_str = request.POST.get('date', str(date.today()))
    # FIX: validate and convert date string to a real date object
    meal_date = _parse_date(meal_date_str)

    meal_type = request.POST.get('meal_type', 'lunch')
    # FIX: validate meal_type against known values
    if meal_type not in MEAL_ORDER:
        meal_type = 'lunch'

    name = request.POST.get('name', '').strip()

    # FIX: use _safe_int for all numeric fields
    calories = _safe_int(request.POST.get('calories'))
    protein  = _safe_int(request.POST.get('protein'))
    carbs    = _safe_int(request.POST.get('carbs'))
    fat      = _safe_int(request.POST.get('fat'))

    # If no macros provided, try to estimate from name
    if name and calories == 0:
        est = estimate_nutrition(name)
        calories = est['kcal']
        protein  = est['protein']
        carbs    = est['carbs']
        fat      = est['fat']

    notes = request.POST.get('notes', '').strip()

    if name:
        MealEntry.objects.create(
            user=request.user,
            date=meal_date,
            meal_type=meal_type,
            name=name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            notes=notes,
        )
    return redirect(f'/meals/?date={meal_date}')


@login_required
@require_POST
def delete_meal(request, entry_id):
    entry      = get_object_or_404(MealEntry, id=entry_id, user=request.user)
    entry_date = entry.date
    entry.delete()
    return redirect(f'/meals/?date={entry_date}')


@login_required
@require_POST
def set_goals(request):
    try:
        NutritionGoal.objects.update_or_create(
            user=request.user,
            defaults={
                'calories': _safe_int(request.POST.get('calories'), 1800),
                'protein':  _safe_int(request.POST.get('protein'),  120),
                'carbs':    _safe_int(request.POST.get('carbs'),    180),
                'fat':      _safe_int(request.POST.get('fat'),      60),
            }
        )
    except Exception:
        pass
    return redirect('/meals/')


@login_required
@require_POST
def save_recipe(request):
    name     = request.POST.get('name', '').strip()
    category = request.POST.get('category', 'lunch')

    if name:
        # FIX: safely cast all numeric fields before use
        calories  = _safe_int(request.POST.get('calories'))
        protein   = _safe_int(request.POST.get('protein'))
        prep_time = _safe_int(request.POST.get('prep_time'))

        # Auto-estimate if calories not provided
        if calories == 0:
            est      = estimate_nutrition(name)
            calories = est['kcal']
            protein  = est['protein']

        RecipeIdea.objects.create(
            user=request.user,
            name=name,
            category=category,
            ingredients=request.POST.get('ingredients', ''),
            instructions=request.POST.get('instructions', ''),
            calories=calories,
            protein=protein,
            prep_time=prep_time,
        )
    return redirect('/meals/')


@login_required
@require_POST
def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(RecipeIdea, id=recipe_id, user=request.user)
    recipe.delete()
    return redirect('/meals/')