# Market Intelligence & Fact-Checker Module

This module extends DeepVerify Studio with advanced market intelligence capabilities, including automated scraping of corporate announcements, AI-powered analysis, and fact-checking functionality.

## 🚀 Features

### Core Capabilities
- **Automated Scraping**: BSE/NSE corporate announcements with PDF processing
- **AI Analysis**: Hugging Face models for red flag detection and sentiment analysis
- **Credibility Scoring**: Weighted algorithm combining multiple analysis factors
- **Fact-Checker**: Verify user content against official announcements
- **Historical Anomaly Detection**: Compare claims against company financial data
- **Real-time Dashboard**: Monitor announcements and analysis results

### Technical Features
- **Database Integration**: Supabase PostgreSQL with optimized schemas
- **File Storage**: Supabase Storage for PDF documents
- **Background Processing**: Async analysis with progress tracking
- **API Endpoints**: RESTful API for all intelligence operations
- **Modern UI**: React/Next.js interface with real-time updates

## 🏗️ Architecture

```
Market Intelligence Module/
├── Backend/
│   ├── models/
│   │   ├── announcement.py          # Announcement data model
│   │   └── company_financial.py     # Company financial data model
│   ├── api/routes/
│   │   └── intelligence.py          # API endpoints
│   ├── services/
│   │   ├── intelligence_analysis.py # AI analysis engine
│   │   ├── intelligence_scraper.py  # Web scraping service
│   │   └── intelligence_fact_checker.py # Fact-checking service
│   └── scripts/
│       └── setup_cron.py            # Cron job setup
├── Frontend/
│   ├── pages/
│   │   ├── intelligence.tsx         # Main intelligence page
│   │   └── forensics.tsx            # Updated forensics page
│   └── lib/
│       └── api.ts                   # API client functions
└── Database/
    ├── announcements table          # Scraped announcements
    └── company_financials table     # Historical financial data
```

## 📊 Database Schema

### Announcements Table
```sql
CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_symbol TEXT NOT NULL,
    title TEXT NOT NULL,
    announcement_date TIMESTAMP NOT NULL,
    pdf_url TEXT UNIQUE NOT NULL,
    storage_path TEXT,
    full_text TEXT,
    status TEXT DEFAULT 'pending',
    credibility_score FLOAT,
    analysis_summary JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Company Financials Table
```sql
CREATE TABLE company_financials (
    id SERIAL PRIMARY KEY,
    company_symbol TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    last_quarter_revenue_cr FLOAT,
    last_quarter_profit_cr FLOAT,
    market_cap_cr FLOAT,
    pe_ratio FLOAT,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔧 Installation & Setup

### 1. Backend Setup

```bash
# Install additional dependencies
cd backend
pip install -r requirements.txt

# The new dependencies include:
# - transformers==4.35.2 (Hugging Face models)
# - beautifulsoup4==4.12.2 (Web scraping)
# - requests==2.31.0 (HTTP requests)
# - pandas==2.1.3 (Data processing)
# - lxml==4.9.3 (XML/HTML parsing)
```

### 2. Database Setup

The new tables will be automatically created when you start the backend server. The models are imported in `core/database.py`.

### 3. Environment Variables

Add these to your `.env` file:

```env
# Market Intelligence Settings
SCRAPER_SECRET_KEY=your-secret-scraper-key
HUGGING_FACE_CACHE_DIR=./models
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🚀 Usage

### 1. Accessing Market Intelligence

Navigate to `http://localhost:3000/intelligence` to access the Market Intelligence dashboard.

### 2. Viewing Announcements

The dashboard shows:
- **Statistics**: Total announcements, analyzed count, average credibility
- **Announcement List**: Recent announcements with credibility scores
- **Status Indicators**: Color-coded credibility and analysis status

### 3. Fact-Checker

Use the Fact-Checker tab to:
- **Paste Text**: Verify any text content against official announcements
- **Upload Files**: Upload PDFs or text files for verification
- **Get Results**: Receive verification status, confidence scores, and evidence

### 4. Automated Scraping

Set up automated scraping using the provided cron job setup:

```bash
cd backend/scripts
python setup_cron.py
```

## 📡 API Endpoints

### Announcements
- `GET /api/intelligence/announcements` - List announcements
- `GET /api/intelligence/announcements/{id}` - Get announcement details
- `POST /api/intelligence/analyze/{id}` - Trigger analysis

### Fact-Checker
- `POST /api/intelligence/fact-check` - Verify content

### Scraper
- `POST /api/intelligence/run-scraper` - Trigger scraping (cron job)

### Statistics
- `GET /api/intelligence/stats` - Get module statistics
- `GET /api/intelligence/companies` - List companies

## 🤖 AI Analysis Engine

### Red Flag Detection
Uses Hugging Face's zero-shot classification to detect:
- Promotional hype
- Unrealistic projections
- Vague language
- Conflicting information
- Suspicious timing

### Sentiment Analysis
Analyzes announcement sentiment using:
- Cardiff NLP's Twitter RoBERTa model
- Confidence scoring
- Risk assessment

### Historical Anomaly Detection
- Extracts numerical claims from announcements
- Compares against historical financial data
- Identifies significant deviations (>50% threshold)

### Credibility Scoring Algorithm
```python
base_score = 10.0
base_score -= len(red_flags) * 1.5  # Red flag penalty
base_score -= sentiment_penalty     # Sentiment penalty
base_score -= anomaly_penalty       # Anomaly penalty
final_score = max(0.0, min(10.0, base_score))
```

## 🔍 Fact-Checker Process

### 1. Content Analysis
- Extract company names, financial figures, and dates
- Use regex patterns for claim identification
- Map company names to stock symbols

### 2. Database Search
- Search for matching announcements by company
- Calculate similarity scores
- Rank results by relevance

### 3. Verification Results
- **Verified Authentic**: High confidence match (>70%)
- **Partially Verified**: Medium confidence (40-70%)
- **Potentially Misleading**: Low confidence (<40%)
- **Unverified**: No matches found

## 📈 Monitoring & Maintenance

### Logs
- Backend logs: `backend/logs/app.log`
- Scraper logs: `/var/log/market-intelligence-scraper.log`

### Health Checks
- API health: `GET /health`
- Database connectivity: Automatic on startup
- Model loading: Check startup logs

### Performance Metrics
- Scraping success rate
- Analysis completion time
- API response times
- Database query performance

## 🔒 Security Considerations

### API Security
- Secret key authentication for scraper endpoint
- Rate limiting on fact-checker endpoint
- Input validation and sanitization

### Data Privacy
- Secure PDF storage in Supabase
- Encrypted database connections
- No sensitive data in logs

### Model Security
- Local model caching
- Fallback to rule-based analysis
- Error handling for model failures

## 🚧 Development & Customization

### Adding New Analysis Types
1. Extend `IntelligenceAnalysisService`
2. Add new analysis methods
3. Update credibility scoring algorithm
4. Add frontend display components

### Custom Scrapers
1. Extend `IntelligenceScraperService`
2. Add new scraping methods
3. Update data extraction logic
4. Test with target websites

### UI Customization
1. Modify `intelligence.tsx` for layout changes
2. Update API client in `api.ts`
3. Add new components as needed
4. Customize styling and themes

## 📚 Dependencies

### Backend
- `transformers`: Hugging Face model integration
- `beautifulsoup4`: Web scraping
- `requests`: HTTP client
- `pandas`: Data processing
- `lxml`: XML/HTML parsing
- `PyPDF2`: PDF text extraction

### Frontend
- `@heroicons/react`: Icons
- `framer-motion`: Animations
- `axios`: HTTP client
- `next`: React framework

## 🐛 Troubleshooting

### Common Issues

1. **Models not loading**
   - Check internet connection for initial download
   - Verify disk space for model caching
   - Check Hugging Face API limits

2. **Scraping failures**
   - Verify website structure hasn't changed
   - Check network connectivity
   - Review rate limiting

3. **Database errors**
   - Verify Supabase connection
   - Check table permissions
   - Review migration status

4. **Frontend issues**
   - Check API endpoint URLs
   - Verify CORS configuration
   - Review browser console errors

### Debug Mode
Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

## 🚀 Deployment

### Production Considerations
1. **Environment Variables**: Set all required secrets
2. **Database**: Use production Supabase instance
3. **Storage**: Configure production storage bucket
4. **Monitoring**: Set up logging and alerting
5. **Scaling**: Consider load balancing for high traffic

### Docker Deployment
```yaml
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - SCRAPER_SECRET_KEY=${SCRAPER_SECRET_KEY}
  
  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
```

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Test individual components
4. Create detailed issue reports

## 🎯 Future Enhancements

### Planned Features
- **Real-time Notifications**: Alert on high-risk announcements
- **Advanced Analytics**: Trend analysis and reporting
- **API Rate Limiting**: Protect against abuse
- **Multi-language Support**: International announcements
- **Mobile App**: Native mobile interface
- **Integration APIs**: Third-party platform integration

### Performance Optimizations
- **Caching**: Redis for frequently accessed data
- **CDN**: Static asset delivery
- **Database Indexing**: Optimized query performance
- **Background Jobs**: Queue-based processing
- **Load Balancing**: Horizontal scaling

---

**Market Intelligence Module** - Advanced corporate announcement analysis and fact-checking for the digital age.
