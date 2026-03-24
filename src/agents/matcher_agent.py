from typing import Any, Dict, List
from datetime import datetime

from src.core.base_agent import BaseAgent
from src.core.models import AgentType, Task
from src.services.llm_service import LLMService


class MatcherAgent(BaseAgent):
    def __init__(self, llm_service: LLMService, agent_id: str = None):
        super().__init__(agent_id=agent_id, agent_type=AgentType.MATCHER)
        self.llm_service = llm_service
        
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute matching task."""
        task_type = task.input_data.get("type")
        
        if task_type == "match_resume_job":
            return await self._match_resume_job(task.input_data)
        else:
            raise ValueError(f"Unknown matching task type: {task_type}")
            
    async def _match_resume_job(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match resume against job description and calculate compatibility score."""
        resume_data = input_data.get("resume_data", {})
        job_data = input_data.get("job_data", {})
        
        # Calculate basic compatibility scores
        skill_match_score = self._calculate_skill_match(resume_data, job_data)
        experience_match_score = self._calculate_experience_match(resume_data, job_data)
        
        # Use LLM for comprehensive analysis
        analysis_prompt = self._create_matching_prompt(resume_data, job_data)
        llm_analysis = await self.llm_service.generate_completion(
            prompt=analysis_prompt,
            max_tokens=2000,
            temperature=0.2
        )
        
        # Calculate overall match score
        overall_score = (skill_match_score * 0.4 + experience_match_score * 0.3 + 
                        self._extract_llm_score(llm_analysis) * 0.3)
        
        result = {
            "match_score": round(overall_score, 2),
            "skill_match_score": round(skill_match_score, 2),
            "experience_match_score": round(experience_match_score, 2),
            "detailed_analysis": llm_analysis,
            "strengths": self._extract_strengths(llm_analysis),
            "weaknesses": self._extract_weaknesses(llm_analysis),
            "recommendations": self._extract_recommendations(llm_analysis),
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        return {"analysis_result": result}
        
    def _calculate_skill_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate skill matching score."""
        resume_skills = self._extract_skills_list(resume_data)
        job_requirements = self._extract_job_requirements(job_data)
        
        if not job_requirements:
            return 0.0
            
        matched_skills = 0
        for requirement in job_requirements:
            for skill in resume_skills:
                if self._skills_match(skill.lower(), requirement.lower()):
                    matched_skills += 1
                    break
                    
        return (matched_skills / len(job_requirements)) * 100
        
    def _calculate_experience_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """Calculate experience level matching score."""
        # This is a simplified implementation
        # In a real scenario, you'd analyze work experience more thoroughly
        
        resume_experience = self._extract_experience_years(resume_data)
        required_experience = self._extract_required_experience(job_data)
        
        if required_experience == 0:
            return 100.0
            
        if resume_experience >= required_experience:
            return 100.0
        else:
            return (resume_experience / required_experience) * 100
            
    def _extract_skills_list(self, resume_data: Dict[str, Any]) -> List[str]:
        """Extract list of skills from resume data."""
        skills = []
        
        # From basic detection
        if "detected_skills" in resume_data:
            skills.extend(resume_data["detected_skills"])
            
        # From LLM extraction
        llm_data = resume_data.get("llm_extracted", {})
        if isinstance(llm_data, dict) and "skills" in llm_data:
            if isinstance(llm_data["skills"], list):
                skills.extend(llm_data["skills"])
                
        return list(set(skills))  # Remove duplicates
        
    def _extract_job_requirements(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract job requirements from job data."""
        requirements = []
        
        llm_data = job_data.get("llm_extracted", {})
        if isinstance(llm_data, dict):
            if "required_skills" in llm_data:
                if isinstance(llm_data["required_skills"], list):
                    requirements.extend(llm_data["required_skills"])
            if "technical_skills" in llm_data:
                if isinstance(llm_data["technical_skills"], list):
                    requirements.extend(llm_data["technical_skills"])
                    
        return requirements
        
    def _skills_match(self, skill1: str, skill2: str) -> bool:
        """Check if two skills match (with some fuzzy matching)."""
        # Simple substring matching for now
        return skill1 in skill2 or skill2 in skill1
        
    def _extract_experience_years(self, resume_data: Dict[str, Any]) -> int:
        """Extract years of experience from resume."""
        # Simplified implementation - would need more sophisticated parsing
        return 3  # Default assumption
        
    def _extract_required_experience(self, job_data: Dict[str, Any]) -> int:
        """Extract required years of experience from job description."""
        # Simplified implementation - would parse from job requirements
        return 2  # Default assumption
        
    def _create_matching_prompt(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """Create prompt for LLM-based matching analysis."""
        return f"""
        Analyze the compatibility between this resume and job description. Provide a comprehensive analysis.
        
        RESUME DATA:
        {resume_data}
        
        JOB DESCRIPTION DATA:
        {job_data}
        
        Please provide analysis in the following JSON format:
        {{
            "overall_match_score": <0-100>,
            "strengths": ["strength1", "strength2", ...],
            "weaknesses": ["weakness1", "weakness2", ...],
            "recommendations": ["recommendation1", "recommendation2", ...],
            "detailed_breakdown": {{
                "skill_analysis": "...",
                "experience_analysis": "...",
                "education_analysis": "...",
                "cultural_fit": "..."
            }}
        }}
        
        Consider:
        1. Technical skill alignment
        2. Experience level match
        3. Education requirements
        4. Industry experience
        5. Role progression
        6. Cultural fit indicators
        
        Provide only valid JSON without any additional text or markdown.
        """
        
    def _extract_llm_score(self, llm_analysis: str) -> float:
        """Extract match score from LLM analysis."""
        try:
            # This would parse the JSON response from LLM
            # For now, return a default score
            return 75.0
        except:
            return 75.0
            
    def _extract_strengths(self, llm_analysis: str) -> List[str]:
        """Extract strengths from LLM analysis."""
        # This would parse the JSON response from LLM
        return ["Strong technical background", "Relevant experience"]
        
    def _extract_weaknesses(self, llm_analysis: str) -> List[str]:
        """Extract weaknesses from LLM analysis."""
        # This would parse the JSON response from LLM
        return ["Limited experience with specific framework"]
        
    def _extract_recommendations(self, llm_analysis: str) -> List[str]:
        """Extract recommendations from LLM analysis."""
        # This would parse the JSON response from LLM
        return ["Highlight relevant projects", "Emphasize adaptability"]