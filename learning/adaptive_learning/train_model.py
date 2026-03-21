"""
Train the Adaptive Learning ML Model v2 (Behavioral Focused)
Generates synthetic training data based on 13 behavioral/performance features
and trains an XGBoost classifier for highly adaptive difficulty prediction.
"""
import os
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib


def generate_persona_data(n_samples=5000):
    """
    Generate synthetic training data based on 13 behavioral personas.
    
    Features:
    1-8: Original (accuracy, avg_time, first_attempt, difficulty, sessions, trend, mastery, is_new)
    9-13: Behavioral (engagement, active_ratio, tab_rate, interaction_density, session_dev)
    """
    np.random.seed(42)
    data = []
    
    for _ in range(n_samples):
        # 1. Base Context
        curr_diff = np.random.randint(1, 4)
        sessions = np.random.randint(1, 51)
        is_new = 1 if sessions == 1 else 0
        
        # 2. Assign Persona (Randomly)
        persona_roll = np.random.random()
        
        # Define default ranges (Normal Learner)
        accuracy = np.random.uniform(60, 80)
        avg_time = np.random.uniform(40, 60)
        first_attempt = accuracy + np.random.uniform(-5, 5)
        engagement = np.random.uniform(60, 85)
        active_ratio = np.random.uniform(0.7, 0.9)
        tab_rate = np.random.uniform(0.1, 1.0)
        interaction_density = np.random.uniform(5, 12)
        session_dev = np.random.uniform(-0.1, 0.1)
        score_trend = np.random.uniform(-5, 10)
        
        # --- PERSONA OVERRIDES ---
        
        if is_new:
            accuracy = np.random.uniform(40, 65)
            next_diff = 1
        
        elif persona_roll < 0.25: # "Fast Learner / Deep Learner"
            accuracy = np.random.uniform(85, 98)
            avg_time = np.random.uniform(20, 35)
            engagement = np.random.uniform(85, 100)
            active_ratio = np.random.uniform(0.9, 1.0)
            tab_rate = np.random.uniform(0, 0.3)
            interaction_density = np.random.uniform(12, 20)
            score_trend = np.random.uniform(10, 20)
            next_diff = min(3, curr_diff + 1)
            
        elif persona_roll < 0.45: # "Distracted High-Achiever" (Cheat Risk)
            accuracy = np.random.uniform(90, 100)
            avg_time = np.random.uniform(10, 25) # Too fast
            tab_rate = np.random.uniform(3.0, 8.0) # Search for answers
            active_ratio = np.random.uniform(0.4, 0.7)
            session_dev = np.random.uniform(-0.8, -0.4) # Skimming
            next_diff = curr_diff # Penalty: Don't move up despite high score
            
        elif persona_roll < 0.70: # "Struggling but Diligent"
            accuracy = np.random.uniform(30, 55)
            avg_time = np.random.uniform(70, 110)
            engagement = np.random.uniform(70, 95)
            active_ratio = np.random.uniform(0.8, 1.0)
            tab_rate = np.random.uniform(0, 0.5)
            session_dev = np.random.uniform(0.4, 0.8) # Taking too long
            score_trend = np.random.uniform(-15, 0)
            next_diff = max(1, curr_diff - 1)
            
        else: # "Average/Maintain"
            next_diff = curr_diff
            
        # 3. Final processing & Clipping
        accuracy = np.clip(accuracy, 0, 100)
        first_attempt = np.clip(first_attempt, 0, 100)
        mastery = accuracy / 100
        
        data.append([
            accuracy, avg_time, first_attempt, curr_diff, sessions, 
            score_trend, mastery, is_new, engagement, active_ratio,
            tab_rate, interaction_density, session_dev, next_diff
        ])
    
    columns = [
        'accuracy', 'avg_time_per_question', 'first_attempt_correct', 'current_difficulty',
        'sessions_completed', 'score_trend', 'mastery_level', 'is_new_topic',
        'engagement_score', 'active_time_ratio', 'tab_switch_rate', 
        'interaction_density', 'session_length_dev', 'next_difficulty'
    ]
    
    return pd.DataFrame(data, columns=columns)


def train_v2_model():
    """Train the XGBoost model with 13 features"""
    print("Generating Behavioral-Focused Synthetic Data...")
    df = generate_persona_data(n_samples=10000)
    
    # Save training data
    ml_models_dir = os.path.join(os.path.dirname(__file__), 'ml_models')
    os.makedirs(ml_models_dir, exist_ok=True)
    data_path = os.path.join(ml_models_dir, 'v2_training_data.csv')
    df.to_csv(data_path, index=False)
    
    # Split features and target
    # Map next_difficulty (1,2,3) to (0,1,2) for XGBoost
    X = df.drop('next_difficulty', axis=1)
    y = df['next_difficulty'] - 1
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\nTraining XGBoost on {len(X_train)} samples with 13 features...")
    
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        objective='multi:softmax',
        num_class=3,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"\n✅ Model v2 Accuracy: {acc:.2%}")
    print("\nBehavioral Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Stay/Drop (1)', 'Stay/Med (2)', 'Stay/Hard (3)']))
    
    # Feature Importance
    importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
    print("\nFeature Importance (How much behavior matters):")
    print(importances)
    
    # Save model
    model_path = os.path.join(ml_models_dir, 'adaptive_model_v2.pkl')
    # Use joblib to save for compatibility with predictor
    joblib.dump(model, model_path)
    print(f"\n🚀 Fine-tuned Model saved to: {model_path}")
    
    return model


if __name__ == '__main__':
    train_v2_model()
