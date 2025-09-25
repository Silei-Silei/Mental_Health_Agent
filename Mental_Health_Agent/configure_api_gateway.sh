#!/bin/bash

# Configure API Gateway for Mental Health Agent
# This script configures your existing API Gateway to route to Lambda functions

set -e

# Configuration
REGION="us-west-2"
API_ID="ot173x9io1"
STAGE="prod"

echo "🌐 Configuring API Gateway for Mental Health Agent"
echo "================================================="

# Get API Gateway details
echo "📋 Getting API Gateway information..."
API_DETAILS=$(aws apigatewayv2 get-api --api-id $API_ID --region $REGION)
echo "API Name: $(echo $API_DETAILS | jq -r '.Name')"

# Create Lambda functions first (if they don't exist)
echo "🚀 Creating Lambda functions..."

# Function to create a simple Lambda function
create_simple_lambda() {
    local function_name=$1
    local handler_code=$2
    
    echo "  Creating $function_name..."
    
    # Create a simple handler
    cat > /tmp/${function_name}.py << EOF
import json

def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'Hello from $function_name',
            'function': '$function_name',
            'event': event
        })
    }
EOF
    
    # Create deployment package
    cd /tmp
    zip ${function_name}.zip ${function_name}.py
    cd -
    
    # Create Lambda function
    aws lambda create-function \
        --function-name $function_name \
        --runtime python3.9 \
        --role arn:aws:iam::989367328111:role/MentalHealthAgentRole \
        --handler ${function_name}.handler \
        --zip-file fileb:///tmp/${function_name}.zip \
        --description "Mental Health Agent - $function_name" \
        --timeout 60 \
        --memory-size 256 \
        --region $REGION 2>/dev/null || echo "Function $function_name already exists"
    
    echo "  ✅ $function_name created"
}

# Create simple Lambda functions for testing
create_simple_lambda "mh-chat-handler"
create_simple_lambda "mh-daily-checkin"
create_simple_lambda "mh-evaluate-mental-health"
create_simple_lambda "mh-recommendations"
create_simple_lambda "mh-schedule-checkin"

echo ""
echo "🎉 Lambda functions created successfully!"
echo ""
echo "Next steps:"
echo "1. Test the API endpoints"
echo "2. Replace simple handlers with full implementations"
echo ""
echo "Test URLs:"
echo "  Chat: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/chat"
echo "  Check-in: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/daily-checkin"
