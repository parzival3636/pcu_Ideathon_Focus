"""
Question Generation using Grok AI API (xAI)
Falls back to template-based generation if API fails
"""
import os
import json
import random
import time
import re
from typing import List, Dict


class QuestionGenerator:
    """
    ML-powered question generator using Grok AI API.
    Generates industry-grade technical questions from full transcript context.
    """

    def __init__(self):
        from django.conf import settings
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
        self.model_name = "gemini-2.0-flash"
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    # -------------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------------

    def generate_mcq_questions(self, content: str, concepts: List[str], difficulty: int, count: int) -> List[Dict]:
        """Generate MCQ questions — Gemini API first, concept-based fallback second"""
        try:
            if self.api_key:
                questions = self._call_gemini_api(content, concepts, difficulty, count, 'mcq')
                if questions and len(questions) >= count // 2:
                    return questions[:count]
                print(f"[QGen] Gemini returned only {len(questions) if questions else 0} MCQ — using fallback")
            else:
                print("[QGen] GEMINI_API_KEY not set — using fallback MCQ generator")
        except Exception as e:
            print(f"[QGen] Gemini MCQ failed: {e} — using fallback")
        return self._generate_fallback_mcq(content, concepts, difficulty, count)

    def generate_short_answer_questions(self, content: str, concepts: List[str], difficulty: int, count: int) -> List[Dict]:
        """Generate Short Answer questions — Gemini API first, concept-based fallback second"""
        try:
            if self.api_key:
                questions = self._call_gemini_api(content, concepts, difficulty, count, 'short_answer')
                if questions and len(questions) >= count // 2:
                    return questions[:count]
                print(f"[QGen] Gemini returned only {len(questions) if questions else 0} SA — using fallback")
            else:
                print("[QGen] GEMINI_API_KEY not set — using fallback Short Answer generator")
        except Exception as e:
            print(f"[QGen] Gemini SA failed: {e} — using fallback")
        return self._generate_fallback_short_answer(content, concepts, difficulty, count)

    def generate_problem_solving_questions(self, content: str, concepts: List[str], difficulty: int, count: int) -> List[Dict]:
        """Generate Problem Solving questions — Gemini API first, concept-based fallback second"""
        try:
            if self.api_key:
                questions = self._call_gemini_api(content, concepts, difficulty, count, 'problem_solving')
                if questions and len(questions) >= count // 2:
                    return questions[:count]
                print(f"[QGen] Gemini returned only {len(questions) if questions else 0} PS — using fallback")
            else:
                print("[QGen] GEMINI_API_KEY not set — using fallback Problem Solving generator")
        except Exception as e:
            print(f"[QGen] Gemini PS failed: {e} — using fallback")
        return self._generate_fallback_problem_solving(content, concepts, difficulty, count)

    def assess_answer(self, question: str, expected_answer: str, user_answer: str, question_type: str) -> Dict:
        """
        Assess open-ended answer using Gemini AI API.
        Returns dict with score (0-100), is_correct (bool), feedback (str), confidence (float)
        """
        if not user_answer or not user_answer.strip():
            return {"score": 0.0, "is_correct": False, "feedback": "No answer provided.", "confidence": 1.0}

        try:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not set")
            result = self._call_gemini_assessment(question, expected_answer, user_answer, question_type)
            if result:
                return result
        except Exception as e:
            print(f"[QGen] Gemini assessment failed: {e}")

        return self._fallback_evaluate(user_answer, expected_answer)

    # -------------------------------------------------------------------------
    # CORE GEMINI API CALL
    # -------------------------------------------------------------------------

    def _call_gemini_api(self, content: str, concepts: List[str], difficulty: int, count: int, question_type: str) -> List[Dict]:
        """Call Gemini AI API to generate questions from the full transcript context"""
        import google.generativeai as genai

        difficulty_map = {1: 'intermediate', 2: 'advanced', 3: 'expert'}
        difficulty_text = difficulty_map.get(difficulty, 'intermediate')

        # Build a smart transcript summary for context (Gemini can handle much more, but we keep it efficient)
        transcript_summary = self._build_transcript_summary(content, concepts)

        if question_type == 'mcq':
            prompt = self._get_mcq_prompt(transcript_summary, concepts, difficulty_text, count)
        elif question_type == 'short_answer':
            prompt = self._get_short_answer_prompt(transcript_summary, concepts, difficulty_text, count)
        else:
            prompt = self._get_problem_solving_prompt(transcript_summary, concepts, difficulty_text, count)

        system_msg = (
            "You are a senior software engineer and technical interviewer with 15+ years of industry experience. "
            "You write exam questions at the level of top tech company interviews (Google, Meta, etc). "
            "You ONLY output valid JSON arrays. No markdown, no explanation text."
        )

        for attempt in range(self.max_retries):
            try:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)
                
                response = model.generate_content(
                    f"{system_msg}\n\n{prompt}",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.5,
                        max_output_tokens=4000,
                    )
                )
                
                content_text = response.text.strip()

                # Strip markdown code fences if present
                content_text = re.sub(r'^```(?:json)?\s*', '', content_text, flags=re.MULTILINE)
                content_text = re.sub(r'\s*```$', '', content_text, flags=re.MULTILINE)
                content_text = content_text.strip()

                # Extract JSON array
                json_start = content_text.find('[')
                json_end = content_text.rfind(']') + 1
                if json_start != -1 and json_end > json_start:
                    questions = json.loads(content_text[json_start:json_end])
                    # Validate and normalize
                    validated = self._validate_questions(questions, question_type)
                    if validated:
                        print(f"[QGen] Gemini generated {len(validated)} {question_type} questions")
                        return validated

            except Exception as e:
                print(f"[QGen] Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        return []

    def _call_gemini_assessment(self, question: str, expected_answer: str, user_answer: str, question_type: str) -> Dict:
        """Call Gemini AI API to assess an open-ended answer"""
        import google.generativeai as genai

        prompt = f"""You are evaluating a student's answer to a technical question.

Question: {question}

Expected Answer (reference): {expected_answer}

Student's Answer: {user_answer}

Question Type: {question_type}

Evaluate strictly based on technical accuracy and completeness. Score 0-100.
- 90-100: Excellent, covers all key concepts with correct details
- 70-89: Good, covers most key concepts
- 50-69: Partial, covers some concepts but missing key details
- 0-49: Incorrect or insufficient

Return ONLY this JSON object:
{{
  "score": 75,
  "is_correct": true,
  "feedback": "Specific technical feedback here",
  "confidence": 0.9
}}"""

        for attempt in range(self.max_retries):
            try:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=400,
                    )
                )
                
                content_text = response.text.strip()
                content_text = re.sub(r'^```(?:json)?\s*', '', content_text, flags=re.MULTILINE)
                content_text = re.sub(r'\s*```$', '', content_text, flags=re.MULTILINE)

                json_start = content_text.find('{')
                json_end = content_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    assessment = json.loads(content_text[json_start:json_end])
                    assessment['is_correct'] = assessment.get('score', 0) >= 70
                    return assessment

            except Exception as e:
                print(f"[QGen] Assessment attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        return None

    # -------------------------------------------------------------------------
    # SMART TRANSCRIPT SUMMARIZATION
    # -------------------------------------------------------------------------

    def _build_transcript_summary(self, content: str, concepts: List[str]) -> str:
        """
        Build a smart summary of the transcript for question generation.
        Takes evenly-spaced excerpts across the entire transcript so Grok
        sees the full topic coverage — not just the first 2000 chars.
        Max ~12000 chars (safe for Grok's context).
        """
        max_chars = 12000
        if len(content) <= max_chars:
            return content

        # Take: start + evenly-spaced middle chunks + end
        chunk_size = 1500
        n_middle_chunks = (max_chars - 2 * chunk_size) // chunk_size
        step = (len(content) - 2 * chunk_size) // max(n_middle_chunks, 1)

        parts = []
        # Opening
        parts.append(content[:chunk_size])
        # Middle samples
        for i in range(n_middle_chunks):
            start = chunk_size + i * step
            parts.append(f"...[{int(start/len(content)*100)}% into video]..." + content[start:start + chunk_size])
        # Closing
        parts.append("...[end of video]..." + content[-chunk_size:])

        summary = "\n".join(parts)
        return summary[:max_chars]

    # -------------------------------------------------------------------------
    # FALLBACK GENERATORS (no API key needed)
    # -------------------------------------------------------------------------

    def _extract_key_sentences(self, content: str, concepts: List[str], n: int = 30) -> List[str]:
        """Extract key sentences from transcript using keyword frequency"""
        if not content or len(content) < 50:
            return []

        # Split into sentences (handle spoken transcript format)
        sentences = re.split(r'[.!?]\s+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and len(s.strip()) < 300]

        if not sentences:
            return []

        # Score sentences by concept keyword presence
        concept_words = set()
        for c in (concepts or []):
            concept_words.update(w.lower() for w in c.split() if len(w) > 3)

        # Also extract frequent technical words from transcript
        words = re.findall(r'\b[a-zA-Z_]{4,}\b', content.lower())
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        # Top 50 most frequent words (excluding common English words)
        stopwords = {'this', 'that', 'with', 'from', 'have', 'will', 'your', 'they', 'about',
                      'what', 'when', 'which', 'there', 'their', 'would', 'could', 'should',
                      'been', 'some', 'them', 'than', 'just', 'also', 'into', 'more', 'very',
                      'like', 'then', 'going', 'here', 'want', 'know', 'really', 'right',
                      'because', 'something', 'those', 'these', 'does', 'make', 'thing',
                      'well', 'okay', 'gonna', 'being', 'actually', 'basically', 'need'}
        tech_words = sorted(
            [(w, f) for w, f in word_freq.items() if w not in stopwords and f >= 3],
            key=lambda x: -x[1]
        )[:50]
        tech_word_set = set(w for w, _ in tech_words)

        scored = []
        for s in sentences:
            s_lower = s.lower()
            score = sum(2 for kw in concept_words if kw in s_lower)
            score += sum(1 for tw in tech_word_set if tw in s_lower)
            # Bonus for code-like content
            if any(c in s for c in ['()', '=', 'def ', 'class ', 'import ', 'return ']):
                score += 3
            scored.append((score, s))

        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored[:n]]

    def _get_concept_topics(self, concepts: List[str], content: str) -> List[str]:
        """Get clean concept list, falling back to keyword extraction"""
        if concepts and len(concepts) >= 3:
            return [c for c in concepts if len(c) > 2][:20]

        # Extract from content using frequency analysis
        words = re.findall(r'\b[a-zA-Z_]{5,}\b', content.lower())
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        stopwords = {'about', 'there', 'which', 'would', 'could', 'should', 'their',
                      'going', 'something', 'because', 'really', 'actually', 'basically',
                      'things', 'right', 'gonna', 'these', 'those', 'where', 'being'}
        topics = sorted(
            [(w, f) for w, f in freq.items() if w not in stopwords and f >= 5],
            key=lambda x: -x[1]
        )
        return [w for w, _ in topics[:20]]

    def _generate_fallback_mcq(self, content: str, concepts: List[str], difficulty: int, count: int) -> List[Dict]:
        """Generate concept-based MCQ questions from transcript without AI API"""
        topics = self._get_concept_topics(concepts, content)
        if not topics:
            topics = ['programming', 'development', 'software', 'technology']

        key_sentences = self._extract_key_sentences(content, concepts, n=count * 3)

        # MCQ question templates — technical and specific
        templates = [
            ("What is the primary purpose of {concept} in this context?",
             ["To optimize performance and efficiency", "To handle data processing and transformation",
              "To manage memory allocation", "To provide user interface components"]),
            ("Which of the following best describes how {concept} works?",
             ["It processes data sequentially in a pipeline", "It uses a tree-based hierarchy for organization",
              "It implements a callback mechanism for async operations", "It creates isolated scopes for variables"]),
            ("What would happen if {concept} is not properly implemented?",
             ["Runtime errors and unexpected behavior", "Memory leaks and performance degradation",
              "Security vulnerabilities in the application", "Compilation failures and syntax errors"]),
            ("In what scenario would you primarily use {concept}?",
             ["When handling large datasets efficiently", "When building reusable component architectures",
              "When implementing error handling strategies", "When optimizing network requests"]),
            ("Which statement about {concept} is most accurate?",
             ["It is essential for maintaining code organization", "It primarily improves runtime performance",
              "It helps with debugging and testing", "It is used for data serialization"]),
            ("What is a key advantage of using {concept}?",
             ["Better code reusability and maintainability", "Faster execution and lower memory usage",
              "Improved security and data validation", "Easier testing and debugging"]),
            ("How does {concept} differ from traditional approaches?",
             ["It provides a more declarative syntax", "It uses lazy evaluation for efficiency",
              "It enforces strict type checking", "It automates resource management"]),
            ("What common mistake do developers make with {concept}?",
             ["Not handling edge cases properly", "Using it in inappropriate contexts",
              "Ignoring performance implications", "Failing to test with different inputs"]),
        ]

        questions = []
        for i in range(count):
            concept = topics[i % len(topics)]
            template_q, template_opts = templates[i % len(templates)]
            correct_idx = random.randint(0, 3)

            # Build the options — shuffle them so correct isn't always first
            options = list(template_opts)
            random.shuffle(options)

            questions.append({
                'type': 'mcq',
                'question': template_q.format(concept=concept),
                'options': options,
                'correct_index': correct_idx,
                'explanation': f"This question tests understanding of {concept} as covered in the study material.",
                'concept': concept,
                'points': 1
            })

        print(f"[QGen] Fallback generated {len(questions)} MCQ questions from {len(topics)} concepts")
        return questions

    def _generate_fallback_short_answer(self, content: str, concepts: List[str], difficulty: int, count: int) -> List[Dict]:
        """Generate concept-based short answer questions from transcript without AI API"""
        topics = self._get_concept_topics(concepts, content)
        if not topics:
            topics = ['programming', 'development']

        templates = [
            "Explain what {concept} is and why it is important in software development.",
            "Describe how {concept} works and give a practical example of its usage.",
            "What are the key benefits and potential drawbacks of using {concept}?",
            "Compare and contrast {concept} with an alternative approach you know.",
            "Explain a real-world scenario where {concept} would be the best solution.",
            "What are the common patterns associated with {concept} and when should you use them?",
            "Describe the relationship between {concept} and related concepts in this domain.",
            "How would you explain {concept} to a junior developer?",
        ]

        questions = []
        for i in range(count):
            concept = topics[i % len(topics)]
            template = templates[i % len(templates)]
            questions.append({
                'type': 'short_answer',
                'question': template.format(concept=concept),
                'expected_answer': f"A thorough explanation of {concept} including its purpose, usage, benefits, and practical applications as discussed in the study material.",
                'explanation': f"Tests understanding of {concept}.",
                'concept': concept,
                'points': 2
            })

        print(f"[QGen] Fallback generated {len(questions)} Short Answer questions")
        return questions

    def _generate_fallback_problem_solving(self, content: str, concepts: List[str], difficulty: int, count: int) -> List[Dict]:
        """Generate concept-based problem solving questions from transcript without AI API"""
        topics = self._get_concept_topics(concepts, content)
        if not topics:
            topics = ['programming', 'development']

        templates = [
            "You are building a feature that uses {concept}. Describe your implementation approach step by step, including error handling.",
            "A colleague's code using {concept} is producing unexpected results. Describe your debugging strategy and what common issues you would check for.",
            "Design a small system or module that effectively uses {concept}. Describe the architecture and your reasoning.",
            "Write pseudocode or describe an algorithm that demonstrates proper usage of {concept} in a production environment.",
            "You need to refactor legacy code to use {concept}. What steps would you take and what pitfalls should you avoid?",
            "Explain how you would test a component that heavily relies on {concept}. What test cases would you write?",
        ]

        questions = []
        for i in range(count):
            concept = topics[i % len(topics)]
            template = templates[i % len(templates)]
            questions.append({
                'type': 'problem_solving',
                'question': template.format(concept=concept),
                'expected_answer': f"A detailed solution approach demonstrating practical understanding of {concept}, including implementation steps, error handling, and reasoning.",
                'explanation': f"Tests practical application of {concept}.",
                'concept': concept,
                'points': 3
            })

        print(f"[QGen] Fallback generated {len(questions)} Problem Solving questions")
        return questions

    # -------------------------------------------------------------------------
    # PROMPTS — Industry-grade, topic-aware
    # -------------------------------------------------------------------------

    def _get_mcq_prompt(self, transcript: str, concepts: List[str], difficulty: str, count: int) -> str:
        top_concepts = ', '.join(concepts[:10]) if concepts else 'general programming'
        return f"""Based on the following educational content transcript, generate exactly {count} multiple-choice questions at {difficulty} technical level.

TRANSCRIPT:
{transcript}

KEY TOPICS COVERED: {top_concepts}

STRICT REQUIREMENTS:
1. Questions must test DEEP UNDERSTANDING — not trivia or sentence recall from the transcript
2. Questions must be about the ACTUAL TECHNICAL CONCEPTS taught in the video
3. Each question must have EXACTLY 4 options — all options must be plausible (no "none of the above")
4. Wrong options must be realistic — like real interview wrong answers, not obviously fake
5. correct_index is 0-based (0=A, 1=B, 2=C, 3=D)
6. Difficulty "{difficulty}": write questions that would appear in a technical interview at a top company
7. Explanation should clearly explain WHY the correct answer is right and why others are wrong
8. Do NOT reference the video or transcript directly in question text

Return ONLY a JSON array with exactly {count} items:
[
  {{
    "type": "mcq",
    "question": "Technical question testing understanding of a concept?",
    "options": ["Correct technical answer", "Plausible wrong answer", "Plausible wrong answer", "Plausible wrong answer"],
    "correct_index": 0,
    "explanation": "Detailed technical explanation of why A is correct and why B/C/D are wrong.",
    "concept": "specific concept name",
    "points": 1
  }}
]"""

    def _get_short_answer_prompt(self, transcript: str, concepts: List[str], difficulty: str, count: int) -> str:
        top_concepts = ', '.join(concepts[:10]) if concepts else 'general programming'
        return f"""Based on the following educational content transcript, generate exactly {count} short-answer questions at {difficulty} technical level.

TRANSCRIPT:
{transcript}

KEY TOPICS COVERED: {top_concepts}

STRICT REQUIREMENTS:
1. Questions must require EXPLANATION of a concept — not a yes/no or one-word answer
2. Questions should be at the level of a technical interview or university exam
3. Expected answers should be 3-5 sentences of precise technical content
4. Test understanding, not memorization
5. Do NOT reference "the video" or "the transcript"

Return ONLY a JSON array with exactly {count} items:
[
  {{
    "type": "short_answer",
    "question": "Explain how X works and why it matters in practice?",
    "expected_answer": "Precise 3-5 sentence technical answer covering all key points.",
    "explanation": "What the ideal answer should include and why.",
    "concept": "specific concept name",
    "points": 2
  }}
]"""

    def _get_problem_solving_prompt(self, transcript: str, concepts: List[str], difficulty: str, count: int) -> str:
        top_concepts = ', '.join(concepts[:10]) if concepts else 'general programming'
        return f"""Based on the following educational content transcript, generate exactly {count} practical problem-solving questions at {difficulty} technical level.

TRANSCRIPT:
{transcript}

KEY TOPICS COVERED: {top_concepts}

STRICT REQUIREMENTS:
1. Questions must present a REAL-WORLD SCENARIO that requires applying knowledge from the content
2. For programming topics: include actual code-writing or debugging tasks where appropriate
3. Questions should mirror what a senior engineer would ask in a technical interview
4. Expected answers should include a concrete solution approach with reasoning
5. Do NOT reference "the video" or "the transcript"

Return ONLY a JSON array with exactly {count} items:
[
  {{
    "type": "problem_solving",
    "question": "Real-world scenario or coding problem here. Be specific.",
    "expected_answer": "Detailed solution approach with code/steps/reasoning as appropriate.",
    "explanation": "Why this solution is correct and what concepts it tests.",
    "concept": "specific concept name",
    "points": 3
  }}
]"""

    # -------------------------------------------------------------------------
    # VALIDATION
    # -------------------------------------------------------------------------

    def _validate_questions(self, questions: list, question_type: str) -> List[Dict]:
        """Validate and normalize questions from Grok"""
        valid = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            if not q.get('question') or not q.get('type'):
                continue

            # Force correct type
            q['type'] = question_type

            if question_type == 'mcq':
                opts = q.get('options', [])
                # Must have exactly 4 real options
                if not isinstance(opts, list) or len(opts) < 4:
                    continue
                # Filter out placeholder garbage
                bad_patterns = ['option a', 'option b', 'option c', 'option d',
                                'related to', 'answer here', 'placeholder']
                if any(any(bp in str(o).lower() for bp in bad_patterns) for o in opts):
                    continue
                q['options'] = [str(o) for o in opts[:4]]
                ci = q.get('correct_index', 0)
                q['correct_index'] = int(ci) if isinstance(ci, (int, float)) and 0 <= ci <= 3 else 0
                q.setdefault('points', 1)

            elif question_type == 'short_answer':
                if not q.get('expected_answer'):
                    continue
                q.setdefault('points', 2)

            elif question_type == 'problem_solving':
                if not q.get('expected_answer'):
                    continue
                q.setdefault('points', 3)

            q.setdefault('explanation', '')
            q.setdefault('concept', 'General')
            valid.append(q)

        return valid

    # -------------------------------------------------------------------------
    # FALLBACK EVALUATION (keyword matching)
    # -------------------------------------------------------------------------

    def _fallback_evaluate(self, answer: str, expected: str) -> Dict:
        """Fallback evaluation using keyword matching"""
        if not answer or not expected:
            return {"score": 0.0, "is_correct": False, "feedback": "No answer provided.", "confidence": 1.0}

        keywords = [w for w in expected.lower().split() if len(w) > 4]
        if not keywords:
            return {"score": 50.0, "is_correct": True, "feedback": "Answer received.", "confidence": 0.3}

        matches = sum(1 for kw in keywords if kw in answer.lower())
        score = (matches / len(keywords)) * 100
        return {
            "score": round(score, 1),
            "is_correct": score >= 70,
            "feedback": f"Your answer matched {matches}/{len(keywords)} key concepts.",
            "confidence": 0.5
        }


# -------------------------------------------------------------------------
# LEGACY COMPATIBILITY
# -------------------------------------------------------------------------

def generate_questions(content, difficulty: int, count: int = 10) -> List[Dict]:
    """Legacy function for backward compatibility"""
    qg = QuestionGenerator()
    try:
        questions = qg.generate_mcq_questions(content.transcript, content.key_concepts, difficulty, count)
        if questions:
            return questions
    except Exception as e:
        print(f"Question generation failed: {e}")
    return []
