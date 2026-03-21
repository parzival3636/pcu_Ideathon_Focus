from rest_framework import serializers
from .models import (
    Topic, Content, Assessment, Question, UserAnswer,
    UserProgress, MonitoringSession, ConceptMastery, RevisionQueue,
    StudySession, ProctoringEvent, GeneratedTest, TestQuestion,
    TestSubmission, WhiteboardSnapshot, SessionMetrics, TestReport
)


class TopicSerializer(serializers.ModelSerializer):
    content_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'description', 'current_difficulty', 'mastery_level',
            'sessions_completed', 'content_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'content_count']
    
    def get_content_count(self, obj):
        return obj.contents.count()


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = [
            'id', 'topic', 'title', 'content_type', 'url', 'file',
            'transcript', 'key_concepts', 'source_language', 'processed', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'processed', 'transcript', 'key_concepts', 'source_language']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'options', 'correct_answer_index',
            'correct_answer', 'explanation', 'difficulty', 'concept', 'order'
        ]
        read_only_fields = ['id']


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = [
            'id', 'question', 'selected_answer_index', 'user_answer', 
            'is_correct', 'feedback', 'score',
            'time_taken_seconds', 'attempt_number', 'answered_at'
        ]
        read_only_fields = ['id', 'answered_at', 'is_correct']


class AssessmentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'content', 'content_title', 'difficulty_level', 'total_questions',
            'started_at', 'completed_at', 'is_completed', 'score', 'adaptive_score',
            'time_taken_seconds', 'questions'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'score', 'adaptive_score']


class UserProgressSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    
    class Meta:
        model = UserProgress
        fields = [
            'id', 'topic', 'topic_name', 'current_difficulty', 'mastery_level',
            'total_assessments', 'average_accuracy', 'average_time_per_question',
            'first_attempt_correct_rate', 'last_score', 'score_trend',
            'last_session_at', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class MonitoringSessionSerializer(serializers.ModelSerializer):
    content_title = serializers.CharField(source='content.title', read_only=True)
    
    class Meta:
        model = MonitoringSession
        fields = [
            'id', 'content', 'content_title', 'started_at', 'ended_at',
            'total_time_seconds', 'active_time_seconds', 'tab_switches',
            'focus_lost_count', 'events'
        ]
        read_only_fields = ['id', 'started_at']


class ConceptMasterySerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    
    class Meta:
        model = ConceptMastery
        fields = [
            'id', 'topic', 'topic_name', 'concept_name', 'total_questions',
            'correct_answers', 'accuracy', 'mastery_level', 'next_review_date',
            'review_interval_days', 'last_practiced_at', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class RevisionQueueSerializer(serializers.ModelSerializer):
    concept_name = serializers.CharField(source='concept.concept_name', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    
    class Meta:
        model = RevisionQueue
        fields = [
            'id', 'question', 'question_text', 'concept', 'concept_name',
            'scheduled_for', 'priority', 'times_reviewed', 'times_correct',
            'completed', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Specialized serializers for specific API responses

class AssessmentResultSerializer(serializers.Serializer):
    """Serializer for assessment results with detailed analytics"""
    assessment_id = serializers.IntegerField()
    score = serializers.FloatField()
    adaptive_score = serializers.FloatField()
    time_taken_seconds = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    accuracy = serializers.FloatField()
    
    # Weak concepts
    weak_concepts = serializers.ListField(child=serializers.DictField())
    
    # Next difficulty prediction
    next_difficulty = serializers.IntegerField()
    difficulty_changed = serializers.BooleanField()
    
    # Performance feedback
    feedback_message = serializers.CharField()


class DifficultyPredictionSerializer(serializers.Serializer):
    """Serializer for ML difficulty prediction"""
    current_difficulty = serializers.IntegerField()
    predicted_difficulty = serializers.IntegerField()
    confidence = serializers.FloatField()
    reasoning = serializers.CharField()
    question_count = serializers.IntegerField()


# ============================================================================
# STUDY SESSION MONITORING AND TESTING SERIALIZERS
# ============================================================================

class StudySessionSerializer(serializers.ModelSerializer):
    content_title = serializers.CharField(source='content.title', read_only=True)
    elapsed_study_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = StudySession
        fields = [
            'id', 'user', 'content', 'content_title', 'session_type',
            'started_at', 'ended_at', 'study_duration_seconds', 'break_duration_seconds',
            'break_started_at', 'break_ended_at', 'break_used', 'break_expired',
            'reminder_70_shown', 'reminder_90_shown', 'is_active', 'is_completed',
            'camera_enabled', 'camera_permission_requested', 'elapsed_study_seconds'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at', 'elapsed_study_seconds']
    
    def get_elapsed_study_seconds(self, obj):
        from .session_manager import SessionManager
        if obj.is_active:
            return SessionManager.get_elapsed_study_time(obj)
        return obj.study_duration_seconds


class ProctoringEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProctoringEvent
        fields = ['id', 'session', 'event_type', 'timestamp', 'details']
        read_only_fields = ['id', 'timestamp']


class SessionMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionMetrics
        fields = [
            'id', 'session', 'engagement_score', 'study_speed', 'interaction_rate',
            'total_tab_switches', 'total_focus_losses', 'average_focus_duration_seconds',
            'total_active_time_seconds', 'total_idle_time_seconds', 'active_time_ratio',
            'content_interactions', 'chat_queries_count', 'whiteboard_snapshots_count',
            'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']


class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = [
            'id', 'test', 'question_type', 'question_text', 'options',
            'correct_answer_index', 'expected_answer', 'evaluation_criteria',
            'explanation', 'concept', 'difficulty', 'order', 'points'
        ]
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        """Hide correct answer from students"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Only show correct answer to staff or after submission
        if request and not request.user.is_staff:
            data.pop('correct_answer_index', None)
            data.pop('expected_answer', None)
        
        return data


class TestSubmissionSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    
    class Meta:
        model = TestSubmission
        fields = [
            'id', 'question', 'question_text', 'question_type', 'user',
            'answer_text', 'selected_index', 'is_correct', 'score', 'feedback',
            'time_taken_seconds', 'submitted_at', 'evaluated_by_ml', 'ml_confidence'
        ]
        read_only_fields = ['id', 'submitted_at', 'is_correct', 'score', 'feedback', 'evaluated_by_ml', 'ml_confidence']


class GeneratedTestSerializer(serializers.ModelSerializer):
    questions = TestQuestionSerializer(many=True, read_only=True)
    session_content_title = serializers.CharField(source='session.content.title', read_only=True)
    
    class Meta:
        model = GeneratedTest
        fields = [
            'id', 'session', 'session_content_title', 'user', 'difficulty_level',
            'total_questions', 'mcq_count', 'short_answer_count', 'problem_solving_count',
            'created_at', 'started_at', 'completed_at', 'time_limit_seconds',
            'score', 'is_completed', 'weak_concepts', 'questions'
        ]
        read_only_fields = ['id', 'created_at', 'started_at', 'completed_at', 'score', 'weak_concepts']


class WhiteboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteboardSnapshot
        fields = ['id', 'session', 'image', 'created_at', 'notes']
        read_only_fields = ['id', 'created_at']


# Specialized API response serializers

class SessionStatusSerializer(serializers.Serializer):
    """Real-time session status"""
    session_id = serializers.IntegerField()
    session_type = serializers.CharField()
    is_active = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    elapsed_study_seconds = serializers.IntegerField()
    total_study_seconds = serializers.IntegerField()
    remaining_study_seconds = serializers.IntegerField()
    break_used = serializers.BooleanField()
    break_expired = serializers.BooleanField()
    break_active = serializers.BooleanField()
    break_duration_seconds = serializers.IntegerField()
    camera_enabled = serializers.BooleanField()
    reminder = serializers.DictField()


class ViolationSummarySerializer(serializers.Serializer):
    """Proctoring violation summary"""
    session_id = serializers.IntegerField()
    total_events = serializers.IntegerField()
    violations = serializers.DictField()
    allowed_actions = serializers.DictField()
    camera_status = serializers.DictField()


class TestResultSerializer(serializers.Serializer):
    """Complete test results with analytics"""
    test_id = serializers.IntegerField()
    overall_score = serializers.FloatField()
    total_questions = serializers.IntegerField()
    answered_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    weak_areas = serializers.ListField(child=serializers.DictField())
    next_difficulty = serializers.IntegerField(required=False)
    difficulty_feedback = serializers.CharField(required=False)
