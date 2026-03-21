"""
Simple test runner for bug exploration tests
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning.settings')
django.setup()

# Import test classes
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

def run_tests():
    """Run all bug exploration tests and report results."""
    print("\n" + "="*80)
    print("BUG CONDITION EXPLORATION TESTS - VERIFICATION AFTER FIX")
    print("These tests SHOULD PASS on fixed code to confirm bugs are resolved")
    print("="*80 + "\n")
    
    results = []
    
    # Test 1: 429 Error - Retry Logic
    print("\n[Test 1] Testing 429 Error Handling (Retry Logic)...")
    try:
        test = Test429ErrorBugCondition()
        test.test_no_retry_on_429_error()
        print("  ✅ EXPECTED: Test PASSED (retry logic works)")
        results.append(("Test 1: 429 Error Retry", "PASSED", "Retry logic confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 1: 429 Error Retry", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 1: 429 Error Retry", "ERROR", str(e)[:100]))
    
    # Test 2: API Key Reload
    print("\n[Test 2] Testing API Key Reload...")
    try:
        test = TestAPIKeyReloadBugCondition()
        test.test_api_key_not_reloaded_after_env_change()
        print("  ✅ EXPECTED: Test PASSED (API key reload works)")
        results.append(("Test 2: API Key Reload", "PASSED", "API key reload confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 2: API Key Reload", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 2: API Key Reload", "ERROR", str(e)[:100]))
    
    # Test 3: Rate Limiting
    print("\n[Test 3] Testing Rate Limiting...")
    try:
        test = TestRateLimitingBugCondition()
        test.test_no_rate_limiting_between_calls()
        print("  ✅ EXPECTED: Test PASSED (rate limiting works)")
        results.append(("Test 3: Rate Limiting", "PASSED", "Rate limiting confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 3: Rate Limiting", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 3: Rate Limiting", "ERROR", str(e)[:100]))
    
    # Test 4: Error Messages
    print("\n[Test 4] Testing Error Messages...")
    try:
        test = TestErrorMessageBugCondition()
        test.test_raw_error_messages_not_user_friendly()
        print("  ✅ EXPECTED: Test PASSED (user-friendly error messages work)")
        results.append(("Test 4: Error Messages", "PASSED", "User-friendly errors confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 4: Error Messages", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 4: Error Messages", "ERROR", str(e)[:100]))
    
    # Test 5: Long Transcript Summarization
    print("\n[Test 5] Testing Long Transcript Handling...")
    try:
        test = TestLongTranscriptBugCondition()
        test.test_long_transcript_not_summarized()
        print("  ✅ EXPECTED: Test PASSED (transcript summarization works)")
        results.append(("Test 5: Long Transcript", "PASSED", "Summarization confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 5: Long Transcript", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 5: Long Transcript", "ERROR", str(e)[:100]))
    
    # Test 6: Transcript Extraction Failure
    print("\n[Test 6] Testing Transcript Extraction Failure Handling...")
    try:
        test = TestTranscriptExtractionFailureBugCondition()
        test.test_transcript_failure_blocks_workflow()
        print("  ✅ EXPECTED: Test PASSED (fallback mechanism works)")
        results.append(("Test 6: Transcript Failure", "PASSED", "Fallback confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 6: Transcript Failure", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 6: Transcript Failure", "ERROR", str(e)[:100]))
    
    # Test 7: Session Name Fallback
    print("\n[Test 7] Testing Session Name Fallback...")
    try:
        test = TestSessionNameFallbackBugCondition()
        test.test_no_session_name_fallback()
        print("  ✅ EXPECTED: Test PASSED (session name fallback works)")
        results.append(("Test 7: Session Name Fallback", "PASSED", "Fallback confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 7: Session Name Fallback", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 7: Session Name Fallback", "ERROR", str(e)[:100]))
    
    # Test 8: Ollama Integration
    print("\n[Test 8] Testing Ollama Integration...")
    try:
        test = TestOllamaIntegrationBugCondition()
        test.test_no_ollama_integration()
        print("  ✅ EXPECTED: Test PASSED (Ollama integration works)")
        results.append(("Test 8: Ollama Integration", "PASSED", "Ollama integration confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 8: Ollama Integration", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 8: Ollama Integration", "ERROR", str(e)[:100]))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, status, _ in results if status == "PASSED")
    failed_count = sum(1 for _, status, _ in results if status == "FAILED")
    error_count = sum(1 for _, status, _ in results if status == "ERROR")
    
    for test_name, status, message in results:
        status_symbol = "✅" if status == "PASSED" else ("❌" if status == "FAILED" else "⚠️")
        print(f"{status_symbol} {test_name}: {status}")
        if message:
            print(f"   → {message}")
    
    print(f"\nTotal: {len(results)} tests")
    print(f"  ✅ Passed (fixes confirmed): {passed_count}")
    print(f"  ❌ Failed (fixes incomplete): {failed_count}")
    print(f"  ⚠️  Errors: {error_count}")
    
    print("\n" + "="*80)
    if passed_count == len(results):
        print("✅ ALL TESTS PASSED - All bugs are fixed!")
    elif passed_count > 0:
        print(f"⚠️  {passed_count}/{len(results)} fixes confirmed, {failed_count} still need work")
    else:
        print("❌ NO TESTS PASSED - Fixes may not be working correctly")
    print("="*80 + "\n")

if __name__ == '__main__':
    run_tests()
