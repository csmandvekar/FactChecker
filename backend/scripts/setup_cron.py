#!/usr/bin/env python3
"""
Setup script for Market Intelligence scraper cron job
This script helps configure automated scraping of BSE/NSE announcements
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

def test_scraper_endpoint():
    """Test the scraper endpoint to ensure it's working"""
    try:
        # This would be your actual API endpoint
        api_url = "http://localhost:8000/api/intelligence/run-scraper"
        secret_key = "your-secret-scraper-key"  # Should be in environment variables
        
        response = requests.post(api_url, data={"secret_key": secret_key})
        
        if response.status_code == 200:
            print("✅ Scraper endpoint is working correctly")
            return True
        else:
            print(f"❌ Scraper endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing scraper endpoint: {e}")
        return False

def generate_cron_script():
    """Generate a shell script for cron job setup"""
    script_content = """#!/bin/bash
# Market Intelligence Scraper Cron Job
# This script runs the scraper every 4 hours

# Set environment variables
export DATABASE_URL="${DATABASE_URL}"
export SUPABASE_URL="${SUPABASE_URL}"
export SUPABASE_KEY="${SUPABASE_KEY}"

# API endpoint and secret
API_URL="http://localhost:8000/api/intelligence/run-scraper"
SECRET_KEY="your-secret-scraper-key"

# Make the request
curl -X POST "$API_URL" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "secret_key=$SECRET_KEY" \\
  --max-time 300 \\
  --retry 3

# Log the result
echo "$(date): Scraper job completed" >> /var/log/market-intelligence-scraper.log
"""
    
    script_path = os.path.join(os.path.dirname(__file__), "run_scraper.sh")
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    print(f"✅ Generated cron script at: {script_path}")
    return script_path

def generate_cron_job_instructions():
    """Generate instructions for setting up the cron job"""
    instructions = """
# Market Intelligence Scraper - Cron Job Setup Instructions

## Option 1: Using Cron-Job.org (Recommended for testing)

1. Go to https://cron-job.org/
2. Create a free account
3. Create a new cron job with these settings:
   - URL: http://your-domain.com/api/intelligence/run-scraper
   - Method: POST
   - Body: secret_key=your-secret-scraper-key
   - Schedule: Every 4 hours (0 */4 * * *)
   - Timeout: 300 seconds

## Option 2: Using system cron (For production)

1. Edit your crontab:
   ```bash
   crontab -e
   ```

2. Add this line to run every 4 hours:
   ```bash
   0 */4 * * * /path/to/your/backend/scripts/run_scraper.sh
   ```

3. Make sure the script is executable:
   ```bash
   chmod +x /path/to/your/backend/scripts/run_scraper.sh
   ```

## Option 3: Using Docker (For containerized deployment)

Add this to your docker-compose.yml:
```yaml
services:
  scraper-cron:
    image: your-backend-image
    command: >
      sh -c "
        while true; do
          curl -X POST http://backend:8000/api/intelligence/run-scraper \\
            -H 'Content-Type: application/x-www-form-urlencoded' \\
            -d 'secret_key=your-secret-scraper-key' \\
            --max-time 300;
          sleep 14400;  # 4 hours
        done
      "
    depends_on:
      - backend
    restart: unless-stopped
```

## Security Notes

1. Change the default secret key in production
2. Use environment variables for sensitive data
3. Consider using API authentication instead of secret keys
4. Monitor the scraper logs for errors
5. Set up alerts for failed scraping attempts

## Monitoring

Check the scraper logs:
```bash
tail -f /var/log/market-intelligence-scraper.log
```

Or check the database for new announcements:
```sql
SELECT COUNT(*) FROM announcements WHERE created_at > NOW() - INTERVAL '1 day';
```
"""
    
    instructions_path = os.path.join(os.path.dirname(__file__), "CRON_SETUP_INSTRUCTIONS.md")
    
    with open(instructions_path, 'w') as f:
        f.write(instructions)
    
    print(f"✅ Generated setup instructions at: {instructions_path}")

def main():
    """Main setup function"""
    print("🚀 Market Intelligence Scraper Setup")
    print("=" * 50)
    
    # Test the scraper endpoint
    print("\n1. Testing scraper endpoint...")
    if not test_scraper_endpoint():
        print("⚠️  Scraper endpoint test failed. Make sure your backend is running.")
        return
    
    # Generate cron script
    print("\n2. Generating cron script...")
    script_path = generate_cron_script()
    
    # Generate instructions
    print("\n3. Generating setup instructions...")
    generate_cron_job_instructions()
    
    print("\n✅ Setup complete!")
    print(f"📁 Script location: {script_path}")
    print("📖 Check CRON_SETUP_INSTRUCTIONS.md for detailed setup instructions")
    
    print("\n🔧 Next steps:")
    print("1. Update the secret key in your environment variables")
    print("2. Choose a cron job setup method from the instructions")
    print("3. Test the automated scraping")
    print("4. Monitor the logs for any issues")

if __name__ == "__main__":
    main()
