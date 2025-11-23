"""LLM service for Gemini integration.

All LLM calls are automatically traced by LangSmith when enabled.
See LANGSMITH_SETUP.md for configuration details.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from typing import Optional, Dict, Any
import json
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    """Service for interacting with Gemini LLM."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.api_key,
            temperature=0.1,
            convert_system_message_to_human=True
        )
        logger.info(f"Initialized LLM service with model: {settings.GEMINI_MODEL}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> str:
        """Generate text from prompt."""
        try:
            messages = []
            
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            messages.append(HumanMessage(content=prompt))
            
            # Create a temporary LLM with specified temperature
            llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.api_key,
                temperature=temperature,
                convert_system_message_to_human=True
            )
            
            response = await llm.ainvoke(messages)
            return response.content
        
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate JSON response from prompt."""
        try:
            response = await self.generate(prompt, system_prompt, temperature=0.1)
            
            # Try to extract JSON from response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            return json.loads(response)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nResponse: {response}")
            # Return a default structure
            return {"error": "Failed to parse JSON", "raw_response": response}
        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            raise
    
    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """Generate text with retry logic."""
        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, system_prompt)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
        
        raise Exception("Max retries exceeded")


# Global LLM service instance
llm_service = LLMService()

