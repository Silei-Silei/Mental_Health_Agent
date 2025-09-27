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


def handler(event, context):
    """
    Mental Health Chat Handler
    Provides empathetic conversation and emotional support.
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
    message = body.get("message")
    conversation_history = body.get("conversation_history", [])
    mood_context = body.get("mood_context", {})

    if not user_id or not message:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"error": "Missing required fields: user_id and message"}
            ),
        }

    # Generate conversation ID
    conversation_id = f"conv_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    try:
        # Generate empathetic response using Bedrock
        response_data = generate_empathetic_response(
            user_id, message, conversation_history, mood_context
        )

        # Store conversation in S3
        store_conversation(
            user_id, conversation_id, message, response_data, mood_context
        )

        # Return response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "response": response_data["response"],
                    "suggestions": response_data.get("suggestions", []),
                    "follow_up_questions": response_data.get("follow_up_questions", []),
                    "mood_detected": response_data.get("mood_detected", "neutral"),
                    "conversation_id": conversation_id,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Chat processing failed", "details": str(e)}),
        }


def generate_empathetic_response(
    user_id: str, message: str, conversation_history: List[Dict], mood_context: Dict
) -> Dict[str, Any]:
    """
    Generate an empathetic response using Bedrock Claude.
    """

    # Build context from conversation history
    context = ""
    if conversation_history:
        context = "Previous conversation:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"

    # Build mood context
    mood_info = ""
    if mood_context:
        mood_info = (
            f"Current mood context: {mood_context.get('current_mood', 'unknown')}, "
        )
        mood_info += f"Stress level: {mood_context.get('stress_level', 'unknown')}/10\n"

    # Create prompt for empathetic response
    prompt = f"""You are a compassionate mental health companion. Your role is to provide empathetic, supportive, and helpful responses to users who may be struggling with mental health challenges.

{mood_info}{context}

User's message: "{message}"

Please respond with:
1. An empathetic and understanding response (2-3 sentences)
2. Optional helpful suggestions or coping strategies (1-2 suggestions)
3. Optional follow-up questions to continue the conversation (1-2 questions)
4. Detect the user's mood from their message

Respond in JSON format:
{{
    "response": "Your empathetic response here",
    "suggestions": ["suggestion1", "suggestion2"],
    "follow_up_questions": ["question1", "question2"],
    "mood_detected": "mood (happy, sad, anxious, stressed, neutral, etc.)"
}}

Be warm, non-judgmental, and supportive. Avoid giving medical advice. Focus on emotional support and practical coping strategies."""

    try:
        # Call Bedrock Claude
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ),
        )

        response_body = json.loads(response["body"].read())
        content = response_body["content"][0]["text"]

        # Parse JSON response
        try:
            parsed_response = json.loads(content)
            return parsed_response
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "response": content,
                "suggestions": [],
                "follow_up_questions": [],
                "mood_detected": "neutral",
            }

    except Exception as e:
        # Fallback response if Bedrock fails
        return {
            "response": "I'm here to listen and support you. It sounds like you're going through a challenging time. Remember that it's okay to feel this way, and you're not alone.",
            "suggestions": [
                "Take some deep breaths",
                "Consider talking to a trusted friend or family member",
            ],
            "follow_up_questions": [
                "Would you like to talk more about what's on your mind?",
                "Is there anything specific that's been weighing on you?",
            ],
            "mood_detected": "concerned",
        }


def store_conversation(
    user_id: str,
    conversation_id: str,
    user_message: str,
    response_data: Dict,
    mood_context: Dict,
):
    """
    Store conversation data in S3 for future reference and analysis.
    """
    try:
        conversation_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": user_message,
            "response": response_data["response"],
            "suggestions": response_data.get("suggestions", []),
            "follow_up_questions": response_data.get("follow_up_questions", []),
            "mood_detected": response_data.get("mood_detected", "neutral"),
            "mood_context": mood_context,
        }

        # Store in S3
        key = f"conversations/{user_id}/{conversation_id}.json"
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(conversation_data, ensure_ascii=False),
            ContentType="application/json",
        )

    except Exception as e:
        # Don't fail the request if storage fails
        print(f"Failed to store conversation: {str(e)}")


# Local testing
if __name__ == "__main__":
    test_event = {
        "body": json.dumps(
            {
                "user_id": "test_user_123",
                "message": "I'm feeling really overwhelmed with work and life right now",
                "mood_context": {"current_mood": "overwhelmed", "stress_level": 8},
            }
        )
    }
    result = handler(test_event, None)
    print(json.dumps(result, indent=2))
