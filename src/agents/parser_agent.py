import re
from typing import Any, Dict, List
from datetime import datetime

from src.core.base_agent import BaseAgent
from src.core.models import AgentType, Task
from src.services.llm_service import LLMService


class ParserAgent(BaseAgent):
    def __init__(self, llm_service: LLMService, agent_id: str = None):
        super().__init__(agent_id=agent_id, agent_type=AgentType.PARSER)
        self.llm_service = llm_service
        
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute parsing task based on task type."""
        task_type = task.input_data.get("type")
        
        if task_type == "parse_resume":
            return await self._parse_resume(task.input_data)
        elif task_type == "parse_job_description":
            return await self._parse_job_description(task.input_data)
        else:
            raise ValueError(f"Unknown parsing task type: {task_type}")
            
    async def _parse_resume(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse resume content and extract structured information."""
        content = input_data.get("content", "")
        
        # Basic regex-based extraction
        basic_info = self._extract_basic_info(content)
        
        # Use LLM for advanced parsing
        llm_prompt = self._create_resume_parsing_prompt(content)
        llm_result = await self.llm_service.generate_completion(
            prompt=llm_prompt,
            max_tokens=2000,
            temperature=0.1
        )
        
        # Combine results
        parsed_data = {
            **basic_info,
            "llm_extracted": llm_result,
            "raw_content": content,
            "parsed_at": datetime.utcnow().isoformat()
        }
        
        return {"parsed_data": parsed_data}
        
    async def _parse_job_description(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse job description and extract structured information."""
        description = input_data.get("description", "")
        title = input_data.get("title", "")
        company = input_data.get("company", "")
        
        # Use LLM for job description parsing
        llm_prompt = self._create_job_parsing_prompt(title, company, description)
        llm_result = await self.llm_service.generate_completion(
            prompt=llm_prompt,
            max_tokens=1500,
            temperature=0.1
        )
        
        parsed_data = {
            "title": title,
            "company": company,
            "description": description,
            "llm_extracted": llm_result,
            "parsed_at": datetime.utcnow().isoformat()
        }
        
        return {"parsed_data": parsed_data}
        
    def _extract_basic_info(self, content: str) -> Dict[str, Any]:
        """Extract basic information using regex patterns."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        
        emails = re.findall(email_pattern, content, re.IGNORECASE)
        phones = re.findall(phone_pattern, content)
        
        # Extract potential skills (this is a simplified approach)
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'fastapi', 'django', 'flask', 'express'
        ]
        
        found_skills = []
        content_lower = content.lower()
        for skill in skill_keywords:
            if skill in content_lower:
                found_skills.append(skill)
                
        return {
            "emails": emails,
            "phones": phones,
            "detected_skills": found_skills
        }
        
    def _create_resume_parsing_prompt(self, content: str) -> str:
        """Create prompt for LLM-based resume parsing."""
        return f"""
        Parse the following resume content and extract structured information in JSON format.
        
        Please extract:
        1. Personal information (name, location, but NOT sensitive data like SSN)
        2. Professional summary/objective
        3. Work experience (company, role, dates, responsibilities)
        4. Education (institution, degree, dates, GPA if mentioned)
        5. Skills (technical skills, programming languages, frameworks, tools)
        6. Certifications
        7. Projects (if mentioned)
        8. Languages spoken
        
        Resume content:
        {content}
        
        Provide the response in valid JSON format only, without any additional text or markdown.
        """
        
    def _create_job_parsing_prompt(self, title: str, company: str, description: str) -> str:
        """Create prompt for LLM-based job description parsing."""
        return f"""
        Parse the following job description and extract structured information in JSON format.
        
        Job Title: {title}
        Company: {company}
        
        Please extract:
        1. Key responsibilities and duties
        2. Required skills and qualifications
        3. Preferred skills and qualifications
        4. Experience level required
        5. Education requirements
        6. Technical skills and tools mentioned
        7. Soft skills mentioned
        8. Benefits and perks (if mentioned)
        9. Work arrangement (remote, hybrid, on-site)
        10. Salary range (if mentioned)
        
        Job Description:
        {description}
        
        Provide the response in valid JSON format only, without any additional text or markdown.
        """