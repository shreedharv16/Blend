"""Test script to verify LangSmith integration."""
import asyncio
import os
from app.config import settings
from app.services.llm_service import llm_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_langsmith():
    """Test LangSmith tracing with a simple LLM call."""
    
    print("\n" + "="*60)
    print("🧪 Testing LangSmith Integration")
    print("="*60)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2', 'Not Set')}")
    print(f"   LANGCHAIN_PROJECT: {settings.LANGCHAIN_PROJECT}")
    print(f"   LANGCHAIN_API_KEY: {'✅ Set' if settings.LANGCHAIN_API_KEY else '❌ Not Set'}")
    
    if not settings.LANGCHAIN_API_KEY:
        print("\n⚠️  Warning: LANGCHAIN_API_KEY is not set.")
        print("   Traces will not be sent to LangSmith.")
        print("   Add LANGCHAIN_API_KEY to your .env file to enable tracing.")
        return
    
    print("\n✅ LangSmith is configured correctly!")
    print(f"   Project: {settings.LANGCHAIN_PROJECT}")
    print(f"   Endpoint: {settings.LANGCHAIN_ENDPOINT}")
    
    # Make a test LLM call
    print("\n🤖 Making test LLM call...")
    print("   This call will be traced in LangSmith")
    
    try:
        response = await llm_service.generate(
            prompt="What is 2+2? Answer in one sentence.",
            system_prompt="You are a helpful math assistant.",
            temperature=0.1
        )
        
        print(f"\n📝 Response: {response}")
        print("\n✅ Test successful!")
        print("\n🔍 View this trace in LangSmith:")
        print(f"   1. Go to https://smith.langchain.com")
        print(f"   2. Select project: {settings.LANGCHAIN_PROJECT}")
        print(f"   3. Look for the most recent trace")
        print(f"   4. You should see the prompt and response")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        print("   Check your API keys and network connection")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # Ensure LangSmith is set up
    from app.main import setup_langsmith
    setup_langsmith()
    
    # Run the test
    asyncio.run(test_langsmith())

