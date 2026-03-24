import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog
from redis import Redis

from src.config.settings import settings


logger = structlog.get_logger()


class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        """Acquire a token for making a request."""
        async with self.lock:
            now = time.time()
            # Refill tokens based on time passed
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
            self.tokens = min(self.requests_per_minute, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
            
    async def wait_for_token(self):
        """Wait until a token is available."""
        while not await self.acquire():
            await asyncio.sleep(0.1)


class LLMCache:
    """Cache for LLM responses to reduce API calls."""
    
    def __init__(self, redis_client: Optional[Redis] = None, ttl_hours: int = 24):
        self.redis_client = redis_client
        self.ttl_seconds = ttl_hours * 3600
        self.memory_cache = {}  # Fallback in-memory cache
        
    def _generate_cache_key(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Generate a cache key for the request."""
        import hashlib
        content = f"{prompt}:{model}:{temperature}:{max_tokens}"
        return f"llm_cache:{hashlib.md5(content.encode()).hexdigest()}"
        
    async def get(self, prompt: str, model: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Get cached response if available."""
        cache_key = self._generate_cache_key(prompt, model, temperature, max_tokens)
        
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return cached.decode('utf-8')
            except Exception as e:
                logger.warning("redis_cache_get_error", error=str(e))
                
        # Fallback to memory cache
        if cache_key in self.memory_cache:
            cached_data = self.memory_cache[cache_key]
            if datetime.utcnow() < cached_data['expires_at']:
                return cached_data['response']
            else:
                del self.memory_cache[cache_key]
                
        return None
        
    async def set(self, prompt: str, model: str, temperature: float, max_tokens: int, response: str):
        """Cache the response."""
        cache_key = self._generate_cache_key(prompt, model, temperature, max_tokens)
        
        if self.redis_client:
            try:
                await self.redis_client.setex(cache_key, self.ttl_seconds, response)
            except Exception as e:
                logger.warning("redis_cache_set_error", error=str(e))
                
        # Also store in memory cache as fallback
        self.memory_cache[cache_key] = {
            'response': response,
            'expires_at': datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
        }


class LLMService:
    """Service for interacting with Claude LLM API."""
    
    def __init__(
        self,
        api_key: str = settings.claude_api_key,
        base_url: str = settings.claude_base_url,
        model: str = settings.claude_model,
        max_retries: int = 3,
        timeout: int = 60,
        redis_client: Optional[Redis] = None
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Rate limiting
        self.rate_limiter = RateLimiter(requests_per_minute=60)
        
        # Caching
        self.cache = LLMCache(redis_client=redis_client)
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = settings.claude_max_tokens,
        temperature: float = settings.claude_temperature,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """Generate a completion using the Claude API."""
        
        # Development fallback when using test API key
        if self.api_key == "test-api-key":
            logger.info("llm_mock_response", prompt_length=len(prompt))
            return await self._generate_mock_completion(prompt)
        
        return await self._generate_real_completion(
            prompt, max_tokens, temperature, model, system_prompt, use_cache
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    async def _generate_real_completion(
        self,
        prompt: str,
        max_tokens: int = settings.claude_max_tokens,
        temperature: float = settings.claude_temperature,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """Generate a real completion using the Claude API."""
        
        model = model or self.model
        self.total_requests += 1
        
        # Check cache first
        if use_cache:
            cached_response = await self.cache.get(prompt, model, temperature, max_tokens)
            if cached_response:
                self.cache_hits += 1
                logger.info("llm_cache_hit", prompt_length=len(prompt))
                return cached_response
        
        # Wait for rate limit
        await self.rate_limiter.wait_for_token()
        
        # Prepare request for Claude API format
        messages = [{"role": "user", "content": prompt}]
        
        request_data = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_data["system"] = system_prompt
        
        try:
            logger.info(
                "llm_request_start",
                model=model,
                prompt_length=len(prompt),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            start_time = time.time()
            
            response = await self.client.post(
                f"{self.base_url}/v1/messages",
                json=request_data
            )
            
            response.raise_for_status()
            
            duration = time.time() - start_time
            
            result = response.json()
            content = result["content"][0]["text"]
            
            # Cache the response
            if use_cache:
                await self.cache.set(prompt, model, temperature, max_tokens, content)
            
            self.successful_requests += 1
            
            logger.info(
                "llm_request_success",
                model=model,
                prompt_length=len(prompt),
                response_length=len(content),
                duration=duration,
                usage=result.get("usage", {})
            )
            
            return content
            
        except httpx.HTTPStatusError as e:
            self.failed_requests += 1
            logger.error(
                "llm_request_http_error",
                status_code=e.response.status_code,
                response_text=e.response.text,
                model=model,
                prompt_length=len(prompt)
            )
            
            if e.response.status_code == 429:
                # Rate limit exceeded, wait and retry
                await asyncio.sleep(5)
                
            raise
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(
                "llm_request_error",
                error=str(e),
                error_type=type(e).__name__,
                model=model,
                prompt_length=len(prompt)
            )
            raise
            
    async def generate_structured_completion(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        max_tokens: int = settings.claude_max_tokens,
        temperature: float = settings.claude_temperature,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """Generate a structured JSON response."""
        
        system_prompt = f"""
        You are a helpful assistant that always responds with valid JSON.
        The response must conform to this schema: {json.dumps(response_schema, indent=2)}
        
        Important:
        - Respond only with valid JSON, no additional text or markdown
        - Ensure all required fields are present
        - Follow the exact structure and data types specified
        """
        
        for attempt in range(max_attempts):
            try:
                response = await self.generate_completion(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt
                )
                
                # Clean response (remove markdown formatting if present)
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                # Parse JSON
                parsed_response = json.loads(cleaned_response)
                
                # Basic validation against schema
                if self._validate_response_schema(parsed_response, response_schema):
                    return parsed_response
                else:
                    logger.warning(
                        "llm_schema_validation_failed",
                        attempt=attempt + 1,
                        response=cleaned_response[:200]
                    )
                    
            except json.JSONDecodeError as e:
                logger.warning(
                    "llm_json_parse_error",
                    attempt=attempt + 1,
                    error=str(e),
                    response=response[:200] if 'response' in locals() else None
                )
                
            except Exception as e:
                logger.error(
                    "llm_structured_completion_error",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
            if attempt < max_attempts - 1:
                await asyncio.sleep(1)  # Brief pause before retry
                
        raise ValueError(f"Failed to generate valid structured response after {max_attempts} attempts")
        
    def _validate_response_schema(self, response: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Basic validation of response against schema."""
        # This is a simplified validation - in production, use a proper JSON schema validator
        if not isinstance(response, dict):
            return False
            
        # Check if required fields are present (simplified check)
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in response:
                return False
                
        return True
        
    async def batch_generate_completions(
        self,
        prompts: List[str],
        max_tokens: int = settings.claude_max_tokens,
        temperature: float = settings.claude_temperature,
        max_concurrent: int = 5
    ) -> List[str]:
        """Generate completions for multiple prompts concurrently."""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_prompt(prompt: str) -> str:
            async with semaphore:
                return await self.generate_completion(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
        
        tasks = [process_single_prompt(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error strings
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(f"Error: {str(result)}")
            else:
                processed_results.append(result)
                
        return processed_results
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "cache_hits": self.cache_hits,
            "success_rate": (
                self.successful_requests / self.total_requests 
                if self.total_requests > 0 else 0
            ),
            "cache_hit_rate": (
                self.cache_hits / self.total_requests 
                if self.total_requests > 0 else 0
            )
        }
        
    async def _generate_mock_completion(self, prompt: str) -> str:
        """Generate a mock completion for development/testing."""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        prompt_lower = prompt.lower()
        
        # Resume parsing mock responses
        if "parse" in prompt_lower and "resume" in prompt_lower:
            return """Based on the resume content, here is the extracted information:

Skills: Python, Java, React, AWS, cloud infrastructure, web applications, software development
Experience Level: Senior level (8+ years)
Education: Bachelor of Science in Computer Science
Key Strengths: Extensive experience in web application development, Strong cloud infrastructure knowledge, Multi-language programming proficiency, Full-stack development capabilities
Contact Information: John Doe
Job Titles: Senior Software Engineer, Software Developer
Technical Skills: Python, Java, React, AWS, cloud technologies, web development
Professional Summary: Experienced software engineer with 8 years in developing web applications and cloud infrastructure."""

        # Job description parsing mock responses  
        elif "parse" in prompt_lower and "job" in prompt_lower:
            return """Based on the job description, here are the requirements:

Required Skills: Python, React, cloud technologies, full-stack development
Experience Required: 5+ years
Job Level: Senior level
Company Type: Technology company
Key Responsibilities: Full-stack development, Cloud infrastructure, Web applications
Technical Requirements: Python programming, React framework, Cloud platforms, 5+ years experience
Preferred Qualifications: Bachelor's degree, Team collaboration, Agile methodologies"""

        # Matching/scoring mock responses
        elif "match" in prompt_lower or "score" in prompt_lower:
            return """Resume-Job Match Analysis:

Overall Match Score: 92/100

Skill Match Analysis:
- Python: Excellent match (candidate has extensive experience)
- React: Good match (candidate has relevant experience) 
- Cloud Technologies: Excellent match (specifically mentions AWS and cloud infrastructure)
- Full-stack Development: Excellent match (8 years of web application development)

Experience Match:
- Required: 5+ years
- Candidate: 8 years
- Match: Exceeds requirements

Education Match:
- Required: Not specified
- Candidate: BS Computer Science
- Match: Good foundation

Strengths:
- Exceeds experience requirements
- Strong technical skill alignment
- Relevant educational background
- Demonstrated cloud expertise"""

        # Feedback generation mock responses
        elif "feedback" in prompt_lower:
            return """Professional Feedback and Recommendations:

Strengths:
- Exceptional technical skill alignment with job requirements
- Significant experience advantage (8 years vs 5 required)
- Strong cloud infrastructure background perfect for the role
- Full-stack capabilities align well with company needs

Areas for Improvement:
- Consider highlighting specific React projects or contributions
- Mention specific AWS services and certifications
- Add details about team leadership or mentoring experience
- Include examples of cloud architecture or scalability improvements

Recommendation:
This candidate is an excellent fit for the Full Stack Developer position at TechCorp. With 92% compatibility and experience exceeding requirements, they should be considered a priority candidate. Focus interview on specific React implementations and cloud architecture experience."""

        # Default fallback
        else:
            return f"""I understand you're asking about: {prompt[:100]}...

Here's a professional analysis based on the information provided:

This appears to be related to resume analysis and job matching. Based on the context, I can provide relevant insights about skills, experience, and professional qualifications.

Key areas of focus typically include:
- Technical skills and competencies
- Professional experience and background
- Educational qualifications
- Career progression and achievements
- Alignment with job requirements

For more specific analysis, please provide additional context about what particular aspect you'd like me to focus on."""


# Global LLM service instance
_llm_service = None


async def get_llm_service() -> LLMService:
    """Dependency injection for LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def close_llm_service():
    """Close the global LLM service."""
    global _llm_service
    if _llm_service:
        await _llm_service.client.aclose()
        _llm_service = None