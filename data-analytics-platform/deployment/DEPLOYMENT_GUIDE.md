# DataLens - Deployment Guide: InfinityFree + PythonAnywhere

## Overview: How Split Hosting Works

Your project has TWO parts:
1. **Frontend** (HTML, CSS, JS) → Host on **InfinityFree** (free static hosting)
2. **Backend** (Python/Flask) → Host on **PythonAnywhere** (free Python hosting)

The frontend makes API calls to the backend across the internet. This works because we've set up CORS (Cross-Origin Resource Sharing) in the Flask app.

```
[User Browser]
    ↓
[InfinityFree - Frontend HTML/CSS/JS]
    ↓ API calls (fetch)
[PythonAnywhere - Flask Backend]
    ↓
[Analysis Results]
```

---

## Step 1: Deploy Backend on PythonAnywhere

### 1.1 Create a PythonAnywhere Account
1. Go to https://www.pythonanywhere.com/
2. Click "Create a free account"
3. Sign up with your email

### 1.2 Upload Your Backend Code
1. Log into PythonAnywhere
2. Go to **Files** tab
3. Create a new directory: `data-analytics-platform`
4. Upload these files into that directory:
   - `app.py`
   - `requirements.txt`
   - `utils/__init__.py`
   - `utils/analyzer.py`
   - `utils/report_generator.py`

   Your file structure on PythonAnywhere should be:
   ```
   /home/yourusername/
   └── data-analytics-platform/
       ├── app.py
       ├── requirements.txt
       ├── utils/
       │   ├── __init__.py
       │   ├── analyzer.py
       │   └── report_generator.py
       ├── uploads/       (auto-created)
       └── reports/       (auto-created)
   ```

### 1.3 Set Up a Virtual Environment
1. Go to **Consoles** tab → Open a **Bash console**
2. Run these commands:
   ```bash
   cd ~/data-analytics-platform
   mkvirtualenv datalens --python=python3.11
   pip install flask flask-cors numpy pandas scikit-learn matplotlib reportlab scipy openpyxl xlrd
   ```

   Note: If `mkvirtualenv` doesn't work, try:
   ```bash
   python3.11 -m venv ~/datalens-env
   source ~/datalens-env/bin/activate
   pip install flask flask-cors numpy pandas scikit-learn matplotlib reportlab scipy openpyxl xlrd
   ```

### 1.4 Configure the WSGI File
1. Edit `deployment/wsgi.py` and replace `yourusername` with your actual PythonAnywhere username
2. Upload `wsgi.py` to `/home/yourusername/data-analytics-platform/`

   The WSGI file should look like:
   ```python
   import sys
   import os

   PROJECT_ROOT = '/home/yourusername/data-analytics-platform'
   sys.path.insert(0, PROJECT_ROOT)
   os.environ['FLASK_ENV'] = 'production'
   os.chdir(PROJECT_ROOT)

   from app import app as application
   ```

### 1.5 Create the Web App
1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration** (NOT the Flask template)
4. Select **Python 3.11**
5. Set these in the web app configuration:
   - **Source code**: `/home/yourusername/data-analytics-platform`
   - **Working directory**: `/home/yourusername/data-analytics-platform`
   - **Virtualenv**: `/home/yourusername/.virtualenvs/datalens` (or `~/datalens-env`)
   - **WSGI configuration file**: Click to edit, and paste the content from `wsgi.py`

6. Click **Reload** to apply changes

### 1.6 Verify the Backend
- Your backend URL will be: `https://yourusername.pythonanywhere.com`
- Visit it in your browser - you should see the HTML page (or an error if templates aren't uploaded, which is fine)
- Test the API: `https://yourusername.pythonanywhere.com/api/upload` should return an error (that means it's running!)

---

## Step 2: Deploy Frontend on InfinityFree

### 2.1 Create an InfinityFree Account
1. Go to https://www.infinityfree.com/
2. Sign up for a free account
3. Create a new website/subdomain

### 2.2 Upload Frontend Files
1. Go to **File Manager** in InfinityFree control panel
2. Navigate to `htdocs` directory (this is your web root)
3. Upload these files from the `deployment/frontend/` folder:
   - `index.html`
   - `style.css`
   - `charts.js`
   - `app.js`

   Your file structure on InfinityFree should be:
   ```
   /htdocs/
   ├── index.html
   ├── style.css
   ├── charts.js
   └── app.js
   ```

### 2.3 Configure the API URL
**This is the most important step!**

1. Open `index.html` in the File Manager editor
2. Find this line near the top:
   ```javascript
   const API_URL = 'https://yourusername.pythonanywhere.com';
   ```
3. Replace `yourusername` with your actual PythonAnywhere username
4. Save the file

### 2.4 Verify the Frontend
- Visit your InfinityFree website URL (e.g., `https://yoursite.infinityfreeapp.com`)
- You should see the DataLens upload page
- Try uploading a CSV file - it should connect to your PythonAnywhere backend

---

## Step 3: Test the Full Setup

1. Visit your InfinityFree URL
2. Upload a CSV file
3. Click "Run Analysis"
4. Check all sections work: Overview, Correlations, Predictions, etc.
5. Generate a PDF report

---

## Important Limitations (Free Tier)

### PythonAnywhere Free Tier Limits:
- **100 seconds CPU per day** - Heavy analysis may hit this limit
- **App sleeps after inactivity** - First request after idle takes ~10 seconds to wake up
- **No custom domains** - Must use `yourusername.pythonanywhere.com`
- **512 MB disk space**
- **No outbound internet** on free tier (but inbound API calls work fine)

### InfinityFree Free Tier Limits:
- **Unlimited bandwidth** (fair use)
- **Unlimited disk space** (fair use)
- **No server-side processing** - Only static files (HTML/CSS/JS)
- **No Python/PHP** processing for our use case

### Tips to Avoid PythonAnywhere CPU Limits:
- Keep datasets under 10,000 rows
- Limit prediction periods to 5-10
- Don't run multiple analyses simultaneously
- Use "Light" analysis when possible

---

## Alternative: All-in-One on PythonAnywhere

If split hosting seems complex, you can host EVERYTHING on PythonAnywhere:

1. Upload ALL project files (including templates/ and static/ folders)
2. The Flask app serves both frontend and backend from one place
3. Visit `https://yourusername.pythonanywhere.com` - everything works!

This is actually simpler and recommended for beginners. The split hosting approach is only needed if you want a custom domain or need InfinityFree's unlimited bandwidth.

### File structure for all-in-one on PythonAnywhere:
```
/home/yourusername/data-analytics-platform/
├── app.py
├── requirements.txt
├── wsgi.py
├── utils/
│   ├── __init__.py
│   ├── analyzer.py
│   └── report_generator.py
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       └── charts.js
├── sample_data.csv
├── uploads/       (auto-created)
└── reports/       (auto-created)
```

---

## Troubleshooting

### "CORS error" in browser console
- Make sure `flask-cors` is installed on PythonAnywhere
- Check that `CORS(app, resources={r"/api/*": {"origins": "*"}})` is in `app.py`

### "502 Bad Gateway" on PythonAnywhere
- Check your WSGI file has the correct path
- Check the error log in PythonAnywhere Web tab
- Make sure virtualenv has all packages installed

### Frontend loads but can't connect to backend
- Verify the `API_URL` in `index.html` matches your PythonAnywhere URL exactly
- Make sure the URL starts with `https://` not `http://`
- Check that the PythonAnywhere web app is not paused

### PDF report generation fails
- This is the most CPU-intensive operation
- Keep datasets small to avoid hitting CPU limits
- Check PythonAnywhere error logs

### App won't wake up after sleeping
- Free tier apps sleep after inactivity
- Visit the PythonAnywhere URL directly first to wake it up
- Then use your InfinityFree frontend
