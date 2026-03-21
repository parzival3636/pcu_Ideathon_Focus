"""
ML Model Integration for Adaptive Difficulty Prediction
"""
import os
import joblib
import numpy as np
from django.conf import settings


class AdaptiveLearningPredictor:
    """
    Predicts next difficulty level based on student performance (v2 with 13 features)
    """
    
    def __init__(self):
        self.model = None
        # Try multiple model file names, prioritizing V2
        model_dir = os.path.join(settings.BASE_DIR, 'adaptive_learning', 'ml_models')
        possible_models = [
            'adaptive_model_v2.pkl',
            'adaptive_model.pkl',
            'random_forest_classifier_model.joblib',
            'adaptive_model.joblib'
        ]
        
        self.model_path = None
        for model_name in possible_models:
            path = os.path.join(model_dir, model_name)
            if os.path.exists(path):
                self.model_path = path
                break
        
        self.is_v2 = "v2" in (self.model_path or "")
        self.load_model()
    
    def load_model(self):
        """Load the trained ML model"""
        try:
            if self.model_path and os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                version = "v2 (13 features)" if self.is_v2 else "v1 (8 features)"
                print(f"✅ ML Model {version} loaded from {self.model_path}")
            else:
                print(f"⚠️ ML Model not found. Using rule-based fallback.")
        except Exception as e:
            print(f"❌ Error loading ML model: {e}")
            self.model = None
    
    def predict_next_difficulty(self, user_data):
        """
        Predict next difficulty level using 13 features (v2) or 8 features (v1)
        """
        features = self._extract_features(user_data)
        
        if self.model is not None:
            try:
                # Predict
                prediction = self.model.predict([features])[0]
                
                # XGBoost v2 outputs 0,1,2 -> map back to 1,2,3
                if self.is_v2:
                    prediction += 1
                
                # Apply business rules
                prediction = self._apply_business_rules(prediction, user_data)
                return int(prediction)
            except Exception as e:
                print(f"ML prediction failed: {e}, using rule-based fallback")
        
        return self._rule_based_prediction(user_data)
    
    def _extract_features(self, user_data):
        """Extract features in correct order for ML model"""
        if self.is_v2:
            # 13 Features for v2
            return [
                user_data.get('accuracy', 50.0),
                user_data.get('avg_time_per_question', 60.0),
                user_data.get('first_attempt_correct', 50.0),
                user_data.get('current_difficulty', 1),
                user_data.get('sessions_completed', 1),
                user_data.get('score_trend', 0.0),
                user_data.get('mastery_level', 0.0),
                user_data.get('is_new_topic', 0),
                user_data.get('engagement_score', 70.0),
                user_data.get('active_time_ratio', 0.8),
                user_data.get('tab_switch_rate', 0.5),
                user_data.get('interaction_density', 8.0),
                user_data.get('session_length_dev', 0.0)
            ]
        else:
            # Original 8 features for v1
            return [
                user_data.get('accuracy', 50.0),
                user_data.get('avg_time_per_question', 60.0),
                user_data.get('first_attempt_correct', 50.0),
                user_data.get('current_difficulty', 1),
                user_data.get('sessions_completed', 1),
                user_data.get('score_trend', 0.0),
                user_data.get('mastery_level', 0.0),
                user_data.get('is_new_topic', 0)
            ]
    
    def _apply_business_rules(self, prediction, user_data):
        """
        Apply hard constraints to ML prediction
        
        Business Rules:
        1. New topics always start at difficulty 1
        2. Difficulty boundaries: 1-3
        3. No skipping levels (change by ±1 only)
        4. Performance thresholds
        """
        current_difficulty = user_data.get('current_difficulty', 1)
        accuracy = user_data.get('accuracy', 50.0)
        sessions_completed = user_data.get('sessions_completed', 1)
        is_new_topic = user_data.get('is_new_topic', 0)
        
        # Rule 1: New topics always start at difficulty 1
        if is_new_topic == 1:
            return 1
        
        # Rule 2: Enforce boundaries
        prediction = max(1, min(3, prediction))
        
        # Rule 3: No skipping levels
        if abs(prediction - current_difficulty) > 1:
            if prediction > current_difficulty:
                prediction = current_difficulty + 1
            else:
                prediction = current_difficulty - 1
        
        # Rule 4: Performance thresholds
        if accuracy < 50:
            # Must decrease difficulty
            prediction = max(1, current_difficulty - 1)
        elif accuracy > 85 and sessions_completed > 2:
            # Must increase difficulty
            prediction = min(3, current_difficulty + 1)
        
        return prediction
    
    def _rule_based_prediction(self, user_data):
        """
        Fallback rule-based prediction if ML model fails
        """
        accuracy = user_data.get('accuracy', 50.0)
        current_difficulty = user_data.get('current_difficulty', 1)
        sessions_completed = user_data.get('sessions_completed', 1)
        score_trend = user_data.get('score_trend', 0.0)
        is_new_topic = user_data.get('is_new_topic', 0)
        
        # New topic
        if is_new_topic == 1:
            return 1
        
        # Fast learner (high accuracy, positive trend)
        if accuracy >= 85 and sessions_completed >= 2:
            return min(3, current_difficulty + 1)
        
        # Struggling (low accuracy)
        if accuracy < 50:
            return max(1, current_difficulty - 1)
        
        # Improving (positive trend)
        if score_trend > 10 and accuracy >= 70:
            return min(3, current_difficulty + 1)
        
        # Declining (negative trend)
        if score_trend < -10:
            return max(1, current_difficulty - 1)
        
        # Stay at current level
        return current_difficulty
    
    def calculate_adaptive_score(self, accuracy, avg_time, first_attempt_rate, difficulty):
        """
        Calculate adaptive score (0-100) based on multiple factors
        
        Formula:
        - Base score: accuracy
        - Time bonus: faster = better (up to +10)
        - First attempt bonus: (up to +10)
        - Difficulty multiplier: harder questions = more points
        """
        base_score = accuracy
        
        # Time bonus (faster is better, but not too fast)
        if 20 <= avg_time <= 40:
            time_bonus = 10
        elif 40 < avg_time <= 60:
            time_bonus = 5
        else:
            time_bonus = 0
        
        # First attempt bonus
        first_attempt_bonus = (first_attempt_rate / 100) * 10
        
        # Difficulty multiplier
        difficulty_multiplier = 1.0 + (difficulty - 1) * 0.1
        
        # Calculate final score
        adaptive_score = (base_score + time_bonus + first_attempt_bonus) * difficulty_multiplier
        
        # Cap at 100
        return min(100, adaptive_score)
    
    def get_question_count(self, difficulty):
        """
        Determine number of questions based on difficulty
        
        Easy (1): 8-10 questions
        Medium (2): 10-12 questions
        Hard (3): 12-15 questions
        """
        question_counts = {
            1: 10,  # Easy
            2: 12,  # Medium
            3: 15   # Hard
        }
        return question_counts.get(difficulty, 10)


# Global predictor instance
predictor = AdaptiveLearningPredictor()


def predict_next_difficulty(user_data):
    """Convenience function for predictions"""
    return predictor.predict_next_difficulty(user_data)


def calculate_adaptive_score(accuracy, avg_time, first_attempt_rate, difficulty):
    """Convenience function for adaptive scoring"""
    return predictor.calculate_adaptive_score(accuracy, avg_time, first_attempt_rate, difficulty)
