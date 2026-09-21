"""
Brand-new test script (different filename on purpose) to rule out any
file-caching weirdness with the old test_foundry.py / foundry.py names.

Run with:
    python test_ai_service.py
"""
import traceback
from dotenv import load_dotenv

load_dotenv()

from services import ai_service

print(f"Loading ai_service module from: {ai_service.__file__}")
print("Testing Azure OpenAI connection...")
print(f"Endpoint: {ai_service.ENDPOINT}")
print(f"Deployment: {ai_service.DEPLOYMENT}")
print(f"API key present: {bool(ai_service.API_KEY)}")
print("-" * 50)

try:
    result = ai_service.analyze_profile(
        resume_text="Test resume with Python and SQL skills",
        jd_text="Looking for a data analyst with Python and SQL",
    )
    print("SUCCESS!")
    print(result)
except Exception:
    print("FAILED with this full traceback:")
    print("-" * 50)
    traceback.print_exc()
