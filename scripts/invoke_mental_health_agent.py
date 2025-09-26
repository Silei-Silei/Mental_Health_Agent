import os
import json
import argparse
import datetime
import boto3
import requests
import uuid

def invoke_bedrock_chat(message: str, region: str):
    """
    Call the Bedrock Claude model with the text prompt and return the response text.
    """
    client = boto3.client("bedrock-runtime", region_name=region)
    
    resp = client.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": 200
        })
    )
    return resp["body"].read().decode()

def invoke_api(base_url: str, path: str, payload: dict, headers: dict = None, timeout: int = 30):
    """
    Call any HTTP endpoint with POST and JSON body.
    Simple helper to invoke API Gateway endpoint.
    """
    if not base_url:
        raise ValueError("API base URL is required. Pass --api-base or set API_BASE env var.")
    if base_url.endswith('/'):
        base = base_url[:-1]
    else:
        base = base_url

    # Construct full URL endpoint
    url = f"{base}{path}"

    # POST JSON to the API endpoint
    resp = requests.post(url, json=payload, headers=headers or {}, timeout=timeout)
    resp.raise_for_status()

    # Return parsed JSON body
    return resp.json()

def invoke_agent(message: str, *, region: str, agent_id: str, alias_id: str) -> str:
    """
    Send a message to a Bedrock Agent and return the aggregated text response.
    """
    client = boto3.client("bedrock-agent-runtime", region_name=region)
    resp = client.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=str(uuid.uuid4()),
        inputText=message,
    )

    # Event stream: aggregate all chunk bytes into a single string
    out = []
    completion = resp.get("completion")
    if completion is not None:
        for event in completion:
            chunk = event.get("chunk")
            if chunk and "bytes" in chunk:
                out.append(chunk["bytes"].decode("utf-8", errors="ignore"))
    return "".join(out)

def save_to_s3(text: str, bucket: str, key: str, region: str):
    """Save text content to S3 as UTF-8 encoded object"""
    s3 = boto3.client("s3", region_name=region)
    s3.put_object(Bucket=bucket, Key=key, Body=text.encode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Mental Health Agent helper invoker")
    sub = parser.add_subparsers(dest="command", required=True)

    # Chat with mental health agent
    chat_p = sub.add_parser("chat", help="Chat with the mental health agent")
    chat_p.add_argument("--user-id", required=True, help="Unique user identifier")
    chat_p.add_argument("--message", required=True, help="User's message")
    chat_p.add_argument("--conversation-history", help="JSON string of conversation history")
    chat_p.add_argument("--mood-context", help="JSON string of current mood context")
    chat_p.add_argument("--api-base", default=os.environ.get("API_BASE"), help="Base URL like https://abc.execute-api.us-east-1.amazonaws.com/prod")

    # Daily check-in
    checkin_p = sub.add_parser("checkin", help="Perform daily mental health check-in")
    checkin_p.add_argument("--user-id", required=True, help="Unique user identifier")
    checkin_p.add_argument("--checkin-type", choices=["morning", "evening", "custom"], default="custom", help="Type of check-in")
    checkin_p.add_argument("--mood-rating", type=int, choices=range(1, 11), help="Mood rating 1-10")
    checkin_p.add_argument("--energy-level", type=int, choices=range(1, 11), help="Energy level 1-10")
    checkin_p.add_argument("--sleep-quality", type=int, choices=range(1, 11), help="Sleep quality 1-10")
    checkin_p.add_argument("--stress-level", type=int, choices=range(1, 11), help="Stress level 1-10")
    checkin_p.add_argument("--anxiety-level", type=int, choices=range(1, 11), help="Anxiety level 1-10")
    checkin_p.add_argument("--social-connection", type=int, choices=range(1, 11), help="Social connection 1-10")
    checkin_p.add_argument("--productivity", type=int, choices=range(1, 11), help="Productivity level 1-10")
    checkin_p.add_argument("--gratitude", help="One thing you're grateful for today")
    checkin_p.add_argument("--challenges", help="Main challenge or concern today")
    checkin_p.add_argument("--goals", help="One goal for today")
    checkin_p.add_argument("--additional-notes", help="Any additional thoughts or feelings")
    checkin_p.add_argument("--api-base", default=os.environ.get("API_BASE"), help="Base URL")

    # Mental health evaluation
    eval_p = sub.add_parser("evaluate", help="Perform mental health evaluation")
    eval_p.add_argument("--user-id", required=True, help="Unique user identifier")
    eval_p.add_argument("--evaluation-period", choices=["week", "month", "quarter", "custom"], default="week", help="Time period for evaluation")
    eval_p.add_argument("--include-chat-analysis", action="store_true", default=True, help="Include chat conversation analysis")
    eval_p.add_argument("--include-checkin-data", action="store_true", default=True, help="Include check-in questionnaire data")
    eval_p.add_argument("--api-base", default=os.environ.get("API_BASE"), help="Base URL")

    # Get recommendations
    rec_p = sub.add_parser("recommendations", help="Get personalized mental health recommendations")
    rec_p.add_argument("--user-id", required=True, help="Unique user identifier")
    rec_p.add_argument("--recommendation-type", choices=["immediate", "daily", "weekly", "stress_relief", "mood_boost", "sleep_aid"], default="immediate", help="Type of recommendations")
    rec_p.add_argument("--current-mood", help="User's current mood for context")
    rec_p.add_argument("--content-types", nargs="+", choices=["video", "audio", "text", "interactive"], help="Preferred content types")
    rec_p.add_argument("--duration", choices=["short", "medium", "long"], help="Preferred duration")
    rec_p.add_argument("--activity-level", choices=["low", "moderate", "high"], help="Preferred activity level")
    rec_p.add_argument("--interests", nargs="+", help="User interests")
    rec_p.add_argument("--urgency-level", choices=["low", "medium", "high"], default="medium", help="Urgency level")
    rec_p.add_argument("--api-base", default=os.environ.get("API_BASE"), help="Base URL")

    # Schedule check-in
    schedule_p = sub.add_parser("schedule", help="Schedule proactive check-ins")
    schedule_p.add_argument("--user-id", required=True, help="Unique user identifier")
    schedule_p.add_argument("--mental-health-score", type=float, help="Current mental health score 0-100")
    schedule_p.add_argument("--risk-level", choices=["low", "moderate", "high", "critical"], help="Assessed risk level")
    schedule_p.add_argument("--preferred-checkin-times", nargs="+", help="Preferred check-in times (HH:MM format)")
    schedule_p.add_argument("--max-checkins-per-week", type=int, help="Maximum check-ins per week")
    schedule_p.add_argument("--notification-methods", nargs="+", choices=["push", "email", "sms"], help="Notification methods")
    schedule_p.add_argument("--last-checkin-date", help="Date of last check-in (ISO format)")
    schedule_p.add_argument("--api-base", default=os.environ.get("API_BASE"), help="Base URL")

    # User profile management (NEW)
    profile_p = sub.add_parser("profile", help="Manage user profiles")
    profile_p.add_argument("--user-id", required=True, help="Unique user identifier")
    profile_p.add_argument("--action", choices=["get_profile", "get_insights", "get_context", "update_demographics", "reset_profile"], default="get_profile", help="Profile action to perform")
    profile_p.add_argument("--context-type", choices=["chat", "recommendations", "evaluation"], help="Context type for get_context action")
    profile_p.add_argument("--age-range", help="Age range for demographics update")
    profile_p.add_argument("--timezone", help="Timezone for demographics update")
    profile_p.add_argument("--preferred-language", help="Preferred language for demographics update")
    profile_p.add_argument("--api-base", default=os.environ.get("API_BASE"), help="Base URL")

    # Bedrock Agent (talk to Bedrock Agent; Agent decides which Lambda/action to call)
    agent_p = sub.add_parser("agent", help="Send a message to the Bedrock Agent")
    agent_p.add_argument("--message", required=True, help="User message for the Agent")
    agent_p.add_argument("--agent-id", default=os.environ.get("AGENT_ID"), help="Bedrock Agent ID (or set AGENT_ID)")
    agent_p.add_argument("--agent-alias-id", default=os.environ.get("AGENT_ALIAS_ID"), help="Bedrock Agent alias ID (or set AGENT_ALIAS_ID)")
    agent_p.add_argument("--save-s3", action="store_true", help="Save Agent response to S3")

    # Simple Bedrock chat (for testing)
    bedrock_p = sub.add_parser("bedrock-chat", help="Direct Bedrock chat (for testing)")
    bedrock_p.add_argument("--message", default="Hello, I'm feeling a bit stressed today.", help="Message to send to Bedrock")
    bedrock_p.add_argument("--save-s3", action="store_true", help="Save response to S3")

    args = parser.parse_args()

    region = os.environ.get("AWS_REGION", "us-east-1")
    bucket = os.environ.get("MH_BUCKET", "mental-health-agent")

    if args.command == "chat":
        payload = {
            "user_id": args.user_id,
            "message": args.message
        }
        
        if args.conversation_history:
            try:
                payload["conversation_history"] = json.loads(args.conversation_history)
            except json.JSONDecodeError:
                print("Warning: Invalid conversation_history JSON, ignoring")
        
        if args.mood_context:
            try:
                payload["mood_context"] = json.loads(args.mood_context)
            except json.JSONDecodeError:
                print("Warning: Invalid mood_context JSON, ignoring")
        
        result = invoke_api(args.api_base, "/chat", payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "checkin":
        responses = {}
        if args.mood_rating:
            responses["mood_rating"] = args.mood_rating
        if args.energy_level:
            responses["energy_level"] = args.energy_level
        if args.sleep_quality:
            responses["sleep_quality"] = args.sleep_quality
        if args.stress_level:
            responses["stress_level"] = args.stress_level
        if args.anxiety_level:
            responses["anxiety_level"] = args.anxiety_level
        if args.social_connection:
            responses["social_connection"] = args.social_connection
        if args.productivity:
            responses["productivity"] = args.productivity
        if args.gratitude:
            responses["gratitude"] = args.gratitude
        if args.challenges:
            responses["challenges"] = args.challenges
        if args.goals:
            responses["goals"] = args.goals

        payload = {
            "user_id": args.user_id,
            "checkin_type": args.checkin_type,
            "responses": responses
        }
        
        if args.additional_notes:
            payload["additional_notes"] = args.additional_notes

        result = invoke_api(args.api_base, "/daily-checkin", payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "evaluate":
        payload = {
            "user_id": args.user_id,
            "evaluation_period": args.evaluation_period,
            "include_chat_analysis": args.include_chat_analysis,
            "include_checkin_data": args.include_checkin_data
        }
        
        result = invoke_api(args.api_base, "/evaluate-mental-health", payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "recommendations":
        payload = {
            "user_id": args.user_id,
            "recommendation_type": args.recommendation_type,
            "urgency_level": args.urgency_level
        }
        
        if args.current_mood:
            payload["current_mood"] = args.current_mood
        
        preferences = {}
        if args.content_types:
            preferences["content_types"] = args.content_types
        if args.duration:
            preferences["duration"] = args.duration
        if args.activity_level:
            preferences["activity_level"] = args.activity_level
        if args.interests:
            preferences["interests"] = args.interests
        
        if preferences:
            payload["preferences"] = preferences

        result = invoke_api(args.api_base, "/recommendations", payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "schedule":
        payload = {
            "user_id": args.user_id
        }
        
        if args.mental_health_score is not None:
            payload["mental_health_score"] = args.mental_health_score
        if args.risk_level:
            payload["risk_level"] = args.risk_level
        if args.last_checkin_date:
            payload["last_checkin_date"] = args.last_checkin_date
        
        user_preferences = {}
        if args.preferred_checkin_times:
            user_preferences["preferred_checkin_times"] = args.preferred_checkin_times
        if args.max_checkins_per_week:
            user_preferences["max_checkins_per_week"] = args.max_checkins_per_week
        if args.notification_methods:
            user_preferences["notification_methods"] = args.notification_methods
        
        if user_preferences:
            payload["user_preferences"] = user_preferences

        result = invoke_api(args.api_base, "/schedule-checkin", payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "profile":
        payload = {
            "user_id": args.user_id,
            "action": args.action
        }
        
        if args.action == "get_context" and args.context_type:
            payload["data"] = {"context_type": args.context_type}
        elif args.action == "update_demographics":
            demographics = {}
            if args.age_range:
                demographics["age_range"] = args.age_range
            if args.timezone:
                demographics["timezone"] = args.timezone
            if args.preferred_language:
                demographics["preferred_language"] = args.preferred_language
            if demographics:
                payload["data"] = {"demographics": demographics}

        result = invoke_api(args.api_base, "/user-profile", payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "agent":
        if not args.agent_id or not args.agent_alias_id:
            raise ValueError("Missing Agent identifiers. Provide --agent-id and --agent-alias-id or set AGENT_ID / AGENT_ALIAS_ID env vars.")
        
        reply = invoke_agent(
            args.message,
            region=region,
            agent_id=args.agent_id,
            alias_id=args.agent_alias_id
        )
        print(reply)

        if args.save_s3:
            run_id = os.environ.get("RUN_ID", datetime.datetime.utcnow().strftime("run_%Y-%m-%d_%H-%M-%S"))
            key = f"output/{run_id}/agent_output.txt"
            save_to_s3(reply, bucket, key, region)
            print(f"Output saved to s3://{bucket}/{key}")
        return

    if args.command == "bedrock-chat":
        text = invoke_bedrock_chat(args.message, region)
        print(text)
        if args.save_s3:
            run_id = os.environ.get("RUN_ID", datetime.datetime.utcnow().strftime("run_%Y-%m-%d_%H-%M-%S"))
            key = f"output/{run_id}/bedrock_output.txt"
            save_to_s3(text, bucket, key, region)
            print(f"Output saved to s3://{bucket}/{key}")
        return

if __name__ == "__main__":
    main()
