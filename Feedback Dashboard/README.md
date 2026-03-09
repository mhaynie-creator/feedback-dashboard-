# Revver In-App Feedback Dashboard

## 🚀 Quick Start - Deploy to Vercel

### Option 1: Replace your existing project (Recommended)

1. **Download all files** from this folder
2. **Go to your GitHub repository** (`feedback-dashboard`)
3. **Delete all existing files** in the repo
4. **Upload these new files:**
   - `index.html` (root level)
   - `data/` folder (with all JSON files inside)
5. **Commit the changes**
6. **Vercel auto-deploys!** (usually within 30-60 seconds)

### Option 2: Create a new Vercel project

1. Create a new GitHub repository
2. Upload `index.html` and the `data/` folder
3. Connect to Vercel and deploy

---

## 📁 Project Structure

```
feedback-dashboard/
├── index.html              ← Dashboard (loads data from JSON)
├── data/
│   ├── manifest.json       ← Lists all available months
│   ├── 2025-01.json        ← January 2025 data
│   ├── 2025-02.json        ← February 2025 data
│   ├── ...                 ← (all 2025 months)
│   ├── 2026-01.json        ← January 2026 data
│   └── 2026-02.json        ← February 2026 data
└── generate_monthly_json.py ← Script to create new month's JSON
```

---

## 📅 Monthly Update Process

### Your new workflow each month:

1. **Complete your manual categorization** in the spreadsheet as usual

2. **Upload the categorized CSV to Claude** and say:
   > "Here's March 2026's categorized feedback. Generate the JSON for my dashboard."

3. **I'll generate a JSON file** (e.g., `2026-03.json`) with all the metrics

4. **Upload the JSON to your GitHub repo:**
   - Go to `data/` folder in your repo
   - Click "Add file" → "Upload files"
   - Upload the new JSON file (e.g., `2026-03.json`)
   - Commit

5. **Update manifest.json:**
   - Click on `data/manifest.json`
   - Click the pencil (edit) icon
   - Add the new filename to the `files` array:
     ```json
     "files": [
       "2025-01.json",
       ...
       "2026-02.json",
       "2026-03.json"  ← Add new month here
     ]
     ```
   - Update `lastUpdated` to current month
   - Commit

6. **Done!** Vercel auto-deploys in ~30 seconds

---

## 🔧 Manual JSON Generation (Advanced)

If you want to generate JSON files yourself:

```bash
# Install Python 3 if needed
python generate_monthly_json.py your_categorized_file.csv 2026-03
```

This creates `2026-03.json` ready to upload.

---

## 📊 Data Format Reference

Each month's JSON file contains:

```json
{
  "period": "2026-03",
  "total": 180,
  "categories": {
    "Sentiment Only": 70,
    "User Interface & Navigation": 25,
    ...
  },
  "sentiment": {
    "Positive": 85,
    "Negative": 70,
    "Neutral": 25
  },
  "userType": {
    "Guest": 100,
    "Regular": 80
  },
  "guestTop5": { ... },
  "regularTop5": { ... },
  "churnRisk": [
    {
      "domain": "example.com",
      "accountId": "12345",
      "note": "Quote from feedback...",
      "userType": "Regular"
    }
  ],
  "takeaways": [
    "• <strong>Key insight:</strong> Description here"
  ]
}
```

---

## ✅ Included Data

This package includes:
- **All 2025 data** (January - November 2025)
- **January 2026** (145 entries, 2 churn risks)
- **February 2026** (207 entries, 5 churn risks)

---

## 🆘 Troubleshooting

**Dashboard shows "Error loading data"**
- Make sure `data/manifest.json` exists
- Make sure all files listed in manifest.json exist in the data folder

**New month not showing**
- Check that you added the filename to `manifest.json`
- Check that the JSON file is valid (no syntax errors)

**Charts not updating**
- Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache

---

## 📧 Questions?

Just upload your monthly CSV and ask me to generate the JSON!
