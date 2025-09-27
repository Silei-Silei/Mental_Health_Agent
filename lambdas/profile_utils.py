"""
User Profile Utilities
Shared functions for user profile management across all Lambda functions.
"""

import os
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics

# AWS clients
s3 = boto3.client("s3")

# Configuration
BUCKET = os.environ.get("MH_BUCKET", "mental-health-agent")


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Retrieve user profile from S3. Creates default profile if doesn't exist.
    """
    try:
        profile_key = f"profiles/{user_id}/profile.json"
        response = s3.get_object(Bucket=BUCKET, Key=profile_key)
        profile = json.loads(response["Body"].read())
        return profile
    except Exception as e:
        print(f"Profile not found for user {user_id}, creating default: {str(e)}")
        return create_default_profile(user_id)


def create_default_profile(user_id: str) -> Dict[str, Any]:
    """
    Create a default user profile for new users.
    """
    default_profile = {
        "user_id": user_id,
        "profile_created": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat(),
        "profile_version": "1.0",
        "demographics": {
            "age_range": "unknown",
            "timezone": "UTC",
            "preferred_language": "en",
        },
        "mental_health_baseline": {
            "average_mood_rating": 5.0,
            "average_stress_level": 5.0,
            "average_energy_level": 5.0,
            "average_sleep_quality": 5.0,
            "average_anxiety_level": 5.0,
            "average_social_connection": 5.0,
            "average_productivity": 5.0,
            "typical_concerns": [],
            "strengths": [],
            "data_points_count": 0,
        },
        "communication_patterns": {
            "preferred_response_style": "supportive",
            "common_emotional_states": [],
            "effective_coping_strategies": [],
            "conversation_frequency": "unknown",
            "response_length_preference": "medium",
            "total_conversations": 0,
        },
        "content_preferences": {
            "preferred_content_types": ["video", "audio"],
            "preferred_duration": "medium",
            "preferred_activity_level": "moderate",
            "effective_recommendations": [],
            "ineffective_recommendations": [],
            "recommendation_interactions": 0,
        },
        "behavioral_patterns": {
            "checkin_consistency": 0.0,
            "preferred_checkin_times": ["09:00", "18:00"],
            "engagement_level": "unknown",
            "response_time_pattern": "unknown",
            "total_checkins": 0,
        },
        "mental_health_insights": {
            "risk_factors": [],
            "protective_factors": [],
            "triggers": [],
            "warning_signs": [],
            "last_evaluation_score": None,
            "trend_direction": "stable",
        },
        "personalization_data": {
            "custom_greetings": [],
            "personalized_encouragements": [],
            "contextual_suggestions": [],
            "learning_notes": [],
        },
    }

    # Store the default profile
    store_user_profile(user_id, default_profile)
    return default_profile


def store_user_profile(user_id: str, profile: Dict[str, Any]):
    """
    Store user profile in S3.
    """
    try:
        profile["last_updated"] = datetime.utcnow().isoformat()
        profile_key = f"profiles/{user_id}/profile.json"

        s3.put_object(
            Bucket=BUCKET,
            Key=profile_key,
            Body=json.dumps(profile, ensure_ascii=False),
            ContentType="application/json",
        )

        print(f"Profile stored for user {user_id}")

    except Exception as e:
        print(f"Failed to store profile for user {user_id}: {str(e)}")


def update_profile_from_checkin(user_id: str, checkin_data: Dict[str, Any]):
    """
    Update user profile based on check-in data.
    """
    profile = get_user_profile(user_id)
    baseline = profile["mental_health_baseline"]

    # Update baseline metrics with weighted average
    responses = checkin_data.get("responses", {})
    data_count = baseline["data_points_count"]

    if data_count == 0:
        # First check-in, set initial values
        baseline["average_mood_rating"] = responses.get("mood_rating", 5)
        baseline["average_stress_level"] = responses.get("stress_level", 5)
        baseline["average_energy_level"] = responses.get("energy_level", 5)
        baseline["average_sleep_quality"] = responses.get("sleep_quality", 5)
        baseline["average_anxiety_level"] = responses.get("anxiety_level", 5)
        baseline["average_social_connection"] = responses.get("social_connection", 5)
        baseline["average_productivity"] = responses.get("productivity", 5)
    else:
        # Update with weighted average (more weight to recent data)
        weight = min(0.3, 1.0 / (data_count + 1))  # Decreasing weight

        baseline["average_mood_rating"] = (1 - weight) * baseline[
            "average_mood_rating"
        ] + weight * responses.get("mood_rating", baseline["average_mood_rating"])
        baseline["average_stress_level"] = (1 - weight) * baseline[
            "average_stress_level"
        ] + weight * responses.get("stress_level", baseline["average_stress_level"])
        baseline["average_energy_level"] = (1 - weight) * baseline[
            "average_energy_level"
        ] + weight * responses.get("energy_level", baseline["average_energy_level"])
        baseline["average_sleep_quality"] = (1 - weight) * baseline[
            "average_sleep_quality"
        ] + weight * responses.get("sleep_quality", baseline["average_sleep_quality"])
        baseline["average_anxiety_level"] = (1 - weight) * baseline[
            "average_anxiety_level"
        ] + weight * responses.get("anxiety_level", baseline["average_anxiety_level"])
        baseline["average_social_connection"] = (1 - weight) * baseline[
            "average_social_connection"
        ] + weight * responses.get(
            "social_connection", baseline["average_social_connection"]
        )
        baseline["average_productivity"] = (1 - weight) * baseline[
            "average_productivity"
        ] + weight * responses.get("productivity", baseline["average_productivity"])

    baseline["data_points_count"] += 1

    # Update concerns and strengths
    concerns = checkin_data.get("concerns", [])
    for concern in concerns:
        if concern not in baseline["typical_concerns"]:
            baseline["typical_concerns"].append(concern)

    # Update behavioral patterns
    profile["behavioral_patterns"]["total_checkins"] += 1

    # Store updated profile
    store_user_profile(user_id, profile)


def update_profile_from_chat(user_id: str, chat_data: Dict[str, Any]):
    """
    Update user profile based on chat conversation data.
    """
    profile = get_user_profile(user_id)
    comm_patterns = profile["communication_patterns"]

    # Update conversation count
    comm_patterns["total_conversations"] += 1

    # Update emotional states
    mood_detected = chat_data.get("mood_detected", "neutral")
    if mood_detected not in comm_patterns["common_emotional_states"]:
        comm_patterns["common_emotional_states"].append(mood_detected)

    # Keep only top 5 most common emotional states
    comm_patterns["common_emotional_states"] = comm_patterns["common_emotional_states"][
        -5:
    ]

    # Update conversation frequency
    if comm_patterns["total_conversations"] > 1:
        comm_patterns["conversation_frequency"] = "regular"

    # Store updated profile
    store_user_profile(user_id, profile)


def update_profile_from_recommendations(
    user_id: str, recommendation_data: Dict[str, Any]
):
    """
    Update user profile based on recommendation interactions.
    """
    profile = get_user_profile(user_id)
    content_prefs = profile["content_preferences"]

    # Update recommendation interactions count
    content_prefs["recommendation_interactions"] += 1

    # Track effective recommendations (simplified - in real implementation, you'd track user feedback)
    recommendations = recommendation_data.get("recommendations", [])
    for rec in recommendations:
        rec_title = rec.get("title", "")
        if rec_title and rec_title not in content_prefs["effective_recommendations"]:
            content_prefs["effective_recommendations"].append(rec_title)

    # Keep only recent effective recommendations
    content_prefs["effective_recommendations"] = content_prefs[
        "effective_recommendations"
    ][-10:]

    # Store updated profile
    store_user_profile(user_id, profile)


def update_profile_from_evaluation(user_id: str, evaluation_data: Dict[str, Any]):
    """
    Update user profile based on mental health evaluation results.
    """
    profile = get_user_profile(user_id)
    insights = profile["mental_health_insights"]

    # Update evaluation score
    insights["last_evaluation_score"] = evaluation_data.get("overall_score")

    # Update risk factors and strengths
    risk_factors = evaluation_data.get("risk_factors", [])
    strengths = evaluation_data.get("strengths", [])

    insights["risk_factors"] = list(set(insights["risk_factors"] + risk_factors))
    insights["strengths"] = list(set(insights["strengths"] + strengths))

    # Update trend direction
    insights["trend_direction"] = evaluation_data.get("mood_trend", "stable")

    # Store updated profile
    store_user_profile(user_id, profile)


def get_profile_insights(user_id: str) -> Dict[str, Any]:
    """
    Generate insights from user profile data.
    """
    profile = get_user_profile(user_id)

    insights = {
        "user_id": user_id,
        "profile_age_days": calculate_profile_age(profile),
        "engagement_level": calculate_engagement_level(profile),
        "mental_health_trends": analyze_mental_health_trends(profile),
        "personalization_recommendations": generate_personalization_recommendations(
            profile
        ),
        "profile_completeness": calculate_profile_completeness(profile),
    }

    return insights


def calculate_profile_age(profile: Dict[str, Any]) -> int:
    """Calculate how many days since profile creation."""
    try:
        created_date = datetime.fromisoformat(profile["profile_created"])
        return (datetime.utcnow() - created_date).days
    except:
        return 0


def calculate_engagement_level(profile: Dict[str, Any]) -> str:
    """Calculate user engagement level based on activity."""
    total_interactions = (
        profile["mental_health_baseline"]["data_points_count"]
        + profile["communication_patterns"]["total_conversations"]
        + profile["content_preferences"]["recommendation_interactions"]
    )

    if total_interactions >= 20:
        return "high"
    elif total_interactions >= 10:
        return "medium"
    elif total_interactions >= 3:
        return "low"
    else:
        return "new"


def analyze_mental_health_trends(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze mental health trends from profile data."""
    baseline = profile["mental_health_baseline"]
    insights = profile["mental_health_insights"]

    return {
        "current_baseline": {
            "mood": baseline["average_mood_rating"],
            "stress": baseline["average_stress_level"],
            "energy": baseline["average_energy_level"],
            "sleep": baseline["average_sleep_quality"],
        },
        "trend_direction": insights["trend_direction"],
        "primary_concerns": baseline["typical_concerns"],
        "key_strengths": baseline["strengths"],
        "risk_level": (
            "high"
            if len(insights["risk_factors"]) >= 3
            else "moderate" if len(insights["risk_factors"]) >= 1 else "low"
        ),
    }


def generate_personalization_recommendations(profile: Dict[str, Any]) -> List[str]:
    """Generate recommendations for improving personalization."""
    recommendations = []

    # Check profile completeness
    if profile["mental_health_baseline"]["data_points_count"] < 5:
        recommendations.append(
            "Encourage more frequent check-ins to build better baseline"
        )

    if profile["communication_patterns"]["total_conversations"] < 3:
        recommendations.append(
            "Promote chat feature to understand communication preferences"
        )

    if profile["content_preferences"]["recommendation_interactions"] < 2:
        recommendations.append(
            "Increase recommendation engagement to learn content preferences"
        )

    # Check for patterns
    if len(profile["mental_health_baseline"]["typical_concerns"]) > 0:
        recommendations.append(
            "Focus on addressing recurring concerns in recommendations"
        )

    return recommendations


def calculate_profile_completeness(profile: Dict[str, Any]) -> float:
    """Calculate profile completeness percentage."""
    total_fields = 0
    completed_fields = 0

    # Check baseline data
    baseline = profile["mental_health_baseline"]
    if baseline["data_points_count"] > 0:
        completed_fields += 1
    total_fields += 1

    # Check communication patterns
    comm = profile["communication_patterns"]
    if comm["total_conversations"] > 0:
        completed_fields += 1
    total_fields += 1

    # Check content preferences
    content = profile["content_preferences"]
    if content["recommendation_interactions"] > 0:
        completed_fields += 1
    total_fields += 1

    # Check behavioral patterns
    behavior = profile["behavioral_patterns"]
    if behavior["total_checkins"] > 0:
        completed_fields += 1
    total_fields += 1

    return (completed_fields / total_fields) * 100 if total_fields > 0 else 0


def get_personalized_context(user_id: str, context_type: str) -> str:
    """
    Get personalized context for different use cases.
    """
    profile = get_user_profile(user_id)

    if context_type == "chat":
        comm_patterns = profile["communication_patterns"]
        baseline = profile["mental_health_baseline"]

        context = f"""User Profile Context:
- Preferred response style: {comm_patterns['preferred_response_style']}
- Common emotional states: {', '.join(comm_patterns['common_emotional_states'][-3:])}
- Average mood rating: {baseline['average_mood_rating']:.1f}/10
- Average stress level: {baseline['average_stress_level']:.1f}/10
- Total conversations: {comm_patterns['total_conversations']}"""

        return context

    elif context_type == "recommendations":
        content_prefs = profile["content_preferences"]
        effective_recs = content_prefs["effective_recommendations"]

        context = f"""User Content Preferences:
- Preferred content types: {', '.join(content_prefs['preferred_content_types'])}
- Preferred duration: {content_prefs['preferred_duration']}
- Effective recommendations: {', '.join(effective_recs[-3:])}
- Total recommendation interactions: {content_prefs['recommendation_interactions']}"""

        return context

    elif context_type == "evaluation":
        insights = profile["mental_health_insights"]
        baseline = profile["mental_health_baseline"]

        context = f"""User Mental Health Profile:
- Baseline mood: {baseline['average_mood_rating']:.1f}/10
- Baseline stress: {baseline['average_stress_level']:.1f}/10
- Risk factors: {', '.join(insights['risk_factors'])}
- Strengths: {', '.join(insights['strengths'])}
- Last evaluation score: {insights['last_evaluation_score'] or 'N/A'}
- Trend direction: {insights['trend_direction']}"""

        return context

    return "No specific context available"


# Local testing
if __name__ == "__main__":
    # Test profile creation and updates
    test_user_id = "test_user_profile"

    # Create default profile
    profile = create_default_profile(test_user_id)
    print("Created default profile:", json.dumps(profile, indent=2))

    # Test profile insights
    insights = get_profile_insights(test_user_id)
    print("Profile insights:", json.dumps(insights, indent=2))
