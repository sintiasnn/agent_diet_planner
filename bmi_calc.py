# Add this function to calculate BMI and health status
def calculate_bmi_status(weight, height):
   """
   Calculate BMI and return status message
   """
   height_m = height / 100  # Convert cm to meters
   bmi = weight / (height_m ** 2)
  
   if bmi < 18.5:
       status = "underweight"
       message = "⚠️ Your BMI suggests you're underweight. Consider increasing calorie intake with nutrient-dense foods."
   elif 18.5 <= bmi < 25:
       status = "normal"
       message = "✅ Your BMI is in the healthy range. Let's maintain this balance!"
   elif 25 <= bmi < 30:
       status = "overweight"
       message = "⚠️ Your BMI suggests you're overweight. Focus on gradual weight loss through balanced nutrition."
   else:
       status = "obese"
       message = "❗ Your BMI indicates obesity. Please consult a healthcare provider for personalized guidance."
  
   return {
       "value": round(bmi, 1),
       "status": status,
       "message": message
   }