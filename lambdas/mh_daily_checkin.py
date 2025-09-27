import os
import json
import time
import uuid
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# AWS clients
s3 = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime")

# Configuration
BUCKET = os.environ.get("MH_BUCKET", "mental-health-agent")
REGION = os.environ.get("AWS_REGION", "us-east-1")


def handler(event, context):
    """
    Daily Mental Health Check-in Handler
    Collects structured mental health data through questionnaires.
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
    checkin_type = body.get("checkin_type", "custom")
    responses = body.get("responses", {})
    additional_notes = body.get("additional_notes", "")

    if not user_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing required field: user_id"}),
        }

    # Generate check-in ID
    checkin_id = f"checkin_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    try:
        # Process check-in data
        checkin_data = process_checkin_data(
            user_id, checkin_type, responses, additional_notes
        )

        # Store check-in data
        store_checkin_data(user_id, checkin_id, checkin_data)

        # Generate insights and recommendations
        insights = generate_checkin_insights(responses, checkin_type)
        recommendations = generate_immediate_recommendations(responses, checkin_type)

        # Determine next check-in suggestion
        next_checkin = suggest_next_checkin(checkin_data, user_id)

        # Return response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "checkin_id": checkin_id,
                    "message": generate_encouraging_message(checkin_data),
                    "insights": insights,
                    "recommendations": recommendations,
                    "next_checkin_suggested": next_checkin,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": "Check-in processing failed", "details": str(e)}
            ),
        }


def process_checkin_data(
    user_id: str, checkin_type: str, responses: Dict, additional_notes: str
) -> Dict[str, Any]:
    """
    Process and validate check-in data.
    """

    # Validate required fields
    required_fields = ["mood_rating", "energy_level", "sleep_quality", "stress_level"]
    for field in required_fields:
        if field not in responses:
            responses[field] = 5  # Default neutral value

    # Calculate overall wellness score
    wellness_score = calculate_wellness_score(responses)

    # Determine mood category
    mood_category = categorize_mood(responses.get("mood_rating", 5))

    # Identify areas of concern
    concerns = identify_concerns(responses)

    return {
        "user_id": user_id,
        "checkin_type": checkin_type,
        "responses": responses,
        "additional_notes": additional_notes,
        "wellness_score": wellness_score,
        "mood_category": mood_category,
        "concerns": concerns,
        "timestamp": datetime.utcnow().isoformat(),
    }


def calculate_wellness_score(responses: Dict) -> float:
    """
    Calculate overall wellness score from check-in responses.
    """
    # Weight different factors
    weights = {
        "mood_rating": 0.25,
        "energy_level": 0.20,
        "sleep_quality": 0.20,
        "stress_level": 0.20,  # Inverted - lower stress is better
        "anxiety_level": 0.10,  # Inverted - lower anxiety is better
        "social_connection": 0.05,
    }

    score = 0
    total_weight = 0

    for factor, weight in weights.items():
        if factor in responses:
            value = responses[factor]
            # Invert stress and anxiety (lower is better)
            if factor in ["stress_level", "anxiety_level"]:
                value = 11 - value  # Convert 1-10 to 10-1
            score += float(value) * weight
            total_weight += weight

    return round((score / total_weight) * 10, 1) if total_weight > 0 else 5.0


def categorize_mood(mood_rating: int) -> str:
    """
    Categorize mood rating into descriptive categories.
    """
    if mood_rating >= 8:
        return "excellent"
    elif mood_rating >= 6:
        return "good"
    elif mood_rating >= 4:
        return "neutral"
    elif mood_rating >= 2:
        return "low"
    else:
        return "very_low"


def identify_concerns(responses: Dict) -> List[str]:
    """
    Identify areas of concern based on responses.
    """
    concerns = []

    if responses.get("mood_rating", 5) <= 3:
        concerns.append("low_mood")
    if responses.get("stress_level", 5) >= 8:
        concerns.append("high_stress")
    if responses.get("anxiety_level", 5) >= 8:
        concerns.append("high_anxiety")
    if responses.get("sleep_quality", 5) <= 3:
        concerns.append("poor_sleep")
    if responses.get("energy_level", 5) <= 3:
        concerns.append("low_energy")
    if responses.get("social_connection", 5) <= 3:
        concerns.append("social_isolation")

    return concerns


def generate_checkin_insights(responses: Dict, checkin_type: str) -> str:
    """
    Generate insights about the user's responses.
    """
    wellness_score = calculate_wellness_score(responses)
    mood_category = categorize_mood(responses.get("mood_rating", 5))

    insights = []

    if wellness_score >= 7:
        insights.append("You're doing well overall! Your wellness score is strong.")
    elif wellness_score >= 5:
        insights.append("You're in a moderate state. There's room for improvement.")
    else:
        insights.append(
            "It looks like you're going through a challenging time. Remember, this is temporary."
        )

    # Add specific insights
    if responses.get("gratitude"):
        insights.append(
            f"It's wonderful that you're grateful for: {responses['gratitude']}"
        )

    if responses.get("challenges"):
        insights.append(
            "I notice you mentioned some challenges. It's brave to acknowledge them."
        )

    return " ".join(insights)


def generate_immediate_recommendations(responses: Dict, checkin_type: str) -> List[str]:
    """
    Generate immediate recommendations based on check-in responses.
    """
    recommendations = []
    concerns = identify_concerns(responses)

    if "high_stress" in concerns:
        recommendations.append(
            "Try some deep breathing exercises or a short meditation"
        )
        recommendations.append(
            "Consider taking a 10-minute break to step away from stressors"
        )

    if "low_mood" in concerns:
        recommendations.append("Listen to some uplifting music or watch a funny video")
        recommendations.append("Reach out to a friend or family member for support")

    if "poor_sleep" in concerns:
        recommendations.append("Try establishing a relaxing bedtime routine")
        recommendations.append("Avoid screens 1 hour before bed")

    if "low_energy" in concerns:
        recommendations.append("Take a short walk or do some light stretching")
        recommendations.append("Make sure you're staying hydrated")

    if "high_anxiety" in concerns:
        recommendations.append("Practice grounding techniques (5-4-3-2-1 method)")
        recommendations.append("Try progressive muscle relaxation")

    if not concerns:
        recommendations.append(
            "Keep up the great work! Continue with your current positive habits"
        )
        recommendations.append("Consider sharing your positive energy with others")

    return recommendations[:3]  # Limit to 3 recommendations


def suggest_next_checkin(checkin_data: Dict, user_id: str) -> str:
    """
    Suggest when the next check-in should be.
    """
    wellness_score = checkin_data["wellness_score"]
    concerns = checkin_data["concerns"]

    if wellness_score < 4 or len(concerns) >= 3:
        # High concern - suggest tomorrow
        next_date = datetime.utcnow() + timedelta(days=1)
        return f"Tomorrow at the same time ({next_date.strftime('%H:%M')})"
    elif wellness_score < 6 or len(concerns) >= 1:
        # Moderate concern - suggest in 2 days
        next_date = datetime.utcnow() + timedelta(days=2)
        return f"In 2 days ({next_date.strftime('%Y-%m-%d')})"
    else:
        # Good state - suggest in a week
        next_date = datetime.utcnow() + timedelta(days=7)
        return f"In a week ({next_date.strftime('%Y-%m-%d')})"


def generate_encouraging_message(checkin_data: Dict) -> str:
    """
    Generate an encouraging message based on check-in data.
    """
    wellness_score = checkin_data["wellness_score"]
    mood_category = checkin_data["mood_category"]

    if wellness_score >= 7:
        return "Thank you for checking in! It's wonderful to hear you're doing well. Keep up the great work!"
    elif wellness_score >= 5:
        return "Thank you for sharing how you're feeling. You're taking important steps toward better mental health."
    else:
        return "Thank you for being honest about how you're feeling. Remember, you're not alone, and it's okay to not be okay."


def store_checkin_data(user_id: str, checkin_id: str, checkin_data: Dict):
    """
    Store check-in data in S3 for analysis and tracking.
    """
    try:
        # Store individual check-in
        key = f"checkins/{user_id}/{checkin_id}.json"
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(checkin_data, ensure_ascii=False),
            ContentType="application/json",
        )

        # Update user's check-in history
        update_user_checkin_history(user_id, checkin_data)

    except Exception as e:
        print(f"Failed to store check-in data: {str(e)}")


def update_user_checkin_history(user_id: str, checkin_data: Dict):
    """
    Update user's check-in history for trend analysis.
    """
    try:
        history_key = f"users/{user_id}/checkin_history.json"

        # Try to get existing history
        try:
            response = s3.get_object(Bucket=BUCKET, Key=history_key)
            history = json.loads(response["Body"].read())
        except:
            history = {"checkins": [], "created_at": datetime.utcnow().isoformat()}

        # Add new check-in
        history["checkins"].append(
            {
                "checkin_id": checkin_data.get("checkin_id", ""),
                "timestamp": checkin_data["timestamp"],
                "wellness_score": checkin_data["wellness_score"],
                "mood_category": checkin_data["mood_category"],
                "concerns": checkin_data["concerns"],
            }
        )

        # Keep only last 30 check-ins
        history["checkins"] = history["checkins"][-30:]
        history["updated_at"] = datetime.utcnow().isoformat()

        # Store updated history
        s3.put_object(
            Bucket=BUCKET,
            Key=history_key,
            Body=json.dumps(history, ensure_ascii=False),
            ContentType="application/json",
        )

    except Exception as e:
        print(f"Failed to update check-in history: {str(e)}")


# Local testing
if __name__ == "__main__":
    test_event = {
        "body": json.dumps(
            {
                "user_id": "test_user_123",
                "checkin_type": "morning",
                "responses": {
                    "mood_rating": 6,
                    "energy_level": 5,
                    "sleep_quality": 7,
                    "stress_level": 6,
                    "anxiety_level": 4,
                    "social_connection": 7,
                    "productivity": 6,
                    "gratitude": "Having a good cup of coffee",
                    "challenges": "Work presentation tomorrow",
                    "goals": "Finish the presentation",
                },
                "additional_notes": "Feeling a bit nervous about the presentation",
            }
        )
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
