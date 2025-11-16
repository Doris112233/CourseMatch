# VAGrades Integration Guide

This guide explains how to integrate GPA data from [VAGrades](https://vagrades.com/uva) into the CourseMatch system.

## Overview

VAGrades provides historical grade data for UVA courses. This integration allows CourseMatch to:
- Replace `typicalGrade` with actual `averageGPA` data
- Provide more accurate course difficulty insights
- Help students make informed course selections

## Files

1. **`scrape_vagrades.py`** - Scraper for VAGrades (requires Selenium for JavaScript-rendered content)
2. **`update_courses_with_gpa.py`** - Utility to integrate GPA data into courses
3. **`data/course_gpa_data.json`** - Storage for GPA data (created automatically)

## Setup

### Option 1: Manual Data Entry (Recommended for MVP)

1. Visit [VAGrades](https://vagrades.com/uva) and search for courses
2. Manually collect GPA data for your courses
3. Create/edit `data/course_gpa_data.json`:

```json
{
  "CS3102": {"averageGPA": 3.2},
  "COMM3020": {"averageGPA": 3.5},
  "ARTS2000": {"averageGPA": 3.7},
  "MATH1310": {"averageGPA": 2.8}
}
```

4. Run the update script:
```bash
python update_courses_with_gpa.py
```

### Option 2: Automated Scraping (Advanced)

**Note:** VAGrades is a React app, so scraping requires Selenium.

1. Install Selenium:
```bash
pip install selenium
```

2. Install ChromeDriver (required for Selenium):
   - macOS: `brew install chromedriver`
   - Linux: Download from https://chromedriver.chromium.org/
   - Windows: Download and add to PATH

3. Run the scraper:
```bash
python scrape_vagrades.py
```

**Limitations:**
- VAGrades may have rate limiting
- JavaScript rendering is slow
- Terms of service should be reviewed
- May require authentication for some data

## Data Format

### Input Format (`course_gpa_data.json`)

```json
{
  "COURSE_ID": {
    "averageGPA": 3.5
  },
  "CS3102": {
    "averageGPA": 3.2,
    "typicalGrade": "B+"
  }
}
```

Or simplified format:
```json
{
  "CS3102": 3.2,
  "COMM3020": 3.5
}
```

### Course Update

The script updates courses with:
- `averageGPA`: Numeric GPA (0.0-4.0)
- `typicalGrade`: Letter grade derived from GPA

## Usage

### Update Courses with GPA Data

```bash
cd backend
python update_courses_with_gpa.py
```

This will:
1. Load existing courses from `data/courses.json`
2. Load GPA data from `data/course_gpa_data.json`
3. Match courses by ID
4. Update courses with GPA information
5. Create a backup of original courses
6. Save updated courses

### Scrape VAGrades (if Selenium available)

```bash
cd backend
python scrape_vagrades.py
```

This will:
1. Attempt to scrape GPA data from VAGrades
2. Save data to `data/vagrades_data.json`
3. Integrate into courses automatically

## Course Matching

After updating courses with GPA data, the matching algorithm will:
- Use `averageGPA` for more accurate difficulty assessment
- Consider GPA when matching student preferences
- Display GPA information in course recommendations

## Example

Before:
```json
{
  "id": "CS3102",
  "typicalGrade": "B",
  "difficulty": 3
}
```

After:
```json
{
  "id": "CS3102",
  "averageGPA": 3.2,
  "typicalGrade": "B",
  "difficulty": 3
}
```

## Notes

- **Data Privacy**: VAGrades data is aggregated and public
- **Terms of Service**: Review VAGrades ToS before scraping
- **Rate Limiting**: Be respectful with request delays
- **Backup**: Always creates backup before updating
- **Matching**: Course IDs must match exactly or use department + number format

## Troubleshooting

**No GPA data found:**
- Check that `course_gpa_data.json` exists and has data
- Verify course IDs match exactly

**Selenium errors:**
- Ensure ChromeDriver is installed and in PATH
- Check Chrome browser version matches ChromeDriver

**API not working:**
- VAGrades is a React app, direct API may not be available
- Use Selenium for JavaScript-rendered content

## Future Enhancements

- Direct API integration if VAGrades provides one
- Batch processing for large datasets
- Automatic updates on schedule
- Integration with other grade data sources

