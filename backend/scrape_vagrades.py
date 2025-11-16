"""
Web scraper for VAGrades (https://vagrades.com/uva)
Scrapes course GPA data and integrates it with existing course dataset

Note: VAGrades is a React app, so we'll try to find API endpoints or use Selenium
for JavaScript-rendered content. This script attempts multiple approaches.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from urllib.parse import urljoin, quote

BASE_URL = "https://vagrades.com"
UVA_BASE = f"{BASE_URL}/uva"
DELAY = 2  # Delay between requests to be respectful
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
OUTPUT_FILE = os.path.join(DATA_DIR, 'vagrades_data.json')

# Try to use Selenium if available, otherwise fall back to API attempts
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available. Install with: pip install selenium")

def get_page(url):
    """Fetch a page with error handling"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_course_gpa_from_page(html):
    """Parse GPA data from a course page"""
    soup = BeautifulSoup(html, 'html.parser')
    gpa_data = {}
    
    # For React apps, data might be in JSON embedded in script tags
    # Look for JSON data in script tags
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for JSON data structures
            # Pattern: {"gpa": 3.2} or {"averageGPA": 3.2} or similar
            json_patterns = [
                r'["\']gpa["\']\s*:\s*([0-9]+\.[0-9]+)',
                r'["\']averageGPA["\']\s*:\s*([0-9]+\.[0-9]+)',
                r'["\']avgGPA["\']\s*:\s*([0-9]+\.[0-9]+)',
                r'gpa["\']?\s*[:=]\s*([0-9]+\.[0-9]+)',
            ]
            for pattern in json_patterns:
                matches = re.findall(pattern, script.string, re.IGNORECASE)
                if matches:
                    try:
                        gpa_value = float(matches[0])
                        if 0.0 <= gpa_value <= 4.0:
                            gpa_data['averageGPA'] = gpa_value
                            return gpa_data
                    except:
                        pass
    
    # Method 1: Look for GPA in text content
    gpa_pattern = r'GPA[:\s]*([0-9]+\.[0-9]+)'
    gpa_matches = re.findall(gpa_pattern, html, re.IGNORECASE)
    if gpa_matches:
        try:
            gpa_value = float(gpa_matches[0])
            if 0.0 <= gpa_value <= 4.0:
                gpa_data['averageGPA'] = gpa_value
                return gpa_data
        except:
            pass
    
    # Method 2: Look for average grade
    avg_grade_pattern = r'Average[:\s]*(Grade|GPA)[:\s]*([A-F][+-]?)'
    avg_grade_matches = re.findall(avg_grade_pattern, html, re.IGNORECASE)
    if avg_grade_matches:
        grade_letter = avg_grade_matches[0][1]
        # Convert letter grade to GPA
        grade_to_gpa = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        }
        if grade_letter.upper() in grade_to_gpa:
            gpa_data['averageGPA'] = grade_to_gpa[grade_letter.upper()]
            gpa_data['typicalGrade'] = grade_letter.upper()
            return gpa_data
    
    # Method 3: Look for data in tables or specific divs
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                text = ' '.join([cell.get_text(strip=True) for cell in cells])
                # Look for GPA patterns
                gpa_match = re.search(r'([0-9]+\.[0-9]+)', text)
                if gpa_match and 'gpa' in text.lower():
                    try:
                        gpa_value = float(gpa_match.group(1))
                        if 0.0 <= gpa_value <= 4.0:
                            gpa_data['averageGPA'] = gpa_value
                            return gpa_data
                    except:
                        pass
    
    return gpa_data

def search_course_api(course_id, department):
    """Try to find course data via API endpoints"""
    # VAGrades API patterns - check network tab for actual endpoints
    api_urls = [
        f"{BASE_URL}/api/uva/courses/{course_id}",
        f"{BASE_URL}/api/uva/{course_id}",
        f"{BASE_URL}/api/courses/{course_id}",
        f"{BASE_URL}/api/grades/{course_id}",
    ]
    
    for url in api_urls:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Extract GPA from API response
                    if isinstance(data, dict):
                        if 'gpa' in data:
                            return {'averageGPA': float(data['gpa'])}
                        if 'averageGPA' in data:
                            return {'averageGPA': float(data['averageGPA'])}
                        if 'avgGPA' in data:
                            return {'averageGPA': float(data['avgGPA'])}
                        # Check nested structures
                        if 'course' in data and isinstance(data['course'], dict):
                            course_data = data['course']
                            if 'gpa' in course_data:
                                return {'averageGPA': float(course_data['gpa'])}
                            if 'averageGPA' in course_data:
                                return {'averageGPA': float(course_data['averageGPA'])}
                except:
                    pass
        except:
            pass
    
    return None

def search_course_selenium(course_id, department):
    """Search for course using Selenium (for JavaScript-rendered content)"""
    if not SELENIUM_AVAILABLE:
        return None
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)
        
        # Correct URL pattern: https://vagrades.com/uva/{COURSE_ID}
        url = f"{UVA_BASE}/{course_id}"
        
        try:
            print(f"    Loading {url} with Selenium...")
            driver.get(url)
            time.sleep(5)  # Wait for React to render (longer wait for React apps)
            
            # Look for GPA in the rendered page
            page_text = driver.page_source
            
            # Also try to find GPA in visible text
            try:
                # Look for elements containing GPA
                gpa_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'GPA') or contains(text(), 'gpa')]")
                for elem in gpa_elements:
                    text = elem.text
                    # Extract GPA number
                    gpa_match = re.search(r'([0-9]+\.[0-9]+)', text)
                    if gpa_match:
                        gpa_value = float(gpa_match.group(1))
                        if 0.0 <= gpa_value <= 4.0:
                            driver.quit()
                            return {'averageGPA': gpa_value}
            except:
                pass
            
            # Parse from page source
            gpa_data = parse_course_gpa_from_page(page_text)
            
            if gpa_data:
                driver.quit()
                return gpa_data
        except Exception as e:
            print(f"    Selenium page load error: {e}")
        
        driver.quit()
    except Exception as e:
        print(f"  Selenium error: {e}")
    
    return None

def search_course_on_vagrades(course_id, department):
    """Search for a course on VAGrades and get its GPA data"""
    # VAGrades is a React app, so data is loaded via JavaScript
    # URL pattern: https://vagrades.com/uva/{COURSE_ID}
    
    # Try API first (fastest, but may not exist)
    api_data = search_course_api(course_id, department)
    if api_data:
        return api_data
    
    # Selenium is REQUIRED for React apps - try it
    if SELENIUM_AVAILABLE:
        print(f"    Using Selenium to load JavaScript-rendered content...")
        selenium_data = search_course_selenium(course_id, department)
        if selenium_data:
            return selenium_data
    else:
        print(f"    ⚠️  Selenium not available - cannot scrape React app without it")
        print(f"    Install with: pip install selenium")
        print(f"    Then install ChromeDriver: brew install chromedriver (macOS)")
        print(f"    Or manually add GPA data to data/course_gpa_data.json")
    
    # Fallback: try direct URL (won't work for React, but try anyway)
    url = f"{UVA_BASE}/{course_id}"
    html = get_page(url)
    if html:
        # For React apps, the HTML is minimal, but check anyway
        gpa_data = parse_course_gpa_from_page(html)
        if gpa_data:
            return gpa_data
    
    return None

def scrape_vagrades_for_courses(courses, limit=None):
    """Scrape VAGrades for GPA data for given courses"""
    vagrades_data = {}
    total = len(courses) if limit is None else min(limit, len(courses))
    
    print(f"Scraping VAGrades for {total} courses...")
    
    for i, course in enumerate(courses[:total] if limit else courses):
        course_id = course.get('id', '')
        department = course.get('department', '')
        
        if not course_id or not department:
            continue
        
        print(f"[{i+1}/{total}] Searching for {course_id} ({department})...")
        print(f"  URL: {UVA_BASE}/{course_id}")
        
        gpa_data = search_course_on_vagrades(course_id, department)
        
        if gpa_data:
            vagrades_data[course_id] = gpa_data
            print(f"  ✓ Found GPA data: {gpa_data}")
        else:
            print(f"  ✗ No GPA data found")
            if not SELENIUM_AVAILABLE:
                print(f"    Note: VAGrades is a React app - Selenium is required for scraping")
        
        time.sleep(DELAY)  # Be respectful
    
    return vagrades_data

def integrate_gpa_data(courses, vagrades_data):
    """Integrate VAGrades GPA data into course dataset"""
    updated_count = 0
    
    for course in courses:
        course_id = course.get('id', '')
        if course_id in vagrades_data:
            gpa_info = vagrades_data[course_id]
            
            # Replace typicalGrade with averageGPA if available
            if 'averageGPA' in gpa_info:
                course['averageGPA'] = gpa_info['averageGPA']
                # Keep typicalGrade for backward compatibility, but update if we have better data
                if 'typicalGrade' in gpa_info:
                    course['typicalGrade'] = gpa_info['typicalGrade']
                else:
                    # Convert GPA to letter grade if not provided
                    gpa = gpa_info['averageGPA']
                    if gpa >= 3.7:
                        course['typicalGrade'] = 'A'
                    elif gpa >= 3.3:
                        course['typicalGrade'] = 'B+'
                    elif gpa >= 3.0:
                        course['typicalGrade'] = 'B'
                    elif gpa >= 2.7:
                        course['typicalGrade'] = 'B-'
                    elif gpa >= 2.3:
                        course['typicalGrade'] = 'C+'
                    elif gpa >= 2.0:
                        course['typicalGrade'] = 'C'
                    else:
                        course['typicalGrade'] = 'C-'
                
                updated_count += 1
    
    print(f"\n✓ Updated {updated_count} courses with GPA data")
    return courses

def main():
    """Main function to scrape and integrate VAGrades data"""
    # Load existing courses
    if not os.path.exists(COURSES_FILE):
        print(f"Error: {COURSES_FILE} not found")
        return
    
    with open(COURSES_FILE, 'r') as f:
        courses = json.load(f)
    
    print(f"Loaded {len(courses)} courses from {COURSES_FILE}")
    
    # Try to load existing VAGrades data if available
    vagrades_data = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f:
            vagrades_data = json.load(f)
        print(f"Loaded {len(vagrades_data)} existing VAGrades entries")
    
    # Scrape for courses that don't have data yet
    courses_to_scrape = [c for c in courses if c.get('id') not in vagrades_data]
    
    if courses_to_scrape:
        print(f"\nScraping {len(courses_to_scrape)} new courses...")
        new_data = scrape_vagrades_for_courses(courses_to_scrape, limit=50)  # Limit for testing
        vagrades_data.update(new_data)
        
        # Save VAGrades data
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(vagrades_data, f, indent=2)
        print(f"\nSaved VAGrades data to {OUTPUT_FILE}")
    else:
        print("\nAll courses already have VAGrades data")
    
    # Integrate into courses
    print("\nIntegrating GPA data into courses...")
    updated_courses = integrate_gpa_data(courses, vagrades_data)
    
    # Save updated courses
    backup_file = COURSES_FILE.replace('.json', '_backup.json')
    if os.path.exists(COURSES_FILE):
        import shutil
        shutil.copy(COURSES_FILE, backup_file)
        print(f"Created backup: {backup_file}")
    
    with open(COURSES_FILE, 'w') as f:
        json.dump(updated_courses, f, indent=2)
    
    print(f"✓ Updated courses saved to {COURSES_FILE}")

if __name__ == '__main__':
    main()

