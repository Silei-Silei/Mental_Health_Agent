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
    Schedule Proactive Check-in Handler
    Determines when to proactively check in with users based on their mental health status.
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
            "body": json.dumps({
                "error": "Invalid request body",
                "details": str(e)
            })
        }
    
    # Extract parameters
    user_id = body.get("user_id")
    mental_health_score = body.get("mental_health_score", 50)
    risk_level = body.get("risk_level", "moderate")
    user_preferences = body.get("user_preferences", {})
    last_checkin_date = body.get("last_checkin_date")
    
    if not user_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Missing required field: user_id"
            })
        }
    
    # Generate schedule ID
    schedule_id = f"schedule_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    try:
        # Determine check-in frequency and timing
        scheduling_decision = determine_checkin_schedule(
            mental_health_score, risk_level, user_preferences, last_checkin_date
        )
        
        # Generate personalized message
        message = generate_scheduling_message(scheduling_decision, mental_health_score, risk_level)
        
        # Store scheduling decision
        store_scheduling_decision(user_id, schedule_id, scheduling_decision, mental_health_score, risk_level)
        
        # Return response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "schedule_id": schedule_id,
                "next_checkin_date": scheduling_decision["next_checkin_date"],
                "checkin_frequency": scheduling_decision["checkin_frequency"],
                "reasoning": scheduling_decision["reasoning"],
                "notification_scheduled": scheduling_decision["notification_scheduled"],
                "message": message
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Scheduling failed",
                "details": str(e)
            })
        }

def determine_checkin_schedule(
    mental_health_score: float, 
    risk_level: str, 
    user_preferences: Dict, 
    last_checkin_date: str
) -> Dict[str, Any]:
    """
    Determine the optimal check-in schedule based on mental health status and preferences.
    """
    
    # Parse last check-in date
    last_checkin = None
    if last_checkin_date:
        try:
            last_checkin = datetime.fromisoformat(last_checkin_date.replace('Z', '+00:00'))
        except:
            last_checkin = datetime.utcnow() - timedelta(days=1)
    else:
        last_checkin = datetime.utcnow() - timedelta(days=1)
    
    # Get user's preferred check-in times
    preferred_times = user_preferences.get("preferred_checkin_times", ["09:00", "18:00"])
    max_checkins_per_week = user_preferences.get("max_checkins_per_week", 5)
    notification_methods = user_preferences.get("notification_methods", ["push"])
    
    # Determine check-in frequency based on mental health score and risk level
    if mental_health_score < 30 or risk_level == "critical":
        # High concern - check in tomorrow at the same time
        next_checkin_date = last_checkin + timedelta(days=1)
        checkin_frequency = "daily"
        reasoning = "Your mental health score indicates you need more frequent support. I'll check in with you tomorrow to see how you're doing."
        
    elif mental_health_score < 50 or risk_level == "high":
        # Moderate-high concern - check in every 2 days
        next_checkin_date = last_checkin + timedelta(days=2)
        checkin_frequency = "every_2_days"
        reasoning = "I want to make sure you're getting the support you need. I'll check in with you in 2 days."
        
    elif mental_health_score < 70 or risk_level == "moderate":
        # Moderate concern - check in every 3-4 days
        next_checkin_date = last_checkin + timedelta(days=3)
        checkin_frequency = "every_3_days"
        reasoning = "I'll check in with you in a few days to see how you're doing and provide support if needed."
        
    else:
        # Good mental health - check in weekly
        next_checkin_date = last_checkin + timedelta(days=7)
        checkin_frequency = "weekly"
        reasoning = "You're doing well! I'll check in with you next week to continue supporting your mental health journey."
    
    # Adjust timing based on user preferences
    if preferred_times:
        # Use the first preferred time for the next check-in
        preferred_time = preferred_times[0]
        hour, minute = map(int, preferred_time.split(':'))
        next_checkin_date = next_checkin_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Ensure we don't exceed max check-ins per week
    if checkin_frequency == "daily" and max_checkins_per_week < 7:
        checkin_frequency = f"every_{max_checkins_per_week}_days"
        next_checkin_date = last_checkin + timedelta(days=max_checkins_per_week)
        reasoning += f" I've adjusted the frequency to respect your preference of {max_checkins_per_week} check-ins per week."
    
    # Determine if notifications should be scheduled
    notification_scheduled = len(notification_methods) > 0
    
    return {
        "next_checkin_date": next_checkin_date.isoformat(),
        "checkin_frequency": checkin_frequency,
        "reasoning": reasoning,
        "notification_scheduled": notification_scheduled,
        "notification_methods": notification_methods,
        "mental_health_score": mental_health_score,
        "risk_level": risk_level
    }

def generate_scheduling_message(scheduling_decision: Dict, mental_health_score: float, risk_level: str) -> str:
    """
    Generate a personalized message about the scheduling decision.
    """
    
    next_checkin_date = datetime.fromisoformat(scheduling_decision["next_checkin_date"])
    checkin_frequency = scheduling_decision["checkin_frequency"]
    
    # Base message based on mental health score
    if mental_health_score < 30:
        message = "I'm concerned about how you're feeling right now. I want to make sure you have the support you need, so I'll check in with you tomorrow at the same time."
    elif mental_health_score < 50:
        message = "I can see you're going through a challenging time. I'll check in with you in a couple of days to see how you're doing and offer support."
    elif mental_health_score < 70:
        message = "I'll check in with you in a few days to see how you're doing. Remember, I'm here whenever you need to talk."
    else:
        message = "You're doing great! I'll check in with you next week to continue supporting your mental health journey."
    
    # Add specific timing information
    if checkin_frequency == "daily":
        message += " I'll be checking in with you daily to provide consistent support."
    elif checkin_frequency == "every_2_days":
        message += " I'll check in with you every couple of days."
    elif checkin_frequency == "every_3_days":
        message += " I'll check in with you every few days."
    elif checkin_frequency == "weekly":
        message += " I'll check in with you weekly."
    
    # Add encouragement
    if mental_health_score < 50:
        message += " Remember, you're not alone in this, and it's okay to not be okay. Taking care of your mental health is important."
    else:
        message += " Keep up the great work with your mental health!"
    
    return message

def store_scheduling_decision(
    user_id: str, 
    schedule_id: str, 
    scheduling_decision: Dict, 
    mental_health_score: float, 
    risk_level: str
):
    """
    Store the scheduling decision for future reference and tracking.
    """
    try:
        schedule_data = {
            "schedule_id": schedule_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "mental_health_score": mental_health_score,
            "risk_level": risk_level,
            "scheduling_decision": scheduling_decision
        }
        
        # Store individual schedule
        key = f"schedules/{user_id}/{schedule_id}.json"
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(schedule_data, ensure_ascii=False),
            ContentType="application/json"
        )
        
        # Update user's schedule history
        update_user_schedule_history(user_id, schedule_data)
        
    except Exception as e:
        print(f"Failed to store scheduling decision: {str(e)}")

def update_user_schedule_history(user_id: str, schedule_data: Dict):
    """
    Update user's schedule history for tracking and analysis.
    """
    try:
        history_key = f"users/{user_id}/schedule_history.json"
        
        # Try to get existing history
        try:
            response = s3.get_object(Bucket=BUCKET, Key=history_key)
            history = json.loads(response["Body"].read())
        except:
            history = {"schedules": [], "created_at": datetime.utcnow().isoformat()}
        
        # Add new schedule
        history["schedules"].append({
            "schedule_id": schedule_data["schedule_id"],
            "timestamp": schedule_data["timestamp"],
            "mental_health_score": schedule_data["mental_health_score"],
            "risk_level": schedule_data["risk_level"],
            "checkin_frequency": schedule_data["scheduling_decision"]["checkin_frequency"],
            "next_checkin_date": schedule_data["scheduling_decision"]["next_checkin_date"]
        })
        
        # Keep only last 20 schedules
        history["schedules"] = history["schedules"][-20:]
        history["updated_at"] = datetime.utcnow().isoformat()
        
        # Store updated history
        s3.put_object(
            Bucket=BUCKET,
            Key=history_key,
            Body=json.dumps(history, ensure_ascii=False),
            ContentType="application/json"
        )
        
    except Exception as e:
        print(f"Failed to update schedule history: {str(e)}")

def get_user_checkin_patterns(user_id: str) -> Dict[str, Any]:
    """
    Analyze user's check-in patterns to inform scheduling decisions.
    """
    try:
        # Get check-in history
        checkin_history_key = f"users/{user_id}/checkin_history.json"
        response = s3.get_object(Bucket=BUCKET, Key=checkin_history_key)
        history = json.loads(response["Body"].read())
        
        checkins = history.get("checkins", [])
        
        if not checkins:
            return {"pattern": "new_user", "consistency": 0}
        
        # Analyze consistency
        total_checkins = len(checkins)
        recent_checkins = checkins[-7:]  # Last 7 check-ins
        
        # Calculate consistency score
        if total_checkins >= 7:
            # Check if user has been checking in regularly
            consistency_score = len(recent_checkins) / 7
        else:
            consistency_score = total_checkins / 7
        
        # Determine pattern
        if consistency_score >= 0.8:
            pattern = "highly_consistent"
        elif consistency_score >= 0.5:
            pattern = "moderately_consistent"
        else:
            pattern = "inconsistent"
        
        return {
            "pattern": pattern,
            "consistency": consistency_score,
            "total_checkins": total_checkins,
            "recent_checkins": len(recent_checkins)
        }
        
    except Exception as e:
        print(f"Failed to get user check-in patterns: {str(e)}")
        return {"pattern": "unknown", "consistency": 0}

def adjust_schedule_for_user_patterns(scheduling_decision: Dict, user_patterns: Dict) -> Dict[str, Any]:
    """
    Adjust scheduling decision based on user's historical patterns.
    """
    
    pattern = user_patterns.get("pattern", "unknown")
    consistency = user_patterns.get("consistency", 0)
    
    # Adjust frequency based on user consistency
    if pattern == "highly_consistent" and consistency >= 0.8:
        # User is very consistent, we can be more flexible
        current_frequency = scheduling_decision["checkin_frequency"]
        if current_frequency == "daily":
            scheduling_decision["checkin_frequency"] = "every_2_days"
            scheduling_decision["reasoning"] += " Since you've been very consistent with check-ins, I'll adjust to every 2 days."
    
    elif pattern == "inconsistent" and consistency < 0.3:
        # User is inconsistent, we should be more persistent
        current_frequency = scheduling_decision["checkin_frequency"]
        if current_frequency in ["weekly", "every_3_days"]:
            scheduling_decision["checkin_frequency"] = "every_2_days"
            scheduling_decision["reasoning"] += " I'll check in more frequently to help you stay consistent with your mental health routine."
    
    return scheduling_decision

# Local testing
if __name__ == "__main__":
    test_event = {
        "body": json.dumps({
            "user_id": "test_user_123",
            "mental_health_score": 35,
            "risk_level": "high",
            "user_preferences": {
                "preferred_checkin_times": ["09:00", "18:00"],
                "max_checkins_per_week": 5,
                "notification_methods": ["push", "email"]
            },
            "last_checkin_date": "2024-01-15T09:00:00Z"
        })
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
