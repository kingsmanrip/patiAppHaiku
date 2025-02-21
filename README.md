# Employee Schedule Scanner

A Streamlit application that processes employee schedule images using the Haiku Vision API to extract and analyze work schedules.

## Features

- **Image Processing**: Upload and process images of employee schedules
- **Schedule Extraction**: Automatically extracts schedule information including:
  - Employee name
  - Work days
  - Shift times
  - Work locations
- **Intelligent Analysis**:
  - Uses Haiku AI to understand complex time formats
  - Calculates total hours worked
  - Provides natural language summary of the schedule
- **Organization**:
  - Creates individual folders for each employee
  - Stores schedule data with timestamps
  - Maintains history of processed schedules
- **Data Protection**:
  - Prevents duplicate week entries
  - Validates schedule data before processing
  - Ensures data integrity per employee
- **Data Export**:
  - Saves complete schedule data as JSON
  - Organizes files by employee name
  - Includes timestamps and processing metadata

## Installation

1. Clone this repository:
```bash
git clone https://github.com/kingsmanrip/patiAppHaiku.git
cd patiAppHaiku
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to a new file named `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and replace `your-api-key-here` with your actual Haiku API key
   - Never commit the `.env` file to version control
   - Keep your API key secure and private

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Upload an image of an employee schedule using the file uploader

3. Click "Process Schedule" to analyze the image

4. The app will:
   - Check for duplicate entries of the same week
   - Display the schedule table if no duplicates found
   - Show total hours worked and schedule summary
   - Save data in employee-specific folder

## File Organization

The app creates a structured file organization:
```
schedules/
├── employee_name1/
│   ├── employee_name1_schedule_20250221_123456.json
│   └── employee_name1_schedule_20250221_234567.json
└── employee_name2/
    └── employee_name2_schedule_20250221_345678.json
```

Each JSON file contains:
- Raw schedule data
- AI analysis results
- Processing timestamp
- Total hours calculation
- Schedule summary

## Duplicate Prevention

The app includes several safeguards:
- Checks for existing schedules of the same week
- Identifies weeks by matching 5 or more weekdays
- Prevents accidental duplicate entries
- Requires administrator contact for schedule updates

## Dependencies

- streamlit==1.31.1
- requests==2.31.0
- python-dotenv==1.0.0
- pandas==2.2.0

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys private and secure
- Regularly rotate your API keys
- Use environment variables for all sensitive data
- The `.env` file is listed in `.gitignore` to prevent accidental commits

## Notes

- The application uses Haiku's AI to understand various time formats
- Files are automatically organized by employee name
- Each processed schedule creates a new JSON file with timestamp
- Employee names are sanitized for safe folder names
- Duplicate schedules for the same week are not allowed
