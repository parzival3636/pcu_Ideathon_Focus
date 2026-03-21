"""
RAG Chat Integration - Using Grok AI for content-based Q&A
"""
import os
import requests
from django.utils import timezone
from .models import StudySession


class RAGChatIntegration:
    """Integrate with Google Gemini AI for content-based Q&A"""
    
    def __init__(self):
        from django.conf import settings
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
        self.model_name = "gemini-2.0-flash"
        self.timeout = 30  # seconds
    
    @classmethod
    def send_query(cls, session_id: int, query: str, context: str = None) -> dict:
        """
        Send query to Gemini AI with content context
        
        Args:
            session_id: StudySession ID
            query: User's question
            context: Optional additional context
            
        Returns:
            dict with response from Gemini AI
        """
        try:
            session = StudySession.objects.get(id=session_id)
        except StudySession.DoesNotExist:
            return {'error': 'Session not found'}
        
        # Get content from session
        content_text = session.content.transcript if session.content else ""
        
        # Use provided context or content transcript
        # Gemini has a very large context window, so we can send more if needed,
        # but 15000 chars is usually plenty for most videos/docs.
        full_context = context or content_text[:15000]
        
        try:
            # Create instance to access instance variables
            instance = cls()
            
            if not instance.api_key:
                return {
                    'error': 'GEMINI_API_KEY not configured',
                    'fallback_response': 'Chat service is not configured. Please set up your Gemini API key.'
                }
            
            import google.generativeai as genai
            genai.configure(api_key=instance.api_key)
            model = genai.GenerativeModel(instance.model_name)
            
            # Prepare prompt with context
            system_prompt = """You are an intelligent tutor helping students understand their study material.
STRICT RULE: Answer questions ONLY based on the provided content context below. 
Do NOT use your outside knowledge to answer. If the answer is not in the content, say "I'm sorry, but that information is not covered in your study material."
Be clear, concise, and educational."""
            
            user_prompt = f"""CONTENT CONTEXT:
{full_context}

STUDENT QUESTION: {query}

INSTRUCTION: Answer strictly from the content context above."""
            
            # Call Gemini
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2, # Lower temperature for more factual responses
                    max_output_tokens=1000,
                )
            )
            
            answer = response.text
            
            # Record interaction
            cls.record_chat_interaction(session_id, query, answer)
            
            return {
                'success': True,
                'response': answer,
                'sources': ['Gemini AI'],
                'confidence': 0.95
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"[RAG] Gemini query failed: {error_msg}")
            return {
                'error': f'Gemini query failed: {error_msg}',
                'fallback_response': 'I encountered an error processing your question with Gemini. Please try again.'
            }
    
    @classmethod
    def record_chat_interaction(cls, session_id: int, query: str, response: str) -> dict:
        """
        Record chat usage as engagement event
        
        Args:
            session_id: StudySession ID
            query: User's question
            response: RAG backend response
            
        Returns:
            dict with success status
        """
        try:
            from .monitoring_collector import MonitoringCollector
            
            # Record as monitoring event
            result = MonitoringCollector.record_event(
                session_id,
                'chat_query',
                {
                    'query': query[:200],  # Limit stored query length
                    'response_length': len(response),
                    'timestamp': str(timezone.now())
                }
            )
            
            return result
        
        except Exception as e:
            return {'error': f'Failed to record interaction: {str(e)}'}
    
    @classmethod
    def get_chat_history(cls, session_id: int) -> dict:
        """
        Get chat history for a session
        
        Args:
            session_id: StudySession ID
            
        Returns:
            dict with chat history
        """
        try:
            session = StudySession.objects.get(id=session_id)
            metrics = session.metrics
            
            # Extract chat events from content_interactions
            chat_count = metrics.chat_queries_count
            
            return {
                'success': True,
                'session_id': session_id,
                'total_queries': chat_count,
                'message': 'Chat history tracking is active'
            }
        
        except Exception as e:
            return {'error': f'Failed to get chat history: {str(e)}'}
