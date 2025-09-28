import os
import json
import time
import uuid
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics

# AWS clients
s3 = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime")

# Configuration
BUCKET = os.environ.get("MH_BUCKET", "mental-health-agent")
REGION = os.environ.get("AWS_REGION", "us-east-1")


def handler(event, context):
    """
    Mental Health Evaluation Handler
    Analyzes user's mental health data to provide quantitative assessment.
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
    evaluation_period = body.get("evaluation_period", "week")
    include_chat_analysis = body.get("include_chat_analysis", True)
    include_checkin_data = body.get("include_checkin_data", True)

    if not user_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing required field: user_id"}),
        }

    # Generate evaluation ID
    evaluation_id = f"eval_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    try:
        # Collect data for evaluation
        evaluation_data = collect_evaluation_data(
            user_id, evaluation_period, include_chat_analysis, include_checkin_data
        )

        if not evaluation_data["has_data"]:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "error": "Insufficient data for evaluation",
                        "message": "Please complete at least one check-in before requesting an evaluation",
                    }
                ),
            }

        # Perform mental health evaluation
        evaluation_results = perform_mental_health_evaluation(evaluation_data)

        # Store evaluation results
        store_evaluation_results(user_id, evaluation_id, evaluation_results)

        # Return response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "evaluation_id": evaluation_id,
                    "overall_score": evaluation_results["overall_score"],
                    "mood_trend": evaluation_results["mood_trend"],
                    "stress_level": evaluation_results["stress_level"],
                    "risk_factors": evaluation_results["risk_factors"],
                    "strengths": evaluation_results["strengths"],
                    "recommendations": evaluation_results["recommendations"],
                    "follow_up_needed": evaluation_results["follow_up_needed"],
                    "next_evaluation_date": evaluation_results["next_evaluation_date"],
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": "Evaluation processing failed", "details": str(e)}
            ),
        }


def collect_evaluation_data(
    user_id: str,
    evaluation_period: str,
    include_chat_analysis: bool,
    include_checkin_data: bool,
) -> Dict[str, Any]:
    """
    Collect all relevant data for mental health evaluation.
    """

    # Calculate date range
    end_date = datetime.utcnow()
    if evaluation_period == "week":
        start_date = end_date - timedelta(days=7)
    elif evaluation_period == "month":
        start_date = end_date - timedelta(days=30)
    elif evaluation_period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:  # custom or default to week
        start_date = end_date - timedelta(days=7)

    evaluation_data = {
        "user_id": user_id,
        "evaluation_period": evaluation_period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "has_data": False,
        "checkin_data": [],
        "chat_data": [],
        "conversation_moods": [],
    }

    # Collect check-in data
    if include_checkin_data:
        checkin_data = get_user_checkin_data(user_id, start_date, end_date)
        evaluation_data["checkin_data"] = checkin_data
        evaluation_data["has_data"] = len(checkin_data) > 0

    # Collect chat data
    if include_chat_analysis:
        chat_data = get_user_chat_data(user_id, start_date, end_date)
        evaluation_data["chat_data"] = chat_data
        evaluation_data["conversation_moods"] = [
            conv.get("mood_detected", "neutral") for conv in chat_data
        ]
        if not evaluation_data["has_data"]:
            evaluation_data["has_data"] = len(chat_data) > 0

    return evaluation_data


def get_user_checkin_data(
    user_id: str, start_date: datetime, end_date: datetime
) -> List[Dict]:
    """
    Retrieve user's check-in data within the specified date range.
    """
    try:
        # Try to get check-in history
        history_key = f"users/{user_id}/checkin_history.json"
        response = s3.get_object(Bucket=BUCKET, Key=history_key)
        history = json.loads(response["Body"].read())

        # Filter check-ins within date range
        filtered_checkins = []
        for checkin in history.get("checkins", []):
            checkin_date = datetime.fromisoformat(checkin["timestamp"])
            if start_date <= checkin_date <= end_date:
                filtered_checkins.append(checkin)

        return filtered_checkins

    except Exception as e:
        print(f"Failed to get check-in data: {str(e)}")
        return []


def get_user_chat_data(
    user_id: str, start_date: datetime, end_date: datetime
) -> List[Dict]:
    """
    Retrieve user's chat conversation data within the specified date range.
    """
    try:
        # List conversation files for the user
        prefix = f"conversations/{user_id}/"
        response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)

        conversations = []
        for obj in response.get("Contents", []):
            if obj["Key"].endswith(".json"):
                try:
                    conv_response = s3.get_object(Bucket=BUCKET, Key=obj["Key"])
                    conv_data = json.loads(conv_response["Body"].read())

                    conv_date = datetime.fromisoformat(conv_data["timestamp"])
                    if start_date <= conv_date <= end_date:
                        conversations.append(conv_data)

                except Exception as e:
                    print(f"Failed to read conversation {obj['Key']}: {str(e)}")
                    continue

        return conversations

    except Exception as e:
        print(f"Failed to get chat data: {str(e)}")
        return []


def perform_mental_health_evaluation(evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive mental health evaluation.
    """

    checkin_data = evaluation_data["checkin_data"]
    chat_data = evaluation_data["chat_data"]
    conversation_moods = evaluation_data["conversation_moods"]

    # Calculate overall score
    overall_score = calculate_overall_score(checkin_data, conversation_moods)

    # Analyze mood trend
    mood_trend = analyze_mood_trend(checkin_data, conversation_moods)

    # Assess stress level
    stress_level = assess_stress_level(checkin_data, conversation_moods)

    # Identify risk factors
    risk_factors = identify_risk_factors(checkin_data, conversation_moods)

    # Identify strengths
    strengths = identify_strengths(checkin_data, conversation_moods)

    # Generate recommendations
    recommendations = generate_evaluation_recommendations(
        overall_score, risk_factors, strengths
    )

    # Determine if follow-up is needed
    follow_up_needed = determine_follow_up_needed(overall_score, risk_factors)

    # Suggest next evaluation date
    next_evaluation_date = suggest_next_evaluation_date(overall_score, follow_up_needed)

    return {
        "overall_score": overall_score,
        "mood_trend": mood_trend,
        "stress_level": stress_level,
        "risk_factors": risk_factors,
        "strengths": strengths,
        "recommendations": recommendations,
        "follow_up_needed": follow_up_needed,
        "next_evaluation_date": next_evaluation_date,
        "evaluation_timestamp": datetime.utcnow().isoformat(),
    }


def calculate_overall_score(
    checkin_data: List[Dict], conversation_moods: List[str]
) -> float:
    """
    Calculate overall mental health score (0-100).
    """
    if not checkin_data:
        # Base score on conversation moods if no check-in data
        mood_scores = {
            "happy": 80,
            "good": 70,
            "neutral": 50,
            "sad": 30,
            "anxious": 25,
            "stressed": 20,
        }
        if conversation_moods:
            avg_mood_score = statistics.mean(
                [mood_scores.get(mood, 50) for mood in conversation_moods]
            )
            return round(avg_mood_score, 1)
        return 50.0

    # Calculate from check-in data
    wellness_scores = [checkin.get("wellness_score", 50) for checkin in checkin_data]
    avg_wellness = statistics.mean(wellness_scores) if wellness_scores else 50

    # Convert 0-10 scale to 0-100 scale
    overall_score = avg_wellness * 10

    # Adjust based on conversation moods
    if conversation_moods:
        mood_adjustments = {
            "happy": 5,
            "good": 2,
            "neutral": 0,
            "sad": -5,
            "anxious": -8,
            "stressed": -10,
        }
        mood_adjustment = statistics.mean(
            [mood_adjustments.get(mood, 0) for mood in conversation_moods]
        )
        overall_score += mood_adjustment

    return round(max(0, min(100, overall_score)), 1)


def analyze_mood_trend(checkin_data: List[Dict], conversation_moods: List[str]) -> str:
    """
    Analyze mood trend over time.
    """
    if len(checkin_data) < 2:
        return "stable"  # Not enough data for trend analysis

    # Sort check-ins by timestamp
    sorted_checkins = sorted(checkin_data, key=lambda x: x["timestamp"])

    # Calculate trend from wellness scores
    wellness_scores = [checkin.get("wellness_score", 50) for checkin in sorted_checkins]

    if len(wellness_scores) >= 2:
        # Simple linear trend
        first_half = statistics.mean(wellness_scores[: len(wellness_scores) // 2])
        second_half = statistics.mean(wellness_scores[len(wellness_scores) // 2 :])

        if second_half > first_half + 1:
            return "improving"
        elif second_half < first_half - 1:
            return "declining"
        else:
            return "stable"

    return "stable"


def assess_stress_level(checkin_data: List[Dict], conversation_moods: List[str]) -> str:
    """
    Assess current stress level category.
    """
    if not checkin_data:
        # Base on conversation moods
        stress_indicators = ["stressed", "anxious", "overwhelmed"]
        if any(mood in conversation_moods for mood in stress_indicators):
            return "high"
        return "moderate"

    # Calculate average stress from check-ins
    stress_scores = [
        checkin.get("responses", {}).get("stress_level", 5) for checkin in checkin_data
    ]
    avg_stress = statistics.mean(stress_scores) if stress_scores else 5

    if avg_stress >= 8:
        return "critical"
    elif avg_stress >= 6:
        return "high"
    elif avg_stress >= 4:
        return "moderate"
    else:
        return "low"


def identify_risk_factors(
    checkin_data: List[Dict], conversation_moods: List[str]
) -> List[str]:
    """
    Identify mental health risk factors.
    """
    risk_factors = []

    # Analyze check-in data
    if checkin_data:
        all_concerns = []
        for checkin in checkin_data:
            all_concerns.extend(checkin.get("concerns", []))

        # Count concern frequency
        concern_counts: dict[str, int] = {}
        for concern in all_concerns:
            concern_counts[concern] = concern_counts.get(concern, 0) + 1

        # Identify persistent concerns
        for concern, count in concern_counts.items():
            if count >= len(checkin_data) * 0.5:  # Present in 50%+ of check-ins
                risk_factors.append(concern)

    # Analyze conversation moods
    negative_moods = ["sad", "anxious", "stressed", "overwhelmed", "depressed"]
    negative_count = sum(1 for mood in conversation_moods if mood in negative_moods)

    if negative_count >= len(conversation_moods) * 0.6:  # 60%+ negative moods
        risk_factors.append("persistent_negative_mood")

    # Check for isolation
    if checkin_data:
        social_scores = [
            checkin.get("responses", {}).get("social_connection", 5)
            for checkin in checkin_data
        ]
        avg_social = statistics.mean(social_scores) if social_scores else 5
        if avg_social <= 3:
            risk_factors.append("social_isolation")

    return list(set(risk_factors))  # Remove duplicates


def identify_strengths(
    checkin_data: List[Dict], conversation_moods: List[str]
) -> List[str]:
    """
    Identify mental health strengths and positive patterns.
    """
    strengths = []

    # Analyze check-in data
    if checkin_data:
        # Check for gratitude practice
        gratitude_responses = [
            checkin.get("responses", {}).get("gratitude", "")
            for checkin in checkin_data
        ]
        gratitude_count = sum(
            1 for g in gratitude_responses if g and len(g.strip()) > 0
        )
        if gratitude_count >= len(checkin_data) * 0.7:  # 70%+ show gratitude
            strengths.append("gratitude_practice")

        # Check for goal setting
        goal_responses = [
            checkin.get("responses", {}).get("goals", "") for checkin in checkin_data
        ]
        goal_count = sum(1 for g in goal_responses if g and len(g.strip()) > 0)
        if goal_count >= len(checkin_data) * 0.7:  # 70%+ set goals
            strengths.append("goal_oriented")

        # Check for consistent check-ins
        if len(checkin_data) >= 3:
            strengths.append("consistent_self_monitoring")

    # Analyze conversation moods
    positive_moods = ["happy", "good", "positive", "optimistic"]
    positive_count = sum(1 for mood in conversation_moods if mood in positive_moods)

    if positive_count >= len(conversation_moods) * 0.4:  # 40%+ positive moods
        strengths.append("positive_outlook")

    # Check for engagement
    if len(conversation_moods) >= 3:
        strengths.append("active_engagement")

    return strengths


def generate_evaluation_recommendations(
    overall_score: float, risk_factors: List[str], strengths: List[str]
) -> List[str]:
    """
    Generate personalized recommendations based on evaluation.
    """
    recommendations = []

    # Score-based recommendations
    if overall_score < 40:
        recommendations.append(
            "Consider reaching out to a mental health professional for support"
        )
        recommendations.append(
            "Focus on basic self-care: sleep, nutrition, and gentle movement"
        )
    elif overall_score < 60:
        recommendations.append("Implement daily stress management techniques")
        recommendations.append("Consider regular check-ins to monitor progress")
    elif overall_score < 80:
        recommendations.append("Continue current positive habits")
        recommendations.append("Consider expanding your wellness routine")
    else:
        recommendations.append("Maintain your excellent mental health practices")
        recommendations.append("Consider sharing your strategies with others")

    # Risk factor-based recommendations
    if "high_stress" in risk_factors:
        recommendations.append(
            "Practice daily relaxation techniques like deep breathing or meditation"
        )
    if "poor_sleep" in risk_factors:
        recommendations.append(
            "Establish a consistent sleep routine and bedtime ritual"
        )
    if "social_isolation" in risk_factors:
        recommendations.append(
            "Make an effort to connect with friends or family regularly"
        )
    if "low_mood" in risk_factors:
        recommendations.append(
            "Engage in activities that bring you joy and fulfillment"
        )

    # Strength-based recommendations
    if "gratitude_practice" in strengths:
        recommendations.append(
            "Continue your gratitude practice - it's a powerful tool"
        )
    if "goal_oriented" in strengths:
        recommendations.append("Keep setting and working toward meaningful goals")

    return recommendations[:5]  # Limit to 5 recommendations


def determine_follow_up_needed(overall_score: float, risk_factors: List[str]) -> bool:
    """
    Determine if immediate follow-up is needed.
    """
    if overall_score < 30:
        return True
    if len(risk_factors) >= 3:
        return True
    if "critical" in risk_factors or "persistent_negative_mood" in risk_factors:
        return True

    return False


def suggest_next_evaluation_date(overall_score: float, follow_up_needed: bool) -> str:
    """
    Suggest when the next evaluation should be conducted.
    """
    if follow_up_needed:
        next_date = datetime.utcnow() + timedelta(days=3)
        return next_date.strftime("%Y-%m-%d")
    elif overall_score < 60:
        next_date = datetime.utcnow() + timedelta(days=7)
        return next_date.strftime("%Y-%m-%d")
    else:
        next_date = datetime.utcnow() + timedelta(days=14)
        return next_date.strftime("%Y-%m-%d")


def store_evaluation_results(
    user_id: str, evaluation_id: str, evaluation_results: Dict
):
    """
    Store evaluation results in S3.
    """
    try:
        evaluation_data = {
            "evaluation_id": evaluation_id,
            "user_id": user_id,
            **evaluation_results,
        }

        key = f"evaluations/{user_id}/{evaluation_id}.json"
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(evaluation_data, ensure_ascii=False),
            ContentType="application/json",
        )

    except Exception as e:
        print(f"Failed to store evaluation results: {str(e)}")


# Local testing
if __name__ == "__main__":
    test_event = {
        "body": json.dumps(
            {
                "user_id": "test_user_123",
                "evaluation_period": "week",
                "include_chat_analysis": True,
                "include_checkin_data": True,
            }
        )
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
