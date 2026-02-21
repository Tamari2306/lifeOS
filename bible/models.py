from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ReadingPlan(models.Model):
    """A monthly book reading plan."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_plans')
    book_name  = models.CharField(max_length=100)   # e.g. "Psalms"
    month      = models.IntegerField()               # 1-12
    year       = models.IntegerField()
    total_chapters = models.IntegerField(default=1)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"{self.user.username} — {self.book_name} ({self.month}/{self.year})"

    @property
    def chapters_per_day(self):
        from calendar import monthrange
        days = monthrange(self.year, self.month)[1]
        return max(1, round(self.total_chapters / days, 1))


class ReadingLog(models.Model):
    """Records a chapter read on a specific day."""
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_logs')
    plan    = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    book    = models.CharField(max_length=100)
    chapter = models.IntegerField()
    date    = models.DateField()
    note    = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-date', '-chapter']
        unique_together = ('user', 'book', 'chapter', 'date')

    def __str__(self):
        return f"{self.user.username} — {self.book} ch.{self.chapter} ({self.date})"


class PrayerRequest(models.Model):
    STATUS = [('active', 'Active'), ('answered', 'Answered')]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prayer_requests')
    text       = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS, default='active')
    created_at = models.DateField(auto_now_add=True)
    answered_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class Memorization(models.Model):
    """Bible verses the user is memorizing."""
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memorizations')
    reference = models.CharField(max_length=100)  # e.g. "John 3:16"
    text      = models.TextField()
    mastered  = models.BooleanField(default=False)
    added_at  = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']


DAILY_VERSES = [
    {"ref": "Philippians 4:13",    "text": "I can do all things through Christ who strengthens me."},
    {"ref": "Jeremiah 29:11",      "text": "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future."},
    {"ref": "Proverbs 3:5-6",      "text": "Trust in the Lord with all your heart and lean not on your own understanding; in all your ways submit to him, and he will make your paths straight."},
    {"ref": "Isaiah 40:31",        "text": "But those who hope in the Lord will renew their strength. They will soar on wings like eagles; they will run and not grow weary, they will walk and not be faint."},
    {"ref": "Romans 8:28",         "text": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose."},
    {"ref": "Psalm 23:1",          "text": "The Lord is my shepherd; I shall not want."},
    {"ref": "Matthew 6:33",        "text": "But seek first his kingdom and his righteousness, and all these things will be given to you as well."},
    {"ref": "John 3:16",           "text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."},
    {"ref": "Psalm 46:10",         "text": "Be still and know that I am God; I will be exalted among the nations, I will be exalted in the earth."},
    {"ref": "2 Timothy 1:7",       "text": "For God has not given us a spirit of fear, but of power and of love and of a sound mind."},
    {"ref": "Proverbs 31:25",      "text": "She is clothed with strength and dignity; she can laugh at the days to come."},
    {"ref": "Romans 12:2",         "text": "Do not conform to the pattern of this world, but be transformed by the renewing of your mind."},
    {"ref": "Psalm 139:14",        "text": "I praise you because I am fearfully and wonderfully made; your works are wonderful, I know that full well."},
    {"ref": "Lamentations 3:22-23","text": "Because of the Lord's great love we are not consumed, for his compassions never fail. They are new every morning; great is your faithfulness."},
    {"ref": "Joshua 1:9",          "text": "Have I not commanded you? Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go."},
    {"ref": "Psalm 37:4",          "text": "Delight yourself in the Lord and he will give you the desires of your heart."},
    {"ref": "Matthew 11:28",       "text": "Come to me, all you who are weary and burdened, and I will give you rest."},
    {"ref": "1 Corinthians 13:4",  "text": "Love is patient, love is kind. It does not envy, it does not boast, it is not proud."},
    {"ref": "Psalm 121:1-2",       "text": "I lift up my eyes to the mountains — where does my help come from? My help comes from the Lord, the Maker of heaven and earth."},
    {"ref": "John 16:33",          "text": "I have told you these things, so that in you you may have peace. In this world you will have trouble. But take heart! I have overcome the world."},
    {"ref": "Ephesians 3:20",      "text": "Now to him who is able to do immeasurably more than all we ask or imagine, according to his power that is at work within us."},
    {"ref": "Psalm 91:1",          "text": "Whoever dwells in the shelter of the Most High will rest in the shadow of the Almighty."},
    {"ref": "Isaiah 41:10",        "text": "So do not fear, for I am with you; do not be dismayed, for I am your God. I will strengthen you and help you."},
    {"ref": "Galatians 5:22-23",   "text": "But the fruit of the Spirit is love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, and self-control."},
    {"ref": "Psalm 16:8",          "text": "I have set the Lord always before me. Because he is at my right hand, I will not be shaken."},
    {"ref": "Hebrews 11:1",        "text": "Now faith is confidence in what we hope for and assurance about what we do not see."},
    {"ref": "1 John 4:4",          "text": "You, dear children, are from God and have overcome them, because the one who is in you is greater than the one who is in the world."},
    {"ref": "Romans 15:13",        "text": "May the God of hope fill you with all joy and peace as you trust in him, so that you may overflow with hope by the power of the Holy Spirit."},
    {"ref": "Deuteronomy 31:6",    "text": "Be strong and courageous. Do not be afraid or terrified because of them, for the Lord your God goes with you."},
    {"ref": "Colossians 3:23",     "text": "Whatever you do, work at it with all your heart, as working for the Lord, not for human masters."},
    {"ref": "Zephaniah 3:17",      "text": "The Lord your God is with you, the Mighty Warrior who saves. He will take great delight in you; in his love he will no longer rebuke you, but will rejoice over you with singing."},
]