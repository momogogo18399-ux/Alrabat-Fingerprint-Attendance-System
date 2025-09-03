# 🚀 Vercel Auto-Deploy Setup Guide

## 📋 Prerequisites

1. **Vercel Account**: Create account at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Ensure your code is on GitHub
3. **Environment Variables**: Set up required environment variables

## 🔧 Setup Instructions

### 1. Connect GitHub to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Select the repository: `Alrabat-Fingerprint-Attendance-System`

### 2. Configure Environment Variables

In Vercel Dashboard → Project Settings → Environment Variables, add:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Security Configuration
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key

# Database Configuration
DATABASE_URL=your_database_url

# Optional: Face Recognition (if enabled)
FACE_RECOGNITION_ENABLED=false
```

### 3. GitHub Actions Setup

The project includes automatic deployment via GitHub Actions:

- **File**: `.github/workflows/vercel-deploy.yml`
- **Trigger**: Every push to `main` branch
- **Action**: Automatically deploys to Vercel

### 4. Required GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to GitHub → Settings → Secrets and variables → Actions
2. Add the following secrets:

```bash
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=your_vercel_org_id
VERCEL_PROJECT_ID=your_vercel_project_id
```

## 🔄 Auto-Deploy Process

### How it Works:

1. **Push to GitHub**: When you push code to `main` branch
2. **GitHub Actions**: Automatically triggers deployment
3. **Vercel Build**: Builds and deploys the application
4. **Live Update**: Your Vercel app updates automatically

### Manual Deployment:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

## 📁 Project Structure for Vercel

```
├── api/
│   └── index.py          # Vercel serverless function
├── web_app.py            # Main Flask application
├── vercel.json           # Vercel configuration
├── package.json          # Node.js configuration
├── requirements.txt      # Python dependencies
├── .vercelignore         # Files to ignore
└── vercel-build.sh       # Build script
```

## 🛠️ Configuration Files

### vercel.json
- **Runtime**: Python 3.11
- **Max Lambda Size**: 50MB
- **Max Duration**: 30 seconds
- **Routes**: All requests to `web_app.py`

### .vercelignore
- Excludes desktop GUI files
- Excludes build artifacts
- Excludes documentation files

## 🚨 Troubleshooting

### Common Issues:

1. **Build Timeout**: Increase `maxDuration` in `vercel.json`
2. **Memory Issues**: Increase `maxLambdaSize`
3. **Import Errors**: Check `PYTHONPATH` in environment variables
4. **Missing Dependencies**: Verify `requirements.txt`

### Debug Commands:

```bash
# Test locally
vercel dev

# Check logs
vercel logs

# Redeploy
vercel --prod --force
```

## 📊 Monitoring

- **Vercel Dashboard**: Monitor deployments and performance
- **GitHub Actions**: Check deployment status
- **Application Logs**: View real-time logs in Vercel

## 🔐 Security Notes

- Environment variables are encrypted in Vercel
- Never commit sensitive data to GitHub
- Use Vercel's built-in security features
- Enable HTTPS (automatic in Vercel)

## 📞 Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **GitHub Actions**: [docs.github.com/actions](https://docs.github.com/actions)
- **Project Issues**: [GitHub Issues](https://github.com/momogogo18399-ux/Alrabat-Fingerprint-Attendance-System/issues)

---

**🎉 Your application will now automatically deploy to Vercel whenever you push to GitHub!**
