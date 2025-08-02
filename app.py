import os
from google.oauth2 import service_account
import streamlit as st
from google.cloud import bigquery
from vertexai.preview.generative_models import GenerativeModel
import vertexai
import datetime
import time
import pandas as pd
from bmi_calc import calculate_bmi_status

# Get configuration from environment
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "sintia-agentic-ai")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

#CONSTANTS Dataset and table in BigQuery
DATASET = "diet_planner_data"
TABLE = "user_plans"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize BigQuery client
try:
   # For Cloud Run, use default credentials
   bq_client = bigquery.Client()
except:
   # For local development, use service account from secrets
   if "gcp_service_account" in st.secrets:
       service_account_info = dict(st.secrets["gcp_service_account"])
       credentials = service_account.Credentials.from_service_account_info(service_account_info)
       bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
   else:
       st.error("BigQuery client initialization failed")
       st.stop()

# Create BigQuery table if not exists
def setup_bq_table(bq_client):
   dataset_id = f"{st.secrets['gcp']['project_id']}.{DATASET}"
   table_id = f"{dataset_id}.{TABLE}"
  
   schema = [
       bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
       bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
       bigquery.SchemaField("weight", "FLOAT", mode="REQUIRED"),
       bigquery.SchemaField("height", "INTEGER", mode="REQUIRED"),
       bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
       bigquery.SchemaField("gender", "STRING", mode="REQUIRED"),
       bigquery.SchemaField("diet_plan", "STRING", mode="REQUIRED")
   ]
  
   try:
       bq_client.get_table(table_id)
   except:
       table = bigquery.Table(table_id, schema=schema)
       bq_client.create_table(table)
       st.toast("BigQuery table created successfully")

# Generate diet plan using Gemini Pro
def generate_diet_plan(params):
   try:
       model = GenerativeModel("gemini-2.5-pro")
       prompt = f"""
       Create a personalized 7-day diet plan for:
       - {params['gender']}, {params['age']} years old
       - Weight: {params['weight']} kg
       - Height: {params['height']} cm
      
       Include:
       1. Daily calorie target
       2. Macronutrient breakdown (carbs, protein, fat)
       3. Meal timing and frequency
       4. Food recommendations
       5. Hydration guidance
      
       Make the plan:
       - Nutritionally balanced
       - Practical for daily use
       - Culturally adaptable
       - With portion size guidance
       """
      
       response = model.generate_content(prompt)
       return response.text
   except Exception as e:
       st.error(f"AI generation error: {str(e)}")
       return None

# Save user data to BigQuery
def save_to_bq(bq_client, user_id, plan):
   try:
       dataset_id = f"{st.secrets['gcp']['project_id']}.{DATASET}"
       table_id = f"{dataset_id}.{TABLE}"
      
       row = {
           "user_id": user_id,
           "timestamp": datetime.datetime.utcnow().isoformat(),
           "weight": st.session_state.user_data["weight"],
           "height": st.session_state.user_data["height"],
           "age": st.session_state.user_data["age"],
           "gender": st.session_state.user_data["gender"],
           "diet_plan": plan
       }
      
       errors = bq_client.insert_rows_json(table_id, [row])
       if errors:
           st.error(f"BigQuery error: {errors}")
       else:
           return True
   except Exception as e:
       st.error(f"Data saving error: {str(e)}")
       return False

# Streamlit UI
def main():
   st.set_page_config(page_title="AI Diet Planner", page_icon="🍏", layout="wide")
  
   # Initialize session state
   if "user_data" not in st.session_state:
       st.session_state.user_data = None
   if "diet_plan" not in st.session_state:
       st.session_state.diet_plan = None
  
   # Initialize clients
   #bq_client = init_clients()
   setup_bq_table(bq_client)
  
   st.title("🍏 AI-Powered Diet Planner")
   st.markdown("""
   <style>
   .stProgress > div > div > div > div {
       background-color: #4CAF50;
   }
   [data-testid="stForm"] {
       background: #f0f5ff;
       padding: 20px;
       border-radius: 10px;
       border: 1px solid #e6e9ef;
   }
   </style>
   """, unsafe_allow_html=True)
  
   # User input form
   with st.form("user_profile", clear_on_submit=False):
       st.subheader("Your Profile")
       col1, col2 = st.columns(2)
      
       with col1:
           weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
           height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
          
       with col2:
           age = st.number_input("Age", min_value=18, max_value=100, value=30)
           gender = st.selectbox("Gender", ["Man", "Woman"])
      
       submitted = st.form_submit_button("Generate Diet Plan")
      
       if submitted:
           user_data = {
               "weight": weight,
               "height": height,
               "age": age,
               "gender": gender
           }

           st.session_state.user_data = user_data
           # Calculate BMI
           bmi_result = calculate_bmi_status(weight, height)

           # Display BMI results in a visually distinct box
           with st.container():
               st.subheader("📊 Your Health Assessment")
               col1, col2 = st.columns([1, 3])
      
               with col1:
                   st.metric("BMI", bmi_result["value"])
          
               with col2:
                   if bmi_result["status"] != "normal":
                       st.warning(bmi_result["message"])
                   else:
                       st.success(bmi_result["message"])
      
           # Add BMI scale visualization
           st.markdown(f"""
           <div style="background:#f0f2f6;padding:10px;border-radius:10px;margin-top:10px">
           <small>BMI Scale:</small><br>
           <div style="display:flex;height:20px;background:linear-gradient(90deg,
           #4e79a7 0%,
           #4e79a7 18.5%,
           #60bd68 18.5%,
           #60bd68 25%,
           #f28e2b 25%,
           #f28e2b 30%,
           #e15759 30%,
           #e15759 100%);position:relative">
           <div style="position:absolute;left:{min(100, max(0, (bmi_result["value"]/40)*100))}%;top:-5px">
               ▼
           </div>
           </div>
           <div style="display:flex;justify-content:space-between">
           <span>Underweight (<18.5)</span>
           <span>Healthy (18.5-25)</span>
           <span>Overweight (25-30)</span>
           <span>Obese (30+)</span>
           </div>
           </div>
           """, unsafe_allow_html=True)

           # Store BMI in session state
           st.session_state.bmi = bmi_result         
  
   # Plan generation and display
   if submitted and st.session_state.user_data:
       with st.spinner("🧠 Generating your personalized diet plan using Gemini AI..."):
           #diet_plan = generate_diet_plan(st.session_state.user_data)
           diet_plan = generate_diet_plan({**st.session_state.user_data,"bmi": bmi_result["value"],
                                           "bmi_status": bmi_result["status"]
           })

           if diet_plan:
               st.session_state.diet_plan = diet_plan
              
               # Generate unique user ID
               user_id = f"user_{int(time.time())}"
              
               # Save to BigQuery
               if save_to_bq(bq_client, user_id, diet_plan):
                   st.toast("✅ Plan saved to database!")
  
   # Display generated plan
   if st.session_state.diet_plan:
       st.subheader("Your Personalized Diet Plan")
       st.markdown("---")
       st.markdown(st.session_state.diet_plan)
      
       # Download button
       st.download_button(
           label="Download Plan",
           data=st.session_state.diet_plan,
           file_name="my_diet_plan.md",
           mime="text/markdown"
       )
      
       # Show history
       st.subheader("Your Plan History")
       try:
           query = f"""
               SELECT timestamp, weight, height, age, gender
               FROM `{st.secrets['gcp']['project_id']}.{DATASET}.{TABLE}`
               WHERE user_id LIKE 'user_%'
               ORDER BY timestamp DESC
               LIMIT 5
           """
           history = bq_client.query(query).to_dataframe()
           if not history.empty:
               history["timestamp"] = pd.to_datetime(history["timestamp"])
               st.dataframe(history.style.format({
                   "weight": "{:.1f} kg",
                   "height": "{:.0f} cm"
               }))
           else:
               st.info("No previous plans found")
       except Exception as e:
           st.error(f"History load error: {str(e)}")

if __name__ == "__main__":
   main()