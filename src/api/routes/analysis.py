from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from src.api.auth import get_current_active_user, User
from src.api.middleware import limiter
from src.api.dependencies import get_orchestrator_agent
from src.core.models import Priority
from src.agents.orchestrator_agent import OrchestratorAgent
from src.config import settings


# Global storage for analysis states (in production, use database)
analysis_states_storage = {
    # Demo completed analysis
    "123e4567-e89b-12d3-a456-426614174000": {
        "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "completed",
        "current_step": "completed",
        "steps_completed": ["parsing", "job_parsing", "matching", "feedback"],
        "progress_percentage": 100.0,
        "start_time": "2025-08-20T19:00:00.000000",
        "estimated_completion": None,
        "end_time": "2025-08-20T19:03:45.000000",
        "user_id": "demo_user",
        "results": {
            "resume_analysis": {
                "skills_identified": ["Python", "FastAPI", "Docker", "AWS", "PostgreSQL"],
                "experience_level": "Senior (5+ years)",
                "education": "Bachelor's Degree in Computer Science",
                "key_strengths": [
                    "Strong Python development experience",
                    "Cloud platform expertise (AWS)",
                    "Full-stack development capabilities",
                    "Database management skills"
                ]
            },
            "job_match_analysis": {
                "overall_match_score": 85,
                "matching_skills": ["Python", "FastAPI", "AWS"],
                "missing_skills": ["Kubernetes", "React"],
                "skill_gaps": [
                    {
                        "skill": "Kubernetes",
                        "importance": "High",
                        "recommendation": "Consider taking a Kubernetes certification course"
                    },
                    {
                        "skill": "React", 
                        "importance": "Medium",
                        "recommendation": "Build a few React projects to demonstrate frontend skills"
                    }
                ]
            },
            "feedback": {
                "strengths": [
                    "Excellent match for Python development requirements",
                    "Strong cloud experience aligns well with job needs",
                    "Database skills are highly relevant"
                ],
                "improvements": [
                    "Add Kubernetes experience to meet all technical requirements",
                    "Consider adding frontend development examples",
                    "Highlight specific AWS services used in previous roles"
                ],
                "recommendation": "Strong candidate with 85% match. Recommended for interview with focus on Kubernetes knowledge assessment."
            }
        }
    }
}


router = APIRouter(tags=["analysis"])


class AnalysisRequest(BaseModel):
    resume_content: str = Field(..., description="Resume content as text")
    resume_filename: str = Field(..., description="Original filename of the resume")
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    job_description: str = Field(..., description="Job description text")
    priority: Priority = Field(default=Priority.MEDIUM, description="Analysis priority")


class FileAnalysisRequest(BaseModel):
    file_id: str = Field(..., description="ID of the uploaded resume file")
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    job_description: str = Field(..., description="Job description text")
    priority: Priority = Field(default=Priority.MEDIUM, description="Analysis priority")


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str
    estimated_completion_time: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    current_step: Optional[str] = None
    steps_completed: List[str] = Field(default_factory=list)
    progress_percentage: float
    start_time: Optional[str] = None
    estimated_completion: Optional[str] = None
    results: Optional[dict] = None
    error_message: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    analysis_id: str
    status: str
    results: dict
    execution_summary: dict


class AnalysisListResponse(BaseModel):
    analyses: List[AnalysisStatusResponse]
    total_count: int


@router.get("/")
async def analysis_info():
    """Analysis service information."""
    return {
        "service": "Resume Analysis Service",
        "endpoints": {
            "start_analysis": "POST /start",
            "start_from_file": "POST /start-from-file (uses uploaded file)",
            "get_status": "GET /status/{analysis_id}",
            "get_result": "GET /result/{analysis_id}",
            "cancel_analysis": "DELETE /cancel/{analysis_id}",
            "list_analyses": "GET /list",
            "batch_analysis": "POST /batch"
        },
        "features": [
            "Resume parsing and extraction",
            "Job description matching",
            "Skill gap analysis", 
            "Personalized feedback generation",
            "Real-time progress tracking"
        ]
    }


@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """Start a new resume analysis."""
    
    try:
        # Start the analysis workflow
        analysis_id = await orchestrator.start_workflow(
            user_id=current_user.id,
            session_id=f"session_{current_user.id}_{int(datetime.utcnow().timestamp())}",
            resume_content=analysis_request.resume_content,
            resume_filename=analysis_request.resume_filename,
            job_title=analysis_request.job_title,
            company=analysis_request.company,
            job_description=analysis_request.job_description,
            priority=analysis_request.priority
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Analysis workflow started successfully",
            estimated_completion_time=None  # Would be calculated based on queue
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.post("/start-from-file", response_model=AnalysisResponse)
async def start_analysis_from_file(
    analysis_request: FileAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """Start a new resume analysis using an uploaded file."""
    
    try:
        # Import here to avoid circular import
        from src.api.routes.upload import uploaded_files_storage
        
        # Get user's uploaded files
        user_files = uploaded_files_storage.get(current_user.id, [])
        
        # Find the requested file
        file_data = None
        for uploaded_file in user_files:
            if uploaded_file["file_id"] == analysis_request.file_id:
                file_data = uploaded_file
                break
        
        if not file_data:
            raise HTTPException(
                status_code=404,
                detail="File not found or you don't have access to this file"
            )
        
        # Extract resume content
        resume_content = file_data.get("file_content")
        if not resume_content:
            # For non-text files, provide a placeholder
            resume_content = f"[File: {file_data['filename']} - Content extraction not supported for {file_data['content_type']}. Please use manual text input for full analysis.]"
        
        # Start the analysis workflow
        analysis_id = await orchestrator.start_workflow(
            user_id=current_user.id,
            session_id=f"session_{current_user.id}_{int(datetime.utcnow().timestamp())}",
            resume_content=resume_content,
            resume_filename=file_data["filename"],
            job_title=analysis_request.job_title,
            company=analysis_request.company,
            job_description=analysis_request.job_description,
            priority=analysis_request.priority
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message=f"Analysis started for file: {file_data['filename']}",
            estimated_completion_time=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """Get the status of an analysis."""
    
    # Check global storage first
    analysis_data = analysis_states_storage.get(analysis_id)
    if analysis_data:
        # Verify analysis belongs to user (for demo, allow demo_user access)
        if analysis_data.get("user_id") != current_user.id and current_user.id != "demo_user":
            raise HTTPException(status_code=403, detail="Not authorized to access this analysis")
        
        return AnalysisStatusResponse(**analysis_data)
    
    # Check orchestrator workflow states (for new analyses)
    status = orchestrator.get_workflow_status(analysis_id)
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisStatusResponse(**status)


@router.get("/result/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """Get the completed analysis result."""
    
    # Check global storage first
    analysis_data = analysis_states_storage.get(analysis_id)
    if analysis_data:
        # Verify analysis belongs to user
        if analysis_data.get("user_id") != current_user.id and current_user.id != "demo_user":
            raise HTTPException(status_code=403, detail="Not authorized to access this analysis")
        
        if analysis_data["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed. Current status: {analysis_data['status']}"
            )
        
        # Calculate duration for demo data
        try:
            start_time = datetime.fromisoformat(analysis_data["start_time"])
            end_time = datetime.fromisoformat(analysis_data["end_time"]) if analysis_data.get("end_time") else datetime.utcnow()
            duration_seconds = (end_time - start_time).total_seconds()
        except:
            duration_seconds = 225  # Demo: 3 minutes 45 seconds
        
        return AnalysisResultResponse(
            analysis_id=analysis_id,
            status=analysis_data["status"],
            results=analysis_data.get("results", {}),
            execution_summary={
                "steps_completed": analysis_data.get("steps_completed", []),
                "start_time": analysis_data.get("start_time"),
                "end_time": analysis_data.get("end_time"),
                "duration_seconds": duration_seconds
            }
        )
    
    # Check orchestrator workflow states (for new analyses)
    status = orchestrator.get_workflow_status(analysis_id)
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis not completed. Current status: {status['status']}"
        )
    
    # Get the full results from the orchestrator's workflow state
    workflow_state = orchestrator.workflow_states.get(analysis_id)
    if not workflow_state:
        raise HTTPException(status_code=404, detail="Analysis results not found")
    
    return AnalysisResultResponse(
        analysis_id=analysis_id,
        status=workflow_state["status"],
        results=workflow_state.get("results", {}),
        execution_summary={
            "steps_completed": workflow_state.get("steps_completed", []),
            "start_time": workflow_state.get("start_time") if isinstance(workflow_state.get("start_time"), str) else workflow_state.get("start_time").isoformat() if workflow_state.get("start_time") else None,
            "end_time": workflow_state.get("end_time") if isinstance(workflow_state.get("end_time"), str) else workflow_state.get("end_time").isoformat() if workflow_state.get("end_time") else None,
            "duration_seconds": 5.0  # Demo duration
        }
    )


@router.delete("/cancel/{analysis_id}")
async def cancel_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """Cancel a running analysis."""
    
    # Verify analysis belongs to user
    status = orchestrator.get_workflow_status(analysis_id)
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if status["status"] not in ["running", "pending"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel analysis in {status['status']} state"
        )
    
    success = await orchestrator.cancel_workflow(analysis_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel analysis")
    
    return {"message": "Analysis cancelled successfully", "analysis_id": analysis_id}


@router.get("/list", response_model=AnalysisListResponse)
async def list_user_analyses(
    current_user: User = Depends(get_current_active_user),
    limit: int = 10,
    offset: int = 0,
    status_filter: Optional[str] = None,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """List user's analyses with optional status filtering."""
    
    # Get all workflow states from orchestrator
    all_workflows = []
    
    # Include demo analysis
    demo_analysis = AnalysisStatusResponse(
        analysis_id="123e4567-e89b-12d3-a456-426614174000",
        status="completed",
        current_step="completed",
        steps_completed=["parsing", "job_parsing", "matching", "feedback"],
        progress_percentage=100.0,
        start_time=datetime.utcnow().isoformat(),
        estimated_completion=None
    )
    all_workflows.append(demo_analysis)
    
    # Add real workflows from orchestrator
    for workflow_id, workflow_data in orchestrator.workflow_states.items():
        if workflow_data.get("user_id") == current_user.id:
            workflow_status = orchestrator.get_workflow_status(workflow_id)
            if workflow_status:
                analysis = AnalysisStatusResponse(
                    analysis_id=workflow_status.get("analysis_id", workflow_id),
                    status=workflow_status.get("status", "unknown"),
                    current_step=workflow_status.get("current_step", "unknown"),
                    steps_completed=workflow_status.get("steps_completed", []),
                    progress_percentage=workflow_status.get("progress_percentage", 0.0),
                    start_time=workflow_status.get("start_time"),
                    estimated_completion=workflow_status.get("estimated_completion")
                )
                all_workflows.append(analysis)
    
    # Apply status filter if provided
    if status_filter:
        all_workflows = [a for a in all_workflows if a.status == status_filter]
    
    # Sort by start time (newest first)
    all_workflows.sort(key=lambda x: x.start_time or "", reverse=True)
    
    return AnalysisListResponse(
        analyses=all_workflows[offset:offset + limit],
        total_count=len(all_workflows)
    )


@router.post("/batch", response_model=List[AnalysisResponse])
async def start_batch_analysis(
    analysis_requests: List[AnalysisRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
):
    """Start multiple analyses in batch."""
    
    if len(analysis_requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 analyses allowed in a single batch"
        )
    
    results = []
    
    for i, analysis_request in enumerate(analysis_requests):
        try:
            analysis_id = await orchestrator.start_workflow(
                user_id=current_user.id,
                session_id=f"batch_session_{current_user.id}_{int(datetime.utcnow().timestamp())}_{i}",
                resume_content=analysis_request.resume_content,
                resume_filename=analysis_request.resume_filename,
                job_title=analysis_request.job_title,
                company=analysis_request.company,
                job_description=analysis_request.job_description,
                priority=Priority.LOW  # Batch operations get lower priority
            )
            
            results.append(AnalysisResponse(
                analysis_id=analysis_id,
                status="started",
                message="Analysis workflow started successfully"
            ))
            
        except Exception as e:
            results.append(AnalysisResponse(
                analysis_id="error",
                status="failed",
                message=f"Failed to start analysis: {str(e)}"
            ))
    
    return results