"""FastAPI dependency functions for agent creation and management."""

from typing import Annotated
from fastapi import Depends
from functools import lru_cache

from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.parser_agent import ParserAgent
from src.agents.matcher_agent import MatcherAgent
from src.agents.feedback_agent import FeedbackAgent
from src.services.llm_service import LLMService
from src.services.s3_service import S3Service
from src.services.dynamodb_service import DynamoDBService
from src.services.sqs_service import SQSService
from src.config import settings


@lru_cache()
def get_llm_service() -> LLMService:
    """Get a singleton LLM service instance."""
    return LLMService()


@lru_cache()
def get_s3_service() -> S3Service:
    """Get a singleton S3 service instance."""
    return S3Service(
        region=settings.aws_region,
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        bucket_name=settings.aws_s3_bucket
    )


@lru_cache()
def get_dynamodb_service() -> DynamoDBService:
    """Get a singleton DynamoDB service instance."""
    return DynamoDBService(
        region=settings.aws_region,
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        table_name=settings.aws_dynamodb_table
    )


@lru_cache()
def get_sqs_service() -> SQSService:
    """Get a singleton SQS service instance."""
    return SQSService(
        region=settings.aws_region,
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        queue_url=settings.aws_sqs_queue_url
    )


def get_parser_agent(
    llm_service: Annotated[LLMService, Depends(get_llm_service)]
) -> ParserAgent:
    """Create a new parser agent instance."""
    return ParserAgent(llm_service=llm_service)


def get_matcher_agent(
    llm_service: Annotated[LLMService, Depends(get_llm_service)]
) -> MatcherAgent:
    """Create a new matcher agent instance."""
    return MatcherAgent(llm_service=llm_service)


def get_feedback_agent(
    llm_service: Annotated[LLMService, Depends(get_llm_service)]
) -> FeedbackAgent:
    """Create a new feedback agent instance."""
    return FeedbackAgent(llm_service=llm_service)


@lru_cache()
def get_orchestrator_agent() -> OrchestratorAgent:
    """Get a singleton orchestrator agent instance with all dependencies."""
    llm_service = get_llm_service()
    parser_agent = ParserAgent(llm_service=llm_service)
    matcher_agent = MatcherAgent(llm_service=llm_service)
    feedback_agent = FeedbackAgent(llm_service=llm_service)
    
    return OrchestratorAgent(
        parser_agent=parser_agent,
        matcher_agent=matcher_agent,
        feedback_agent=feedback_agent
    )