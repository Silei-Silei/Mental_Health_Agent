# 🧠 Mental Health Chatbot Agent

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

A comprehensive mental health support system built with AWS Bedrock and Lambda functions. This agent provides empathetic conversation, daily check-ins, mental health evaluation, personalized recommendations, and proactive check-in scheduling.

## 🌟 Features

- 💬 **Empathetic Chat** - AI-powered conversations with emotional support
- 📊 **Daily Check-ins** - Structured mental health questionnaires
- 📈 **Health Evaluation** - Quantitative analysis of mental health trends
- 🎯 **Personalized Recommendations** - Tailored content and activities
- ⏰ **Proactive Companions** - Intelligent scheduling of check-ins
- 🔒 **Privacy-First** - Secure data handling and user confidentiality
- ☁️ **Cloud-Ready** - Deploy to Streamlit Cloud or AWS infrastructure

## 🚀 Quick Start

**For immediate testing:**
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Mental_Health_Agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the playground (requires AWS deployment first)
streamlit run streamlit_playground.py
```

**For full deployment, see the [Deployment Guide](#-deployment-guide) below.**

**For instant public access, see [Cloud Deployment](#-cloud-deployment-options) below.**

## 🧠 Overview

The Mental Health Agent is designed to be a supportive companion that:
1. **Chats** - Provides empathetic conversation and emotional support
2. **Daily Check-ins** - Collects mental health status through structured questionnaires
3. **Evaluates** - Quantitatively assesses mental health situation using data analysis
4. **Recommends** - Suggests personalized content (videos, exercises, activities) based on needs
5. **Schedules** - Proactively schedules check-ins based on mental health status

## 🏗️ Architecture

- **API Contract**: `agent/openapi.yaml` defines the endpoints
- **Lambda Functions**: `lambdas/` contains the business logic
- **Infrastructure**: `infra/` has AWS IAM policies and trust relationships
- **Client Scripts**: `scripts/` provides CLI interface
- **Playground**: `streamlit_playground.py` offers a web interface for testing
- **Deployment Scripts**: Automated deployment and configuration scripts

## 📁 Project Structure

```
Mental_Health_Agent/
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI/CD pipeline
├── .streamlit/
│   └── config.toml               # Streamlit configuration
├── agent/
│   └── openapi.yaml              # API contract definition
├── infra/
│   ├── lambda_trust.json         # IAM trust policy for Lambda
│   └── lambda_bucket_policy.json # S3 bucket access policy
├── lambdas/
│   ├── mh_chat_handler.py        # Chat functionality
│   ├── mh_daily_checkin.py       # Daily check-in processing
│   ├── mh_evaluate_mental_health.py # Mental health evaluation
│   ├── mh_recommendations.py     # Personalized recommendations
│   └── mh_schedule_checkin.py    # Companion scheduling
├── scripts/
│   └── invoke_mental_health_agent.py # CLI interface
├── tests/
│   ├── __init__.py               # Test package
│   └── test_api.py                # API tests
├── add_api_routes.sh             # API Gateway route configuration
├── CONTRIBUTING.md               # Contribution guidelines
├── DEPLOYMENT_CLOUD.md           # Cloud deployment instructions
├── LICENSE                        # MIT License
├── README.md                      # Project documentation
├── deploy_lambdas.sh             # Lambda deployment script
├── requirements.txt              # Python dependencies
├── run.sh                        # Environment setup and testing
├── setup.py                      # Python package setup
├── streamlit_app.py              # Streamlit Cloud deployment version
└── streamlit_playground.py       # Web-based testing interface
```

## 🌐 Cloud Deployment Options

**Want to share your Mental Health Agent without requiring others to deploy AWS infrastructure?**

### Option 1: Streamlit Cloud (Recommended)
Deploy to Streamlit Cloud for instant public access:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add Streamlit Cloud deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Connect your GitHub repository
   - Select `streamlit_app.py` as main file
   - Set environment variables: `API_BASE` and `MH_BUCKET`
   - Deploy!

3. **Share the URL**: `https://your-app.streamlit.app`

**Benefits**: Free hosting, instant access, no AWS setup required for users

### Option 2: Other Cloud Platforms
- **Heroku**: `streamlit_app.py` + `Procfile`
- **Railway**: Auto-detect Python, set env vars
- **Render**: Web service with build/start commands
- **Google Cloud Run**: Containerized deployment

### Option 3: Public API
Make your API Gateway publicly accessible:
- Remove API key requirements
- Enable CORS
- Add rate limiting
- Share API URL: `https://your-api.execute-api.region.amazonaws.com`

**See [DEPLOYMENT_CLOUD.md](DEPLOYMENT_CLOUD.md) for detailed instructions.**

## 🚀 Deployment Guide

This section provides step-by-step instructions for deploying the Mental Health Agent to AWS.

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Python 3.9+** installed
4. **Node.js** (for API Gateway deployment tools)

### Step 1: AWS Setup

1. **Create S3 Bucket**:
   ```bash
   aws s3 mb s3://your-mental-health-agent-bucket
   ```

2. **Create IAM Role** for Lambda functions:
   ```bash
   aws iam create-role --role-name MentalHealthAgentRole --assume-role-policy-document file://infra/lambda_trust.json
   aws iam put-role-policy --role-name MentalHealthAgentRole --policy-name S3BucketAccess --policy-document file://infra/lambda_bucket_policy.json
   ```

3. **Attach Bedrock Permissions**:
   ```bash
   aws iam attach-role-policy --role-name MentalHealthAgentRole --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
   ```

### Step 2: Deploy Lambda Functions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Deploy All Functions**:
   ```bash
   chmod +x deploy_lambdas.sh
   ./deploy_lambdas.sh
   ```

   This script will:
   - Package each Lambda function with dependencies
   - Deploy to AWS Lambda with proper IAM roles
   - Set up environment variables (MH_BUCKET)
   - Configure timeout and memory settings
   - Handle all 5 Lambda functions automatically

**What the script does:**
- Creates deployment packages for each Lambda function
- Uses the IAM role created in Step 1
- Sets up proper environment variables
- Handles AWS region configuration
- Provides error handling and status updates

### Step 3: Create API Gateway

1. **Create HTTP API**:
   ```bash
   aws apigatewayv2 create-api --name mental-health-agent-api --protocol-type HTTP --target arn:aws:lambda:us-west-2:YOUR_ACCOUNT_ID:function:mh-chat-handler
   ```

2. **Add API Routes**:
   ```bash
   chmod +x add_api_routes.sh
   ./add_api_routes.sh
   ```

   This script will:
   - Create integrations for each Lambda function
   - Set up all 5 API routes (/chat, /daily-checkin, etc.)
   - Grant API Gateway permission to invoke Lambda functions
   - Handle HTTP API Gateway configuration

3. **Deploy API**:
   ```bash
   aws apigatewayv2 create-deployment --api-id YOUR_API_ID --stage-name prod
   ```

**What the script does:**
- Creates Lambda integrations for each endpoint
- Sets up POST routes for all 5 functions
- Configures proper permissions for API Gateway
- Handles error cases and provides feedback

### Step 4: Configure Environment

1. **Set Environment Variables**:
   ```bash
   export API_BASE=https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com
   export MH_BUCKET=your-mental-health-agent-bucket
   ```

2. **Update Configuration**:
   - Update `streamlit_playground.py` with your API Gateway URL
   - Update `run.sh` with your bucket name

### Step 5: Test Deployment

1. **Use the Test Script**:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

   This script will:
   - Set up environment variables automatically
   - Test all API endpoints
   - Run the Streamlit playground
   - Provide debugging information

2. **Manual Testing**:
   ```bash
   # Test individual endpoints
   python scripts/invoke_mental_health_agent.py chat --user-id "test_user" --message "Hello"
   python scripts/invoke_mental_health_agent.py daily-checkin --user-id "test_user" --checkin-type "morning"
   python scripts/invoke_mental_health_agent.py evaluate --user-id "test_user" --evaluation-period "week"
   ```

3. **Run Playground**:
   ```bash
   streamlit run streamlit_playground.py
   ```

4. **Verify All Functions**:
   - Chat functionality
   - Daily check-in processing
   - Mental health evaluation
   - Recommendation generation
   - Companion scheduling

**What run.sh does:**
- Automatically sets API_BASE and MH_BUCKET environment variables
- Tests all 5 API endpoints with sample data
- Launches the Streamlit playground
- Provides helpful debugging output

### Step 6: Production Considerations

1. **Custom Domain** (Optional):
   ```bash
   aws apigatewayv2 create-domain-name --domain-name your-domain.com --domain-name-configurations CertificateArn=YOUR_CERT_ARN
   ```

2. **Monitoring Setup**:
   - Enable CloudWatch logging
   - Set up alarms for errors
   - Monitor API Gateway metrics

3. **Security Hardening**:
   - Enable API key authentication
   - Set up CORS policies
   - Implement rate limiting
