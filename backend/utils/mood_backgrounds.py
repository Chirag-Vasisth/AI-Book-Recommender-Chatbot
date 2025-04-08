from typing import Dict

def get_mood_context(mood: str) -> str:
    """
    Get contextual prompt based on user's selected mood.
    
    Args:
        mood: Selected mood from UI
    
    Returns:
        Context string for the prompt
    """
    mood_contexts = {
        'default': 'The user hasn\'t specified a particular mood.',
        'adventurous': 'The user is in an adventurous mood and might enjoy exciting, fast-paced books.',
        'romantic': 'The user is in a romantic mood and might enjoy love stories or emotional narratives.',
        'mysterious': 'The user is in a mysterious mood and might enjoy thrillers, mysteries, or suspenseful books.',
        'thoughtful': 'The user is in a thoughtful mood and might enjoy philosophical, literary, or intellectually stimulating books.'
    }
    
    return mood_contexts.get(mood.lower(), mood_contexts['default'])