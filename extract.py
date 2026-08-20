import os
from google import genai

# Connect to Gemini using the API key stored in your environment
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Test that Gemini is working
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello and confirm that you are ready to extract financial data."
)

print(response.text)
