#!/bin/bash
# Railway deployment script - SECURE VERSION

echo "🚀 Deploying openblog..."

# SECURITY NOTE: API keys are now stored in Railway environment variables
# Use: railway variables --set "KEY=value" to set them securely
echo "⚠️  Make sure you've set these environment variables in Railway:"
echo "   - GEMINI_API_KEY"
echo "   - SERPER_API_KEY" 
echo "   - DATAFORSEO_LOGIN"
echo "   - DATAFORSEO_PASSWORD"

echo "✅ Using secure environment variables from Railway"

# Deploy to Railway
railway up --detach

echo "🎯 Deployment initiated"