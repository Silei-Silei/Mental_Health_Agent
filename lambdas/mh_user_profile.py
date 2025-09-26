import os
import json
import time
import uuid
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import profile utilities
from profile_utils import (
    get_user_profile, 
    store_user_profile, 
    update_profile_from_checkin,
    update_profile_from_chat,
    update_profile_from_recommendations,
    update_profile_from_evaluation,
    get_profile_insights,
    get_personalized_context
)

# AWS clients
s3 = boto3.client("s3")

# Configuration
BUCKET = os.environ.get("MH_BUCKET", "mental-health-agent")
REGION = os.environ.get("AWS_REGION", "us-east-1")

def handler(event, context):
    """
    User Profile Management Handler
    Manages user profiles for enhanced personalization and memory.
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
    action = body.get("action", "get_profile")
    data = body.get("data", {})
    
    if not user_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Missing required field: user_id"
            })
        }
    
    try:
        if action == "get_profile":
            # Get user profile
            profile = get_user_profile(user_id)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "profile": profile,
                    "message": "Profile retrieved successfully"
                })
            }
        
        elif action == "get_insights":
            # Get profile insights
            insights = get_profile_insights(user_id)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "insights": insights,
                    "message": "Profile insights generated successfully"
                })
            }
        
        elif action == "get_context":
            # Get personalized context for specific use case
            context_type = data.get("context_type", "chat")
            context = get_personalized_context(user_id, context_type)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "context_type": context_type,
                    "context": context,
                    "message": "Personalized context generated successfully"
                })
            }
        
        elif action == "update_from_checkin":
            # Update profile from check-in data
            update_profile_from_checkin(user_id, data)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "message": "Profile updated from check-in data"
                })
            }
        
        elif action == "update_from_chat":
            # Update profile from chat data
            update_profile_from_chat(user_id, data)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "message": "Profile updated from chat data"
                })
            }
        
        elif action == "update_from_recommendations":
            # Update profile from recommendation data
            update_profile_from_recommendations(user_id, data)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "message": "Profile updated from recommendation data"
                })
            }
        
        elif action == "update_from_evaluation":
            # Update profile from evaluation data
            update_profile_from_evaluation(user_id, data)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "message": "Profile updated from evaluation data"
                })
            }
        
        elif action == "update_demographics":
            # Update demographic information
            profile = get_user_profile(user_id)
            demographics = data.get("demographics", {})
            profile["demographics"].update(demographics)
            store_user_profile(user_id, profile)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "message": "Demographics updated successfully"
                })
            }
        
        elif action == "reset_profile":
            # Reset profile to default (for testing)
            from profile_utils import create_default_profile
            profile = create_default_profile(user_id)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "user_id": user_id,
                    "message": "Profile reset to default",
                    "profile": profile
                })
            }
        
        else:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "get_profile", "get_insights", "get_context",
                        "update_from_checkin", "update_from_chat", 
                        "update_from_recommendations", "update_from_evaluation",
                        "update_demographics", "reset_profile"
                    ]
                })
            }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Profile operation failed",
                "details": str(e)
            })
        }

# Local testing
if __name__ == "__main__":
    # Test profile operations
    test_event = {
        "body": json.dumps({
            "user_id": "test_user_profile",
            "action": "get_profile"
        })
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
