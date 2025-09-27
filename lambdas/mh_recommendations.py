import os
import json
import time
import uuid
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any

# AWS clients
s3 = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime")

# Configuration
BUCKET = os.environ.get("MH_BUCKET", "mental-health-agent")
REGION = os.environ.get("AWS_REGION", "us-east-1")

# Content database (in a real implementation, this would be in a database)
CONTENT_DATABASE = {
    "funny_videos": [
        {
            "title": "Funny Cat Compilation",
            "type": "video",
            "description": (
                "A collection of hilarious cat videos to brighten your day"
            ),
            "url": "https://example.com/funny-cats",
            "duration": "5 minutes",
            "difficulty": "beginner",
            "mood_benefit": "laughter and joy",
            "priority": "high",
        },
        {
            "title": "Stand-up Comedy Special",
            "type": "video",
            "description": "Light-hearted comedy to lift your spirits",
            "url": "https://example.com/comedy-special",
            "duration": "30 minutes",
            "difficulty": "beginner",
            "mood_benefit": "humor and entertainment",
            "priority": "medium",
        },
    ],
    "yoga_videos": [
        {
            "title": "Gentle Morning Yoga",
            "type": "video",
            "description": "Peaceful yoga flow to start your day with calm energy",
            "url": "https://example.com/morning-yoga",
            "duration": "15 minutes",
            "difficulty": "beginner",
            "mood_benefit": "calm and centered",
            "priority": "high",
        },
        {
            "title": "Stress Relief Yoga",
            "type": "video",
            "description": "Yoga poses specifically designed to reduce stress and tension",
            "url": "https://example.com/stress-yoga",
            "duration": "20 minutes",
            "difficulty": "beginner",
            "mood_benefit": "stress reduction",
            "priority": "high",
        },
        {
            "title": "Bedtime Yoga Flow",
            "type": "video",
            "description": "Relaxing yoga sequence to prepare for restful sleep",
            "url": "https://example.com/bedtime-yoga",
            "duration": "25 minutes",
            "difficulty": "beginner",
            "mood_benefit": "relaxation and sleep preparation",
            "priority": "medium",
        },
    ],
    "meditation": [
        {
            "title": "5-Minute Breathing Meditation",
            "type": "audio",
            "description": "Quick breathing exercise to center yourself",
            "url": "https://example.com/breathing-meditation",
            "duration": "5 minutes",
            "difficulty": "beginner",
            "mood_benefit": "calm and focus",
            "priority": "high",
        },
        {
            "title": "Body Scan Relaxation",
            "type": "audio",
            "description": "Progressive relaxation technique to release tension",
            "url": "https://example.com/body-scan",
            "duration": "15 minutes",
            "difficulty": "beginner",
            "mood_benefit": "deep relaxation",
            "priority": "medium",
        },
    ],
    "breathing_exercises": [
        {
            "title": "4-7-8 Breathing Technique",
            "type": "interactive",
            "description": "Simple breathing pattern to reduce anxiety and stress",
            "url": "https://example.com/478-breathing",
            "duration": "3 minutes",
            "difficulty": "beginner",
            "mood_benefit": "anxiety reduction",
            "priority": "high",
        },
        {
            "title": "Box Breathing Exercise",
            "type": "interactive",
            "description": "Equal breathing pattern for calm and focus",
            "url": "https://example.com/box-breathing",
            "duration": "5 minutes",
            "difficulty": "beginner",
            "mood_benefit": "focus and calm",
            "priority": "medium",
        },
    ],
    "music": [
        {
            "title": "Nature Sounds Playlist",
            "type": "audio",
            "description": "Soothing sounds of nature for relaxation",
            "url": "https://example.com/nature-sounds",
            "duration": "60 minutes",
            "difficulty": "beginner",
            "mood_benefit": "peace and tranquility",
            "priority": "medium",
        },
        {
            "title": "Upbeat Motivation Music",
            "type": "audio",
            "description": "Energetic music to boost your mood and motivation",
            "url": "https://example.com/motivation-music",
            "duration": "45 minutes",
            "difficulty": "beginner",
            "mood_benefit": "energy and motivation",
            "priority": "medium",
        },
    ],
    "activities": [
        {
            "title": "Gratitude Journaling",
            "type": "text",
            "description": "Write down three things you're grateful for today",
            "url": "https://example.com/gratitude-journal",
            "duration": "10 minutes",
            "difficulty": "beginner",
            "mood_benefit": "positive mindset",
            "priority": "high",
        },
        {
            "title": "Mindful Walking",
            "type": "interactive",
            "description": "Take a 10-minute mindful walk to clear your mind",
            "url": "https://example.com/mindful-walking",
            "duration": "10 minutes",
            "difficulty": "beginner",
            "mood_benefit": "clarity and movement",
            "priority": "medium",
        },
    ],
}


def handler(event, context):
    """
    Personalized Mental Health Recommendations Handler
    Provides tailored recommendations based on user's mental health status and preferences.
    """

    # Parse request body
    try:
        if event and "body" in event and event["body"]:
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
        else:
            body = {}
    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid request body", "details": str(e)}),
        }

    # Extract parameters
    user_id = body.get("user_id")
    recommendation_type = body.get("recommendation_type", "immediate")
    current_mood = body.get("current_mood", "neutral")
    preferences = body.get("preferences", {})
    urgency_level = body.get("urgency_level", "medium")

    if not user_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing required field: user_id"}),
        }

    # Generate recommendation ID
    recommendation_id = f"rec_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    try:
        # Get user's mental health context
        user_context = get_user_mental_health_context(user_id)

        # Generate personalized recommendations
        recommendations = generate_personalized_recommendations(
            recommendation_type,
            current_mood,
            preferences,
            urgency_level,
            user_context,
        )

        # Generate personalized message
        personalized_message = generate_personalized_message(
            current_mood, recommendations, user_context
        )

        # Generate follow-up suggestions
        follow_up_suggestions = generate_follow_up_suggestions(
            recommendation_type, current_mood
        )

        # Store recommendations
        store_recommendations(user_id, recommendation_id, recommendations, user_context)

        # Return response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "recommendation_id": recommendation_id,
                    "recommendations": recommendations,
                    "personalized_message": personalized_message,
                    "follow_up_suggestions": follow_up_suggestions,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": "Recommendation generation failed", "details": str(e)}
            ),
        }


def get_user_mental_health_context(user_id: str) -> Dict[str, Any]:
    """
    Get user's recent mental health context from stored data.
    """
    try:
        # Get recent check-in data
        history_key = f"users/{user_id}/checkin_history.json"
        response = s3.get_object(Bucket=BUCKET, Key=history_key)
        history = json.loads(response["Body"].read())

        recent_checkins = history.get("checkins", [])[-5:]  # Last 5 check-ins

        # Get recent evaluation
        evaluations_key = f"evaluations/{user_id}/"
        eval_response = s3.list_objects_v2(Bucket=BUCKET, Prefix=evaluations_key)

        latest_evaluation = None
        if eval_response.get("Contents"):
            # Get the most recent evaluation
            latest_eval_key = max(
                eval_response["Contents"], key=lambda x: x["LastModified"]
            )["Key"]
            eval_data = s3.get_object(Bucket=BUCKET, Key=latest_eval_key)
            latest_evaluation = json.loads(eval_data["Body"].read())

        return {
            "recent_checkins": recent_checkins,
            "latest_evaluation": latest_evaluation,
            "user_id": user_id,
        }

    except Exception as e:
        print(f"Failed to get user context: {str(e)}")
        return {"recent_checkins": [], "latest_evaluation": None, "user_id": user_id}


def generate_personalized_recommendations(
    recommendation_type: str,
    current_mood: str,
    preferences: Dict,
    urgency_level: str,
    user_context: Dict,
) -> List[Dict[str, Any]]:
    """
    Generate personalized recommendations based on user's needs.
    """

    recommendations = []

    # Determine content types based on preferences
    preferred_content_types = preferences.get("content_types", ["video", "audio"])
    preferred_duration = preferences.get("duration", "medium")
    preferred_activity_level = preferences.get("activity_level", "moderate")

    # Map duration preferences
    duration_map = {
        "short": ["5 minutes", "3 minutes", "10 minutes"],
        "medium": ["15 minutes", "20 minutes", "25 minutes"],
        "long": ["30 minutes", "45 minutes", "60 minutes"],
    }

    # Get relevant content based on recommendation type and mood
    content_categories = get_content_categories_for_needs(
        recommendation_type, current_mood, urgency_level
    )

    # Filter and rank content
    for category in content_categories:
        if category in CONTENT_DATABASE:
            for content in CONTENT_DATABASE[category]:
                # Check if content matches preferences
                if content["type"] in preferred_content_types:
                    if preferred_duration == "any" or content[
                        "duration"
                    ] in duration_map.get(preferred_duration, []):
                        # Add priority boost based on urgency and mood match
                        priority_score = calculate_priority_score(
                            content, current_mood, urgency_level, user_context
                        )
                        content_with_score = content.copy()
                        content_with_score["priority_score"] = priority_score
                        recommendations.append(content_with_score)

    # Sort by priority score and return top recommendations
    recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
    return recommendations[:5]  # Return top 5 recommendations


def get_content_categories_for_needs(
    recommendation_type: str, current_mood: str, urgency_level: str
) -> List[str]:
    """
    Determine which content categories are most relevant for the user's needs.
    """
    categories = []

    # Base categories on recommendation type
    if recommendation_type == "stress_relief":
        categories.extend(["breathing_exercises", "meditation", "yoga_videos"])
    elif recommendation_type == "mood_boost":
        categories.extend(["funny_videos", "music", "activities"])
    elif recommendation_type == "sleep_aid":
        categories.extend(["meditation", "music", "yoga_videos"])
    elif recommendation_type == "immediate":
        categories.extend(["breathing_exercises", "funny_videos", "music"])
    elif recommendation_type == "daily":
        categories.extend(["yoga_videos", "meditation", "activities"])
    elif recommendation_type == "weekly":
        categories.extend(["activities", "music", "yoga_videos"])

    # Adjust based on current mood
    if current_mood in ["sad", "depressed", "low"]:
        categories.extend(["funny_videos", "music", "activities"])
    elif current_mood in ["anxious", "stressed", "overwhelmed"]:
        categories.extend(["breathing_exercises", "meditation", "yoga_videos"])
    elif current_mood in ["tired", "exhausted"]:
        categories.extend(["meditation", "music", "activities"])

    # Adjust based on urgency
    if urgency_level == "high":
        categories = ["breathing_exercises", "funny_videos"] + categories

    return list(set(categories))  # Remove duplicates


def calculate_priority_score(
    content: Dict, current_mood: str, urgency_level: str, user_context: Dict
) -> int:
    """
    Calculate priority score for content recommendation.
    """
    score = 0

    # Base priority from content
    priority_map = {"high": 3, "medium": 2, "low": 1}
    score += priority_map.get(content.get("priority", "medium"), 2)

    # Mood benefit matching
    mood_benefit = content.get("mood_benefit", "").lower()
    if current_mood in ["sad", "depressed"] and "joy" in mood_benefit:
        score += 2
    elif current_mood in ["anxious", "stressed"] and "calm" in mood_benefit:
        score += 2
    elif current_mood in ["tired"] and "energy" in mood_benefit:
        score += 2

    # Urgency boost
    if urgency_level == "high" and content.get("duration") in [
        "3 minutes",
        "5 minutes",
    ]:
        score += 2

    # User context boost
    if user_context.get("latest_evaluation"):
        overall_score = user_context["latest_evaluation"].get("overall_score", 50)
        if overall_score < 40 and "relaxation" in mood_benefit:
            score += 1

    return score


def generate_personalized_message(
    current_mood: str, recommendations: List[Dict], user_context: Dict
) -> str:
    """
    Generate a personalized, encouraging message for the user.
    """

    # Base message on current mood
    mood_messages = {
        "happy": "It's wonderful to see you're feeling good! Here are some recommendations to keep that positive energy flowing.",
        "sad": "I understand you're going through a tough time. These recommendations are designed to help lift your spirits and provide comfort.",
        "anxious": "Feeling anxious can be overwhelming. These gentle activities are specifically chosen to help you find calm and peace.",
        "stressed": "Stress can take a toll on both mind and body. These recommendations focus on relaxation and stress relief.",
        "tired": "When you're feeling tired, it's important to be gentle with yourself. These activities are designed to restore your energy naturally.",
        "neutral": "Here are some personalized recommendations to help you feel your best today.",
    }

    base_message = mood_messages.get(current_mood, mood_messages["neutral"])

    # Add context from user's situation
    if user_context.get("latest_evaluation"):
        overall_score = user_context["latest_evaluation"].get("overall_score", 50)
        if overall_score < 40:
            base_message += " Remember, taking care of your mental health is a journey, and every small step counts."
        elif overall_score > 70:
            base_message += " You're doing great with your mental health journey!"

    # Add encouragement based on recommendations
    if recommendations:
        top_rec = recommendations[0]
        if (
            top_rec.get("type") == "video"
            and "funny" in top_rec.get("title", "").lower()
        ):
            base_message += " Sometimes a good laugh is exactly what we need!"
        elif "breathing" in top_rec.get("title", "").lower():
            base_message += (
                " Deep breathing can be incredibly powerful for calming your mind."
            )

    return base_message


def generate_follow_up_suggestions(
    recommendation_type: str, current_mood: str
) -> List[str]:
    """
    Generate follow-up suggestions for the user.
    """
    suggestions = []

    if recommendation_type == "immediate":
        suggestions.append(
            "Try one of these recommendations right now and see how you feel"
        )
        suggestions.append("Set a reminder to check in with yourself in an hour")
    elif recommendation_type == "daily":
        suggestions.append(
            "Consider making one of these activities part of your daily routine"
        )
        suggestions.append(
            "Track how these activities affect your mood over the next few days"
        )
    elif recommendation_type == "stress_relief":
        suggestions.append(
            "Practice these stress-relief techniques regularly, not just when you're stressed"
        )
        suggestions.append(
            "Notice which techniques work best for you and keep them handy"
        )

    # Mood-specific suggestions
    if current_mood in ["sad", "depressed"]:
        suggestions.append("Consider reaching out to a friend or family member today")
    elif current_mood in ["anxious", "stressed"]:
        suggestions.append(
            "Remember that these feelings are temporary and you have tools to manage them"
        )

    return suggestions[:3]  # Limit to 3 suggestions


def store_recommendations(
    user_id: str,
    recommendation_id: str,
    recommendations: List[Dict],
    user_context: Dict,
):
    """
    Store recommendations for future reference and analysis.
    """
    try:
        recommendation_data = {
            "recommendation_id": recommendation_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "recommendations": recommendations,
            "user_context": user_context,
        }

        key = f"recommendations/{user_id}/{recommendation_id}.json"
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(recommendation_data, ensure_ascii=False),
            ContentType="application/json",
        )

    except Exception as e:
        print(f"Failed to store recommendations: {str(e)}")


# Local testing
if __name__ == "__main__":
    test_event = {
        "body": json.dumps(
            {
                "user_id": "test_user_123",
                "recommendation_type": "stress_relief",
                "current_mood": "anxious",
                "preferences": {
                    "content_types": ["video", "audio"],
                    "duration": "short",
                    "activity_level": "low",
                },
                "urgency_level": "high",
            }
        )
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
