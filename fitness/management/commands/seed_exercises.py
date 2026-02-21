"""
Management command: seed_exercises
Run with: python manage.py seed_exercises

Seeds all personalized workout exercises for:
  Age 26 | Weight 50kg | Female | Goal: Body Recomposition
"""

from django.core.management.base import BaseCommand
from fitness.models import Exercise


EXERCISES = [
    # ── ABS & CORE ──────────────────────────────────────────────
    {"name": "Plank Hold",           "category": "Core",     "default_reps": 30, "sets": 3, "description": "Hold 30s, rest 20s"},
    {"name": "Bicycle Crunches",     "category": "Core",     "default_reps": 20, "sets": 3, "description": "Each side counts as 1"},
    {"name": "Leg Raises",           "category": "Core",     "default_reps": 15, "sets": 3, "description": "Keep lower back flat"},
    {"name": "Russian Twists",       "category": "Core",     "default_reps": 20, "sets": 3, "description": "Use bodyweight or bottle"},
    {"name": "Dead Bug",             "category": "Core",     "default_reps": 12, "sets": 3, "description": "Slow & controlled"},
    {"name": "Mountain Climbers",    "category": "Core",     "default_reps": 30, "sets": 3, "description": "Fast pace, 30 total"},

    # ── LOWER BODY (GLUTES & HIPS) ───────────────────────────────
    {"name": "Bodyweight Squats",    "category": "Lower",    "default_reps": 20, "sets": 4, "description": "Full depth, chest up"},
    {"name": "Glute Bridges",        "category": "Lower",    "default_reps": 20, "sets": 4, "description": "Squeeze at the top"},
    {"name": "Reverse Lunges",       "category": "Lower",    "default_reps": 12, "sets": 3, "description": "Each leg"},
    {"name": "Hip Thrusts",          "category": "Lower",    "default_reps": 15, "sets": 4, "description": "Use sofa or chair edge"},
    {"name": "Sumo Squats",          "category": "Lower",    "default_reps": 15, "sets": 3, "description": "Wide stance, toes out 45°"},
    {"name": "Donkey Kicks",         "category": "Lower",    "default_reps": 15, "sets": 3, "description": "Each leg, squeeze glute"},
    {"name": "Side-Lying Clam",      "category": "Lower",    "default_reps": 20, "sets": 3, "description": "Each side"},
    {"name": "Wall Sit",             "category": "Lower",    "default_reps": 40, "sets": 3, "description": "Hold 40 seconds"},

    # ── UPPER BODY ───────────────────────────────────────────────
    {"name": "Knee Push-Ups",        "category": "Upper",    "default_reps": 12, "sets": 3, "description": "Progress to full push-ups"},
    {"name": "Tricep Dips",          "category": "Upper",    "default_reps": 12, "sets": 3, "description": "Use chair"},
    {"name": "Shoulder Taps",        "category": "Upper",    "default_reps": 20, "sets": 3, "description": "In plank position"},
    {"name": "Arm Circles",          "category": "Upper",    "default_reps": 20, "sets": 3, "description": "Each direction"},
    {"name": "Superman Hold",        "category": "Upper",    "default_reps": 12, "sets": 3, "description": "Squeeze back muscles"},

    # ── FULL BODY CARDIO ─────────────────────────────────────────
    {"name": "Jumping Jacks",        "category": "Cardio",   "default_reps": 30, "sets": 3, "description": "Warm up or circuit"},
    {"name": "Burpees",              "category": "Cardio",   "default_reps": 10, "sets": 3, "description": "Full range, jump at top"},
    {"name": "High Knees",           "category": "Cardio",   "default_reps": 30, "sets": 3, "description": "30 total, fast pace"},
    {"name": "Jump Squats",          "category": "Cardio",   "default_reps": 15, "sets": 3, "description": "Land softly"},
    {"name": "Skater Jumps",         "category": "Cardio",   "default_reps": 20, "sets": 3, "description": "Side to side"},

    # ── RECOVERY & MOBILITY ──────────────────────────────────────
    {"name": "Hip Flexor Stretch",   "category": "Recovery", "default_reps": 30, "sets": 2, "description": "Each side, 30s hold"},
    {"name": "Child's Pose",         "category": "Recovery", "default_reps": 45, "sets": 2, "description": "Hold 45 seconds"},
    {"name": "Cat-Cow Stretch",      "category": "Recovery", "default_reps": 10, "sets": 2, "description": "Breathe through each"},
    {"name": "Seated Forward Fold",  "category": "Recovery", "default_reps": 40, "sets": 2, "description": "Hold 40s, no bouncing"},
    {"name": "Pigeon Pose",          "category": "Recovery", "default_reps": 45, "sets": 2, "description": "Each side, 45s hold"},
]


class Command(BaseCommand):
    help = 'Seeds personalized workout exercises (female, 26yo, 50kg, body recomposition)'

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for data in EXERCISES:
            ex, created = Exercise.objects.get_or_create(
                name=data['name'],
                defaults={
                    'category':     data['category'],
                    'default_reps': data['default_reps'],
                    'sets':         data['sets'],
                    'description':  data.get('description', ''),
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS('  Created: ' + ex.name))
            else:
                skipped_count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            str(created_count) + ' exercises created, ' +
            str(skipped_count) + ' already existed.'
        ))
        self.stdout.write(self.style.SUCCESS('Done! Run the server and open /fitness/'))