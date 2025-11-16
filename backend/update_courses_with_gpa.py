"""
Utility to update courses with GPA data from VAGrades
This script can work with:
1. Manual GPA data file (JSON)
2. Scraped data from VAGrades (if available)
3. Direct integration with course matching
"""

import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
GPA_DATA_FILE = os.path.join(DATA_DIR, 'course_gpa_data.json')

def load_gpa_data():
    """Load GPA data from file"""
    if os.path.exists(GPA_DATA_FILE):
        with open(GPA_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_gpa_data(gpa_data):
    """Save GPA data to file"""
    with open(GPA_DATA_FILE, 'w') as f:
        json.dump(gpa_data, f, indent=2)

def gpa_to_letter_grade(gpa):
    """Convert GPA to letter grade"""
    if gpa >= 3.7:
        return 'A'
    elif gpa >= 3.3:
        return 'B+'
    elif gpa >= 3.0:
        return 'B'
    elif gpa >= 2.7:
        return 'B-'
    elif gpa >= 2.3:
        return 'C+'
    elif gpa >= 2.0:
        return 'C'
    elif gpa >= 1.7:
        return 'C-'
    elif gpa >= 1.3:
        return 'D+'
    elif gpa >= 1.0:
        return 'D'
    elif gpa >= 0.7:
        return 'D-'
    else:
        return 'F'

def update_courses_with_gpa(courses, gpa_data):
    """Update courses with GPA data"""
    updated_count = 0
    
    for course in courses:
        course_id = course.get('id', '')
        
        # Try exact match first
        if course_id in gpa_data:
            gpa_info = gpa_data[course_id]
        else:
            # Try department + number format (e.g., "CS3102" -> "CS 3102")
            dept = course.get('department', '')
            course_num = course_id.replace(dept, '') if dept else course_id
            alt_id = f"{dept} {course_num}".strip()
            if alt_id in gpa_data:
                gpa_info = gpa_data[alt_id]
            else:
                continue
        
        # Update course with GPA data
        if isinstance(gpa_info, dict):
            if 'averageGPA' in gpa_info:
                course['averageGPA'] = float(gpa_info['averageGPA'])
                # Update typicalGrade based on GPA
                course['typicalGrade'] = gpa_to_letter_grade(course['averageGPA'])
                updated_count += 1
            elif 'gpa' in gpa_info:
                course['averageGPA'] = float(gpa_info['gpa'])
                course['typicalGrade'] = gpa_to_letter_grade(course['averageGPA'])
                updated_count += 1
        elif isinstance(gpa_info, (int, float)):
            # Direct GPA value
            course['averageGPA'] = float(gpa_info)
            course['typicalGrade'] = gpa_to_letter_grade(course['averageGPA'])
            updated_count += 1
    
    return updated_count

def main():
    """Main function"""
    # Load courses
    if not os.path.exists(COURSES_FILE):
        print(f"Error: {COURSES_FILE} not found")
        return
    
    with open(COURSES_FILE, 'r') as f:
        courses = json.load(f)
    
    print(f"Loaded {len(courses)} courses")
    
    # Load GPA data
    gpa_data = load_gpa_data()
    
    if not gpa_data:
        print(f"\nNo GPA data found in {GPA_DATA_FILE}")
        print("Creating template file...")
        
        # Create template with sample entries
        template = {
            "CS3102": {"averageGPA": 3.2},
            "COMM3020": {"averageGPA": 3.5},
            "ARTS 2000": {"averageGPA": 3.7},
            # Add more entries here or run scrape_vagrades.py
        }
        
        save_gpa_data(template)
        print(f"Template created at {GPA_DATA_FILE}")
        print("Please add GPA data to this file, or run scrape_vagrades.py")
        return
    
    print(f"Loaded {len(gpa_data)} GPA entries")
    
    # Create backup
    backup_file = COURSES_FILE.replace('.json', '_backup.json')
    import shutil
    if os.path.exists(COURSES_FILE):
        shutil.copy(COURSES_FILE, backup_file)
        print(f"Created backup: {backup_file}")
    
    # Update courses
    updated_count = update_courses_with_gpa(courses, gpa_data)
    
    # Save updated courses
    with open(COURSES_FILE, 'w') as f:
        json.dump(courses, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} courses with GPA data")
    print(f"✓ Saved to {COURSES_FILE}")

if __name__ == '__main__':
    main()

