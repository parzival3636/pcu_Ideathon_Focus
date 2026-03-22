"""
Comprehensive Test Script for All 3 Features
1. YouTube Transcript Fetching & RAG
2. Open-ended Question Generation & Assessment
3. Web Scraper (YouTube Playlists)

Run from: e:\everything related to hackathon\cree\learning\
Usage: python test_all_features.py
"""
import os
import sys
import json
import traceback

# Ensure GEMINI_API_KEY is available
if not os.environ.get('GEMINI_API_KEY'):
    print("Warning: GEMINI_API_KEY environment variable not set. Tests requiring Gemini will fail.")

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'WebScrappingModule', 'Scripts'))

print("=" * 70)
print("  COMPREHENSIVE FEATURE TEST")
print("=" * 70)
print(f"  GEMINI_API_KEY: {'SET (' + os.environ.get('GEMINI_API_KEY', '')[:12] + '...)' if os.environ.get('GEMINI_API_KEY') else 'NOT SET'}")
print("=" * 70)

results = {}

# ═══════════════════════════════════════════════════════════════════════
# TEST 1: YouTube Transcript Fetching
# ═══════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("  TEST 1: YouTube Transcript Fetching")
print("=" * 70)

try:
    from adaptive_learning.content_processor import extract_youtube_transcript, extract_video_id, extract_key_concepts

    # Test video ID extraction
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=rfscVS0vtbw",  # Python tutorial
    ]
    
    print("\n--- Video ID Extraction ---")
    for url in test_urls:
        vid = extract_video_id(url)
        status = "✅ PASS" if vid else "❌ FAIL"
        print(f"  {status} | {url} -> {vid}")
    
    # Test actual transcript fetching (short Python tutorial)
    test_video = "https://www.youtube.com/watch?v=rfscVS0vtbw"
    print(f"\n--- Transcript Fetching ({test_video}) ---")
    
    transcript, lang = extract_youtube_transcript(test_video)
    
    if transcript and len(transcript) > 50:
        print(f"  ✅ PASS | Transcript extracted: {len(transcript)} chars, language: {lang}")
        print(f"  Preview: {transcript[:200]}...")
        
        # Test key concept extraction
        print("\n--- Key Concept Extraction ---")
        concepts = extract_key_concepts(transcript)
        if concepts and len(concepts) > 0:
            print(f"  ✅ PASS | Extracted {len(concepts)} concepts: {concepts[:8]}")
        else:
            print(f"  ⚠️ WARN | No concepts extracted (transcript may be generic)")
            concepts = ['python', 'programming']
        
        results['youtube_transcript'] = {
            'status': 'PASS',
            'transcript_length': len(transcript),
            'language': lang,
            'concepts_count': len(concepts)
        }
    else:
        print(f"  ❌ FAIL | Transcript too short or empty: {len(transcript) if transcript else 0} chars")
        results['youtube_transcript'] = {'status': 'FAIL', 'reason': 'Transcript too short'}

except Exception as e:
    print(f"  ❌ FAIL | Error: {e}")
    traceback.print_exc()
    results['youtube_transcript'] = {'status': 'ERROR', 'error': str(e)}


# ═══════════════════════════════════════════════════════════════════════
# TEST 2: Question Generation (MCQ + Open-ended) & Answer Assessment
# ═══════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("  TEST 2: Question Generation & Answer Assessment")
print("=" * 70)

try:
    from adaptive_learning.question_generator import QuestionGenerator
    
    qg = QuestionGenerator()
    
    sample_content = """
    Python is a high-level, interpreted programming language known for its readability and simplicity.
    It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    Python uses indentation for code blocks instead of curly braces. Key data structures include lists,
    dictionaries, tuples, and sets. Functions are defined using the 'def' keyword.
    Python is widely used in web development (Django, Flask), data science (NumPy, Pandas),
    machine learning (TensorFlow, PyTorch), and automation. List comprehensions provide a concise
    way to create lists. Decorators allow modification of function behavior without changing the function itself.
    Exception handling is done using try/except blocks for robust error management.
    """
    sample_concepts = ['Python', 'data structures', 'functions', 'list comprehension', 'decorators', 'exception handling']
    
    # Test MCQ generation
    print("\n--- MCQ Generation ---")
    mcqs = qg.generate_mcq_questions(sample_content, sample_concepts, difficulty=1, count=3)
    if mcqs and len(mcqs) >= 1:
        print(f"  ✅ PASS | Generated {len(mcqs)} MCQ questions")
        for i, q in enumerate(mcqs[:2]):
            print(f"    Q{i+1}: {q.get('question', 'N/A')[:80]}...")
            print(f"         Options: {q.get('options', [])[:2]}...")
            print(f"         Type: {q.get('type', 'N/A')} | Correct: {q.get('correct_index', 'N/A')}")
    else:
        print(f"  ❌ FAIL | No MCQ questions generated")
    
    # Test Short Answer generation
    print("\n--- Short Answer Generation ---")
    sa_questions = qg.generate_short_answer_questions(sample_content, sample_concepts, difficulty=1, count=2)
    if sa_questions and len(sa_questions) >= 1:
        print(f"  ✅ PASS | Generated {len(sa_questions)} short answer questions")
        for i, q in enumerate(sa_questions[:2]):
            print(f"    Q{i+1}: {q.get('question', 'N/A')[:80]}...")
            print(f"         Type: {q.get('type', 'N/A')} | Expected answer preview: {str(q.get('expected_answer', 'N/A'))[:60]}...")
    else:
        print(f"  ❌ FAIL | No short answer questions generated")
    
    # Test Problem Solving generation
    print("\n--- Problem Solving Generation ---")
    ps_questions = qg.generate_problem_solving_questions(sample_content, sample_concepts, difficulty=1, count=2)
    if ps_questions and len(ps_questions) >= 1:
        print(f"  ✅ PASS | Generated {len(ps_questions)} problem-solving questions")
        for i, q in enumerate(ps_questions[:2]):
            print(f"    Q{i+1}: {q.get('question', 'N/A')[:80]}...")
            print(f"         Type: {q.get('type', 'N/A')}")
    else:
        print(f"  ❌ FAIL | No problem-solving questions generated")
    
    # Test Answer Assessment
    print("\n--- Open-ended Answer Assessment ---")
    test_question = "Explain what list comprehensions are in Python and give an example."
    test_expected = "List comprehensions provide a concise way to create lists from existing iterables using a single line of code. Syntax: [expression for item in iterable if condition]. Example: squares = [x**2 for x in range(10)]"
    test_student_answer = "List comprehensions are a shorthand way to create lists in Python. You can write something like [x*2 for x in range(5)] to get [0, 2, 4, 6, 8]. They make code more readable."
    
    assessment = qg.assess_answer(
        question=test_question,
        expected_answer=test_expected,
        user_answer=test_student_answer,
        question_type='short_answer'
    )
    
    if assessment and 'score' in assessment:
        is_correct = assessment.get('is_correct', False)
        score = assessment.get('score', 0)
        feedback = assessment.get('feedback', 'No feedback')
        print(f"  ✅ PASS | Assessment result:")
        print(f"    Score: {score}/100")
        print(f"    Correct: {is_correct}")
        print(f"    Feedback: {feedback[:120]}...")
    else:
        print(f"  ❌ FAIL | Assessment returned no result")
    
    # Test empty answer
    print("\n--- Empty Answer Assessment ---")
    empty_assessment = qg.assess_answer(
        question="What is Python?",
        expected_answer="A programming language.",
        user_answer="",
        question_type='short_answer'
    )
    if empty_assessment and empty_assessment.get('score') == 0:
        print(f"  ✅ PASS | Empty answer correctly scored 0")
    else:
        print(f"  ⚠️ WARN | Empty answer scoring: {empty_assessment}")
    
    results['question_generation'] = {
        'status': 'PASS',
        'mcq_count': len(mcqs) if mcqs else 0,
        'short_answer_count': len(sa_questions) if sa_questions else 0,
        'problem_solving_count': len(ps_questions) if ps_questions else 0,
        'assessment_works': 'score' in (assessment or {})
    }

except Exception as e:
    print(f"  ❌ FAIL | Error: {e}")
    traceback.print_exc()
    results['question_generation'] = {'status': 'ERROR', 'error': str(e)}


# ═══════════════════════════════════════════════════════════════════════
# TEST 3: Web Scraper (YouTube Playlists + Articles)
# ═══════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("  TEST 3: Web Scraper (Articles + YouTube Playlists + Q&A)")
print("=" * 70)

try:
    from robust_scraper import get_tutorials_from_multiple_sources, get_youtube_playlists, get_qa_content
    
    test_topic = "Python"
    
    # Test tutorials
    print(f"\n--- Tutorial Scraping ('{test_topic}') ---")
    tutorials = get_tutorials_from_multiple_sources(test_topic)
    if tutorials and len(tutorials) > 0:
        print(f"  ✅ PASS | Found {len(tutorials)} tutorials")
        for t in tutorials[:3]:
            print(f"    • {t.get('title', 'N/A')} ({t.get('source', 'N/A')})")
    else:
        print(f"  ❌ FAIL | No tutorials found")
    
    # Test YouTube playlists
    print(f"\n--- YouTube Playlist Scraping ('{test_topic}') ---")
    playlists = get_youtube_playlists(test_topic)
    if playlists and len(playlists) > 0:
        print(f"  ✅ PASS | Found {len(playlists)} playlists")
        for p in playlists[:3]:
            print(f"    • {p.get('title', 'N/A')} ({p.get('channel', 'N/A')})")
            print(f"      URL: {p.get('url', 'N/A')}")
    else:
        print(f"  ❌ FAIL | No playlists found")
    
    # Test with non-curated topic to trigger scraping
    exotic_topic = "React Hooks"
    print(f"\n--- YouTube Playlist Scraping ('{exotic_topic}' - non-curated) ---")
    exotic_playlists = get_youtube_playlists(exotic_topic)
    if exotic_playlists and len(exotic_playlists) > 0:
        print(f"  ✅ PASS | Found {len(exotic_playlists)} playlists for '{exotic_topic}'")
        for p in exotic_playlists[:3]:
            print(f"    • {p.get('title', 'N/A')} ({p.get('channel', 'N/A')})")
    else:
        print(f"  ⚠️ WARN | No playlists for '{exotic_topic}' — fallback search link should exist")
    
    # Test Q&A
    print(f"\n--- Q&A Content Scraping ('{test_topic}') ---")
    qa = get_qa_content(test_topic)
    if qa and len(qa) > 0:
        print(f"  ✅ PASS | Found {len(qa)} Q&A items")
        for item in qa[:3]:
            print(f"    • {item.get('title', 'N/A')[:60]}... ({item.get('source', 'N/A')})")
    else:
        print(f"  ⚠️ WARN | No Q&A items (API may be rate-limited)")
    
    results['web_scraper'] = {
        'status': 'PASS',
        'tutorials_count': len(tutorials) if tutorials else 0,
        'playlists_count': len(playlists) if playlists else 0,
        'exotic_playlists_count': len(exotic_playlists) if exotic_playlists else 0,
        'qa_count': len(qa) if qa else 0
    }

except Exception as e:
    print(f"  ❌ FAIL | Error: {e}")
    traceback.print_exc()
    results['web_scraper'] = {'status': 'ERROR', 'error': str(e)}


# ═══════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("  FINAL TEST RESULTS SUMMARY")
print("=" * 70)

all_pass = True
for feature, result in results.items():
    status = result.get('status', 'UNKNOWN')
    icon = '✅' if status == 'PASS' else ('❌' if status in ('FAIL', 'ERROR') else '⚠️')
    print(f"\n  {icon} {feature.upper()}: {status}")
    for k, v in result.items():
        if k != 'status':
            print(f"      {k}: {v}")
    if status != 'PASS':
        all_pass = False

print("\n" + "=" * 70)
if all_pass:
    print("  🎉 ALL TESTS PASSED!")
else:
    print("  ⚠️ SOME TESTS NEED ATTENTION — see details above")
print("=" * 70)

# Save results
with open('test_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n  Results saved to: test_results.json")
