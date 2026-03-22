"""
Gemini-based Adaptive MCQ Generation Service
Integrates with the existing content processing pipeline
"""
import google.generativeai as genai
import json
import re
from django.conf import settings
from django.utils import timezone

# Configure Gemini API
GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Module-level variables for rate limiting and retry logic
_last_api_call_time = 0


def _reload_api_key():
    """
    Reload GEMINI_API_KEY from Django settings and reconfigure genai.
    
    This allows dynamic API key updates without restarting the server.
    """
    global GEMINI_API_KEY, model
    GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None)
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    print(f"[Gemini] API key reloaded from settings")


def _rate_limit_delay():
    """
    Enforce minimum 1-second delay between API calls.
    
    Tracks last API call timestamp and sleeps if necessary to maintain
    rate limiting.
    """
    import time
    global _last_api_call_time
    
    current_time = time.time()
    time_since_last_call = current_time - _last_api_call_time
    
    if time_since_last_call < 1.0:
        sleep_time = 1.0 - time_since_last_call
        print(f"[Gemini] Rate limiting: sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)
    
    _last_api_call_time = time.time()


def _call_gemini_with_retry(prompt, max_retries=3):
    """
    Call Gemini API with retry logic and exponential backoff.
    
    Args:
        prompt: The prompt to send to Gemini
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        Response from Gemini API
    
    Raises:
        Exception: User-friendly error message after all retries exhausted
    """
    import time
    
    delays = [2, 4, 8]  # Exponential backoff delays in seconds
    
    for attempt in range(max_retries):
        try:
            # Apply rate limiting before each call
            _rate_limit_delay()
            
            # Make the API call
            response = model.generate_content(prompt)
            return response
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a 429 error or quota/rate limit issue
            is_429_error = ('429' in error_msg or 
                           'quota' in error_msg or 
                           'rate limit' in error_msg or
                           'resource has been exhausted' in error_msg)
            
            if is_429_error:
                if attempt < max_retries - 1:
                    # Reload API key before retry
                    _reload_api_key()
                    
                    delay = delays[attempt]
                    print(f"[Gemini] 429 error on attempt {attempt + 1}/{max_retries}. "
                          f"Retrying in {delay}s after reloading API key...")
                    time.sleep(delay)
                else:
                    # All retries exhausted
                    raise Exception(
                        "API quota exceeded. Please try again in a few minutes or "
                        "update your API key in settings."
                    )
            else:
                # Non-429 error, re-raise immediately
                raise
    
    # Should never reach here, but just in case
    raise Exception("API call failed after all retries")


def _summarize_transcript_with_ollama(transcript, max_length=8000):
    """
    Summarize long transcripts using local Ollama model.
    
    Falls back to truncation if Ollama is unavailable.
    
    Args:
        transcript: The transcript text to summarize
        max_length: Maximum length for the summarized transcript (default: 8000)
    
    Returns:
        Summarized or truncated transcript text
    """
    import requests
    
    # Check if transcript needs summarization
    if len(transcript) <= max_length:
        return transcript
    
    # Get Ollama configuration from Django settings
    ollama_endpoint = getattr(settings, 'OLLAMA_ENDPOINT', 'http://localhost:11434/api/generate')
    ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:3b')
    
    print(f"[Gemini] Transcript too long ({len(transcript)} chars), attempting Ollama summarization...")
    
    try:
        # Call Ollama API
        response = requests.post(
            ollama_endpoint,
            json={
                "model": ollama_model,
                "prompt": f"""Summarize this educational transcript, preserving all key concepts, definitions, examples, and technical details. Keep it under {max_length} characters.

Transcript:
{transcript}

Summary:""",
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('response', '').strip()
            
            if summary and len(summary) > 50:
                print(f"[Gemini] Ollama summarization successful ({len(summary)} chars)")
                return summary[:max_length]  # Ensure it's within limit
            else:
                print(f"[Gemini] Ollama returned empty/short summary, falling back to truncation")
        else:
            print(f"[Gemini] Ollama API returned status {response.status_code}, falling back to truncation")
    
    except requests.exceptions.ConnectionError:
        print(f"[Gemini] Ollama not available (connection refused), falling back to truncation")
    except requests.exceptions.Timeout:
        print(f"[Gemini] Ollama request timed out, falling back to truncation")
    except Exception as e:
        print(f"[Gemini] Ollama error: {e}, falling back to truncation")
    
    # Fallback: truncate to max_length
    print(f"[Gemini] Truncating transcript to {max_length} chars")
    return transcript[:max_length]


def _generate_questions_from_session_name(session_name, user_state=4):
    """
    Generate MCQs from session name as last resort fallback.
    
    This ensures questions are ALWAYS generated even when all other methods fail.
    
    Args:
        session_name: Session name or workspace name to use as topic
        user_state: 1=confused, 2=bored, 3=overloaded, 4=focused
    
    Returns:
        dict with questions and metadata
    """
    if user_state not in USER_STATE_CONFIG:
        user_state = 4  # Default to focused

    config = USER_STATE_CONFIG[user_state]
    num_q = config["num_questions"]
    
    # Simpler prompt for session name fallback
    prompt = f"""You are an expert quiz generator for the topic: {session_name}

Generate EXACTLY {num_q} multiple choice questions about {session_name}.
Focus on fundamental concepts and basic understanding.

RULES:
- Generate EXACTLY {num_q} MCQ questions
- Each question must have 4 options (A, B, C, D)
- Only one correct answer
- Include brief explanation for correct answer (single line, no newlines)
- Focus on core concepts and practical knowledge
- CRITICAL: Do NOT use newlines, line breaks, or \\n characters anywhere in the JSON
- CRITICAL: Keep all text on single lines

Return ONLY valid JSON array (no markdown, no extra text, no newlines in strings):
[
  {{
    "question": "Question text here?",
    "options": {{"A": "option1", "B": "option2", "C": "option3", "D": "option4"}},
    "answer": "B",
    "explanation": "Brief explanation why B is correct",
    "concept": "Specific concept being tested",
    "difficulty_level": "easy|intermediate"
  }}
]"""

    try:
        response = _call_gemini_with_retry(prompt)
        raw_text = response.text.strip()
        
        questions = clean_and_parse_json(raw_text, "Gemini SessionFallback")
        
        print(f"[Gemini] Session name fallback generated {len(questions)} questions for: {session_name}")
        
        return {
            "success": True,
            "num_questions": len(questions),
            "difficulty": "basic",
            "topic": session_name,
            "questions": questions,
            "generation_method": "session_name_fallback"
        }
    except Exception as e:
        print(f"[Gemini] Session name fallback error: {e}")
        return {
            "success": False,
            "error": str(e),
            "questions": []
        }


def clean_and_parse_json(raw_text: str, context: str = "Gemini") -> list:
    """
    Robust JSON parsing with multiple fallback strategies.
    
    Args:
        raw_text: Raw response text from Gemini
        context: Context string for logging
    
    Returns:
        Parsed JSON list
    
    Raises:
        json.JSONDecodeError: If all parsing strategies fail
    """
    # Clean markdown formatting
    cleaned = re.sub(r'^```json\s*', '', raw_text)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()
    
    # Remove control characters that break JSON parsing (except newlines for now)
    cleaned = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f]', ' ', cleaned)
    
    # Replace smart quotes with regular quotes
    cleaned = cleaned.replace('"', '"').replace('"', '"')
    cleaned = cleaned.replace(''', "'").replace(''', "'")
    
    # Try to find and extract just the JSON array if there's extra text
    json_match = re.search(r'\[\s*\{.*\}\s*\]', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    
    print(f"[{context}] Attempting to parse JSON (length: {len(cleaned)} chars)")
    
    try:
        # First attempt: direct parsing
        questions = json.loads(cleaned)
        
        # Post-process: remove newlines from all string values
        for q in questions:
            if 'question' in q:
                q['question'] = q['question'].replace('\n', ' ').replace('\r', ' ')
            if 'explanation' in q:
                q['explanation'] = q['explanation'].replace('\n', ' ').replace('\r', ' ')
            if 'concept' in q:
                q['concept'] = q['concept'].replace('\n', ' ').replace('\r', ' ')
            if 'options' in q and isinstance(q['options'], dict):
                for key in q['options']:
                    q['options'][key] = q['options'][key].replace('\n', ' ').replace('\r', ' ')
        
        return questions
        
    except json.JSONDecodeError as e:
        print(f"[{context}] First parse failed at position {e.pos}: {e.msg}")
        print(f"[{context}] Context around error: ...{cleaned[max(0, e.pos-50):e.pos+50]}...")
        
        # Second attempt: Try to fix common issues
        # Fix trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        # Replace newlines within string values (between quotes)
        # This is a heuristic approach
        def replace_newlines_in_strings(match):
            return match.group(0).replace('\n', ' ').replace('\r', ' ')
        
        cleaned = re.sub(r'"[^"]*"', replace_newlines_in_strings, cleaned)
        
        try:
            questions = json.loads(cleaned)
            
            # Post-process again
            for q in questions:
                if 'question' in q:
                    q['question'] = q['question'].replace('\n', ' ').replace('\r', ' ')
                if 'explanation' in q:
                    q['explanation'] = q['explanation'].replace('\n', ' ').replace('\r', ' ')
                if 'concept' in q:
                    q['concept'] = q['concept'].replace('\n', ' ').replace('\r', ' ')
                if 'options' in q and isinstance(q['options'], dict):
                    for key in q['options']:
                        q['options'][key] = q['options'][key].replace('\n', ' ').replace('\r', ' ')
            
            return questions
            
        except json.JSONDecodeError as e2:
            print(f"[{context}] Second parse failed: {e2}")
            print(f"[{context}] Full response (first 1000 chars): {raw_text[:1000]}")
            raise

# User state configuration
USER_STATE_CONFIG = {
    1: {
        "label": "confused",
        "num_questions": 20,
        "difficulty": "beginner",
        "instruction": "The user is confused. Generate 20 SIMPLE questions that reinforce basic understanding. All questions should be easy to build confidence.",
        "take_break": False,
        "difficulty_distribution": "all_easy"
    },
    2: {
        "label": "bored",
        "num_questions": 20,
        "difficulty": "advanced",
        "instruction": "The user is bored. Generate 20 CHALLENGING questions. First 15 should be intermediate-advanced, last 5 should be very difficult to challenge the user.",
        "take_break": False,
        "difficulty_distribution": "progressive_hard"
    },
    3: {
        "label": "overloaded",
        "num_questions": 10,
        "difficulty": "easy",
        "instruction": "The user is overloaded. Generate only 10 EASY questions focusing on key takeaways. Keep it simple and straightforward.",
        "take_break": True,
        "difficulty_distribution": "all_easy"
    },
    4: {
        "label": "focused",
        "num_questions": 20,
        "difficulty": "intermediate-to-advanced",
        "instruction": "The user is focused. Generate 20 questions: First 15 should be intermediate level, last 5 should be significantly harder to test deep understanding.",
        "take_break": False,
        "difficulty_distribution": "progressive"
    },
}


def extract_technical_content(transcript: str) -> str:
    """Extract educational content from transcript."""
    prompt = f"""You are an educational content extractor.
Remove: filler, jokes, timestamps, sponsor segments, "like and subscribe", greetings.
Extract: key concepts, definitions, facts, processes, examples.
Output as structured bullet points grouped by topic.

RAW TRANSCRIPT:
\"\"\"
{transcript}
\"\"\"

OUTPUT (bullet points only):"""

    try:
        response = _call_gemini_with_retry(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error extracting content: {e}")
        return transcript  # Fallback to original


def generate_adaptive_mcqs(technical_content: str, user_state: int = 4) -> dict:
    """Generate adaptive MCQs based on user state."""
    if user_state not in USER_STATE_CONFIG:
        user_state = 4  # Default to focused

    config = USER_STATE_CONFIG[user_state]
    num_q = config["num_questions"]
    instruction = config["instruction"]
    difficulty = config["difficulty"]

    prompt = f"""You are an expert quiz generator.

CONTEXT: {instruction}
DIFFICULTY: {difficulty}
NUMBER OF QUESTIONS: {num_q}

RULES:
- Generate EXACTLY {num_q} MCQ questions
- Each question must be DIRECTLY and SOLELY answerable from the provided content below
- DO NOT make up facts, concepts, or information not present in the content
- DO NOT hallucinate or invent questions about topics not covered in the content
- Each question must have 4 options (A, B, C, D)
- Only one correct answer
- Include brief explanation for correct answer referencing the content
- Vary question types (definition, application, analysis)

CONTENT:
\"\"\"
{technical_content}
\"\"\"

Return ONLY valid JSON array (no markdown, no extra text):
[{{
  "question": "Question text?",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "answer": "A",
  "explanation": "Why A is correct based on the content.",
  "concept": "Specific concept from the content being tested"
}}]"""

    try:
        response = _call_gemini_with_retry(prompt)
        raw = response.text.strip()

        questions = clean_and_parse_json(raw, "Gemini MCQ")

        return {
            "user_state": config["label"],
            "difficulty": difficulty,
            "num_questions": len(questions),
            "take_break_suggestion": config["take_break"],
            "questions": questions,
            "success": True
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Error generating MCQs: {error_msg}")
        
        # Check if it's a user-friendly error message (from retry logic)
        if "API quota exceeded" in error_msg or "try again" in error_msg:
            return {
                "success": False,
                "error": error_msg,
                "questions": []
            }
        else:
            return {
                "success": False,
                "error": f"Error generating MCQs: {error_msg}",
                "questions": []
            }


def generate_test2_questions(topic: str, user_state: int, weak_concepts: set, score: float) -> dict:
    """
    Generate Test 2: ALWAYS 15 simplified + 5 harder questions.
    
    Args:
        topic: Topic name
        user_state: Not used - Test 2 is always simplified
        weak_concepts: Set of concepts user got wrong
        score: Test 1 score percentage
    
    Returns:
        dict with questions and metadata
    """
    weak_list = ', '.join(weak_concepts) if weak_concepts else 'None - student did well'

    # Test 2 is ALWAYS: 15 easier questions + 5 harder questions
    prompt = f"""You are an expert quiz generator creating TEST 2 (follow-up test) for the topic: {topic}

CONTEXT: Student scored {score:.0f}% on Test 1.
WEAK CONCEPTS from Test 1: {weak_list}

TEST 2 STRUCTURE (ALWAYS):
- Questions 1-15: EASIER/SIMPLIFIED questions
  * If weak concepts exist: Focus on those concepts with clearer, simpler questions
  * If no weak concepts: Cover fundamental concepts in a straightforward way
- Questions 16-20: HARDER questions
  * Challenge the student with advanced concepts or tricky scenarios
  * Test deeper understanding and application

RULES:
- Generate EXACTLY 20 MCQ questions about {topic}
- Each question must have 4 options (A, B, C, D)
- Only one correct answer
- Include brief explanation for correct answer (single line, no newlines)
- Questions 1-15 should be noticeably EASIER than typical questions
- Questions 16-20 should be CHALLENGING
- CRITICAL: Do NOT use newlines, line breaks, or \\n characters anywhere in the JSON
- CRITICAL: Keep all text on single lines - no multi-line strings
- CRITICAL: Use spaces instead of newlines for readability in explanations

Return ONLY valid JSON array (no markdown, no extra text, no newlines in strings):
[
  {{
    "question": "Question text here?",
    "options": {{"A": "option1", "B": "option2", "C": "option3", "D": "option4"}},
    "answer": "B",
    "explanation": "Brief explanation why B is correct",
    "concept": "Specific concept being tested",
    "difficulty_level": "easy|hard"
  }}
]"""

    try:
        response = _call_gemini_with_retry(prompt)
        raw_text = response.text.strip()
        
        questions = clean_and_parse_json(raw_text, "Gemini Test2")
        
        print(f"[Gemini Test2] Generated {len(questions)} questions (15 easier + 5 harder) for topic: {topic}")
        
        return {
            "success": True,
            "num_questions": len(questions),
            "difficulty": "adaptive",
            "topic": topic,
            "questions": questions
        }
    except json.JSONDecodeError as e:
        print(f"[Gemini Test2] JSON parsing error: {e}")
        print(f"[Gemini Test2] Raw response (first 500 chars): {raw_text[:500]}")
        return {
            "success": False,
            "error": f"Failed to parse Gemini response: {str(e)}",
            "questions": []
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini Test2] Error generating questions: {error_msg}")
        
        # Check if it's a user-friendly error message
        if "API quota exceeded" in error_msg or "try again" in error_msg:
            return {
                "success": False,
                "error": error_msg,
                "questions": []
            }
        else:
            return {
                "success": False,
                "error": f"Error generating Test 2 questions: {error_msg}",
                "questions": []
            }


def generate_questions_from_topic(topic: str, user_state: int = 4) -> dict:
    """
    Generate MCQs directly from a topic name (e.g., "Python", "Machine Learning").
    
    Args:
        topic: Topic name or subject (e.g., "Python", "Data Structures")
        user_state: 1=confused, 2=bored, 3=overloaded, 4=focused
    
    Returns:
        dict with questions and metadata
    """
    if user_state not in USER_STATE_CONFIG:
        user_state = 4  # Default to focused

    config = USER_STATE_CONFIG[user_state]
    num_q = config["num_questions"]
    instruction = config["instruction"]
    difficulty = config["difficulty"]
    distribution = config.get("difficulty_distribution", "progressive")

    # Build difficulty-specific instructions
    if distribution == "all_easy":
        difficulty_guide = "All questions should be EASY level - testing basic concepts and definitions."
    elif distribution == "progressive":
        difficulty_guide = f"Questions 1-15: INTERMEDIATE level. Questions 16-{num_q}: HARD level (challenging, requiring deep understanding)."
    elif distribution == "progressive_hard":
        difficulty_guide = f"Questions 1-15: INTERMEDIATE-ADVANCED level. Questions 16-{num_q}: VERY HARD level (expert-level, tricky scenarios)."
    else:
        difficulty_guide = "Vary difficulty appropriately."

    prompt = f"""You are an expert quiz generator for the topic: {topic}

CONTEXT: {instruction}
DIFFICULTY: {difficulty}
NUMBER OF QUESTIONS: {num_q}

DIFFICULTY DISTRIBUTION:
{difficulty_guide}

RULES:
- Generate EXACTLY {num_q} MCQ questions about {topic}
- Follow the difficulty distribution strictly
- Cover fundamental concepts, practical applications, and best practices
- Each question must have 4 options (A, B, C, D)
- Only one correct answer
- Include brief explanation for correct answer (single line, no newlines)
- Vary question types (definition, application, analysis, problem-solving)
- Questions should be educational and test real understanding
- For HARD questions: use edge cases, tricky scenarios, or require synthesis of multiple concepts
- CRITICAL: Do NOT use newlines, line breaks, or \\n characters anywhere in the JSON
- CRITICAL: Keep all text on single lines - no multi-line strings
- CRITICAL: Use spaces instead of newlines for readability in explanations

Return ONLY valid JSON array (no markdown, no extra text, no newlines in strings):
[
  {{
    "question": "Question text here?",
    "options": {{"A": "option1", "B": "option2", "C": "option3", "D": "option4"}},
    "answer": "B",
    "explanation": "Brief explanation why B is correct",
    "concept": "Specific concept being tested",
    "difficulty_level": "easy|intermediate|hard"
  }}
]"""

    try:
        response = _call_gemini_with_retry(prompt)
        raw_text = response.text.strip()
        
        questions = clean_and_parse_json(raw_text, "Gemini")
        
        print(f"[Gemini] Generated {len(questions)} questions for topic: {topic} (state: {config['label']})")
        
        return {
            "success": True,
            "num_questions": len(questions),
            "difficulty": difficulty,
            "user_state": user_state,
            "topic": topic,
            "questions": questions
        }
    except json.JSONDecodeError as e:
        print(f"[Gemini] JSON parsing error: {e}")
        print(f"[Gemini] Raw response (first 500 chars): {raw_text[:500]}")
        return {
            "success": False,
            "error": f"Failed to parse Gemini response: {str(e)}",
            "questions": []
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini] Error generating questions: {error_msg}")
        
        # Check if it's a user-friendly error message
        if "API quota exceeded" in error_msg or "try again" in error_msg:
            return {
                "success": False,
                "error": error_msg,
                "questions": []
            }
        else:
            return {
                "success": False,
                "error": f"Error generating questions: {error_msg}",
                "questions": []
            }


def process_content_and_generate_mcqs(transcript: str, user_state: int = 4) -> dict:
    """
    Full pipeline: Extract technical content -> Generate adaptive MCQs

    Args:
        transcript: Raw transcript text
        user_state: 1=confused, 2=bored, 3=overloaded, 4=focused

    Returns:
        dict with questions and metadata
    """
    print(f"[Gemini MCQ] Extracting technical content...")
    technical_content = extract_technical_content(transcript)

    print(f"[Gemini MCQ] Generating MCQs for user state: {USER_STATE_CONFIG.get(user_state, {}).get('label', 'focused')}...")
    result = generate_adaptive_mcqs(technical_content, user_state)

    # Add extracted content for reference
    result["extracted_content"] = technical_content

    return result


# ============================================================================
# DJANGO MODEL INTEGRATION
# ============================================================================

def create_assessment_from_session(session_id, user, content):
    """
    Create assessment with adaptive questions based on study session.
    
    PRIORITY FALLBACK CHAIN (bulletproof):
      1. Use existing transcript from content object
      2. If transcript >8000 chars, summarize with Ollama first
      3. If transcript extraction failed, use topic-based generation
      4. If topic-based generation fails, use session name fallback
    
    This ensures questions are ALWAYS generated no matter what.

    Args:
        session_id: StudySession ID
        user: User instance
        content: Content instance (can be None)

    Returns:
        Assessment instance with generated questions
    """
    from .models import Assessment, Question, StudySession

    # Get the session to extract workspace name and content
    try:
        session = StudySession.objects.get(id=session_id)
        topic = session.workspace_name or "General Programming"
    except StudySession.DoesNotExist:
        topic = "General Programming"
        session = None

    # Default to focused state
    learning_state = 4

    # ── PRIORITY 1: Check existing transcript ──
    transcript = None
    generation_method = None
    result = None  # Initialize result to avoid UnboundLocalError
    
    if content and hasattr(content, 'transcript') and content.transcript:
        transcript = content.transcript.strip()
    
    if transcript and len(transcript) > 100:
        print(f"[Gemini] Attempting transcript-based generation ({len(transcript)} chars)...", flush=True)
        
        # ── PRIORITY 2: Summarize if transcript is too long ──
        if len(transcript) > 8000:
            print(f"[Gemini] Transcript too long, summarizing...", flush=True)
            transcript = _summarize_transcript_with_ollama(transcript)
            generation_method = "transcript_summarized"
        else:
            generation_method = "transcript"
        
        try:
            result = process_content_and_generate_mcqs(transcript, learning_state)
            if result.get('success'):
                print(f"[Gemini] [OK] Transcript-based generation succeeded", flush=True)
            else:
                raise Exception(result.get('error', 'Unknown error'))
        except Exception as e:
            print(f"[Gemini] Transcript-based generation failed: {e}", flush=True)
            print(f"[Gemini] Falling back to topic-based generation...", flush=True)
            transcript = None  # Clear transcript to trigger fallback
            result = None  # Clear result to trigger fallback
    
    # ── PRIORITY 3: Topic-based generation fallback ──
    if not transcript or result is None or not result.get('success'):
        print(f"[Gemini] Falling back to topic-based generation: {topic}", flush=True)
        generation_method = "topic"
        
        try:
            result = generate_questions_from_topic(topic, learning_state)
            if result.get('success'):
                print(f"[Gemini] [OK] Topic-based generation succeeded", flush=True)
            else:
                raise Exception(result.get('error', 'Unknown error'))
        except Exception as e:
            print(f"[Gemini] Topic-based generation failed: {e}", flush=True)
            print(f"[Gemini] Using session name fallback...", flush=True)
            result = None  # Clear result to trigger final fallback
    
    # ── PRIORITY 4: Session name fallback (ultimate fallback) ──
    if not result or not result.get('success'):
        print(f"[Gemini] Using session name fallback: {topic}", flush=True)
        generation_method = "session_name_fallback"
        
        result = _generate_questions_from_session_name(topic, learning_state)
        
        if not result.get('success'):
            # This should never happen, but handle it gracefully
            raise Exception(f"All MCQ generation methods failed: {result.get('error')}")

    # Map difficulty to numeric level
    difficulty_map = {
        'beginner': 1, 'easy': 1, 'basic': 1,
        'intermediate': 2, 'intermediate-to-advanced': 2,
        'advanced': 3, 'hard': 3,
    }
    difficulty_level = difficulty_map.get(result.get('difficulty', 'intermediate'), 2)

    # Create Assessment with metadata tracking generation method
    assessment = Assessment.objects.create(
        content=content,
        user=user,
        session_id=session_id,
        test_number=1,
        difficulty_level=difficulty_level,
        total_questions=result['num_questions']
    )

    # Create Questions
    for idx, q_data in enumerate(result['questions']):
        options_dict = q_data['options']
        options_list = [
            options_dict.get('A', ''),
            options_dict.get('B', ''),
            options_dict.get('C', ''),
            options_dict.get('D', '')
        ]

        answer_letter = q_data['answer'].upper()
        correct_index = ord(answer_letter) - ord('A')

        Question.objects.create(
            assessment=assessment,
            question_text=q_data['question'],
            options=options_list,
            correct_answer_index=correct_index,
            explanation=q_data.get('explanation', ''),
            difficulty=difficulty_level,
            concept=q_data.get('concept', 'General'),
            order=idx
        )

    # Set test_available_until on the session
    from datetime import timedelta
    try:
        if session:
            session.test_available_until = timezone.now() + timedelta(hours=6)
            session.save()
    except:
        pass

    print(f"[Gemini] Created assessment {assessment.id} with {result['num_questions']} questions "
          f"(method: {generation_method})", flush=True)

    return assessment


def create_followup_assessment(test1_assessment_id, score_percentage=None):
    """
    Create Test 2 (adaptive retry) based on Test 1 results.
    
    Uses the ACTUAL transcript content + wrong concepts from Test 1.
    Falls back to topic-based generation only if no transcript is available.

    Args:
        test1_assessment_id: Assessment ID for the completed Test 1
        score_percentage: Test 1 score (0-100) — determines user state

    Returns:
        Assessment instance for Test 2
    """
    from .models import Assessment, Question, UserAnswer, StudySession
    from datetime import timedelta
    import sys

    try:
        test1 = Assessment.objects.get(id=test1_assessment_id, is_completed=True, test_number=1)
    except Assessment.DoesNotExist:
        raise ValueError("Test 1 not found or not completed")

    # Check if Test 2 already exists
    existing_test2 = Assessment.objects.filter(
        parent_assessment=test1,
        test_number=2
    ).first()
    if existing_test2:
        print(f"[Followup] Test 2 already exists (ID: {existing_test2.id})", flush=True)
        return existing_test2

    # Get topic and transcript from session
    topic = "General Programming"
    transcript = None
    try:
        session = StudySession.objects.get(id=test1.session_id)
        topic = session.workspace_name or "General Programming"
    except:
        pass

    # Get transcript from content
    if test1.content and hasattr(test1.content, 'transcript') and test1.content.transcript:
        transcript = test1.content.transcript.strip()
        if len(transcript) > 100:
            print(f"[Followup] [OK] Using TRANSCRIPT ({len(transcript)} chars) for Test 2", flush=True)

    # Identify wrong concepts AND the actual wrong questions from Test 1
    user_answers = UserAnswer.objects.filter(
        question__assessment=test1,
        user=test1.user
    ).select_related('question')

    wrong_concepts = set()
    wrong_questions_detail = []
    all_concepts = set()
    for answer in user_answers:
        all_concepts.add(answer.question.concept)
        if not answer.is_correct:
            wrong_concepts.add(answer.question.concept)
            wrong_questions_detail.append({
                'question': answer.question.question_text,
                'concept': answer.question.concept,
                'correct_answer': answer.question.options[answer.question.correct_answer_index] if answer.question.options else 'N/A',
            })

    # Determine user state based on Test 1 score
    if score_percentage is None:
        score_percentage = test1.score or 50
    
    # Map score to user state
    if score_percentage < 40:
        user_state = 1  # confused - simplify
        difficulty_level = 1
    elif score_percentage < 60:
        user_state = 3  # overloaded - reduce questions, simplify
        difficulty_level = 1
    elif score_percentage < 80:
        user_state = 4  # focused - balanced
        difficulty_level = 2
    else:
        user_state = 2  # bored - make it harder
        difficulty_level = 3

    state_label = USER_STATE_CONFIG[user_state]['label']
    print(f"[Followup] Test 1 score: {score_percentage:.0f}% → User state: {state_label}", flush=True)
    print(f"[Followup] Wrong concepts: {wrong_concepts}", flush=True)
    print(f"[Followup] Wrong questions count: {len(wrong_questions_detail)}", flush=True)

    # Build context about weak areas
    wrong_list = ', '.join(wrong_concepts) if wrong_concepts else 'None'
    
    # Build wrong questions summary for the prompt
    wrong_q_summary = ""
    if wrong_questions_detail:
        wrong_q_summary = "\n\nSPECIFIC QUESTIONS THE STUDENT GOT WRONG:\n"
        for i, wq in enumerate(wrong_questions_detail[:10], 1):
            wrong_q_summary += f"{i}. [{wq['concept']}] {wq['question']} (Correct: {wq['correct_answer']})\n"

    # Generate Test 2 questions - use transcript if available
    if transcript and len(transcript) > 100:
        # Extract technical content from transcript for Test 2
        technical_content = extract_technical_content(transcript)
        result = _generate_test2_from_content(technical_content, wrong_concepts, wrong_q_summary, score_percentage)
    else:
        result = generate_test2_questions(topic, user_state, wrong_concepts, score_percentage)

    if not result.get('success'):
        raise Exception(f"Test 2 generation failed: {result.get('error')}")

    # Create Test 2 assessment
    test2 = Assessment.objects.create(
        content=test1.content,
        user=test1.user,
        session_id=test1.session_id,
        test_number=2,
        parent_assessment=test1,
        expires_at=timezone.now() + timedelta(hours=6),
        difficulty_level=difficulty_level,
        total_questions=result['num_questions']
    )

    # Create questions
    for idx, q_data in enumerate(result['questions']):
        # Convert options dict to list
        options_dict = q_data['options']
        options_list = [
            options_dict.get('A', ''),
            options_dict.get('B', ''),
            options_dict.get('C', ''),
            options_dict.get('D', '')
        ]

        # Get correct answer index
        answer_letter = q_data['answer'].upper()
        correct_index = ord(answer_letter) - ord('A')

        Question.objects.create(
            assessment=test2,
            question_text=q_data['question'],
            options=options_list,
            correct_answer_index=correct_index,
            explanation=q_data.get('explanation', ''),
            difficulty=difficulty_level,
            concept=q_data.get('concept', 'General'),
            order=idx
        )

    print(f"[Followup] [OK] Created Test 2 (ID: {test2.id}) with {result['num_questions']} questions", flush=True)
    print(f"[Followup] Weak concepts from Test 1: {wrong_list}", flush=True)

    return test2


def _generate_test2_from_content(technical_content, wrong_concepts, wrong_q_summary, score):
    """Generate Test 2 questions from actual transcript content + Test 1 weak areas."""
    weak_list = ', '.join(wrong_concepts) if wrong_concepts else 'None - student did well'

    prompt = f"""You are an expert quiz generator creating TEST 2 (follow-up test).

CONTEXT: Student scored {score:.0f}% on Test 1.
WEAK CONCEPTS from Test 1: {weak_list}
{wrong_q_summary}

CONTENT FROM THE STUDY MATERIAL:
\"\"\"
{technical_content[:8000]}
\"\"\"

TEST 2 STRUCTURE:
- Questions 1-15: EASIER/SIMPLIFIED questions
  * Focus on the weak concepts listed above with clearer, simpler questions
  * Questions MUST be answerable from the study material above
- Questions 16-20: HARDER questions
  * Challenge the student with advanced concepts from the SAME material
  * Test deeper understanding and application

RULES:
- Generate EXACTLY 20 MCQ questions
- ALL questions must be based on the study material above - NO hallucinated content
- Each question must have 4 options (A, B, C, D)
- Only one correct answer
- Include brief explanation (single line)
- CRITICAL: No newlines in JSON string values

Return ONLY valid JSON array:
[
  {{
    "question": "Question text?",
    "options": {{"A": "opt1", "B": "opt2", "C": "opt3", "D": "opt4"}},
    "answer": "B",
    "explanation": "Brief explanation",
    "concept": "concept name",
    "difficulty_level": "easy|hard"
  }}
]"""

    try:
        response = _call_gemini_with_retry(prompt)
        raw_text = response.text.strip()
        questions = clean_and_parse_json(raw_text, "Gemini Test2-Content")
        print(f"[Gemini Test2] [OK] Generated {len(questions)} questions from transcript content", flush=True)
        return {
            "success": True,
            "num_questions": len(questions),
            "difficulty": "adaptive",
            "questions": questions
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[Gemini Test2] [FAIL] Content-based generation failed: {error_msg}", flush=True)
        
        # Check if it's a user-friendly error message
        if "API quota exceeded" in error_msg or "try again" in error_msg:
            return {
                "success": False,
                "error": error_msg,
                "questions": []
            }
        else:
            return {
                "success": False,
                "error": f"Content-based generation failed: {error_msg}",
                "questions": []
            }

