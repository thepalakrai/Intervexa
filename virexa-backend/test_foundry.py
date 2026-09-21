"""
Run this directly to test the Foundry connection on its own,
bypassing FastAPI entirely. This will show the FULL error if
something's wrong with the Azure OpenAI / Foundry setup.

Run with:
    python test_foundry.py
"""
import traceback
from dotenv import load_dotenv

load_dotenv()

from services import foundry

print(f"Loading foundry module from: {foundry.__file__}")
print("Testing Foundry connection...")
print(f"Endpoint: {foundry.ENDPOINT}")
print(f"Deployment: {foundry.DEPLOYMENT}")
print(f"API key present: {bool(foundry.API_KEY)}")
print("-" * 50)

try:
    result = foundry.analyze_profile(
        resume_text="Test resume with Python and SQL skills",
        jd_text="Looking for a data analyst with Python and SQL",
    )
    print("SUCCESS!")
    print(result)
except Exception as e:
    print("FAILED with this full traceback:")
    print("-" * 50)
    traceback.print_exc()
