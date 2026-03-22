"""
REST API Views for Study Session Monitoring and Testing System
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models

from .models import (
    StudySession, ProctoringEvent, GeneratedTest, TestQuestion,
    TestSubmission, WhiteboardSnapshot, SessionMetrics, Content, TestReport
)
from .serializers import (
    StudySessionSerializer, ProctoringEventSerializer, GeneratedTestSerializer,
    TestQuestionSerializer, TestSubmissionSerializer, WhiteboardSnapshotSerializer,
    SessionMetricsSerializer, SessionStatusSerializer, ViolationSummarySerializer,
    TestResultSerializer
)
from .session_manager import SessionManager
from .proctoring_engine import ProctoringEngine
from .monitoring_collector import MonitoringCollector
from .test_generator import TestGenerator
from .assessment_engine import AssessmentEngine


from .whiteboard_manager import WhiteboardManager
from .rag_chat_integration import RAGChatIntegration


class StudySessionViewSet(viewsets.ModelViewSet):
    """Manage study sessions"""
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return StudySession.objects.filter(user=self.request.user)
    
    def create(self, request):
        """Create a new study session with workspace name and limits check"""
        content_id = request.data.get('content_id')
        session_type = request.data.get('session_type', 'recommended')
        workspace_name = request.data.get('workspace_name', 'My Study Session')
        
        # Check session limits
        from .models import SessionLimit
        today = timezone.now().date()
        session_limit, created = SessionLimit.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'sessions_created': 0, 'tests_pending': 0}
        )
        
        # Check if user can create session
        if not session_limit.can_create_session:
            return Response({
                'error': 'Cannot create session',
                'reason': session_limit.blocked_reason,
                'sessions_today': session_limit.sessions_created,
                'max_sessions': session_limit.max_sessions_per_day,
                'tests_pending': session_limit.tests_pending
            }, status=status.HTTP_403_FORBIDDEN)
        
        # If content_id is provided, validate it
        content = None
        if content_id:
            try:
                content = Content.objects.get(id=content_id)
            except Content.DoesNotExist:
                return Response(
                    {'error': 'Content not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Create a placeholder content for the session
            # This allows users to add content later in the session window
            from .models import Topic
            topic, _ = Topic.objects.get_or_create(
                user=request.user,
                name=workspace_name,
                defaults={'description': f'Study session: {workspace_name}'}
            )
            content = Content.objects.create(
                topic=topic,
                title=f'{workspace_name} - Materials',
                content_type='pdf',  # Default type, can be changed later
                processed=False
            )
        
        # Create session with workspace name
        session = SessionManager.create_session(
            user=request.user,
            content=content,
            session_type=session_type,
            workspace_name=workspace_name
        )
        
        # Update session limit
        session_limit.sessions_created += 1
        session_limit.save()
        
        # Initialize proctoring
        proctoring_config = ProctoringEngine.initialize_proctoring(session.id)
        
        serializer = self.get_serializer(session)
        return Response({
            'session': serializer.data,
            'proctoring_config': proctoring_config,
            'session_limit': {
                'sessions_today': session_limit.sessions_created,
                'max_sessions': session_limit.max_sessions_per_day,
                'remaining': session_limit.max_sessions_per_day - session_limit.sessions_created
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get real-time session status"""
        session = self.get_object()
        status_data = SessionManager.get_session_status(session.id)
        serializer = SessionStatusSerializer(data=status_data)
        serializer.is_valid()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_break(self, request, pk=None):
        """Start break timer"""
        session = self.get_object()
        result = SessionManager.start_break(session.id)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def end_break(self, request, pk=None):
        """End break and resume session"""
        session = self.get_object()
        result = SessionManager.end_break(session.id)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete session and generate Test 1 immediately"""
        session = self.get_object()

        # Complete session
        result = SessionManager.complete_session(session.id)

        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # Generate Test 1 IMMEDIATELY (synchronous)
        try:
            from .gemini_mcq_service import create_assessment_from_session
            
            print(f"[Session] Generating Test 1 for session {session.id}...")
            assessment = create_assessment_from_session(
                session_id=session.id,
                user=session.user,
                content=session.content
            )
            print(f"[Session] ✅ Test 1 (Assessment {assessment.id}) created successfully")
            
            result['test_id'] = assessment.id
            result['test_ready'] = True
            result['message'] = 'Session complete! Test 1 is ready.'
            
        except Exception as e:
            print(f"[Session] ⚠️ Test 1 generation FAILED: {e}")
            import traceback
            traceback.print_exc()
            result['test_ready'] = False
            result['error'] = f'Test generation failed: {str(e)}'

        return Response(result)

    
    @action(detail=True, methods=['post'])
    def update_content(self, request, pk=None):
        """Update session's content (when user adds YouTube video)"""
        session = self.get_object()
        content_id = request.data.get('content_id')
        
        if not content_id:
            return Response(
                {'error': 'content_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            content = Content.objects.get(id=content_id)
            session.content = content
            session.save()
            
            return Response({
                'success': True,
                'message': 'Session content updated',
                'content_id': content.id,
                'content_title': content.title
            })
        except Content.DoesNotExist:
            return Response(
                {'error': 'Content not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_camera(self, request, pk=None):
        """Update camera permission status"""
        session = self.get_object()
        enabled = request.data.get('enabled', False)
        
        result = SessionManager.update_camera_status(session.id, enabled)
        ProctoringEngine.record_camera_status(session.id, enabled)
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get session metrics"""
        session = self.get_object()
        
        try:
            metrics = session.metrics
            serializer = SessionMetricsSerializer(metrics)
            return Response(serializer.data)
        except SessionMetrics.DoesNotExist:
            return Response(
                {'error': 'Metrics not available yet'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def violations(self, request, pk=None):
        """Get proctoring violation summary"""
        session = self.get_object()
        summary = ProctoringEngine.get_violation_summary(session.id)
        serializer = ViolationSummarySerializer(data=summary)
        serializer.is_valid()
        return Response(serializer.data)


class MonitoringViewSet(viewsets.ViewSet):
    """Handle monitoring events"""
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Record a monitoring event"""
        session_id = request.data.get('session_id')
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data', {})
        
        result = MonitoringCollector.record_event(session_id, event_type, event_data)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def update_metrics(self, request):
        """Update real-time metrics"""
        session_id = request.data.get('session_id')
        
        metrics = MonitoringCollector.update_real_time_metrics(session_id)
        
        return Response(metrics)


class ProctoringViewSet(viewsets.ViewSet):
    """Handle proctoring events"""
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Record a proctoring event"""
        session_id = request.data.get('session_id')
        event_type = request.data.get('event_type')
        
        if event_type == 'tab_switch':
            result = ProctoringEngine.record_tab_switch(session_id)
        elif event_type == 'copy_attempt':
            result = ProctoringEngine.record_copy_attempt(session_id)
        elif event_type == 'paste_attempt':
            result = ProctoringEngine.record_paste_attempt(session_id)
        elif event_type == 'focus_lost':
            result = ProctoringEngine.record_focus_lost(session_id)
        elif event_type == 'focus_gained':
            result = ProctoringEngine.record_focus_gained(session_id)
        elif event_type == 'screenshot_attempt':
            source = request.data.get('source', 'content')
            result = ProctoringEngine.record_screenshot_attempt(session_id, source)
        else:
            return Response(
                {'error': 'Invalid event type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result)


class TestViewSet(viewsets.ModelViewSet):
    """Manage generated tests"""
    serializer_class = GeneratedTestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return GeneratedTest.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate test from session"""
        session_id = request.data.get('session_id')
        difficulty = request.data.get('difficulty', 1)
        
        try:
            test = TestGenerator.generate_test(session_id, difficulty)
            serializer = self.get_serializer(test, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Test generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start test timer"""
        test = self.get_object()
        
        if test.started_at:
            return Response(
                {'error': 'Test already started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        test.started_at = timezone.now()
        test.save()
        
        serializer = self.get_serializer(test)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        """Submit answer to a question"""
        test = self.get_object()
        question_id = request.data.get('question_id')
        answer_text = request.data.get('answer_text', '')
        selected_index = request.data.get('selected_index')
        time_taken = request.data.get('time_taken_seconds', 0)
        
        try:
            question = TestQuestion.objects.get(id=question_id, test=test)
        except TestQuestion.DoesNotExist:
            return Response(
                {'error': 'Question not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Evaluate based on question type
        try:
            if question.question_type == 'mcq':
                submission = AssessmentEngine.evaluate_mcq(
                    question_id, request.user, selected_index, time_taken
                )
            elif question.question_type == 'short_answer':
                submission = AssessmentEngine.evaluate_short_answer(
                    question_id, request.user, answer_text, time_taken
                )
            elif question.question_type == 'problem_solving':
                submission = AssessmentEngine.evaluate_problem_solving(
                    question_id, request.user, answer_text, time_taken
                )
            else:
                return Response(
                    {'error': 'Invalid question type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = TestSubmissionSerializer(submission)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': f'Answer evaluation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete test and get results"""
        test = self.get_object()
        
        if test.is_completed:
            return Response(
                {'error': 'Test already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as completed
        test.completed_at = timezone.now()
        test.is_completed = True
        test.save()
        
        # Calculate score
        score_result = AssessmentEngine.calculate_test_score(test.id)
        
        # Identify weak areas
        weak_areas = AssessmentEngine.identify_weak_areas(test.id)
        
        # Calculate scores by type
        from .models import TestSubmission, TestQuestion, TestResult, WeakPoint, SessionLimit
        
        submissions = TestSubmission.objects.filter(question__test=test)
        
        # Calculate type-specific scores
        mcq_submissions = submissions.filter(question__question_type='mcq')
        mcq_correct = mcq_submissions.filter(is_correct=True).count()
        mcq_total = mcq_submissions.count()
        mcq_score = (mcq_correct / mcq_total * 100) if mcq_total > 0 else 0
        
        short_submissions = submissions.filter(question__question_type='short_answer')
        short_score = short_submissions.aggregate(models.Avg('score'))['score__avg'] or 0
        
        problem_submissions = submissions.filter(question__question_type='problem_solving')
        problem_score = problem_submissions.aggregate(models.Avg('score'))['score__avg'] or 0
        
        # Overall score
        total_score = score_result.get('overall_score', 0)
        correct_answers = score_result.get('correct_answers', 0)
        total_questions = score_result.get('total_questions', 0)
        
        # Calculate time taken
        time_taken = 0
        if test.started_at and test.completed_at:
            time_taken = int((test.completed_at - test.started_at).total_seconds())
        
        # Identify weak topics (<70% accuracy)
        weak_topics = []
        concept_scores = {}
        
        for submission in submissions:
            concept = submission.question.concept
            if concept not in concept_scores:
                concept_scores[concept] = {'correct': 0, 'total': 0}
            
            concept_scores[concept]['total'] += 1
            if submission.is_correct or (submission.score and submission.score >= 70):
                concept_scores[concept]['correct'] += 1
        
        for concept, scores in concept_scores.items():
            accuracy = (scores['correct'] / scores['total'] * 100) if scores['total'] > 0 else 0
            if accuracy < 70:
                weak_topics.append({
                    'name': concept,
                    'accuracy': accuracy,
                    'questions': scores['total']
                })
                
                # Create or update WeakPoint
                weak_point, created = WeakPoint.objects.get_or_create(
                    user=test.user,
                    topic=concept,
                    defaults={
                        'subtopic': '',
                        'incorrect_count': scores['total'] - scores['correct'],
                        'total_attempts': scores['total'],
                        'accuracy': accuracy,
                        'confidence_score': accuracy / 100
                    }
                )
                
                if not created:
                    # Update existing weak point
                    weak_point.incorrect_count += scores['total'] - scores['correct']
                    weak_point.total_attempts += scores['total']
                    weak_point.accuracy = (weak_point.total_attempts - weak_point.incorrect_count) / weak_point.total_attempts * 100
                    weak_point.confidence_score = weak_point.accuracy / 100
                    weak_point.save()
        
        # Create TestResult
        test_result = TestResult.objects.create(
            user=test.user,
            test=test,
            session=test.session,
            total_score=total_score,
            total_questions=total_questions,
            correct_answers=correct_answers,
            time_taken_seconds=time_taken,
            mcq_score=mcq_score,
            short_answer_score=short_score,
            problem_solving_score=problem_score,
            weak_topics=weak_topics
        )
        
        # Generate comprehensive AMCAT-style report
        from .report_generator import ReportGenerator
        from .email_service import EmailService
        
        try:
            report = ReportGenerator.generate_report(test_result.id)
            email_result = EmailService.send_test_report(test.user, test_result, report)
        except Exception as e:
            print(f"[TestViewSet] Report generation failed: {e}")
            email_result = EmailService._send_basic_email(test.user, test_result)
        
        if email_result.get('success'):
            test_result.email_sent = True
            test_result.email_sent_at = timezone.now()
            test_result.save()
        
        # Update SessionLimit - mark test as completed
        from datetime import date
        session_limit = SessionLimit.objects.filter(
            user=test.user,
            date=date.today()
        ).first()
        
        if session_limit:
            session_limit.tests_pending = max(0, session_limit.tests_pending - 1)
            session_limit.tests_completed += 1
            
            # Check if can create new session
            if session_limit.tests_pending == 0 and session_limit.sessions_created < session_limit.max_sessions_per_day:
                session_limit.can_create_session = True
                session_limit.blocked_reason = ""
            
            session_limit.save()
        
        # Prepare ML input and predict next difficulty
        try:
            ml_input = AssessmentEngine.prepare_ml_input(test.id, test.session.id)
            
            from .ml_predictor import predict_next_difficulty
            next_difficulty = predict_next_difficulty(ml_input)
            
            difficulty_feedback = TestViewSet._get_difficulty_feedback(
                test.difficulty_level, next_difficulty
            )
        except Exception as e:
            next_difficulty = test.difficulty_level
            difficulty_feedback = "Unable to predict next difficulty"
        
        # Prepare response
        result = {
            'test_id': test.id,
            'test_result_id': test_result.id,
            'overall_score': total_score,
            'total_questions': total_questions,
            'answered_questions': score_result.get('answered_questions', 0),
            'correct_answers': correct_answers,
            'time_taken_seconds': time_taken,
            'mcq_score': mcq_score,
            'short_answer_score': short_score,
            'problem_solving_score': problem_score,
            'weak_topics': weak_topics,
            'weak_areas': weak_areas,
            'next_difficulty': next_difficulty,
            'difficulty_feedback': difficulty_feedback,
            'email_sent': email_result.get('success', False)
        }
        
        serializer = TestResultSerializer(data=result)
        serializer.is_valid()
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Get the full AMCAT-style report for a completed test"""
        test = self.get_object()
        
        if not test.is_completed:
            return Response(
                {'error': 'Test not completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to get existing report
        try:
            from .models import TestResult
            test_result = TestResult.objects.get(test=test)
            report = TestReport.objects.get(test_result=test_result)
        except (TestResult.DoesNotExist, TestReport.DoesNotExist):
            # Generate report on the fly
            try:
                from .models import TestResult
                test_result = TestResult.objects.get(test=test)
                from .report_generator import ReportGenerator
                report = ReportGenerator.generate_report(test_result.id)
            except TestResult.DoesNotExist:
                return Response(
                    {'error': 'Test result not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': f'Report generation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response({
            'report_id': report.id,
            'test_id': test.id,
            'generated_at': report.generated_at.isoformat(),
            'score_summary': report.score_summary,
            'concept_breakdown': report.concept_breakdown,
            'behavioral_analysis': report.behavioral_analysis,
            'response_patterns': report.response_patterns,
            'recommendations': report.recommendations,
        })

    @staticmethod
    def _get_difficulty_feedback(current, next_level):
        """Generate feedback for difficulty change"""
        if next_level > current:
            return f"Great job! Moving up to difficulty level {next_level}."
        elif next_level < current:
            return f"Let's practice more at difficulty level {next_level}."
        else:
            return f"Continue practicing at difficulty level {current}."


class WhiteboardViewSet(viewsets.ModelViewSet):
    """Manage whiteboard snapshots"""
    serializer_class = WhiteboardSnapshotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return WhiteboardSnapshot.objects.filter(session__user=self.request.user)
    
    def create(self, request):
        """Save whiteboard snapshot"""
        session_id = request.data.get('session_id')
        image_data = request.data.get('image_data')
        notes = request.data.get('notes', '')
        
        try:
            session = StudySession.objects.get(id=session_id, user=request.user)
        except StudySession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Use WhiteboardManager to capture screenshot
        result = WhiteboardManager.capture_screenshot(session_id, image_data, notes)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        # Record as monitoring event
        MonitoringCollector.record_event(session_id, 'whiteboard_snapshot')
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def download(self, request):
        """Download whiteboard for a session"""
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'session_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = WhiteboardManager.download_whiteboard(session_id)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        
        return Response(result)


class ChatViewSet(viewsets.ViewSet):
    """Handle RAG chat queries"""
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Send chat query to RAG backend"""
        session_id = request.data.get('session_id')
        query = request.data.get('query')
        context = request.data.get('context')
        
        if not session_id or not query:
            return Response(
                {'error': 'session_id and query are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify session belongs to user
        try:
            session = StudySession.objects.get(id=session_id, user=request.user)
        except StudySession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Send query to RAG backend
        result = RAGChatIntegration.send_query(session_id, query, context)
        
        if 'error' in result:
            # Return fallback response if available
            if 'fallback_response' in result:
                return Response({
                    'response': result['fallback_response'],
                    'error': result['error'],
                    'is_fallback': True
                })
            return Response(result, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get chat history for a session"""
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'session_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = RAGChatIntegration.get_chat_history(session_id)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
        
        return Response(result)
