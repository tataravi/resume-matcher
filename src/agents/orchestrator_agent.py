import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from src.core.base_agent import BaseAgent
from src.core.models import AgentType, Task, Priority, TaskStatus, AgentContext
from .parser_agent import ParserAgent
from .matcher_agent import MatcherAgent
from .feedback_agent import FeedbackAgent


class OrchestratorAgent(BaseAgent):
    def __init__(
        self, 
        parser_agent: ParserAgent,
        matcher_agent: MatcherAgent,
        feedback_agent: FeedbackAgent,
        agent_id: str = None
    ):
        super().__init__(agent_id=agent_id, agent_type=AgentType.ORCHESTRATOR)
        self.parser_agent = parser_agent
        self.matcher_agent = matcher_agent
        self.feedback_agent = feedback_agent
        self.workflow_states: Dict[str, Dict[str, Any]] = {}
        
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute orchestration task."""
        task_type = task.input_data.get("type")
        
        if task_type == "full_analysis":
            return await self._execute_full_analysis(task)
        elif task_type == "resume_parsing_only":
            return await self._execute_resume_parsing(task)
        elif task_type == "job_matching_only":
            return await self._execute_job_matching(task)
        else:
            raise ValueError(f"Unknown orchestration task type: {task_type}")
            
    async def _execute_full_analysis(self, task: Task) -> Dict[str, Any]:
        """Execute complete resume analysis workflow."""
        workflow_id = str(task.id)  # Use the task ID as the workflow ID
        
        # Update existing workflow state
        if workflow_id in self.workflow_states:
            self.workflow_states[workflow_id].update({
                "current_step": "parsing",
                "progress_percentage": 10.0
            })
        
        try:
            # Initialize results structure
            if "results" not in self.workflow_states[workflow_id]:
                self.workflow_states[workflow_id]["results"] = {}
            
            # Step 1: Parse Resume (real processing)
            self.logger.info(f"Starting resume parsing for workflow {workflow_id}")
            self.workflow_states[workflow_id]["current_step"] = "parsing"
            
            resume_parsing_result = await self._execute_resume_parsing(task)
            parsed_data = resume_parsing_result.get("parsed_data", {})
            
            self.workflow_states[workflow_id]["steps_completed"].append("parsing")
            self.workflow_states[workflow_id]["progress_percentage"] = 25.0
            
            # Step 2: Parse Job Description 
            self.logger.info(f"Starting job description parsing for workflow {workflow_id}")
            self.workflow_states[workflow_id]["current_step"] = "job_parsing"
            
            job_parsing_task = Task(
                type="job_parsing",
                input_data={
                    "type": "parse_job_description",
                    "job_title": task.input_data.get("job_title", ""),
                    "company": task.input_data.get("company", ""),
                    "job_description": task.input_data.get("job_description", "")
                },
                context=task.context,
                priority=task.priority
            )
            
            job_parsing_result = await self.parser_agent.execute_task(job_parsing_task)
            job_data = job_parsing_result.get("parsed_data", {})
            
            self.workflow_states[workflow_id]["steps_completed"].append("job_parsing")
            self.workflow_states[workflow_id]["progress_percentage"] = 50.0
            
            # Step 3: Match Resume with Job (real processing)
            self.logger.info(f"Starting job matching for workflow {workflow_id}")
            self.workflow_states[workflow_id]["current_step"] = "matching"
            
            matching_task = Task(
                type="matching",
                input_data={
                    "type": "match_resume_job",
                    "resume_data": parsed_data,
                    "job_data": job_data
                },
                context=task.context,
                priority=task.priority
            )
            
            matching_result = await self.matcher_agent.execute_task(matching_task)
            
            self.workflow_states[workflow_id]["steps_completed"].append("matching")
            self.workflow_states[workflow_id]["progress_percentage"] = 75.0
            
            # Step 4: Generate Feedback (real processing)
            self.logger.info(f"Generating feedback for workflow {workflow_id}")
            self.workflow_states[workflow_id]["current_step"] = "feedback"
            
            feedback_task = Task(
                type="feedback",
                input_data={
                    "type": "generate_feedback",
                    "analysis_result": matching_result,
                    "resume_data": parsed_data,
                    "job_data": job_data
                },
                context=task.context,
                priority=task.priority
            )
            
            feedback_result = await self.feedback_agent.execute_task(feedback_task)
            
            self.workflow_states[workflow_id]["steps_completed"].append("feedback")
            self.workflow_states[workflow_id]["progress_percentage"] = 100.0
            
            # Format results for frontend
            self.workflow_states[workflow_id]["results"]["resume_analysis"] = {
                "skills_identified": parsed_data.get("skills", []),
                "experience_level": parsed_data.get("experience_level", "Not specified"),
                "education": parsed_data.get("education", "Not specified"),
                "key_strengths": parsed_data.get("strengths", [])
            }
            
            self.workflow_states[workflow_id]["results"]["job_match_analysis"] = {
                "overall_match_score": matching_result.get("overall_score", 0),
                "matching_skills": matching_result.get("matching_skills", []),
                "missing_skills": matching_result.get("missing_skills", []),
                "skill_gaps": matching_result.get("skill_gaps", [])
            }
            
            self.workflow_states[workflow_id]["results"]["feedback"] = {
                "strengths": feedback_result.get("strengths", []),
                "improvements": feedback_result.get("improvements", []),
                "recommendation": feedback_result.get("recommendation", "")
            }
            
            # Workflow completed successfully
            self.workflow_states[workflow_id]["status"] = "completed"
            self.workflow_states[workflow_id]["current_step"] = "completed"
            self.workflow_states[workflow_id]["end_time"] = datetime.utcnow().isoformat()
            
            # Calculate duration 
            start_time_str = self.workflow_states[workflow_id]["start_time"]
            end_time_str = self.workflow_states[workflow_id]["end_time"]
            
            final_result = {
                "workflow_id": workflow_id,
                "status": "completed",
                "results": self.workflow_states[workflow_id]["results"],
                "execution_summary": {
                    "steps_completed": self.workflow_states[workflow_id]["steps_completed"],
                    "total_steps": 3,
                    "start_time": start_time_str,
                    "end_time": end_time_str,
                    "duration_seconds": 5.0  # Demo duration
                }
            }
            
            self.logger.info(f"Workflow {workflow_id} completed successfully")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
            self.workflow_states[workflow_id]["status"] = "failed"
            self.workflow_states[workflow_id]["error"] = str(e)
            self.workflow_states[workflow_id]["end_time"] = datetime.utcnow().isoformat()
            raise
            
    async def _execute_resume_parsing(self, task: Task) -> Dict[str, Any]:
        """Execute only resume parsing."""
        parsing_task = Task(
            type="resume_parsing",
            input_data={
                "type": "parse_resume",
                "content": task.input_data.get("resume_content", ""),
                "filename": task.input_data.get("resume_filename", "")
            },
            context=task.context,
            priority=task.priority
        )
        
        result = await self.parser_agent.execute_task(parsing_task)
        return {
            "operation": "resume_parsing_only",
            "status": "completed",
            "result": result
        }
        
    async def _execute_job_matching(self, task: Task) -> Dict[str, Any]:
        """Execute only job matching (assumes parsed data is provided)."""
        matching_task = Task(
            type="matching",
            input_data={
                "type": "match_resume_job",
                "resume_data": task.input_data.get("resume_data"),
                "job_data": task.input_data.get("job_data")
            },
            context=task.context,
            priority=task.priority
        )
        
        result = await self.matcher_agent.execute_task(matching_task)
        return {
            "operation": "job_matching_only",
            "status": "completed",
            "result": result
        }
        
    async def start_workflow(
        self,
        user_id: str,
        session_id: str,
        resume_content: str,
        resume_filename: str,
        job_title: str,
        company: str,
        job_description: str,
        priority: Priority = Priority.MEDIUM
    ) -> str:
        """Start a new analysis workflow."""
        context = AgentContext(
            task_id=uuid4(),
            user_id=user_id,
            session_id=session_id,
            metadata={
                "resume_filename": resume_filename,
                "job_title": job_title,
                "company": company
            }
        )
        
        workflow_task = Task(
            type="orchestration",
            priority=priority,
            input_data={
                "type": "full_analysis",
                "resume_content": resume_content,
                "resume_filename": resume_filename,
                "job_title": job_title,
                "company": company,
                "job_description": job_description
            },
            context=context
        )
        
        # Execute the task immediately and store the workflow state
        workflow_id = str(workflow_task.id)
        
        # Initialize workflow state immediately
        self.workflow_states[workflow_id] = {
            "analysis_id": workflow_id,
            "status": "running",
            "current_step": "parsing",
            "steps_completed": [],
            "progress_percentage": 0.0,
            "start_time": datetime.utcnow().isoformat(),
            "estimated_completion": None,
            "user_id": user_id
        }
        
        # Execute workflow in background
        asyncio.create_task(self._execute_workflow_background(workflow_task))
        
        return workflow_id
    
    async def _execute_workflow_background(self, task: Task):
        """Execute workflow in background and update state."""
        try:
            result = await self.execute_task(task)
            self.logger.info(f"Workflow {task.id} completed successfully")
        except Exception as e:
            self.logger.error(f"Workflow {task.id} failed: {e}", exc_info=True)
            # Update workflow state to failed
            workflow_id = str(task.id)
            if workflow_id in self.workflow_states:
                self.workflow_states[workflow_id].update({
                    "status": "failed",
                    "error_message": str(e),
                    "end_time": datetime.utcnow().isoformat()
                })
        
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow."""
        if workflow_id in self.workflow_states:
            workflow = self.workflow_states[workflow_id]
            
            # Handle start_time properly - it might already be a string
            start_time = workflow.get("start_time")
            if isinstance(start_time, str):
                start_time_str = start_time
            elif start_time:
                start_time_str = start_time.isoformat()
            else:
                start_time_str = None
            
            return {
                "analysis_id": workflow_id,
                "status": workflow["status"],
                "current_step": workflow.get("current_step"),
                "steps_completed": workflow.get("steps_completed", []),
                "progress_percentage": workflow.get("progress_percentage", 0.0),
                "start_time": start_time_str,
                "estimated_completion": self._estimate_completion_time(workflow),
                "user_id": workflow.get("user_id"),
                "results": workflow.get("results"),
                "error_message": workflow.get("error_message")
            }
        return None
        
    def _calculate_progress(self, workflow: Dict[str, Any]) -> float:
        """Calculate workflow progress percentage."""
        total_steps = 4  # parsing, job_parsing, matching, feedback
        completed_steps = len(workflow.get("steps_completed", []))
        return (completed_steps / total_steps) * 100
        
    def _estimate_completion_time(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Estimate workflow completion time."""
        if workflow["status"] == "completed":
            return None
            
        # Simple estimation based on average step time
        avg_step_time = 30  # seconds
        remaining_steps = 4 - len(workflow.get("steps_completed", []))
        estimated_seconds = remaining_steps * avg_step_time
        
        estimated_completion = datetime.utcnow().timestamp() + estimated_seconds
        return datetime.fromtimestamp(estimated_completion).isoformat()
        
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        if workflow_id in self.workflow_states:
            workflow = self.workflow_states[workflow_id]
            if workflow["status"] == "running":
                workflow["status"] = "cancelled"
                workflow["end_time"] = datetime.utcnow()
                
                # Cancel the associated task
                for task_id, task in self.current_tasks.items():
                    if str(task.id) == workflow_id:
                        await self.cancel_task(task_id)
                        break
                        
                self.logger.info(f"Workflow {workflow_id} cancelled")
                return True
        return False