# Court Data Fetcher & Mini-Dashboard

A web application for fetching and displaying Indian court case information from public eCourts portals.

## 🏛️ Court Chosen

**Target Court**: Delhi District Court via eCourts portal (`https://districts.ecourts.gov.in/`)

**Rationale**: Delhi District Court was chosen because:
- Well-structured eCourts portal with consistent API endpoints
- High case volume ensuring diverse test scenarios
- Standardized form inputs across different case types
- Reliable uptime and response consistency

## 🚀 Features

- **Case Search**: Search by Case Type, Case Number, and Filing Year
- **Data Display**: Clean presentation of case details including parties, dates, and order links
- **PDF Downloads**: Direct links to court orders and judgments
- **Query Logging**: All searches logged in SQLite database
- **Recent History**: Track recent searches with timestamps
- **Error Handling**: User-friendly error messages for invalid inputs or site issues
- **Responsive Design**: Works on desktop and mobile devices

## 🛠️ Tech Stack

- **Backend**: Python 3.8+ with Flask
- **Database**: SQLite3 (easily replaceable with PostgreSQL)
- **Web Scraping**: BeautifulSoup4 + Requests
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Styling**: Modern CSS Grid & Flexbox with gradients

## 📋 Setup Instructions

### Prerequisites

```bash
# Python 3.8 or higher
python --version

# Git (for cloning)
git --version
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/shivswrj/CourtDataFetcher.git
cd court-data-fetcher
```

2. **Create virtual environment**
```bash
python -m venv court_env
source court_env/bin/activate  # On Windows: court_env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment variables**
```bash
# Create .env file
cp .env.example .env

# Edit .env with your configurations
export SECRET_KEY="your-secret-key-here"
export COURT_BASE_URL="https://districts.ecourts.gov.in"
export DATABASE_URL="sqlite:///court_data.db"
```

5. **Initialize database**
```bash
python app.py
# Database will be automatically created on first run
```

6. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

