"""
Preservation Property Tests for Gemini MCQ Service

These tests MUST PASS on unfixed code to establish baseline behavior.
They verify that successful API responses continue to work correctly after the fix.

Expected to PASS on unfixed code because:
1. Successful API responses generate MCQs correctly
2. JSON parsing logic handles various response formats
3. User state configuration produces expected question counts
4. Database operations create correct Assessment and Question objects
5. Transcripts <8000 chars are passed directly without modification
6. Successful transcript extractions don't trigger alternative methods
"""
from unittest.mock import Mock, patch, MagicMock
import json


class TestSuccessfulMCQGenerationPreservation:
    """Test that successful MCQ generation behavior is preserved."""
    
    def test_successful_api_response_generates_mcqs(self):
        """
        Property 2.1: Successful API responses generate MCQs correctly.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.text = '''[{
            "question": "What is Python?",
            "options": {"A": "A programming language", "B": "A snake", "C": "A tool", "D": "A framework"},
            "answer": "A",
            "explanation": "Python is a high-level programming language",
            "concept": "Python Basics"
        }, {
            "question": "What is a variable?",
            "options": {"A": "A constant", "B": "A storage location", "C": "A function", "D": "A class"},
            "answer": "B",
            "explanation": "A variable is a storage location for data",
            "concept": "Variables"
        }]'''
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            # Call the function
            result = gemini_mcq_service.generate_adaptive_mcqs("test content", user_state=4)
            
            # Verify successful generation
            assert result.get('success') == True, "Expected successful MCQ generation"
            assert len(result.get('questions', [])) == 2, "Expected 2 questions"
            assert result['questions'][0]['question'] == "What is Python?"
            assert result['questions'][0]['answer'] == "A"
            assert result['questions'][1]['concept'] == "Variables"
    
    def test_json_parsing_handles_markdown_format(self):
        """
        Property 2.2: JSON parsing handles markdown-wrapped responses.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Mock API response with markdown formatting
        mock_response = Mock()
        mock_response.text = '''```json
[{
    "question": "Test question?",
    "options": {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"},
    "answer": "A",
    "explanation": "Test explanation",
    "concept": "Test Concept"
}]
```'''
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            result = gemini_mcq_service.generate_adaptive_mcqs("test content", user_state=4)
            
            # Verify JSON parsing works
            assert result.get('success') == True
            assert len(result.get('questions', [])) == 1
            assert result['questions'][0]['question'] == "Test question?"
    
    def test_user_state_configuration_produces_correct_counts(self):
        """
        Property 2.3: User state configuration produces expected question counts.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Test different user states
        test_cases = [
            (1, 20, "confused"),   # State 1: confused - 20 easy questions
            (2, 20, "bored"),      # State 2: bored - 20 hard questions
            (3, 10, "overloaded"), # State 3: overloaded - 10 easy questions
            (4, 20, "focused"),    # State 4: focused - 20 progressive questions
        ]
        
        for user_state, expected_count, expected_label in test_cases:
            # Mock API response with correct number of questions
            questions = []
            for i in range(expected_count):
                questions.append({
                    "question": f"Question {i+1}?",
                    "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                    "answer": "A",
                    "explanation": "Test",
                    "concept": "Test"
                })
            
            mock_response = Mock()
            mock_response.text = json.dumps(questions)
            
            with patch.object(gemini_mcq_service, 'model') as mock_model:
                mock_model.generate_content.return_value = mock_response
                
                result = gemini_mcq_service.generate_adaptive_mcqs("test content", user_state=user_state)
                
                # Verify user state configuration
                assert result.get('success') == True
                assert result.get('user_state') == expected_label
                assert result.get('num_questions') == expected_count
    
    def test_short_transcript_passed_directly(self):
        """
        Property 2.4: Transcripts <8000 chars are passed directly without modification.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Create a short transcript
        short_transcript = "A" * 5000
        
        # Mock API response
        mock_response = Mock()
        mock_response.text = '''[{
            "question": "Test?",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "answer": "A",
            "explanation": "Test",
            "concept": "Test"
        }]'''
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            # Call process_content_and_generate_mcqs
            result = gemini_mcq_service.process_content_and_generate_mcqs(short_transcript, user_state=4)
            
            # Verify it was processed successfully
            assert result.get('success') == True
            assert 'extracted_content' in result
            
            # Verify the model was called (transcript was processed)
            assert mock_model.generate_content.called


class TestTopicBasedGenerationPreservation:
    """Test that topic-based generation behavior is preserved."""
    
    def test_topic_based_generation_works(self):
        """
        Property 2.5: Topic-based generation produces valid questions.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Mock API response
        mock_response = Mock()
        mock_response.text = '''[{
            "question": "What is Python used for?",
            "options": {"A": "Web development", "B": "Only games", "C": "Only AI", "D": "Only scripts"},
            "answer": "A",
            "explanation": "Python is versatile and used for web development, AI, data science, and more",
            "concept": "Python Applications",
            "difficulty_level": "intermediate"
        }]'''
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            # Call topic-based generation
            result = gemini_mcq_service.generate_questions_from_topic("Python", user_state=4)
            
            # Verify successful generation
            assert result.get('success') == True
            assert result.get('topic') == "Python"
            assert len(result.get('questions', [])) == 1
            assert result['questions'][0]['concept'] == "Python Applications"
    
    def test_test2_generation_structure(self):
        """
        Property 2.6: Test 2 generation produces 15 easier + 5 harder questions.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Mock API response with 20 questions
        questions = []
        for i in range(15):
            questions.append({
                "question": f"Easy question {i+1}?",
                "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                "answer": "A",
                "explanation": "Easy explanation",
                "concept": "Basic Concept",
                "difficulty_level": "easy"
            })
        for i in range(5):
            questions.append({
                "question": f"Hard question {i+1}?",
                "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                "answer": "A",
                "explanation": "Hard explanation",
                "concept": "Advanced Concept",
                "difficulty_level": "hard"
            })
        
        mock_response = Mock()
        mock_response.text = json.dumps(questions)
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            mock_model.generate_content.return_value = mock_response
            
            # Call Test 2 generation
            result = gemini_mcq_service.generate_test2_questions(
                topic="Python",
                user_state=4,
                weak_concepts={"Variables", "Functions"},
                score=65.0
            )
            
            # Verify structure
            assert result.get('success') == True
            assert result.get('num_questions') == 20
            assert result.get('difficulty') == "adaptive"


class TestDatabaseOperationsPreservation:
    """Test that database operations are preserved."""
    
    def test_assessment_creation_from_session(self):
        """
        Property 2.7: Assessment creation works with valid transcript.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Mock the entire process_content_and_generate_mcqs function
        mock_result = {
            "success": True,
            "num_questions": 1,
            "difficulty": "intermediate",
            "questions": [{
                "question": "Test question?",
                "options": {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"},
                "answer": "A",
                "explanation": "Test explanation",
                "concept": "Test Concept"
            }],
            "extracted_content": "Test content"
        }
        
        with patch.object(gemini_mcq_service, 'process_content_and_generate_mcqs') as mock_process:
            mock_process.return_value = mock_result
            
            # Mock Django models - import from adaptive_learning.models
            with patch('adaptive_learning.models.StudySession') as MockSession:
                with patch('adaptive_learning.models.Assessment') as MockAssessment:
                    with patch('adaptive_learning.models.Question') as MockQuestion:
                        # Mock session
                        mock_session = Mock()
                        mock_session.workspace_name = "Python Programming"
                        MockSession.objects.get.return_value = mock_session
                        
                        # Mock content with transcript
                        mock_content = Mock()
                        mock_content.transcript = "This is a test transcript about Python programming."
                        
                        # Mock Assessment creation
                        mock_assessment = Mock()
                        mock_assessment.id = 1
                        MockAssessment.objects.create.return_value = mock_assessment
                        
                        # Call create_assessment_from_session
                        mock_user = Mock()
                        result = gemini_mcq_service.create_assessment_from_session(
                            session_id=1,
                            user=mock_user,
                            content=mock_content
                        )
                        
                        # Verify assessment was created
                        assert result is not None
                        assert result.id == 1
                        assert MockAssessment.objects.create.called
                        assert MockQuestion.objects.create.called


class TestErrorHandlingPreservation:
    """Test that non-429 error handling is preserved."""
    
    def test_non_429_errors_handled_gracefully(self):
        """
        Property 2.8: Non-429 errors are handled with existing error handling.
        
        EXPECTED: Test PASSES on unfixed code (baseline behavior).
        """
        from adaptive_learning import gemini_mcq_service
        
        # Mock a non-429 error (e.g., network error)
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            mock_model.generate_content.side_effect = Exception("Network error")
            
            # Call the function
            result = gemini_mcq_service.generate_adaptive_mcqs("test content", user_state=4)
            
            # Verify error is handled
            assert result.get('success') == False
            assert 'error' in result
            assert result.get('questions', []) == []
