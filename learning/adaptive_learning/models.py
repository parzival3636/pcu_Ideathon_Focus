from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json
import datetime


class Topic(models.Model):
    """User's learning topics (e.g., Python Programming, Calculus)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_topics')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Progress tracking
    current_difficulty = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])
    mastery_level = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    sessions_completed = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Content(models.Model):
    """Learning content (YouTube, PDF, PPT, Word)"""
    CONTENT_TYPES = [
        ('youtube', 'YouTube Video'),
        ('pdf', 'PDF Document'),
        ('ppt', 'PowerPoint Presentation'),
        ('word', 'Word Document'),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=300)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    
    # Content source
    url = models.URLField(max_length=500, blank=True, null=True)  # For YouTube
    file = models.FileField(upload_to='learning_content/', blank=True, null=True)  # For files
    
    # Extracted data
    transcript = models.TextField(blank=True)  # YouTube transcript or extracted text
    key_concepts = models.JSONField(default=list)  # List of identified concepts
    source_language = models.CharField(max_length=10, default='en', blank=True)  # Detected language (en, hi, mr, etc.)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)  # Has content been processed?
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.topic.name} - {self.title}"


class Assessment(models.Model):
    """Generated quiz/assessment for a content piece"""
    TEST_NUMBERS = [
        (1, 'Test 1 - Initial'),
        (2, 'Test 2 - Adaptive Retry'),
    ]
    
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='assessments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey('StudySession', on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    
    # Two-test system
    test_number = models.IntegerField(default=1, choices=TEST_NUMBERS)
    parent_assessment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='followup_tests')
    expires_at = models.DateTimeField(null=True, blank=True)  # 6-hour window for Test 2
    
    difficulty_level = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])
    total_questions = models.IntegerField(default=10)
    
    # Session tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Results
    score = models.FloatField(null=True, blank=True)  # Percentage
    adaptive_score = models.FloatField(null=True, blank=True)  # ML-calculated score
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} Assessment (Test {self.test_number})"
    
    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at


class Question(models.Model):
    """Individual question in an assessment"""
    DIFFICULTY_LEVELS = [
        (1, 'Easy'),
        (2, 'Medium'),
        (3, 'Hard'),
    ]
    
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice Question'),
        ('short_answer', 'Short Answer'),
        ('problem_solving', 'Problem Solving'),
    ]
    
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    
    question_text = models.TextField()
    options = models.JSONField(null=True, blank=True)  # List of options (for MCQ)
    correct_answer_index = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(3)])
    correct_answer = models.TextField(blank=True, null=True) # Text answer for open-ended
    explanation = models.TextField()
    
    difficulty = models.IntegerField(choices=DIFFICULTY_LEVELS, default=1)
    concept = models.CharField(max_length=200)  # Which concept this tests
    
    order = models.IntegerField(default=0)  # Question order in assessment
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."


class UserAnswer(models.Model):
    """User's answer to a question with timing data"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    selected_answer_index = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(3)])
    user_answer = models.TextField(blank=True, null=True) # For open-ended
    is_correct = models.BooleanField()
    feedback = models.TextField(blank=True, null=True) # AI feedback
    score = models.FloatField(default=0.0) # For open-ended
    
    # Timing data
    time_taken_seconds = models.IntegerField()  # Time to answer this question
    attempt_number = models.IntegerField(default=1)  # If user retries
    
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['answered_at']
    
    def __str__(self):
        return f"{self.user.username} - Q{self.question.order} - {'✓' if self.is_correct else '✗'}"


class UserProgress(models.Model):
    """Overall progress tracking for a user in a topic"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    
    # Current state
    current_difficulty = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])
    mastery_level = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Performance metrics
    total_assessments = models.IntegerField(default=0)
    average_accuracy = models.FloatField(default=0.0)
    average_time_per_question = models.FloatField(default=0.0)
    first_attempt_correct_rate = models.FloatField(default=0.0)
    
    # Trend tracking
    last_score = models.FloatField(null=True, blank=True)
    score_trend = models.FloatField(default=0.0)  # Change from previous session
    
    # Timestamps
    last_session_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'topic']
    
    def __str__(self):
        return f"{self.user.username} - {self.topic.name} Progress"


class MonitoringSession(models.Model):
    """Track user engagement during learning (tab switches, time, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    
    # Session data
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    total_time_seconds = models.IntegerField(default=0)
    active_time_seconds = models.IntegerField(default=0)  # Time actually focused
    tab_switches = models.IntegerField(default=0)
    focus_lost_count = models.IntegerField(default=0)
    
    # Detailed events log
    events = models.JSONField(default=list)  # [{timestamp, event_type, data}, ...]
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} Session"


class ConceptMastery(models.Model):
    """Track mastery of individual concepts within a topic"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    concept_name = models.CharField(max_length=200)
    
    # Performance metrics
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    
    # Mastery level (0.0 to 1.0)
    mastery_level = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Spaced repetition
    next_review_date = models.DateTimeField(null=True, blank=True)
    review_interval_days = models.IntegerField(default=1)
    
    last_practiced_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'topic', 'concept_name']
        ordering = ['mastery_level', 'concept_name']
    
    def __str__(self):
        return f"{self.user.username} - {self.concept_name} ({self.accuracy:.0f}%)"


class RevisionQueue(models.Model):
    """Questions scheduled for revision (spaced repetition)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    concept = models.ForeignKey(ConceptMastery, on_delete=models.CASCADE)
    
    # Scheduling
    scheduled_for = models.DateTimeField()
    priority = models.IntegerField(default=1)  # Higher = more urgent
    
    # History
    times_reviewed = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['scheduled_for', '-priority']
    
    def __str__(self):
        return f"{self.user.username} - {self.concept.concept_name} Review"


# ============================================================================
# STUDY SESSION MONITORING AND TESTING MODELS
# ============================================================================

class StudySession(models.Model):
    """Study session with dual modes: Recommended (2hr) or Standard (Pomodoro)"""
    SESSION_TYPES = [
        ('recommended', 'Recommended Session (2hr + 20min break)'),
        ('standard', 'Standard Session (50min + 10min break)'),
        ('custom', 'Custom Session'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='study_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='recommended')
    
    # Workspace identification
    workspace_name = models.CharField(max_length=200, default='My Study Session')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    study_duration_seconds = models.IntegerField(default=0)
    break_duration_seconds = models.IntegerField(default=0)
    
    # Break tracking
    break_started_at = models.DateTimeField(null=True, blank=True)
    break_ended_at = models.DateTimeField(null=True, blank=True)
    break_used = models.BooleanField(default=False)
    break_expired = models.BooleanField(default=False)
    
    # Reminders (for recommended mode)
    reminder_70_shown = models.BooleanField(default=False)
    reminder_90_shown = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    test_generation_failed = models.BooleanField(default=False)
    test_generation_message = models.TextField(blank=True, null=True)
    
    # Camera/Proctoring
    camera_enabled = models.BooleanField(default=False)
    camera_permission_requested = models.BooleanField(default=False)
    
    # Test availability (6 hours after session ends)
    test_available_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.workspace_name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class ProctoringEvent(models.Model):
    """Track proctoring violations and events during study sessions"""
    EVENT_TYPES = [
        ('tab_switch', 'Tab Switch'),
        ('copy_attempt', 'Copy Attempt'),
        ('paste_attempt', 'Paste Attempt'),
        ('screenshot_blocked', 'Screenshot Blocked'),
        ('screenshot_allowed', 'Screenshot Allowed (Whiteboard/Chat)'),
        ('camera_enabled', 'Camera Enabled'),
        ('camera_disabled', 'Camera Disabled'),
        ('focus_lost', 'Window Focus Lost'),
        ('focus_gained', 'Window Focus Gained'),
    ]
    
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='proctoring_events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)  # Additional event data
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'event_type']),
        ]
    
    def __str__(self):
        return f"{self.session.user.username} - {self.event_type} - {self.timestamp.strftime('%H:%M:%S')}"


class GeneratedTest(models.Model):
    """Auto-generated test after study session completion"""
    session = models.OneToOneField(StudySession, on_delete=models.CASCADE, related_name='generated_test')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_tests')
    
    difficulty_level = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])
    
    # Question counts
    total_questions = models.IntegerField(default=10)
    mcq_count = models.IntegerField(default=4)
    short_answer_count = models.IntegerField(default=3)
    problem_solving_count = models.IntegerField(default=3)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_limit_seconds = models.IntegerField(default=1800)  # 30 minutes default
    
    # Results
    score = models.FloatField(null=True, blank=True)  # Overall percentage
    is_completed = models.BooleanField(default=False)
    
    # Weak areas identified (concepts with <70% accuracy)
    weak_concepts = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - Test (Difficulty {self.difficulty_level}) - {self.created_at.strftime('%Y-%m-%d')}"


class TestQuestion(models.Model):
    """Individual question in a generated test"""
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice Question'),
        ('short_answer', 'Short Answer'),
        ('problem_solving', 'Problem Solving'),
    ]
    
    test = models.ForeignKey(GeneratedTest, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    
    # For MCQ
    options = models.JSONField(null=True, blank=True)  # List of 4 options
    correct_answer_index = models.IntegerField(null=True, blank=True)
    
    # For Short Answer and Problem Solving
    expected_answer = models.TextField(null=True, blank=True)
    evaluation_criteria = models.TextField(null=True, blank=True)  # For ML evaluation
    
    # Common fields
    explanation = models.TextField(blank=True)
    concept = models.CharField(max_length=200)
    difficulty = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    points = models.IntegerField(default=1)  # Weight of question
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.test.user.username} - {self.question_type} Q{self.order}"


class TestSubmission(models.Model):
    """User's answer submission for a test question"""
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Answer data
    answer_text = models.TextField(blank=True)  # For all types
    selected_index = models.IntegerField(null=True, blank=True)  # For MCQ only
    
    # Evaluation
    is_correct = models.BooleanField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)  # 0-100 for ML-evaluated answers
    feedback = models.TextField(blank=True)  # AI-generated feedback
    
    # Timing
    time_taken_seconds = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # ML evaluation metadata
    evaluated_by_ml = models.BooleanField(default=False)
    ml_confidence = models.FloatField(null=True, blank=True)  # 0-1
    
    class Meta:
        ordering = ['submitted_at']
        unique_together = ['question', 'user']
    
    def __str__(self):
        return f"{self.user.username} - Q{self.question.order} - Score: {self.score}"


class WhiteboardSnapshot(models.Model):
    """Whiteboard screenshots taken during study session"""
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='whiteboard_snapshots')
    image = models.ImageField(upload_to='whiteboard_snapshots/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)  # Optional user notes
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.session.user.username} - Whiteboard - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class SessionMetrics(models.Model):
    """Aggregated metrics for ML model input"""
    session = models.OneToOneField(StudySession, on_delete=models.CASCADE, related_name='metrics')
    
    # Engagement metrics
    engagement_score = models.FloatField(default=0.0)  # 0-100
    study_speed = models.FloatField(default=0.0)  # Content units per minute
    interaction_rate = models.FloatField(default=0.0)  # Interactions per minute
    
    # Focus metrics
    total_tab_switches = models.IntegerField(default=0)
    total_focus_losses = models.IntegerField(default=0)
    average_focus_duration_seconds = models.FloatField(default=0.0)
    
    # Time metrics
    total_active_time_seconds = models.IntegerField(default=0)
    total_idle_time_seconds = models.IntegerField(default=0)
    active_time_ratio = models.FloatField(default=0.0)  # active / total
    
    # Content interaction
    content_interactions = models.JSONField(default=dict, blank=True)  # {pause, play, seek, etc.}
    
    # Chat/Whiteboard usage
    chat_queries_count = models.IntegerField(default=0)
    whiteboard_snapshots_count = models.IntegerField(default=0)
    
    # Calculated at session end
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Session Metrics"
    
    def __str__(self):
        return f"{self.session.user.username} - Metrics - Engagement: {self.engagement_score:.1f}%"


# ============================================================================
# ENHANCED FEATURES - Workspace, Limits, Weak Points, Email Results
# ============================================================================


class WeakPoint(models.Model):
    """Track user's weak areas based on test performance"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weak_points')
    topic = models.CharField(max_length=200)  # e.g., "Python Loops"
    subtopic = models.CharField(max_length=200, blank=True)  # e.g., "For Loops"
    
    # Performance metrics
    incorrect_count = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)  # Percentage
    confidence_score = models.FloatField(default=0.0)  # 0-1, lower = weaker
    
    # Tracking
    first_identified = models.DateTimeField(auto_now_add=True)
    last_attempted = models.DateTimeField(auto_now=True)
    
    # Recommendations generated
    recommendations_generated = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['confidence_score', '-incorrect_count']
        unique_together = ['user', 'topic', 'subtopic']
    
    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.accuracy:.0f}%)"


class SessionLimit(models.Model):
    """Track daily session limits (3 per day, blocked until tests completed)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_limits')
    date = models.DateField(default=datetime.date.today)
    
    # Limits
    sessions_created = models.IntegerField(default=0)
    max_sessions_per_day = models.IntegerField(default=3)
    
    # Test tracking
    tests_pending = models.IntegerField(default=0)
    tests_completed = models.IntegerField(default=0)
    
    # Status
    can_create_session = models.BooleanField(default=True)
    blocked_reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.sessions_created}/{self.max_sessions_per_day}"


class TestResult(models.Model):
    """Complete test results with email notification"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_results')
    test = models.OneToOneField(GeneratedTest, on_delete=models.CASCADE, related_name='result')
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='test_results')
    
    # Scores
    total_score = models.FloatField()  # Percentage
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    time_taken_seconds = models.IntegerField()
    
    # Breakdown by type
    mcq_score = models.FloatField(default=0.0)
    short_answer_score = models.FloatField(default=0.0)
    problem_solving_score = models.FloatField(default=0.0)
    
    # Weak topics identified (JSON array of topics with <70% accuracy)
    weak_topics = models.JSONField(default=list)
    
    # Email notification
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.total_score:.1f}% - {self.completed_at.strftime('%Y-%m-%d')}"


class TestReport(models.Model):
    """AMCAT-style comprehensive test report with behavioral analysis"""
    test_result = models.OneToOneField(TestResult, on_delete=models.CASCADE, related_name='report')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_reports')
    
    # Report sections (all JSON)
    score_summary = models.JSONField(default=dict)         # Overall + per-section scores with colors
    concept_breakdown = models.JSONField(default=list)     # Per-concept accuracy, bars, colors
    behavioral_analysis = models.JSONField(default=dict)   # Thinking style, cognitive profile, rhythms
    response_patterns = models.JSONField(default=dict)     # Time distribution, guessing, fatigue
    recommendations = models.JSONField(default=list)       # Personalized study tips
    
    generated_at = models.DateTimeField(auto_now_add=True)
    report_version = models.CharField(max_length=10, default='1.0')
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.user.username} - Report - {self.generated_at.strftime('%Y-%m-%d')}"


class CourseRecommendation(models.Model):
    """Course recommendations based on weak points"""
    weak_point = models.ForeignKey(WeakPoint, on_delete=models.CASCADE, related_name='recommendations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_recommendations')
    
    # Recommendation details
    title = models.CharField(max_length=300)
    source = models.CharField(max_length=50)  # 'youtube', 'article', 'course'
    url = models.URLField(max_length=500)
    description = models.TextField(blank=True)
    
    # Metadata
    relevance_score = models.FloatField(default=0.0)  # How relevant to weak point
    created_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-relevance_score', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.source})"


class BrowserExtensionData(models.Model):
    """Data from browser extension (tab switches, blocked sites)"""
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='extension_data')
    
    # Tab monitoring
    tab_switches = models.IntegerField(default=0)
    blocked_attempts = models.IntegerField(default=0)
    
    # Blocked sites list
    blocked_sites = models.JSONField(default=list)
    
    # Detailed log
    events = models.JSONField(default=list)  # [{timestamp, event_type, url, ...}]
    
    # Status
    extension_active = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_heartbeat']
    
    def __str__(self):
        return f"{self.session.user.username} - Extension Data - {self.tab_switches} switches"


# ============================================================================
# SCRAPER CACHE MODELS
# ============================================================================


class ScrapedContent(models.Model):
    """Cached scraped content from web scraper (articles, playlists, Q&A)"""
    SOURCE_TYPES = [
        ('google', 'Google Article'),
        ('youtube', 'YouTube Playlist'),
        ('stackoverflow', 'Stack Overflow Q&A'),
    ]
    
    topic = models.CharField(max_length=300, db_index=True)
    source = models.CharField(max_length=20, choices=SOURCE_TYPES)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=500)
    description = models.TextField(blank=True)
    votes = models.CharField(max_length=20, blank=True)  # For StackOverflow
    channel = models.CharField(max_length=200, blank=True)  # For YouTube
    
    scraped_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Cache expiry (24 hours)
    
    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['topic', 'source']),
        ]
    
    def __str__(self):
        return f"{self.topic} - {self.source} - {self.title[:50]}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class ScrapeJob(models.Model):
    """Track background scraping jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    topic = models.CharField(max_length=300, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    result_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"ScrapeJob: {self.topic} ({self.status})"
