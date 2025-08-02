import os
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify, send_file
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('court_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT NOT NULL,
            case_number TEXT NOT NULL,
            filing_year TEXT NOT NULL,
            query_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_response TEXT,
            parsed_data TEXT,
            status TEXT DEFAULT 'success'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS case_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT NOT NULL,
            case_number TEXT NOT NULL,
            filing_year TEXT NOT NULL,
            parties_names TEXT,
            filing_date TEXT,
            next_hearing_date TEXT,
            latest_order_link TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

class CourtDataFetcher:
    def __init__(self):
        self.base_url = "https://districts.ecourts.gov.in"
        self.court_code = "DL01"  # Delhi District Court
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_case_data(self, case_type, case_number, filing_year):
        """
        Fetch case data from eCourts portal
        This is a simplified implementation - real implementation would need
        to handle specific court's form structure and anti-bot measures
        """
        try:
            # Step 1: Get the case status page
            search_url = f"{self.base_url}/services/ecourts_services/ecourtindia_v6/"
            
            # Simulate the search process
            search_data = {
                'case_type': case_type,
                'case_no': case_number,
                'case_year': filing_year,
                'court_code': self.court_code
            }
            
            # In real implementation, you'd need to:
            # 1. Handle view state tokens
            # 2. Solve CAPTCHAs (using services like 2captcha)
            # 3. Handle session management
            
            # For demo purposes, return mock data
            return self._get_mock_case_data(case_type, case_number, filing_year)
            
        except Exception as e:
            logger.error(f"Error fetching case data: {str(e)}")
            raise Exception(f"Failed to fetch case data: {str(e)}")
    
    def _get_mock_case_data(self, case_type, case_number, filing_year):
        """Mock data for demonstration - replace with actual scraping logic"""
        mock_data = {
            'parties_names': f"Petitioner Name vs Respondent Name (Case: {case_type}/{case_number}/{filing_year})",
            'filing_date': f"15-01-{filing_year}",
            'next_hearing_date': "25-08-2025",
            'latest_order_link': f"/orders/{case_type}_{case_number}_{filing_year}_latest.pdf",
            'case_status': 'Active',
            'last_order_date': '15-07-2025',
            'court_name': 'Delhi District Court',
            'judge_name': 'Hon\'ble Justice Sample Name'
        }
        return mock_data
    
    def download_pdf(self, pdf_link):
        """Download PDF from court website"""
        try:
            if not pdf_link.startswith('http'):
                pdf_link = urljoin(self.base_url, pdf_link)
            
            response = self.session.get(pdf_link, timeout=30)
            response.raise_for_status()
            
            return response.content
        except Exception as e:
            logger.error(f"Error downloading PDF: {str(e)}")
            return None

# Database operations
def log_query(case_type, case_number, filing_year, raw_response, parsed_data, status='success'):
    conn = sqlite3.connect('court_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO queries (case_type, case_number, filing_year, raw_response, parsed_data, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (case_type, case_number, filing_year, str(raw_response), str(parsed_data), status))
    
    conn.commit()
    conn.close()

def save_case_data(case_data):
    conn = sqlite3.connect('court_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO case_data 
        (case_type, case_number, filing_year, parties_names, filing_date, 
         next_hearing_date, latest_order_link)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        case_data.get('case_type'),
        case_data.get('case_number'), 
        case_data.get('filing_year'),
        case_data.get('parties_names'),
        case_data.get('filing_date'),
        case_data.get('next_hearing_date'),
        case_data.get('latest_order_link')
    ))
    
    conn.commit()
    conn.close()

def get_recent_queries(limit=10):
    conn = sqlite3.connect('court_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT case_type, case_number, filing_year, query_timestamp, status
        FROM queries 
        ORDER BY query_timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

# Flask routes
@app.route('/')
def index():
    recent_queries = get_recent_queries()
    return render_template('index.html', recent_queries=recent_queries)

@app.route('/search', methods=['POST'])
def search_case():
    try:
        case_type = request.form.get('case_type')
        case_number = request.form.get('case_number')
        filing_year = request.form.get('filing_year')
        
        if not all([case_type, case_number, filing_year]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Validate inputs
        if not re.match(r'^\d+$', case_number):
            return jsonify({'error': 'Case number must be numeric'}), 400
        
        if not re.match(r'^20\d{2}$', filing_year):
            return jsonify({'error': 'Filing year must be a valid 4-digit year'}), 400
        
        # Fetch case data
        fetcher = CourtDataFetcher()
        case_data = fetcher.get_case_data(case_type, case_number, filing_year)
        
        # Add search parameters to case data
        case_data.update({
            'case_type': case_type,
            'case_number': case_number,
            'filing_year': filing_year
        })
        
        # Log the query
        log_query(case_type, case_number, filing_year, "Mock response", case_data)
        
        # Save case data
        save_case_data(case_data)
        
        return jsonify({
            'success': True,
            'data': case_data
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        log_query(
            request.form.get('case_type', ''),
            request.form.get('case_number', ''),
            request.form.get('filing_year', ''),
            f"Error: {str(e)}",
            {},
            'error'
        )
        return jsonify({'error': str(e)}), 500

@app.route('/download_pdf')
def download_pdf():
    try:
        pdf_link = request.args.get('link')
        if not pdf_link:
            return jsonify({'error': 'PDF link is required'}), 400
        
        fetcher = CourtDataFetcher()
        pdf_content = fetcher.download_pdf(pdf_link)
        
        if pdf_content:
            # For demo, return a mock PDF response
            return jsonify({
                'success': True,
                'message': 'PDF download would start here',
                'link': pdf_link
            })
        else:
            return jsonify({'error': 'Failed to download PDF'}), 500
            
    except Exception as e:
        logger.error(f"PDF download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True, host='0.0.0.0', port=5000)
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)    