from typing import Any, Dict, List
from datetime import datetime

from src.core.base_agent import BaseAgent
from src.core.models import AgentType, Task
from src.services.llm_service import LLMService


class FeedbackAgent(BaseAgent):
    def __init__(self, llm_service: LLMService, agent_id: str = None):
        super().__init__(agent_id=agent_id, agent_type=AgentType.FEEDBACK)
        self.llm_service = llm_service
        
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute feedback generation task."""
        task_type = task.input_data.get("type")
        
        if task_type == "generate_feedback":
            return await self._generate_feedback(task.input_data)
        elif task_type == "generate_improvement_suggestions":
            return await self._generate_improvement_suggestions(task.input_data)
        else:
            raise ValueError(f"Unknown feedback task type: {task_type}")
            
    async def _generate_feedback(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive feedback based on analysis results."""
        analysis_result = input_data.get("analysis_result", {})
        resume_data = input_data.get("resume_data", {})
        job_data = input_data.get("job_data", {})
        
        feedback_prompt = self._create_feedback_prompt(analysis_result, resume_data, job_data)
        feedback_response = await self.llm_service.generate_completion(
            prompt=feedback_prompt,
            max_tokens=2500,
            temperature=0.3
        )
        
        # Generate specific improvement areas
        improvement_areas = await self._identify_improvement_areas(
            analysis_result, resume_data, job_data
        )
        
        feedback_result = {
            "overall_feedback": feedback_response,
            "improvement_areas": improvement_areas,
            "actionable_steps": self._extract_actionable_steps(feedback_response),
            "priority_recommendations": self._prioritize_recommendations(feedback_response),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {"feedback_result": feedback_result}
        
    async def _generate_improvement_suggestions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific improvement suggestions for the resume."""
        resume_data = input_data.get("resume_data", {})
        job_data = input_data.get("job_data", {})
        target_role = input_data.get("target_role", "")
        
        suggestions_prompt = self._create_improvement_prompt(resume_data, job_data, target_role)
        suggestions_response = await self.llm_service.generate_completion(
            prompt=suggestions_prompt,
            max_tokens=2000,
            temperature=0.2
        )
        
        improvement_suggestions = {
            "content_suggestions": self._extract_content_suggestions(suggestions_response),
            "formatting_suggestions": self._extract_formatting_suggestions(suggestions_response),
            "keyword_suggestions": self._extract_keyword_suggestions(suggestions_response),
            "structure_suggestions": self._extract_structure_suggestions(suggestions_response),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {"improvement_suggestions": improvement_suggestions}
        
    async def _identify_improvement_areas(
        self, analysis_result: Dict[str, Any], resume_data: Dict[str, Any], job_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify specific areas for improvement."""
        areas = []
        
        match_score = analysis_result.get("match_score", 0)
        
        if match_score < 70:
            areas.append({
                "area": "Skills Alignment",
                "priority": "high",
                "description": "Resume lacks key skills mentioned in job requirements",
                "impact": "Critical for initial screening"
            })
            
        if match_score < 60:
            areas.append({
                "area": "Experience Relevance",
                "priority": "high", 
                "description": "Work experience doesn't clearly align with job requirements",
                "impact": "May not pass initial review"
            })
            
        # Add more sophisticated analysis based on specific weaknesses
        weaknesses = analysis_result.get("weaknesses", [])
        for weakness in weaknesses:
            areas.append({
                "area": "Content Enhancement",
                "priority": "medium",
                "description": weakness,
                "impact": "Moderate impact on application success"
            })
            
        return areas
        
    def _create_feedback_prompt(
        self, analysis_result: Dict[str, Any], resume_data: Dict[str, Any], job_data: Dict[str, Any]
    ) -> str:
        """Create prompt for comprehensive feedback generation."""
        return f"""
        Generate comprehensive, actionable feedback for a job application based on the analysis results.
        
        ANALYSIS RESULTS:
        Match Score: {analysis_result.get('match_score', 0)}%
        Strengths: {analysis_result.get('strengths', [])}
        Weaknesses: {analysis_result.get('weaknesses', [])}
        
        RESUME DATA:
        {resume_data}
        
        JOB REQUIREMENTS:
        {job_data}
        
        Please provide feedback in the following JSON format:
        {{
            "summary": "Brief overall assessment",
            "strengths_feedback": {{
                "points": ["strength1", "strength2"],
                "elaboration": "Detailed explanation of strengths"
            }},
            "improvement_areas": {{
                "critical": ["area1", "area2"],
                "moderate": ["area3", "area4"],
                "minor": ["area5"]
            }},
            "specific_recommendations": [
                {{
                    "category": "Skills",
                    "recommendation": "specific advice",
                    "priority": "high|medium|low",
                    "implementation": "how to implement"
                }}
            ],
            "interview_preparation": [
                "talking point 1",
                "talking point 2"
            ]
        }}
        
        Focus on:
        1. Actionable, specific advice
        2. Prioritized recommendations
        3. Interview preparation tips
        4. Ways to better highlight existing qualifications
        5. Skill gaps and how to address them
        
        Provide only valid JSON without additional text or markdown.
        """
        
    def _create_improvement_prompt(
        self, resume_data: Dict[str, Any], job_data: Dict[str, Any], target_role: str
    ) -> str:
        """Create prompt for improvement suggestions."""
        return f"""
        Provide specific resume improvement suggestions for targeting this role: {target_role}
        
        CURRENT RESUME:
        {resume_data}
        
        TARGET JOB:
        {job_data}
        
        Provide suggestions in JSON format:
        {{
            "content_improvements": [
                {{
                    "section": "Professional Summary",
                    "current_issue": "description of issue",
                    "suggested_improvement": "specific improvement",
                    "example": "example text"
                }}
            ],
            "formatting_improvements": [
                {{
                    "area": "formatting area",
                    "suggestion": "specific formatting advice"
                }}
            ],
            "keyword_optimization": {{
                "missing_keywords": ["keyword1", "keyword2"],
                "keyword_placement_tips": ["tip1", "tip2"]
            }},
            "structure_improvements": [
                {{
                    "section": "section name",
                    "improvement": "how to improve this section"
                }}
            ]
        }}
        
        Focus on ATS optimization and human readability.
        Provide only valid JSON without additional text or markdown.
        """
        
    def _extract_actionable_steps(self, feedback_response: str) -> List[str]:
        """Extract actionable steps from feedback."""
        # This would parse the JSON response from LLM
        return [
            "Update skills section with missing technologies",
            "Quantify achievements in work experience",
            "Add relevant projects section"
        ]
        
    def _prioritize_recommendations(self, feedback_response: str) -> List[Dict[str, Any]]:
        """Extract and prioritize recommendations."""
        # This would parse the JSON response from LLM
        return [
            {
                "recommendation": "Add Python and FastAPI to skills",
                "priority": "high",
                "impact": "Increases ATS match score significantly"
            },
            {
                "recommendation": "Quantify project outcomes",
                "priority": "medium", 
                "impact": "Makes achievements more compelling"
            }
        ]
        
    def _extract_content_suggestions(self, suggestions_response: str) -> List[Dict[str, Any]]:
        """Extract content improvement suggestions."""
        # This would parse the JSON response from LLM
        return [
            {
                "section": "Professional Summary",
                "suggestion": "Make it more specific to the target role",
                "priority": "high"
            }
        ]
        
    def _extract_formatting_suggestions(self, suggestions_response: str) -> List[str]:
        """Extract formatting suggestions."""
        return ["Use consistent bullet points", "Ensure consistent date formatting"]
        
    def _extract_keyword_suggestions(self, suggestions_response: str) -> Dict[str, List[str]]:
        """Extract keyword optimization suggestions."""
        return {
            "missing_keywords": ["API development", "microservices"],
            "placement_tips": ["Include keywords in summary", "Use in skill descriptions"]
        }
        
    def _extract_structure_suggestions(self, suggestions_response: str) -> List[Dict[str, str]]:
        """Extract structure improvement suggestions."""
        return [
            {
                "section": "Work Experience",
                "suggestion": "Lead with most relevant experience"
            }
        ]