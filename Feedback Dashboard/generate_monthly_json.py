#!/usr/bin/env python3
"""
generate_monthly_json.py

Generates dashboard-ready JSON from a categorized feedback CSV.

Usage:
    python generate_monthly_json.py input.csv 2026-01

This script reads a manually categorized CSV file and outputs a JSON file
ready for the Revver In-App Feedback Dashboard.

Expected CSV columns:
    - Email or Protected Email Address for AI (for domain extraction)
    - Time (for date validation)
    - AccountID
    - Content (the feedback text)
    - Desktop Version (if present, System = Desktop)
    - Translated Functional Category (the category)
    - Sentiment (Positive/Negative/Neutral)
    - User Type (Guest/Regular)
    - System (Browser/Desktop)
    - Kind of Feedback (General Feedback/Enhancement Request/Bug)
    - Outreach (No follow-up needed/Needs follow-up/Churn risk/UXR candidate)
"""

import csv
import json
import sys
import re
from collections import Counter, defaultdict
from datetime import datetime

def extract_domain(email_or_domain):
    """Extract domain from email or domain string."""
    if not email_or_domain:
        return None
    email_or_domain = str(email_or_domain).strip()
    if '@' in email_or_domain:
        return email_or_domain.split('@')[-1].lower()
    return email_or_domain.lower().split()[0]  # First word if multiple

def is_guest_domain(domain):
    """Check if domain indicates a guest user."""
    guest_domains = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'outlook.com',
        'icloud.com', 'me.com', 'mac.com', 'msn.com', 'live.com',
        'comcast.net', 'verizon.net', 'att.net', 'sbcglobal.net',
        'ymail.com', 'frontier.com', 'proton.me', 'protonmail.com',
        'charter.net', 'centurylink.net'
    }
    return domain in guest_domains if domain else False

def process_csv(filepath):
    """Process the categorized CSV and return aggregated data."""
    
    data = {
        'categories': Counter(),
        'sentiment': Counter(),
        'userType': Counter(),
        'system': Counter(),
        'kindOfFeedback': Counter(),
        'outreach': Counter(),
        'guestCategories': Counter(),
        'regularCategories': Counter(),
        'churnRisk': [],
        'needsFollowup': [],
        'enhancementRequests': 0,
        'bugs': 0,
        'total': 0,
        'domainStats': defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0})
    }
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Skip empty rows
            content = row.get('Content', '').strip()
            if not content:
                continue
            
            data['total'] += 1
            
            # Get key fields with fallbacks
            category = row.get('Translated Functional Category', '').strip() or 'Uncategorized'
            sentiment = row.get('Sentiment', '').strip() or 'Neutral'
            user_type = row.get('User Type', '').strip() or 'Regular'
            system = row.get('System', '').strip() or 'Browser'
            kind = row.get('Kind of Feedback', '').strip() or 'General Feedback'
            outreach = row.get('Outreach', '').strip() or 'No follow-up needed'
            
            # Normalize sentiment
            if sentiment.lower() in ['positive', 'pos']:
                sentiment = 'Positive'
            elif sentiment.lower() in ['negative', 'neg']:
                sentiment = 'Negative'
            else:
                sentiment = 'Neutral'
            
            # Normalize user type
            user_type = 'Guest' if user_type.lower() == 'guest' else 'Regular'
            
            # Normalize system
            if row.get('Desktop Version', '').strip():
                system = 'Desktop'
            else:
                system = 'Desktop' if system.lower() == 'desktop' else 'Browser'
            
            # Count aggregates
            data['categories'][category] += 1
            data['sentiment'][sentiment] += 1
            data['userType'][user_type] += 1
            data['system'][system] += 1
            data['kindOfFeedback'][kind] += 1
            data['outreach'][outreach] += 1
            
            # Category by user type
            if user_type == 'Guest':
                data['guestCategories'][category] += 1
            else:
                data['regularCategories'][category] += 1
            
            # Track special cases
            if kind.lower() == 'enhancement request':
                data['enhancementRequests'] += 1
            elif kind.lower() == 'bug':
                data['bugs'] += 1
            
            # Churn risk accounts
            if 'churn' in outreach.lower():
                domain = extract_domain(row.get('Protected Email Address for AI') or row.get('Email', ''))
                account_id = row.get('AccountID', '')
                data['churnRisk'].append({
                    'domain': domain,
                    'accountId': account_id,
                    'note': content[:100] + '...' if len(content) > 100 else content,
                    'userType': user_type
                })
            
            # Needs follow-up
            if 'follow-up' in outreach.lower() and 'no' not in outreach.lower():
                domain = extract_domain(row.get('Protected Email Address for AI') or row.get('Email', ''))
                account_id = row.get('AccountID', '')
                data['needsFollowup'].append({
                    'domain': domain,
                    'accountId': account_id,
                    'note': content[:100] + '...' if len(content) > 100 else content
                })
            
            # Domain stats
            domain = extract_domain(row.get('Protected Email Address for AI') or row.get('Email', ''))
            if domain:
                data['domainStats'][domain]['total'] += 1
                if sentiment == 'Positive':
                    data['domainStats'][domain]['positive'] += 1
                elif sentiment == 'Negative':
                    data['domainStats'][domain]['negative'] += 1
                else:
                    data['domainStats'][domain]['neutral'] += 1
    
    return data

def get_top_n(counter, n=5):
    """Get top N items from a counter as a dict."""
    return dict(counter.most_common(n))

def calculate_domain_rankings(domain_stats, min_count=3):
    """Calculate top positive and negative domains."""
    top_positive = []
    top_negative = []
    
    for domain, stats in domain_stats.items():
        if stats['total'] >= min_count:
            pos_rate = (stats['positive'] / stats['total']) * 100
            neg_rate = (stats['negative'] / stats['total']) * 100
            
            top_positive.append({
                'domain': domain,
                'rate': round(pos_rate, 1),
                'count': stats['positive'],
                'total': stats['total']
            })
            top_negative.append({
                'domain': domain,
                'rate': round(neg_rate, 1),
                'count': stats['negative'],
                'total': stats['total']
            })
    
    top_positive.sort(key=lambda x: (-x['rate'], -x['total']))
    top_negative.sort(key=lambda x: (-x['rate'], -x['total']))
    
    return top_positive[:10], top_negative[:10]

def generate_takeaways(data):
    """Auto-generate key takeaways based on the data."""
    takeaways = []
    
    total = data['total']
    if total == 0:
        return ["No feedback data for this period."]
    
    # Sentiment summary
    pos_pct = (data['sentiment']['Positive'] / total) * 100
    neg_pct = (data['sentiment']['Negative'] / total) * 100
    
    if pos_pct > neg_pct:
        takeaways.append(f"• <strong>Positive sentiment leads:</strong> {pos_pct:.1f}% positive vs {neg_pct:.1f}% negative")
    else:
        takeaways.append(f"• <strong>Negative sentiment dominates:</strong> {neg_pct:.1f}% negative vs {pos_pct:.1f}% positive")
    
    # Guest vs Regular
    guest_pct = (data['userType']['Guest'] / total) * 100
    if guest_pct > 50:
        takeaways.append(f"• <strong>High guest volume:</strong> {guest_pct:.1f}% of feedback from guest users")
    
    # Top category (excluding Sentiment Only)
    non_sentiment_cats = {k: v for k, v in data['categories'].items() if k != 'Sentiment Only'}
    if non_sentiment_cats:
        top_cat = max(non_sentiment_cats.items(), key=lambda x: x[1])
        takeaways.append(f"• <strong>Top functional issue:</strong> {top_cat[0]} ({top_cat[1]} mentions)")
    
    # Churn risk
    if data['churnRisk']:
        takeaways.append(f"• <strong>Churn risk alert:</strong> {len(data['churnRisk'])} accounts flagged for immediate attention")
    
    # Enhancement requests
    if data['enhancementRequests'] > 0:
        takeaways.append(f"• <strong>Feature requests:</strong> {data['enhancementRequests']} enhancement requests received")
    
    # Bugs
    if data['bugs'] > 0:
        takeaways.append(f"• <strong>Bug reports:</strong> {data['bugs']} bugs reported")
    
    return takeaways

def build_json_output(data, period):
    """Build the final JSON structure for the dashboard."""
    
    top_positive_domains, top_negative_domains = calculate_domain_rankings(data['domainStats'])
    
    output = {
        "period": period,
        "generatedAt": datetime.now().isoformat(),
        "total": data['total'],
        "categories": dict(data['categories'].most_common()),
        "sentiment": dict(data['sentiment']),
        "userType": dict(data['userType']),
        "system": dict(data['system']),
        "guestTop5": get_top_n(data['guestCategories'], 5),
        "regularTop5": get_top_n(data['regularCategories'], 5),
        "kindOfFeedback": dict(data['kindOfFeedback']),
        "outreach": dict(data['outreach']),
        "churnRisk": data['churnRisk'],
        "needsFollowup": data['needsFollowup'],
        "topPositiveDomains": top_positive_domains,
        "topNegativeDomains": top_negative_domains,
        "takeaways": generate_takeaways(data)
    }
    
    return output

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_monthly_json.py <input.csv> <period>")
        print("Example: python generate_monthly_json.py Feb_2026_Feedback.csv 2026-02")
        sys.exit(1)
    
    input_file = sys.argv[1]
    period = sys.argv[2]
    
    # Validate period format
    if not re.match(r'^\d{4}-\d{2}$', period):
        print(f"Error: Period must be in YYYY-MM format (e.g., 2026-02), got: {period}")
        sys.exit(1)
    
    print(f"Processing: {input_file}")
    print(f"Period: {period}")
    
    # Process the CSV
    data = process_csv(input_file)
    
    if data['total'] == 0:
        print("Warning: No valid feedback entries found in CSV.")
    
    # Build JSON output
    output = build_json_output(data, period)
    
    # Write to file
    output_file = f"{period}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Generated: {output_file}")
    print(f"   Total entries: {data['total']}")
    print(f"   Sentiment: +{data['sentiment']['Positive']} / -{data['sentiment']['Negative']} / ={data['sentiment']['Neutral']}")
    print(f"   Users: {data['userType']['Guest']} guests, {data['userType']['Regular']} regular")
    print(f"   Churn risks: {len(data['churnRisk'])}")
    
    return output_file

if __name__ == "__main__":
    main()
