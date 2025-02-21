import streamlit as st
import requests
import json
import base64
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import glob

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(page_title="Employee Schedule Scanner", page_icon="📅", layout="wide")

# API Configuration
API_KEY = os.getenv('HAIKU_API_KEY')
if not API_KEY:
    st.error("❌ API key not found in .env file")
    st.stop()

API_URL = 'https://api.anthropic.com/v1/messages'

def extract_schedule_data(image_bytes):
    """First step: Extract raw schedule data from image"""
    headers = {
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
        'x-api-key': API_KEY
    }
    
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please analyze this employee schedule image and return a JSON object with the following structure:
{
    "employee_name": "string",
    "schedule": [
        {
            "day": "string",
            "location": "string",
            "hours": "string"
        }
    ]
}
Extract the exact times as shown in the image without modifying the format."""
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded_image
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        
        response_data = response.json()
        if 'content' not in response_data or not response_data['content']:
            st.error("❌ No content in API response")
            return None
            
        content = response_data['content'][0]['text']
        # Find the JSON object in the response
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                st.error("❌ Could not find JSON in response")
                return None
        except Exception as e:
            st.error(f"❌ Error parsing JSON: {str(e)}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API request failed: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

def analyze_schedule(schedule_data):
    """Second step: Use Haiku to analyze the schedule and provide a summary"""
    headers = {
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
        'x-api-key': API_KEY
    }
    
    schedule_json = json.dumps(schedule_data, indent=2)
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Given this schedule data:
{schedule_json}

Please analyze the schedule and provide:
1. Calculate the total hours worked for the week
2. Write a brief summary of the schedule

Return your response as a JSON object with this structure:
{{
    "total_hours": number,
    "summary": "string describing the schedule"
}}"""
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        response_data = response.json()
        if 'content' not in response_data or not response_data['content']:
            st.error("❌ No content in API response")
            return None
            
        content = response_data['content'][0]['text']
        # Find the JSON object in the response
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                st.error("❌ Could not find JSON in response")
                return None
        except Exception as e:
            st.error(f"❌ Error parsing JSON: {str(e)}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API request failed: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

def create_schedule_table(data):
    """Create a pandas DataFrame from the schedule data"""
    if not data or 'schedule' not in data:
        return None
    
    try:
        df = pd.DataFrame(data['schedule'])
        return df
    except Exception as e:
        st.error(f"❌ Error creating table: {str(e)}")
        return None

def get_week_dates(schedule_data):
    """Extract the dates from the schedule to identify the week"""
    if not schedule_data or 'schedule' not in schedule_data:
        return None
    
    days = [entry['day'].lower() for entry in schedule_data['schedule']]
    # Check if we have a full week of data
    weekdays = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
    schedule_days = {day.lower() for day in days}
    
    # If we have at least 5 matching weekdays, consider it the same week
    matching_days = schedule_days.intersection(weekdays)
    if len(matching_days) >= 5:
        return sorted(list(matching_days))
    return None

def check_existing_schedule(employee_name, week_dates):
    """Check if a schedule for this week already exists"""
    if not employee_name or not week_dates:
        return False
        
    # Create safe folder name
    folder_name = "".join(c if c.isalnum() else "_" for c in employee_name.lower())
    folder_path = os.path.join(os.getcwd(), "schedules", folder_name)
    
    # If folder doesn't exist, no duplicates
    if not os.path.exists(folder_path):
        return False
    
    # Check all JSON files in the folder
    for file_path in glob.glob(os.path.join(folder_path, "*.json")):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'raw_schedule' in data:
                    existing_dates = get_week_dates(data['raw_schedule'])
                    if existing_dates and set(existing_dates) == set(week_dates):
                        return True
        except Exception:
            continue
    
    return False

def save_to_json(raw_data, analysis):
    """Save both raw data and analysis to JSON file in user-specific folder"""
    if not raw_data or not analysis:
        return None
    
    try:
        # Get employee name from the data
        employee_name = raw_data.get('employee_name', '').strip()
        if not employee_name:
            st.error("❌ Employee name not found in schedule data")
            return None
            
        # Create a safe folder name (replace spaces and special characters)
        folder_name = "".join(c if c.isalnum() else "_" for c in employee_name.lower())
        folder_path = os.path.join(os.getcwd(), "schedules", folder_name)
        
        # Create folders if they don't exist
        os.makedirs(folder_path, exist_ok=True)
        
        # Generate filename with employee name and date
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{folder_name}_schedule_{timestamp}.json"
        file_path = os.path.join(folder_path, filename)
        
        output_data = {
            "raw_schedule": raw_data,
            "analysis": analysis,
            "processed_at": timestamp
        }
        
        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        # Return relative path for display
        return os.path.relpath(file_path, os.getcwd())
    except Exception as e:
        st.error(f"❌ Error saving data: {str(e)}")
        return None

# Streamlit UI
st.title("📅 Employee Schedule Scanner")
st.write("Upload an image of an employee schedule to extract and process the information.")

uploaded_file = st.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    st.success("✅ Image uploaded successfully!")
    
    # Process button
    if st.button("Process Schedule"):
        with st.spinner("Processing image..."):
            # Step 1: Extract schedule data
            image_bytes = uploaded_file.getvalue()
            schedule_data = extract_schedule_data(image_bytes)
            
            if schedule_data:
                # Check for employee name
                employee_name = schedule_data.get('employee_name', '').strip()
                if not employee_name:
                    st.error("❌ Could not find employee name in schedule")
                    st.stop()
                
                # Check for duplicate week
                week_dates = get_week_dates(schedule_data)
                if week_dates and check_existing_schedule(employee_name, week_dates):
                    st.error("❌ A schedule for this week has already been processed!")
                    st.warning("If you need to update this week's schedule, please contact your administrator.")
                    st.stop()
                
                # Create and display table
                df = create_schedule_table(schedule_data)
                if df is not None:
                    st.subheader("Schedule Table")
                    st.table(df)
                    
                    # Step 2: Analyze schedule
                    with st.spinner("Analyzing schedule..."):
                        analysis = analyze_schedule(schedule_data)
                        if analysis:
                            st.markdown("---")
                            # Display total hours
                            st.markdown(
                                f"<h2 style='text-align: center;'>Total Hours Worked: "
                                f"<span style='color: #1f77b4;'>{analysis['total_hours']}</span> hrs</h2>",
                                unsafe_allow_html=True
                            )
                            # Display summary
                            st.markdown(f"**Schedule Summary:**\n{analysis['summary']}")
                            
                            # Save data
                            saved_path = save_to_json(schedule_data, analysis)
                            if saved_path:
                                st.success(f"✅ Data saved to: {saved_path}")
            else:
                st.error("❌ Failed to process the image. Please try again.")
