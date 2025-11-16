# Lou's List Scraper

This script scrapes course data from [Lou's List](https://louslist.org/), an unofficial UVA class schedule website.

## Usage

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper**:
   ```bash
   python scrape_louslist.py
   ```

3. **The scraper will**:
   - Fetch course data from multiple departments
   - Parse course information (ID, title, schedule, instructor, etc.)
   - Save results to `data/courses.json`

## Configuration

Edit `scrape_louslist.py` to customize:

- **Semester**: Change `CURRENT_SEMESTER` variable (e.g., "1262" for Spring 2026)
- **Departments**: Modify the `departments` list in the `main()` function
- **Delay**: Adjust `DELAY` between requests (default: 1 second)

## Departments Available

Popular departments you can scrape:
- `CompSci` - Computer Science
- `COMM` - Commerce
- `DataScience` - Data Science
- `Economics` - Economics
- `Mathematics` - Mathematics
- `Statistics` - Statistics
- `Philosophy` - Philosophy
- `English` - English
- `History` - History
- `Psychology` - Psychology

See [Lou's List](https://louslist.org/) for the full list of departments.

## Notes

- The scraper is respectful with a 1-second delay between requests
- Course titles are generated from course IDs (you may want to enhance this)
- Some fields like prerequisites, GenEd requirements, and career relevance need manual enhancement or additional data sources
- Instructor names are extracted but may need to be matched to professor IDs in `professors.json`

## Limitations

- Course descriptions are basic placeholders
- Prerequisites are not automatically extracted
- GenEd requirements are not automatically determined
- Course difficulty and typical grades are set to defaults

## Future Enhancements

- Scrape course catalog for full descriptions
- Parse prerequisites from course descriptions
- Match instructors to professor database
- Extract GenEd requirements
- Calculate difficulty from historical grade data

