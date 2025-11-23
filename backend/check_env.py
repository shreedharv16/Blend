"""Quick script to check environment variables."""
import sys
from pathlib import Path

# Check if .env exists
env_path = Path(".env")
if not env_path.exists():
    print("❌ .env file not found!")
    print("Please create a .env file in the backend directory")
    sys.exit(1)

print("✅ .env file found")

# Try to load settings
try:
    from app.config import settings
    
    print("\n📋 Configuration loaded successfully!")
    print(f"   Model: {settings.GEMINI_MODEL}")
    print(f"   API Key: {'✅ Set' if settings.api_key else '❌ Missing'}")
    print(f"   Qdrant URL: {'✅ Set' if settings.QDRANT_URL else '❌ Missing'}")
    print(f"   Qdrant API Key: {'✅ Set' if settings.QDRANT_API_KEY else '❌ Missing'}")
    print(f"   LangSmith: {'✅ Enabled' if settings.LANGCHAIN_API_KEY else '⚠️  Optional'}")
    
    # Check critical settings
    if not settings.api_key:
        print("\n❌ ERROR: Neither GOOGLE_API_KEY nor GEMINI_API_KEY is set!")
        sys.exit(1)
    
    if not settings.QDRANT_URL:
        print("\n❌ ERROR: QDRANT_URL is not set!")
        sys.exit(1)
    
    if not settings.QDRANT_API_KEY:
        print("\n❌ ERROR: QDRANT_API_KEY is not set!")
        sys.exit(1)
    
    print("\n✅ All required environment variables are set!")
    print("🚀 You can now run: python run.py")
    
except Exception as e:
    print(f"\n❌ Error loading configuration: {e}")
    sys.exit(1)

