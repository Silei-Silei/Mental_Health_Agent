# 🌐 Deploy to Streamlit Cloud (No AWS Setup Required)

This guide shows how to deploy the Mental Health Agent to Streamlit Cloud so others can use it without any AWS setup.

## 🚀 Quick Deployment to Streamlit Cloud

### Step 1: Prepare Your Repository

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add Streamlit Cloud deployment files"
   git push origin main
   ```

2. **Required Files** (already included):
   - `streamlit_app.py` - Main Streamlit application
   - `.streamlit/config.toml` - Streamlit configuration
   - `requirements.txt` - Python dependencies

### Step 2: Deploy to Streamlit Cloud

1. **Go to [Streamlit Cloud](https://share.streamlit.io/)**
2. **Sign in with GitHub**
3. **Click "New app"**
4. **Select your repository**: `mental_health_agent_starter`
5. **Main file path**: `streamlit_app.py`
6. **Click "Deploy"**

### Step 3: Configure Environment Variables

In Streamlit Cloud dashboard:

1. **Go to your app settings**
2. **Add environment variables**:
   - `API_BASE`: `https://ot173x9io1.execute-api.us-west-2.amazonaws.com`
   - `MH_BUCKET`: `mental-health-agent`

### Step 4: Access Your App

Your app will be available at:
```
https://your-app-name.streamlit.app
```

## 🔧 Alternative Deployment Options

### Option 1: Heroku
```bash
# Create Procfile
echo "web: streamlit run streamlit_app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
git add Procfile
git commit -m "Add Heroku deployment"
git push heroku main
```

### Option 2: Railway
```bash
# Connect GitHub repository
# Railway will auto-detect Python and install dependencies
# Set environment variables in Railway dashboard
```

### Option 3: Render
```bash
# Connect GitHub repository
# Select "Web Service"
# Build command: `pip install -r requirements.txt`
# Start command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
```

## 🎯 Benefits of Cloud Deployment

- ✅ **No AWS setup required** for users
- ✅ **Instant access** via web browser
- ✅ **Free hosting** options available
- ✅ **Easy sharing** with just a URL
- ✅ **Automatic updates** from GitHub

## 🔒 Security Considerations

- **Rate Limiting**: Consider adding rate limiting to prevent abuse
- **API Keys**: You may want to add API key authentication
- **Cost Monitoring**: Monitor your AWS costs for API usage
- **Data Privacy**: Consider data retention policies

## 📊 Usage Monitoring

Monitor your deployment:
- **Streamlit Cloud**: Built-in analytics
- **AWS CloudWatch**: Monitor Lambda invocations
- **API Gateway**: Track request volume and costs

## 🚀 Making It Public

Once deployed, you can:
1. **Share the URL** with anyone
2. **Embed in websites** using iframe
3. **Create QR codes** for easy mobile access
4. **Add to app stores** as a web app

## 💡 Pro Tips

- **Custom Domain**: Use your own domain with Streamlit Cloud Pro
- **Multiple Environments**: Deploy dev/staging/prod versions
- **A/B Testing**: Deploy different versions for testing
- **Analytics**: Use Streamlit's built-in analytics or Google Analytics
