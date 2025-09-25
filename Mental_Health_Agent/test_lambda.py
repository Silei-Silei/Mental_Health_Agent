#!/usr/bin/env python3

import boto3
import json

# Test the Lambda function directly
def test_lambda():
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    # Test event structure
    test_event = {
        "body": json.dumps({
            "user_id": "test_user",
            "message": "Hello, I'm feeling stressed today"
        })
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='mh-chat-handler',
            Payload=json.dumps(test_event)
        )
        
        # Read the response
        payload = json.loads(response['Payload'].read())
        print("Lambda Response:")
        print(json.dumps(payload, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_lambda()
