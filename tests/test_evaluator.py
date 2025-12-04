import sys
import os
# Ensure project root is on sys.path for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from src.video_evaluator import VideoEvaluator, AIProvider


def test_evaluate_sample_transcript():
    evaluator = VideoEvaluator(rubric_path="rubrics/sample-rubric.json", provider=AIProvider.ANTHROPIC, enable_vision=False)
    # Bypass audio processing by calling evaluation directly
    transcript = """This demo shows how to log in, navigate to the dashboard, and create a report. The demo explains the main metrics and how to filter by date."""
    result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])
    assert 'scores' in result
    assert 'overall' in result
    assert 'short_summary' in result


def test_generate_qualitative_feedback():
    evaluator = VideoEvaluator(rubric_path="rubrics/default.json", provider=AIProvider.OPENAI, enable_vision=False)
    
    # Create a mock evaluation with passing score
    passing_evaluation = {
        'scores': {
            'technical_accuracy': {'score': 9, 'note': 'Excellent technical detail'},
            'clarity': {'score': 8, 'note': 'Very clear explanation'},
            'completeness': {'score': 7, 'note': 'Good coverage'},
            'production_quality': {'score': 6, 'note': 'Adequate quality'},
            'value_demonstration': {'score': 8, 'note': 'Strong value prop'},
            'multimodal_alignment': {'score': 7, 'note': 'Good alignment'}
        },
        'overall': {
            'weighted_score': 7.8,
            'method': 'weighted_mean',
            'pass_status': 'pass'
        }
    }
    
    transcript = """This demo shows excellent technical depth with clear explanations of each feature."""
    
    feedback = evaluator.generate_qualitative_feedback(transcript, passing_evaluation)
    
    # Check structure
    assert 'strengths' in feedback
    assert 'improvements' in feedback
    assert 'tone' in feedback
    
    # Check content
    assert len(feedback['strengths']) == 2
    assert len(feedback['improvements']) == 2
    assert feedback['tone'] == 'congratulatory'
    
    # Check each strength has required fields
    for strength in feedback['strengths']:
        assert 'title' in strength
        assert 'description' in strength
    
    # Check each improvement has required fields
    for improvement in feedback['improvements']:
        assert 'title' in improvement
        assert 'description' in improvement


def test_generate_feedback_failing_score():
    evaluator = VideoEvaluator(rubric_path="rubrics/sample-rubric.json", provider=AIProvider.ANTHROPIC, enable_vision=False)
    
    # Create a mock evaluation with failing score
    failing_evaluation = {
        'scores': {
            'technical_accuracy': {'score': 4, 'note': 'Lacks technical detail'},
            'clarity': {'score': 5, 'note': 'Could be clearer'},
            'completeness': {'score': 4, 'note': 'Missing key points'},
            'production_quality': {'score': 6, 'note': 'Adequate quality'},
            'value_demonstration': {'score': 5, 'note': 'Weak value prop'},
            'multimodal_alignment': {'score': 5, 'note': 'Some misalignment'}
        },
        'overall': {
            'weighted_score': 4.8,
            'method': 'weighted_mean',
            'pass_status': 'fail'
        }
    }
    
    transcript = """This demo needs improvement in several areas."""
    
    feedback = evaluator.generate_qualitative_feedback(transcript, failing_evaluation)
    
    # For failing score, tone should be supportive
    assert feedback['tone'] == 'supportive'
    assert len(feedback['strengths']) == 2
    assert len(feedback['improvements']) == 2

