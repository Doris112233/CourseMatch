"""
Web scraper for Lou's List (https://louslist.org/)
Scrapes course data from UVA's unofficial class schedule website
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import os

BASE_URL = "https://louslist.org/"
CURRENT_SEMESTER = "1262"  # Spring 2026 - update as needed
OUTPUT_FILE = "data/courses.json"
DELAY = 1  # Delay between requests to be respectful

def get_page(url):
    """Fetch a page with error handling"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_course_title_row(row):
    """Parse a course title row (2 cells: course code and title)"""
    cells = row.find_all(['td', 'th'])
    if len(cells) != 2:
        return None
    
    try:
        course_code_text = cells[0].get_text(strip=True)
        course_title = cells[1].get_text(strip=True)
        
        # Extract course ID (e.g., "CS 1110" -> "CS1110")
        # Pattern: Department code (2-4 letters) + space + 4 digits
        match = re.match(r'([A-Z]{2,})\s+(\d{4})', course_code_text)
        if not match:
            return None
        
        department = match.group(1)
        number = match.group(2)
        course_id = f"{department}{number}"
        
        return {
            "id": course_id,
            "title": course_title,
            "department": department
        }
    except Exception as e:
        return None

def parse_section_row(row, current_course):
    """Parse a section row (8 cells with section details)"""
    cells = row.find_all(['td', 'th'])
    if len(cells) != 8:
        return None
    
    try:
        text_content = ' '.join([cell.get_text(strip=True) for cell in cells])
        
        # Cell structure appears to be:
        # 0: Section number (e.g., "16135001")
        # 1: Type (e.g., "Lecture")
        # 2: Units (e.g., "(3 Units)")
        # 3: Status (e.g., "Open", "Wait List")
        # 4: Enrollment (e.g., "107 / 200")
        # 5: Instructor name
        # 6: Days and time (e.g., "MoWeFr 12:00pm - 12:50pm")
        # 7: Location (might be empty or in previous cells)
        
        section_text = cells[0].get_text(strip=True)
        type_text = cells[1].get_text(strip=True)
        units_text = cells[2].get_text(strip=True)
        instructor_text = cells[5].get_text(strip=True) if len(cells) > 5 else "TBA"
        time_text = cells[6].get_text(strip=True) if len(cells) > 6 else ""
        
        # Extract section number (last few digits)
        section = section_text[-3:] if len(section_text) >= 3 else section_text
        
        # Extract credits from units text (e.g., "(3 Units)" -> 3)
        units_match = re.search(r'\((\d+)\s*Units?\)', units_text)
        credits = int(units_match.group(1)) if units_match else 3
        
        # Parse schedule
        schedule = []
        if time_text:
            # Format: "MoWeFr 12:00pm - 12:50pm" or "TTh 2:00pm - 3:15pm"
            # Convert to standard format: "MWF 12:00-12:50"
            time_clean = time_text.replace('pm', '').replace('am', '').strip()
            
            days = ""
            time_part = ""
            
            # Extract days and time
            day_match = re.match(r'([A-Za-z]+)\s+(.+)', time_clean)
            if day_match:
                day_str = day_match.group(1)
                time_part = day_match.group(2)
                
                # Handle special combined cases first
                if 'TTh' in day_str or 'TTH' in day_str:
                    days = 'TR'
                else:
                    # Parse individual days
                    if 'Mo' in day_str:
                        days += 'M'
                    if 'We' in day_str:
                        days += 'W'
                    if 'Fr' in day_str:
                        days += 'F'
                    if 'Th' in day_str:
                        days += 'R'
                    if 'Tu' in day_str:
                        days += 'T'
                    if 'Sa' in day_str:
                        days += 'S'
                    if 'Su' in day_str:
                        days += 'U'
            
            if days and time_part:
                # Clean up time format
                time_part = time_part.replace(' - ', '-').strip()
                schedule.append({
                    "time": f"{days} {time_part}",
                    "location": "TBA"  # Location not always in a separate cell
                })
        
        # Determine course type
        course_type = "Lecture"
        type_upper = type_text.upper()
        if "LAB" in type_upper or "Laboratory" in type_upper:
            course_type = "Laboratory"
        elif "DISC" in type_upper or "Discussion" in type_upper:
            course_type = "Discussion"
        elif "SEM" in type_upper or "Seminar" in type_upper:
            course_type = "Seminar"
        
        return {
            "section": section,
            "type": course_type,
            "credits": credits,
            "schedule": schedule,
            "instructor_name": instructor_text if instructor_text else "TBA"
        }
    except Exception as e:
        print(f"Error parsing section row: {e}")
        return None

def get_course_details(course_id, department_page_url):
    """Try to get additional course details from the department page"""
    # This would require parsing the full department page
    # For now, we'll use basic information
    return {}

def scrape_department(department_code, semester=CURRENT_SEMESTER):
    """Scrape all courses from a specific department"""
    url = f"{BASE_URL}page.php?Semester={semester}&Type=Group&Group={department_code}"
    print(f"Scraping {department_code} from {url}")
    
    html = get_page(url)
    if not html:
        print(f"  Failed to fetch page for {department_code}")
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    courses = []
    
    # Find the course table (usually the second table)
    tables = soup.find_all('table')
    
    if len(tables) < 2:
        print(f"  No course table found for {department_code}")
        return []
    
    # Use the second table (first is navigation)
    course_table = tables[1]
    rows = course_table.find_all('tr')
    
    # Skip first 2 rows (header/navigation)
    current_course = None
    i = 2
    
    while i < len(rows):
        row = rows[i]
        cells = row.find_all(['td', 'th'])
        
        # Check if this is a course title row (2 cells)
        if len(cells) == 2:
            course_info = parse_course_title_row(row)
            if course_info:
                current_course = course_info
                i += 1
                continue
        
        # Check if this is a section row (8 cells) and we have a current course
        if len(cells) == 8 and current_course:
            section_info = parse_section_row(row, current_course)
            if section_info:
                # Create course entry with section info
                course_entry = {
                    "id": current_course["id"],
                    "title": current_course["title"],
                    "department": current_course["department"],
                    "section": section_info["section"],
                    "type": section_info["type"],
                    "credits": section_info["credits"],
                    "schedule": section_info["schedule"],
                    "instructor_name": section_info["instructor_name"]
                }
                courses.append(course_entry)
        
        i += 1
    
    print(f"  Found {len(courses)} course sections in {department_code}")
    time.sleep(DELAY)  # Be respectful
    return courses

def get_course_title_from_id(course_id, department):
    """Generate a reasonable course title from course ID"""
    # Extract number from course ID
    number = course_id.replace(department, "")
    
    # Common course title patterns (you can expand this)
    title_map = {
        "1010": "Introduction to",
        "2010": "Intermediate",
        "2110": "Fundamentals of",
        "3000": "Advanced",
        "4000": "Senior Seminar in"
    }
    
    prefix = ""
    for key, value in sorted(title_map.items(), key=lambda x: int(x[0]), reverse=True):
        if number.startswith(key[:2]):
            prefix = value
            break
    
    return f"{prefix} {department}" if prefix else f"{department} {number}"

def scrape_multiple_departments(department_codes, semester=CURRENT_SEMESTER):
    """Scrape courses from multiple departments"""
    all_courses = []
    seen_courses = {}  # Track unique courses by ID
    
    for dept_code in department_codes:
        courses = scrape_department(dept_code, semester)
        for course in courses:
            course_id = course['id']
            
            # Merge sections if course already exists
            if course_id in seen_courses:
                existing = seen_courses[course_id]
                # Add schedule if different and not duplicate
                if course.get('schedule'):
                    for new_schedule in course['schedule']:
                        # Check if this schedule already exists
                        schedule_exists = any(
                            s.get('time') == new_schedule.get('time') 
                            for s in existing['schedule']
                        )
                        if not schedule_exists:
                            existing['schedule'].append(new_schedule)
            else:
                # Create full course entry matching the expected format
                full_course = {
                    "id": course_id,
                    "title": course.get('title', get_course_title_from_id(course_id, course['department'])),
                    "department": course['department'],
                    "credits": course.get('credits', 3),
                    "prerequisites": [],  # Would need to parse from catalog
                    "keywords": [course['department'].lower(), course.get('type', 'lecture').lower()],
                    "description": f"{course.get('type', 'Course')} course in {course['department']}. Course number {course_id}.",
                    "typicalGrade": "B",  # Default - would need historical data
                    "difficulty": 3,  # Default - would need to calculate
                    "schedule": course.get('schedule', []),
                    "instructor": course.get('instructor_name', 'TBA'),
                    "gened": [],  # Would need to parse from catalog
                    "careerRelevance": []  # Would need to infer or parse
                }
                seen_courses[course_id] = full_course
                all_courses.append(full_course)
    
    return list(seen_courses.values())

def get_course_title_from_catalog(course_id, department):
    """Try to get course title from catalog - placeholder for now"""
    # This would require scraping the course catalog
    return f"{department} Course {course_id}"

def main():
    """Main scraping function"""
    print("Starting Lou's List scraper...")
    print(f"Target semester: {CURRENT_SEMESTER}")
    
    # Popular departments to scrape
    # You can expand this list based on your needs
    departments = [

        "Anthropology",
        "Art",
        "EnviSci",
        "CompSci",      # Computer Science
        "COMM",         # Commerce
        "DataScience", # Data Science
        "Economics",    # Economics
        "Mathematics", # Mathematics
        "Statistics",  # Statistics
        "Philosophy", # Philosophy
        "English",      # English
        "History",     # History
        "Psychology"   # Psychology
    ]
    
    print(f"Scraping {len(departments)} departments...")
    courses = scrape_multiple_departments(departments)
    
    print(f"\nScraped {len(courses)} unique courses")
    
    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
    with open(output_path, 'w') as f:
        json.dump(courses, f, indent=2)
    
    print(f"Saved courses to {output_path}")
    print(f"Total courses: {len(courses)}")

if __name__ == "__main__":
    main()

