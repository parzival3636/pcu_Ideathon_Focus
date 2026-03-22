"""
Unit Tests for Helper Functions in Gemini MCQ Service

Tests all helper functions with reduced example counts for faster execution:
- _reload_api_key
- _call_gemini_with_retry
- _rate_limit_delay
- _summarize_transcript_with_ollama
- _generate_questions_from_session_name
"""
from unittest.mock import Mock, patch, MagicMock, call
import time
import json
import pytest


class TestReloadApiKey:
    """Test _reload_api_key() function."""
    
    def test_reload_api_key_updates_global_variables(self):
        """Test that _reload_api_key correctly reads from Django settings and reconfigures genai."""
        from adaptive_learning import gemini_mcq_service
        
        # Mock Django settings
        with patch('adaptive_learning.gemini_mcq_service.settings') as mock_settings:
            with patch('adaptive_learning.gemini_mcq_service.genai') as mock_genai:
                # Set a new API key
                mock_settings.GEMINI_API_KEY = "new_test_api_key_12345"
                
                # Call reload
                gemini_mcq_service._reload_api_key()
                
                # Verify genai.configure was called with new key
                mock_genai.configure.assert_called_with(api_key="new_test_api_key_12345")
                
                # Verify GenerativeModel was recreated
                mock_genai.GenerativeModel.assert_called_with("gemini-2.5-flash")
    
    def test_reload_api_key_uses_fallback_if_no_setting(self):
        """Test that _reload_api_key uses fallback key if GEMINI_API_KEY not in settings."""
        from adaptive_learning import gemini_mcq_service
        
        with patch('adaptive_learning.gemini_mcq_service.settings') as mock_settings:
            with patch('adaptive_learning.gemini_mcq_service.genai') as mock_genai:
                # Simulate missing GEMINI_API_KEY attribute
                mock_settings.GEMINI_API_KEY = None
                type(mock_settings).GEMINI_API_KEY = property(lambda self: None)
                
                # Mock getattr to return a dummy key
                with patch('adaptive_learning.gemini_mcq_service.getattr', return_value='dummy_key_for_testing'):
                    gemini_mcq_service._reload_api_key()
                    
                    # Verify fallback key was used
                    mock_genai.configure.assert_called()


class TestRateLimitDelay:
    """Test _rate_limit_delay() function."""
    
    def test_rate_limit_enforces_one_second_delay(self):
        """Test that _rate_limit_delay enforces minimum 1-second delay between calls."""
        from adaptive_learning import gemini_mcq_service
        
        # Reset the last call time
        gemini_mcq_service._last_api_call_time = 0
        
        # First call should not sleep (no previous call)
        start_time = time.time()
        gemini_mcq_service._rate_limit_delay()
        first_call_time = time.time() - start_time
        
        # First call should be very fast (no sleep needed)
        assert first_call_time < 0.1, "First call should not sleep"
        
        # Second call immediately after should sleep
        start_time = time.time()
        gemini_mcq_service._rate_limit_delay()
        second_call_time = time.time() - start_time
        
        # Second call should sleep for approximately 1 second
        assert second_call_time >= 0.9, f"Second call should sleep ~1s, but took {second_call_time}s"
        assert second_call_time < 1.2, f"Second call should sleep ~1s, but took {second_call_time}s"
    
    def test_rate_limit_no_delay_if_one_second_passed(self):
        """Test that _rate_limit_delay doesn't sleep if 1 second already passed."""
        from adaptive_learning import gemini_mcq_service
        
        # Set last call time to 2 seconds ago
        gemini_mcq_service._last_api_call_time = time.time() - 2.0
        
        # Call should not sleep
        start_time = time.time()
        gemini_mcq_service._rate_limit_delay()
        elapsed = time.time() - start_time
        
        # Should be very fast (no sleep)
        assert elapsed < 0.1, f"Should not sleep if 1s already passed, but took {elapsed}s"


class TestCallGeminiWithRetry:
    """Test _call_gemini_with_retry() function."""
    
    def test_successful_call_returns_immediately(self):
        """Test that successful API calls bypass retry logic."""
        from adaptive_learning import gemini_mcq_service
        
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Success"
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            with patch.object(gemini_mcq_service, '_rate_limit_delay'):
                mock_model.generate_content.return_value = mock_response
                
                # Call should succeed immediately
                result = gemini_mcq_service._call_gemini_with_retry("test prompt")
                
                # Verify only called once (no retries)
                assert mock_model.generate_content.call_count == 1
                assert result == mock_response
    
    def test_429_error_triggers_retry_with_exponential_backoff(self):
        """Test that 429 errors trigger retry with exponential backoff (2s, 4s, 8s)."""
        from adaptive_learning import gemini_mcq_service
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            with patch.object(gemini_mcq_service, '_rate_limit_delay'):
                with patch.object(gemini_mcq_service, '_reload_api_key'):
                    with patch('time.sleep') as mock_sleep:
                        # Mock 429 error on first 2 calls, then success
                        mock_model.generate_content.side_effect = [
                            Exception("429 rate limit exceeded"),
                            Exception("quota exhausted"),
                            Mock(text="Success")
                        ]
                        
                        # Call should retry and eventually succeed
                        result = gemini_mcq_service._call_gemini_with_retry("test prompt")
                        
                        # Verify retries happened
                        assert mock_model.generate_content.call_count == 3
                        
                        # Verify exponential backoff delays (2s, 4s)
                        assert mock_sleep.call_count == 2
                        mock_sleep.assert_any_call(2)
                        mock_sleep.assert_any_call(4)
    
    def test_429_error_reloads_api_key_before_retry(self):
        """Test that API key is reloaded before each retry attempt."""
        from adaptive_learning import gemini_mcq_service
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            with patch.object(gemini_mcq_service, '_rate_limit_delay'):
                with patch.object(gemini_mcq_service, '_reload_api_key') as mock_reload:
                    with patch('time.sleep'):
                        # Mock 429 error on first call, then success
                        mock_model.generate_content.side_effect = [
                            Exception("429 rate limit exceeded"),
                            Mock(text="Success")
                        ]
                        
                        # Call should retry
                        gemini_mcq_service._call_gemini_with_retry("test prompt")
                        
                        # Verify API key was reloaded before retry
                        assert mock_reload.call_count == 1
    
    def test_all_retries_exhausted_raises_user_friendly_error(self):
        """Test that after all retries fail, a user-friendly error is raised."""
        from adaptive_learning import gemini_mcq_service
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            with patch.object(gemini_mcq_service, '_rate_limit_delay'):
                with patch.object(gemini_mcq_service, '_reload_api_key'):
                    with patch('time.sleep'):
                        # Mock 429 error on all calls
                        mock_model.generate_content.side_effect = Exception("429 rate limit exceeded")
                        
                        # Call should raise user-friendly error after 3 retries
                        with pytest.raises(Exception) as exc_info:
                            gemini_mcq_service._call_gemini_with_retry("test prompt", max_retries=3)
                        
                        # Verify user-friendly error message
                        assert "API quota exceeded" in str(exc_info.value)
                        assert "try again in a few minutes" in str(exc_info.value)
                        
                        # Verify 3 attempts were made
                        assert mock_model.generate_content.call_count == 3
    
    def test_non_429_error_raises_immediately(self):
        """Test that non-429 errors are raised immediately without retry."""
        from adaptive_learning import gemini_mcq_service
        
        with patch.object(gemini_mcq_service, 'model') as mock_model:
            with patch.object(gemini_mcq_service, '_rate_limit_delay'):
                # Mock a non-429 error
                mock_model.generate_content.side_effect = Exception("Network error")
                
                # Call should raise immediately
                with pytest.raises(Exception) as exc_info:
                    gemini_mcq_service._call_gemini_with_retry("test prompt")
                
                # Verify only called once (no retries)
                assert mock_model.generate_content.call_count == 1
                assert "Network error" in str(exc_info.value)


class TestSummarizeTranscriptWithOllama:
    """Test _summarize_transcript_with_ollama() function."""
    
    def test_short_transcript_returned_unchanged(self):
        """Test that transcripts <8000 chars are returned unchanged."""
        from adaptive_learning import gemini_mcq_service
        
        short_transcript = "A" * 5000
        
        result = gemini_mcq_service._summarize_transcript_with_ollama(short_transcript, max_length=8000)
        
        # Should return unchanged
        assert result == short_transcript
    
    def test_long_transcript_calls_ollama_api(self):
        """Test that transcripts >8000 chars call Ollama API for summarization."""
        from adaptive_learning import gemini_mcq_service
        import requests
        
        long_transcript = "A" * 10000
        
        with patch('requests.post') as mock_post:
            # Mock successful Ollama response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'response': 'This is a summarized transcript that is much shorter.'
            }
            mock_post.return_value = mock_response
            
            with patch('adaptive_learning.gemini_mcq_service.settings') as mock_settings:
                mock_settings.OLLAMA_ENDPOINT = 'http://localhost:11434/api/generate'
                mock_settings.OLLAMA_MODEL = 'llama3.2:3b'
                
                with patch('adaptive_learning.gemini_mcq_service.getattr', side_effect=lambda obj, attr, default: default):
                    result = gemini_mcq_service._summarize_transcript_with_ollama(long_transcript, max_length=8000)
                    
                    # Verify Ollama was called
                    assert mock_post.called
                    
                    # Verify result is the summary
                    assert result == 'This is a summarized transcript that is much shorter.'
    
    def test_ollama_unavailable_falls_back_to_truncation(self):
        """Test that Ollama unavailability triggers truncation fallback."""
        from adaptive_learning import gemini_mcq_service
        import requests
        
        long_transcript = "A" * 10000
        
        with patch('requests.post') as mock_post:
            # Mock connection error (Ollama not running)
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
            
            with patch('adaptive_learning.gemini_mcq_service.getattr', side_effect=lambda obj, attr, default: default):
                result = gemini_mcq_service._summarize_transcript_with_ollama(long_transcript, max_length=8000)
                
                # Verify result is truncated to 8000 chars
                assert len(result) == 8000
                assert result == long_transcript[:8000]
    
    def test_ollama_timeout_falls_back_to_truncation(self):
        """Test that Ollama timeout triggers truncation fallback."""
        from adaptive_learning import gemini_mcq_service
        import requests
        
        long_transcript = "B" * 10000
        
        with patch('requests.post') as mock_post:
            # Mock timeout error
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            with patch('adaptive_learning.gemini_mcq_service.getattr', side_effect=lambda obj, attr, default: default):
                result = gemini_mcq_service._summarize_transcript_with_ollama(long_transcript, max_length=8000)
                
                # Verify result is truncated
                assert len(result) == 8000
                assert result == long_transcript[:8000]
    
    def test_ollama_empty_response_falls_back_to_truncation(self):
        """Test that empty Ollama response triggers truncation fallback."""
        from adaptive_learning import gemini_mcq_service
        
        long_transcript = "C" * 10000
        
        with patch('requests.post') as mock_post:
            # Mock empty response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'response': ''}
            mock_post.return_value = mock_response
            
            with patch('adaptive_learning.gemini_mcq_service.getattr', side_effect=lambda obj, attr, default: default):
                result = gemini_mcq_service._summarize_transcript_with_ollama(long_transcript, max_length=8000)
                
                # Verify result is truncated
                assert len(result) == 8000
                assert result == long_transcript[:8000]


class TestGenerateQuestionsFromSessionName:
    """Test _generate_questions_from_session_name() function."""
    
    def test_session_name_fallback_generates_valid_questions(self):
        """Test that session name fallback generates valid questions."""
        from adaptive_learning import gemini_mcq_service
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.text = '''[{
            "question": "What is Python?",
            "options": {"A": "A language", "B": "A snake", "C": "A tool", "D": "A framework"},
            "answer": "A",
            "explanation": "Python is a programming language",
            "concept": "Python Basics",
            "difficulty_level": "easy"
        }]'''
        
        with patch.object(gemini_mcq_service, '_call_gemini_with_retry') as mock_call:
            mock_call.return_value = mock_response
            
            result = gemini_mcq_service._generate_questions_from_session_name("Python Programming", user_state=4)
            
            # Verify successful generation
            assert result.get('success') == True
            assert result.get('topic') == "Python Programming"
            assert len(result.get('questions', [])) == 1
            assert result.get('generation_method') == "session_name_fallback"
    
    def test_session_name_fallback_with_different_user_states(self):
        """Test session name fallback with various user states."""
        from adaptive_learning import gemini_mcq_service
        
        test_cases = [
            (1, 20),  # confused - 20 questions
            (2, 20),  # bored - 20 questions
            (3, 10),  # overloaded - 10 questions
            (4, 20),  # focused - 20 questions
        ]
        
        for user_state, expected_count in test_cases:
            # Mock API response with correct number of questions
            questions = []
            for i in range(expected_count):
                questions.append({
                    "question": f"Question {i+1}?",
                    "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                    "answer": "A",
                    "explanation": "Test",
                    "concept": "Test",
                    "difficulty_level": "easy"
                })
            
            mock_response = Mock()
            mock_response.text = json.dumps(questions)
            
            with patch.object(gemini_mcq_service, '_call_gemini_with_retry') as mock_call:
                mock_call.return_value = mock_response
                
                result = gemini_mcq_service._generate_questions_from_session_name(
                    "Test Topic",
                    user_state=user_state
                )
                
                # Verify correct number of questions
                assert result.get('success') == True
                assert result.get('num_questions') == expected_count
    
    def test_session_name_fallback_handles_api_errors(self):
        """Test that session name fallback handles API errors gracefully."""
        from adaptive_learning import gemini_mcq_service
        
        with patch.object(gemini_mcq_service, '_call_gemini_with_retry') as mock_call:
            # Mock API error
            mock_call.side_effect = Exception("API error")
            
            result = gemini_mcq_service._generate_questions_from_session_name("Test Topic", user_state=4)
            
            # Verify error is handled
            assert result.get('success') == False
            assert 'error' in result
            assert result.get('questions', []) == []
