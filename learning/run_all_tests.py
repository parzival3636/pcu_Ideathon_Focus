"""
Comprehensive Test Runner for Gemini MCQ Service
Runs unit tests, integration tests, and verification tests
"""
import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning.settings')
django.setup()

# Import test classes
from adaptive_learning.tests.test_helper_functions import (
    TestReloadApiKey,
    TestRateLimitDelay,
    TestCallGeminiWithRetry,
    TestSummarizeTranscriptWithOllama,
    TestGenerateQuestionsFromSessionName
)

from adaptive_learning.tests.test_gemini_preservation import (
    TestSuccessfulMCQGenerationPreservation,
    TestTopicBasedGenerationPreservation,
    TestDatabaseOperationsPreservation,
    TestErrorHandlingPreservation
)

from adaptive_learning.tests.test_gemini_429_bug_exploration import (
    Test429ErrorBugCondition,
    TestAPIKeyReloadBugCondition,
    TestRateLimitingBugCondition,
    TestErrorMessageBugCondition,
    TestLongTranscriptBugCondition,
    TestTranscriptExtractionFailureBugCondition,
    TestSessionNameFallbackBugCondition,
    TestOllamaIntegrationBugCondition
)


def run_test_method(test_class, method_name, description):
    """Run a single test method and return result."""
    try:
        test_instance = test_class()
        method = getattr(test_instance, method_name)
        method()
        return ("PASSED", None)
    except AssertionError as e:
        return ("FAILED", str(e)[:200])
    except Exception as e:
        return ("ERROR", str(e)[:200])


def run_unit_tests():
    """Run all unit tests for helper functions."""
    print("\n" + "="*80)
    print("UNIT TESTS - Helper Functions")
    print("="*80 + "\n")
    
    results = []
    
    # Test _reload_api_key
    print("[Unit Test 1] Testing _reload_api_key()...")
    status, msg = run_test_method(
        TestReloadApiKey,
        "test_reload_api_key_updates_global_variables",
        "API key reload updates global variables"
    )
    print(f"  [{'PASS' if status == 'PASSED' else 'FAIL'}] {status}: {msg if msg else 'API key reload works'}")
    results.append(("_reload_api_key", status, msg))
    
    # Test _rate_limit_delay
    print("\n[Unit Test 2] Testing _rate_limit_delay()...")
    status, msg = run_test_method(
        TestRateLimitDelay,
        "test_rate_limit_enforces_one_second_delay",
        "Rate limiting enforces 1-second delay"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Rate limiting works'}")
    results.append(("_rate_limit_delay", status, msg))
    
    # Test _call_gemini_with_retry - successful call
    print("\n[Unit Test 3] Testing _call_gemini_with_retry() - successful call...")
    status, msg = run_test_method(
        TestCallGeminiWithRetry,
        "test_successful_call_returns_immediately",
        "Successful calls bypass retry logic"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Successful calls work'}")
    results.append(("_call_gemini_with_retry (success)", status, msg))
    
    # Test _call_gemini_with_retry - 429 retry
    print("\n[Unit Test 4] Testing _call_gemini_with_retry() - 429 retry...")
    status, msg = run_test_method(
        TestCallGeminiWithRetry,
        "test_429_error_triggers_retry_with_exponential_backoff",
        "429 errors trigger exponential backoff"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else '429 retry works'}")
    results.append(("_call_gemini_with_retry (429)", status, msg))
    
    # Test _call_gemini_with_retry - API key reload
    print("\n[Unit Test 5] Testing _call_gemini_with_retry() - API key reload...")
    status, msg = run_test_method(
        TestCallGeminiWithRetry,
        "test_429_error_reloads_api_key_before_retry",
        "API key reloaded before retry"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'API key reload works'}")
    results.append(("_call_gemini_with_retry (reload)", status, msg))
    
    # Test _call_gemini_with_retry - user-friendly error
    print("\n[Unit Test 6] Testing _call_gemini_with_retry() - user-friendly error...")
    status, msg = run_test_method(
        TestCallGeminiWithRetry,
        "test_all_retries_exhausted_raises_user_friendly_error",
        "User-friendly error after retries exhausted"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'User-friendly errors work'}")
    results.append(("_call_gemini_with_retry (error)", status, msg))
    
    # Test _call_gemini_with_retry - non-429 error
    print("\n[Unit Test 7] Testing _call_gemini_with_retry() - non-429 error...")
    status, msg = run_test_method(
        TestCallGeminiWithRetry,
        "test_non_429_error_raises_immediately",
        "Non-429 errors raise immediately"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Non-429 errors work'}")
    results.append(("_call_gemini_with_retry (non-429)", status, msg))
    
    # Test _summarize_transcript_with_ollama - short transcript
    print("\n[Unit Test 8] Testing _summarize_transcript_with_ollama() - short transcript...")
    status, msg = run_test_method(
        TestSummarizeTranscriptWithOllama,
        "test_short_transcript_returned_unchanged",
        "Short transcripts returned unchanged"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Short transcripts work'}")
    results.append(("_summarize_transcript (short)", status, msg))
    
    # Test _summarize_transcript_with_ollama - Ollama call
    print("\n[Unit Test 9] Testing _summarize_transcript_with_ollama() - Ollama call...")
    status, msg = run_test_method(
        TestSummarizeTranscriptWithOllama,
        "test_long_transcript_calls_ollama_api",
        "Long transcripts call Ollama API"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Ollama call works'}")
    results.append(("_summarize_transcript (Ollama)", status, msg))
    
    # Test _summarize_transcript_with_ollama - fallback
    print("\n[Unit Test 10] Testing _summarize_transcript_with_ollama() - fallback...")
    status, msg = run_test_method(
        TestSummarizeTranscriptWithOllama,
        "test_ollama_unavailable_falls_back_to_truncation",
        "Ollama unavailable triggers truncation"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Truncation fallback works'}")
    results.append(("_summarize_transcript (fallback)", status, msg))
    
    # Test _generate_questions_from_session_name
    print("\n[Unit Test 11] Testing _generate_questions_from_session_name()...")
    status, msg = run_test_method(
        TestGenerateQuestionsFromSessionName,
        "test_session_name_fallback_generates_valid_questions",
        "Session name fallback generates questions"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Session name fallback works'}")
    results.append(("_generate_questions_from_session_name", status, msg))
    
    return results


def run_preservation_tests():
    """Run preservation tests to ensure no regressions."""
    print("\n" + "="*80)
    print("PRESERVATION TESTS - Verify No Regressions")
    print("="*80 + "\n")
    
    results = []
    
    # Test successful MCQ generation
    print("[Preservation 1] Testing successful MCQ generation...")
    status, msg = run_test_method(
        TestSuccessfulMCQGenerationPreservation,
        "test_successful_api_response_generates_mcqs",
        "Successful API responses work"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'MCQ generation preserved'}")
    results.append(("Successful MCQ generation", status, msg))
    
    # Test JSON parsing
    print("\n[Preservation 2] Testing JSON parsing...")
    status, msg = run_test_method(
        TestSuccessfulMCQGenerationPreservation,
        "test_json_parsing_handles_markdown_format",
        "JSON parsing handles markdown"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'JSON parsing preserved'}")
    results.append(("JSON parsing", status, msg))
    
    # Test user state configuration
    print("\n[Preservation 3] Testing user state configuration...")
    status, msg = run_test_method(
        TestSuccessfulMCQGenerationPreservation,
        "test_user_state_configuration_produces_correct_counts",
        "User state configuration works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'User state config preserved'}")
    results.append(("User state configuration", status, msg))
    
    # Test short transcript handling
    print("\n[Preservation 4] Testing short transcript handling...")
    status, msg = run_test_method(
        TestSuccessfulMCQGenerationPreservation,
        "test_short_transcript_passed_directly",
        "Short transcripts passed directly"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Short transcript preserved'}")
    results.append(("Short transcript handling", status, msg))
    
    # Test topic-based generation
    print("\n[Preservation 5] Testing topic-based generation...")
    status, msg = run_test_method(
        TestTopicBasedGenerationPreservation,
        "test_topic_based_generation_works",
        "Topic-based generation works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Topic generation preserved'}")
    results.append(("Topic-based generation", status, msg))
    
    # Test Test 2 generation
    print("\n[Preservation 6] Testing Test 2 generation structure...")
    status, msg = run_test_method(
        TestTopicBasedGenerationPreservation,
        "test_test2_generation_structure",
        "Test 2 structure correct"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Test 2 structure preserved'}")
    results.append(("Test 2 generation", status, msg))
    
    # Test assessment creation
    print("\n[Preservation 7] Testing assessment creation...")
    status, msg = run_test_method(
        TestDatabaseOperationsPreservation,
        "test_assessment_creation_from_session",
        "Assessment creation works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Assessment creation preserved'}")
    results.append(("Assessment creation", status, msg))
    
    # Test error handling
    print("\n[Preservation 8] Testing non-429 error handling...")
    status, msg = run_test_method(
        TestErrorHandlingPreservation,
        "test_non_429_errors_handled_gracefully",
        "Non-429 errors handled"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Error handling preserved'}")
    results.append(("Non-429 error handling", status, msg))
    
    return results


def run_bug_verification_tests():
    """Run bug verification tests to confirm fixes work."""
    print("\n" + "="*80)
    print("BUG VERIFICATION TESTS - Confirm Fixes Work")
    print("="*80 + "\n")
    
    results = []
    
    # Test 429 error handling
    print("[Verification 1] Testing 429 error handling...")
    status, msg = run_test_method(
        Test429ErrorBugCondition,
        "test_no_retry_on_429_error",
        "429 retry logic works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else '429 handling fixed'}")
    results.append(("429 error handling", status, msg))
    
    # Test API key reload
    print("\n[Verification 2] Testing API key reload...")
    status, msg = run_test_method(
        TestAPIKeyReloadBugCondition,
        "test_api_key_not_reloaded_after_env_change",
        "API key reload works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'API key reload fixed'}")
    results.append(("API key reload", status, msg))
    
    # Test rate limiting
    print("\n[Verification 3] Testing rate limiting...")
    status, msg = run_test_method(
        TestRateLimitingBugCondition,
        "test_no_rate_limiting_between_calls",
        "Rate limiting works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Rate limiting fixed'}")
    results.append(("Rate limiting", status, msg))
    
    # Test error messages
    print("\n[Verification 4] Testing error messages...")
    status, msg = run_test_method(
        TestErrorMessageBugCondition,
        "test_raw_error_messages_not_user_friendly",
        "User-friendly error messages work"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Error messages fixed'}")
    results.append(("Error messages", status, msg))
    
    # Test long transcript handling
    print("\n[Verification 5] Testing long transcript handling...")
    status, msg = run_test_method(
        TestLongTranscriptBugCondition,
        "test_long_transcript_not_summarized",
        "Transcript summarization works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Long transcript fixed'}")
    results.append(("Long transcript handling", status, msg))
    
    # Test transcript extraction failure
    print("\n[Verification 6] Testing transcript extraction failure...")
    status, msg = run_test_method(
        TestTranscriptExtractionFailureBugCondition,
        "test_transcript_failure_blocks_workflow",
        "Fallback mechanism works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Transcript failure fixed'}")
    results.append(("Transcript extraction failure", status, msg))
    
    # Test session name fallback
    print("\n[Verification 7] Testing session name fallback...")
    status, msg = run_test_method(
        TestSessionNameFallbackBugCondition,
        "test_no_session_name_fallback",
        "Session name fallback works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Session name fallback fixed'}")
    results.append(("Session name fallback", status, msg))
    
    # Test Ollama integration
    print("\n[Verification 8] Testing Ollama integration...")
    status, msg = run_test_method(
        TestOllamaIntegrationBugCondition,
        "test_no_ollama_integration",
        "Ollama integration works"
    )
    print(f"  {'[PASS]' if status == 'PASSED' else '[FAIL]'} {status}: {msg if msg else 'Ollama integration fixed'}")
    results.append(("Ollama integration", status, msg))
    
    return results


def print_summary(unit_results, preservation_results, verification_results):
    """Print comprehensive test summary."""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*80 + "\n")
    
    all_results = [
        ("Unit Tests", unit_results),
        ("Preservation Tests", preservation_results),
        ("Bug Verification Tests", verification_results)
    ]
    
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_tests = 0
    
    for category, results in all_results:
        passed = sum(1 for _, status, _ in results if status == "PASSED")
        failed = sum(1 for _, status, _ in results if status == "FAILED")
        errors = sum(1 for _, status, _ in results if status == "ERROR")
        total = len(results)
        
        total_passed += passed
        total_failed += failed
        total_errors += errors
        total_tests += total
        
        print(f"\n{category}:")
        print(f"  [PASS] Passed: {passed}/{total}")
        print(f"  [FAIL] Failed: {failed}/{total}")
        print(f"  [WARN]  Errors: {errors}/{total}")
    
    print(f"\n{'='*80}")
    print(f"OVERALL RESULTS:")
    print(f"  Total Tests: {total_tests}")
    print(f"  [PASS] Passed: {total_passed} ({total_passed*100//total_tests if total_tests > 0 else 0}%)")
    print(f"  [FAIL] Failed: {total_failed} ({total_failed*100//total_tests if total_tests > 0 else 0}%)")
    print(f"  [WARN]  Errors: {total_errors} ({total_errors*100//total_tests if total_tests > 0 else 0}%)")
    print(f"{'='*80}\n")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED! The bugfix is complete and working correctly.")
    elif total_passed >= total_tests * 0.8:
        print("[PASS] Most tests passed. Minor issues may need attention.")
    elif total_passed >= total_tests * 0.5:
        print("[WARN]  Some tests failed. Review failed tests and fix issues.")
    else:
        print("[FAIL] Many tests failed. Significant work needed.")
    
    print()


def main():
    """Run all tests and report results."""
    print("\n" + "="*80)
    print("GEMINI MCQ SERVICE - COMPREHENSIVE TEST SUITE")
    print("Testing: Unit Tests, Preservation Tests, Bug Verification Tests")
    print("="*80)
    
    start_time = time.time()
    
    # Run all test suites
    unit_results = run_unit_tests()
    preservation_results = run_preservation_tests()
    verification_results = run_bug_verification_tests()
    
    # Print summary
    print_summary(unit_results, preservation_results, verification_results)
    
    elapsed = time.time() - start_time
    print(f"Total execution time: {elapsed:.2f} seconds\n")


if __name__ == '__main__':
    main()

