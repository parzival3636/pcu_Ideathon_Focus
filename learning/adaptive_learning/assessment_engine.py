"""
Assessment Engine - Evaluate test answers and calculate scores
"""
from .models import GeneratedTest, TestQuestion, TestSubmission
from django.db.models import Avg, Count, Q


class AssessmentEngine:
    """Evaluate test answers and calculate scores"""
    
    @classmethod
    def evaluate_mcq(cls, question_id, user, selected_index, time_taken):
        """
        Evaluate MCQ answer
        
        Args:
            question_id: TestQuestion ID
            user: User instance
            selected_index: int (0-3)
            time_taken: seconds
            
        Returns:
            TestSubmission instance
        """
        try:
            question = TestQuestion.objects.get(id=question_id, question_type='mcq')
        except TestQuestion.DoesNotExist:
            raise ValueError("MCQ question not found")
        
        # Check if correct
        is_correct = (selected_index == question.correct_answer_index)
        score = 100.0 if is_correct else 0.0
        
        # Create or update submission
        submission, created = TestSubmission.objects.update_or_create(
            question=question,
            user=user,
            defaults={
                'selected_index': selected_index,
                'answer_text': question.options[selected_index] if question.options else '',
                'is_correct': is_correct,
                'score': score,
                'time_taken_seconds': time_taken,
                'evaluated_by_ml': False
            }
        )
        
        return submission
    
    @classmethod
    def evaluate_short_answer(cls, question_id, user, answer_text, time_taken):
        """
        Evaluate Short Answer using ML
        
        Args:
            question_id: TestQuestion ID
            user: User instance
            answer_text: str
            time_taken: seconds
            
        Returns:
            TestSubmission instance
        """
        try:
            question = TestQuestion.objects.get(id=question_id, question_type='short_answer')
        except TestQuestion.DoesNotExist:
            raise ValueError("Short answer question not found")
        
        # Use ML model to evaluate
        try:
            from .question_generator import QuestionGenerator
            qg = QuestionGenerator()
            
            evaluation = qg.assess_answer(
                question.question_text,
                question.expected_answer,
                answer_text,
                'short_answer'
            )
            
            score = evaluation.get('score', 0)
            is_correct = evaluation.get('is_correct', False)
            feedback = evaluation.get('feedback', '')
            ml_confidence = evaluation.get('confidence', 0.5)
            
        except Exception as e:
            # Fallback: simple keyword matching
            score, is_correct, feedback = cls._fallback_evaluate(
                answer_text, question.expected_answer
            )
            ml_confidence = 0.3
        
        # Create or update submission
        submission, created = TestSubmission.objects.update_or_create(
            question=question,
            user=user,
            defaults={
                'answer_text': answer_text,
                'is_correct': is_correct,
                'score': score,
                'feedback': feedback,
                'time_taken_seconds': time_taken,
                'evaluated_by_ml': True,
                'ml_confidence': ml_confidence
            }
        )
        
        return submission
    
    @classmethod
    def evaluate_problem_solving(cls, question_id, user, answer_text, time_taken):
        """
        Evaluate Problem Solving using ML
        
        Args:
            question_id: TestQuestion ID
            user: User instance
            answer_text: str
            time_taken: seconds
            
        Returns:
            TestSubmission instance
        """
        try:
            question = TestQuestion.objects.get(id=question_id, question_type='problem_solving')
        except TestQuestion.DoesNotExist:
            raise ValueError("Problem solving question not found")
        
        # Use ML model to evaluate
        try:
            from .question_generator import QuestionGenerator
            qg = QuestionGenerator()
            
            evaluation = qg.assess_answer(
                question.question_text,
                question.expected_answer,
                answer_text,
                'problem_solving'
            )
            
            score = evaluation.get('score', 0)
            is_correct = evaluation.get('is_correct', False)
            feedback = evaluation.get('feedback', '')
            ml_confidence = evaluation.get('confidence', 0.5)
            
        except Exception as e:
            # Fallback: simple keyword matching
            score, is_correct, feedback = cls._fallback_evaluate(
                answer_text, question.expected_answer
            )
            ml_confidence = 0.3
        
        # Create or update submission
        submission, created = TestSubmission.objects.update_or_create(
            question=question,
            user=user,
            defaults={
                'answer_text': answer_text,
                'is_correct': is_correct,
                'score': score,
                'feedback': feedback,
                'time_taken_seconds': time_taken,
                'evaluated_by_ml': True,
                'ml_confidence': ml_confidence
            }
        )
        
        return submission
    
    @classmethod
    def _fallback_evaluate(cls, answer, expected):
        """Fallback evaluation using keyword matching. NEVER gives free marks."""
        if not answer or not answer.strip():
            return 0.0, False, "No answer provided."
        if not expected or not expected.strip():
            # No reference answer — can't evaluate, give 0
            return 0.0, False, "Could not evaluate answer (no reference provided)."

        # Extract meaningful keywords (>4 chars) from expected answer
        keywords = [w for w in expected.lower().split() if len(w) > 4]

        if not keywords:
            # Reference answer is too short to evaluate properly — partial credit only if they wrote something
            if len(answer.strip()) > 20:
                return 30.0, False, "Answer too short to evaluate accurately. Partial credit given."
            return 0.0, False, "Answer could not be evaluated — too brief."

        # Count matching keywords  
        matches = sum(1 for kw in keywords if kw in answer.lower())
        score = round((matches / len(keywords)) * 100, 1)
        is_correct = score >= 70
        feedback = f"Your answer matched {matches} out of {len(keywords)} key concepts."

        return score, is_correct, feedback
    
    @classmethod
    def calculate_test_score(cls, test_id):
        """
        Calculate overall test score.
        
        Score = (earned points from answered questions) / (total possible points for ALL questions)
        Unanswered questions count as 0 — no free marks.
        """
        try:
            test = GeneratedTest.objects.get(id=test_id)
        except GeneratedTest.DoesNotExist:
            raise ValueError("Test not found")

        # Total possible points = sum of ALL question points in the test
        all_questions = TestQuestion.objects.filter(test=test)
        total_possible_points = sum(q.points for q in all_questions)
        total_questions = all_questions.count()

        if total_questions == 0:
            return {'error': 'No questions in this test'}

        # Only submissions that were actually answered count
        submissions = TestSubmission.objects.filter(
            question__test=test,
            user=test.user
        )
        answered_count = submissions.count()

        # Earned points from answered questions only
        earned_points = 0
        for submission in submissions:
            if submission.score is not None:
                earned_points += (submission.score / 100.0) * submission.question.points

        # Score % = earned / total_possible (not earned / answered_points)
        # This means skipping a question is the same as getting it wrong
        overall_score = round((earned_points / total_possible_points * 100), 1) if total_possible_points > 0 else 0

        correct_answers = submissions.filter(is_correct=True).count()

        # Update test record
        test.score = overall_score
        test.is_completed = True
        test.save()

        return {
            'test_id': test_id,
            'overall_score': overall_score,
            'total_questions': total_questions,
            'answered_questions': answered_count,
            'unanswered_questions': total_questions - answered_count,
            'correct_answers': correct_answers,
            'total_possible_points': total_possible_points,
            'earned_points': round(earned_points, 2),
        }
    
    @classmethod
    def identify_weak_areas(cls, test_id):
        """
        Identify concepts with <70% accuracy
        
        Args:
            test_id: GeneratedTest ID
            
        Returns:
            list of weak concepts
        """
        try:
            test = GeneratedTest.objects.get(id=test_id)
        except GeneratedTest.DoesNotExist:
            raise ValueError("Test not found")
        
        # Group submissions by concept
        submissions = TestSubmission.objects.filter(
            question__test=test,
            user=test.user
        )
        
        concept_stats = {}
        
        for submission in submissions:
            concept = submission.question.concept
            
            if concept not in concept_stats:
                concept_stats[concept] = {'total': 0, 'correct': 0, 'scores': []}
            
            concept_stats[concept]['total'] += 1
            if submission.is_correct:
                concept_stats[concept]['correct'] += 1
            if submission.score is not None:
                concept_stats[concept]['scores'].append(submission.score)
        
        # Identify weak areas
        weak_areas = []
        
        for concept, stats in concept_stats.items():
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            if avg_score < 70 or accuracy < 70:
                weak_areas.append({
                    'concept': concept,
                    'accuracy': accuracy,
                    'average_score': avg_score,
                    'questions_count': stats['total']
                })
        
        # Update test weak concepts
        test.weak_concepts = [area['concept'] for area in weak_areas]
        test.save()
        
        return weak_areas
    
    @classmethod
    def prepare_ml_input(cls, test_id, session_id):
        """
        Prepare 13 features for ML difficulty predictor (v2)
        """
        from .monitoring_collector import MonitoringCollector
        from .models import StudySession, TestSubmission
        
        try:
            test = GeneratedTest.objects.get(id=test_id)
            session = StudySession.objects.get(id=session_id)
        except (GeneratedTest.DoesNotExist, StudySession.DoesNotExist):
            raise ValueError("Test or Session not found")
        
        # 1-8: Performance & Context
        submissions = TestSubmission.objects.filter(question__test=test, user=test.user)
        total_q = submissions.count()
        correct_q = submissions.filter(is_correct=True).count()
        accuracy = (correct_q / total_q * 100) if total_q > 0 else 0
        avg_time = submissions.aggregate(Avg('time_taken_seconds'))['time_taken_seconds__avg'] or 0
        
        # First attempt rate (we use accuracy as proxy in current schema)
        first_attempt_correct = accuracy
        
        # Sessions completed for this topic
        topic = test.content.topic if test.content else None
        sessions_completed = StudySession.objects.filter(
            user=test.user,
            content__topic=topic,
            is_completed=True
        ).count() if topic else 0
        
        # Score Trend
        prev_test = GeneratedTest.objects.filter(
            user=test.user,
            content__topic=topic,
            is_completed=True
        ).exclude(id=test.id).order_by('-completed_at').first()
        score_trend = accuracy - prev_test.score if prev_test else 0
        
        # 9-13: Behavioral Metrics
        session_metrics = MonitoringCollector.aggregate_metrics(session_id)
        engagement_score = session_metrics.get('engagement_score', 70.0)
        active_time_ratio = session_metrics.get('active_time_ratio', 0.8)
        
        # Rates
        duration_mins = max(session.study_duration_seconds / 60, 1)
        tab_switches = session_metrics.get('tab_switches', 0)
        tab_switch_rate = tab_switches / duration_mins
        
        interactions = sum(session_metrics.get('content_interactions', {}).values())
        interaction_density = interactions / duration_mins
        
        # Session length deviation (Actual vs Expected)
        # Assuming 10 mins as baseline if not specified in content
        expected_duration = 600 
        actual_duration = session.study_duration_seconds
        session_length_dev = (actual_duration - expected_duration) / expected_duration
        session_length_dev = max(-1.0, min(1.0, session_length_dev))
        
        ml_input = {
            'accuracy': float(accuracy),
            'avg_time_per_question': float(avg_time),
            'first_attempt_correct': float(first_attempt_correct),
            'current_difficulty': int(test.difficulty_level),
            'sessions_completed': int(sessions_completed),
            'score_trend': float(score_trend),
            'mastery_level': float(min(accuracy / 100, 1.0)),
            'is_new_topic': 1 if sessions_completed <= 1 else 0,
            'engagement_score': float(engagement_score),
            'active_time_ratio': float(active_time_ratio),
            'tab_switch_rate': float(tab_switch_rate),
            'interaction_density': float(interaction_density),
            'session_length_dev': float(session_length_dev)
        }
        
        return ml_input

    
    @classmethod
    def generate_difficulty_feedback(cls, current_difficulty, next_difficulty):
        """
        Generate feedback message for difficulty level change
        
        Args:
            current_difficulty: int (1-3)
            next_difficulty: int (1-3)
            
        Returns:
            dict with feedback message
        """
        difficulty_names = {
            1: 'Easy',
            2: 'Medium',
            3: 'Hard'
        }
        
        if next_difficulty > current_difficulty:
            message = f"Great progress! Moving from {difficulty_names[current_difficulty]} to {difficulty_names[next_difficulty]} difficulty."
        elif next_difficulty < current_difficulty:
            message = f"Let's review the basics. Moving from {difficulty_names[current_difficulty]} to {difficulty_names[next_difficulty]} difficulty."
        else:
            message = f"Staying at {difficulty_names[current_difficulty]} difficulty. Keep practicing!"
        
        return {
            'message': message,
            'current_difficulty': current_difficulty,
            'next_difficulty': next_difficulty,
            'change': next_difficulty - current_difficulty
        }
