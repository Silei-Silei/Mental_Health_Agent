#!/bin/bash

# Add API Gateway routes for Mental Health Agent
# This script adds the missing routes to your existing API Gateway

set -e

# Configuration
REGION="us-west-2"
API_ID="ot173x9io1"
STAGE="prod"

echo "🌐 Adding API Gateway routes for Mental Health Agent"
echo "==================================================="

# Function to add a route
add_route() {
    local route_key=$1
    local function_name=$2
    local function_arn=$3
    
    echo "Adding route: $route_key -> $function_name"
    
    # Create the route
    aws apigatewayv2 create-route \
        --api-id $API_ID \
        --route-key "$route_key" \
        --target "integrations/$(aws apigatewayv2 create-integration \
            --api-id $API_ID \
            --integration-type AWS_PROXY \
            --integration-uri $function_arn \
            --payload-format-version "2.0" \
            --query 'IntegrationId' \
            --output text)" \
        --region $REGION
    
    echo "  ✅ Route $route_key added successfully"
}

# Get Lambda function ARNs
CHAT_HANDLER_ARN="arn:aws:lambda:us-west-2:989367328111:function:mh-chat-handler"
DAILY_CHECKIN_ARN="arn:aws:lambda:us-west-2:989367328111:function:mh-daily-checkin"
EVALUATE_ARN="arn:aws:lambda:us-west-2:989367328111:function:mh-evaluate-mental-health"
RECOMMENDATIONS_ARN="arn:aws:lambda:us-west-2:989367328111:function:mh-recommendations"
SCHEDULE_ARN="arn:aws:lambda:us-west-2:989367328111:function:mh-schedule-checkin"

# Add all routes
add_route "POST /chat" "mh-chat-handler" $CHAT_HANDLER_ARN
add_route "POST /daily-checkin" "mh-daily-checkin" $DAILY_CHECKIN_ARN
add_route "POST /evaluate-mental-health" "mh-evaluate-mental-health" $EVALUATE_ARN
add_route "POST /recommendations" "mh-recommendations" $RECOMMENDATIONS_ARN
add_route "POST /schedule-checkin" "mh-schedule-checkin" $SCHEDULE_ARN

echo ""
echo "🎉 All routes added successfully!"
echo ""
echo "Test URLs:"
echo "  Chat: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/chat"
echo "  Check-in: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/daily-checkin"
echo "  Evaluation: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/evaluate-mental-health"
echo "  Recommendations: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/recommendations"
echo "  Schedule: https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE/schedule-checkin"
