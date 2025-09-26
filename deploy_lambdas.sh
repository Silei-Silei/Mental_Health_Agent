#!/bin/bash

# Mental Health Agent Lambda Deployment Script
# This script deploys all Lambda functions to AWS

set -e

# Configuration
REGION="us-west-2"
BUCKET="mental-health-agent"
ROLE_NAME="MentalHealthAgentRole"

echo "🧠 Deploying Mental Health Agent Lambda Functions"
echo "================================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI configured"

# Create S3 bucket if it doesn't exist
echo "📦 Creating S3 bucket: $BUCKET"
aws s3 mb s3://$BUCKET --region $REGION 2>/dev/null || echo "Bucket already exists"

# Create IAM role for Lambda functions
echo "🔐 Creating IAM role: $ROLE_NAME"
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file://infra/lambda_trust.json \
    --region $REGION 2>/dev/null || echo "Role already exists"

# Attach policies to the role
echo "📋 Attaching policies to role"
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create custom policy for S3 and Bedrock access
aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name MentalHealthAgentPolicy \
    --policy-document file://infra/lambda_bucket_policy.json

# Wait for role to be ready
echo "⏳ Waiting for IAM role to be ready..."
sleep 10

# Get the role ARN
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "Role ARN: $ROLE_ARN"

# Function to deploy a Lambda function
deploy_lambda() {
    local function_name=$1
    local handler_file=$2
    local description=$3
    
    echo "🚀 Deploying $function_name..."
    
    # Create deployment package
    cd lambdas
    zip -r ../deploy/${function_name}.zip ${handler_file}
    cd ..
    
    # Deploy or update Lambda function
    if aws lambda get-function --function-name $function_name --region $REGION > /dev/null 2>&1; then
        echo "  Updating existing function..."
        aws lambda update-function-code \
            --function-name $function_name \
            --zip-file fileb://deploy/${function_name}.zip \
            --region $REGION
    else
        echo "  Creating new function..."
        aws lambda create-function \
            --function-name $function_name \
            --runtime python3.9 \
            --role $ROLE_ARN \
            --handler ${handler_file%.py}.handler \
            --zip-file fileb://deploy/${function_name}.zip \
            --description "$description" \
            --timeout 60 \
            --memory-size 256 \
            --environment Variables="{MH_BUCKET=$BUCKET}" \
            --region $REGION
    fi
    
    echo "  ✅ $function_name deployed successfully"
}

# Deploy all Lambda functions
deploy_lambda "mh-chat-handler" "mh_chat_handler.py" "Mental Health Chat Handler"
deploy_lambda "mh-daily-checkin" "mh_daily_checkin.py" "Mental Health Daily Check-in"
deploy_lambda "mh-evaluate-mental-health" "mh_evaluate_mental_health.py" "Mental Health Evaluation"
deploy_lambda "mh-recommendations" "mh_recommendations.py" "Mental Health Recommendations"
deploy_lambda "mh-schedule-checkin" "mh_schedule_checkin.py" "Mental Health Schedule Check-in"
deploy_lambda "mh-user-profile" "mh_user_profile.py" "Mental Health User Profile Management"

echo ""
echo "🎉 All Lambda functions deployed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure API Gateway to route to these Lambda functions"
echo "2. Test the endpoints"
echo ""
echo "Lambda function ARNs:"
aws lambda list-functions --region $REGION --query 'Functions[?starts_with(FunctionName, `mh-`)].{Name:FunctionName,Arn:FunctionArn}' --output table
