"""
Simple test runner for preservation tests
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning.settings')
django.setup()

# Import test classes
from adaptive_learning.tests.test_gemini_preservation import (
    TestSuccessfulMCQGenerationPreservation,
    TestTopicBasedGenerationPreservation,
    TestDatabaseOperationsPreservation,
    TestErrorHandlingPreservation
)

def run_tests():
    """Run all preservation tests and report results."""
    print("\n" + "="*80)
    print("PRESERVATION PROPERTY TESTS")
    print("These tests SHOULD PASS on unfixed code to establish baseline behavior")
    print("="*80 + "\n")
    
    results = []
    
    # Test 1: Successful API Response
    print("\n[Test 1] Testing Successful API Response Preservation...")
    try:
        test = TestSuccessfulMCQGenerationPreservation()
        test.test_successful_api_response_generates_mcqs()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 1: Successful API Response", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 1: Successful API Response", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 1: Successful API Response", "ERROR", str(e)[:100]))
    
    # Test 2: JSON Parsing
    print("\n[Test 2] Testing JSON Parsing Preservation...")
    try:
        test = TestSuccessfulMCQGenerationPreservation()
        test.test_json_parsing_handles_markdown_format()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 2: JSON Parsing", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 2: JSON Parsing", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 2: JSON Parsing", "ERROR", str(e)[:100]))
    
    # Test 3: User State Configuration
    print("\n[Test 3] Testing User State Configuration Preservation...")
    try:
        test = TestSuccessfulMCQGenerationPreservation()
        test.test_user_state_configuration_produces_correct_counts()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 3: User State Config", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 3: User State Config", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 3: User State Config", "ERROR", str(e)[:100]))
    
    # Test 4: Short Transcript
    print("\n[Test 4] Testing Short Transcript Preservation...")
    try:
        test = TestSuccessfulMCQGenerationPreservation()
        test.test_short_transcript_passed_directly()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 4: Short Transcript", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 4: Short Transcript", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 4: Short Transcript", "ERROR", str(e)[:100]))
    
    # Test 5: Topic-Based Generation
    print("\n[Test 5] Testing Topic-Based Generation Preservation...")
    try:
        test = TestTopicBasedGenerationPreservation()
        test.test_topic_based_generation_works()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 5: Topic Generation", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 5: Topic Generation", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 5: Topic Generation", "ERROR", str(e)[:100]))
    
    # Test 6: Test2 Generation Structure
    print("\n[Test 6] Testing Test2 Generation Structure Preservation...")
    try:
        test = TestTopicBasedGenerationPreservation()
        test.test_test2_generation_structure()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 6: Test2 Structure", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 6: Test2 Structure", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 6: Test2 Structure", "ERROR", str(e)[:100]))
    
    # Test 7: Assessment Creation
    print("\n[Test 7] Testing Assessment Creation Preservation...")
    try:
        test = TestDatabaseOperationsPreservation()
        test.test_assessment_creation_from_session()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 7: Assessment Creation", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 7: Assessment Creation", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 7: Assessment Creation", "ERROR", str(e)[:100]))
    
    # Test 8: Non-429 Error Handling
    print("\n[Test 8] Testing Non-429 Error Handling Preservation...")
    try:
        test = TestErrorHandlingPreservation()
        test.test_non_429_errors_handled_gracefully()
        print("  ✅ EXPECTED: Test PASSED (baseline behavior preserved)")
        results.append(("Test 8: Non-429 Errors", "PASSED", "Baseline confirmed"))
    except AssertionError as e:
        print(f"  ❌ UNEXPECTED: Test FAILED - {str(e)[:100]}")
        results.append(("Test 8: Non-429 Errors", "FAILED", str(e)[:100]))
    except Exception as e:
        print(f"  ⚠️  ERROR: {str(e)[:100]}")
        results.append(("Test 8: Non-429 Errors", "ERROR", str(e)[:100]))
    
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
        if message and status != "PASSED":
            print(f"   → {message}")
    
    print(f"\nTotal: {len(results)} tests")
    print(f"  ✅ Passed (baseline confirmed): {passed_count}")
    print(f"  ❌ Failed (baseline broken): {failed_count}")
    print(f"  ⚠️  Errors: {error_count}")
    
    print("\n" + "="*80)
    if passed_count == len(results):
        print("✅ ALL TESTS PASSED - Baseline behavior confirmed!")
    elif passed_count > 0:
        print(f"⚠️  {passed_count}/{len(results)} tests passed - some baseline behavior may be broken")
    else:
        print("❌ NO TESTS PASSED - Baseline behavior is broken")
    print("="*80 + "\n")

if __name__ == '__main__':
    run_tests()
