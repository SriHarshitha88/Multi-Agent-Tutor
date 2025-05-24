from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TutorException(Exception):
    """Base exception for the tutor system"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AgentNotFoundError(TutorException):
    """Raised when a requested agent is not found"""
    def __init__(self, agent_type: str, available_agents: list):
        super().__init__(
            message=f"Agent '{agent_type}' not found",
            status_code=404,
            details={"available_agents": available_agents}
        )

class InvalidQueryError(TutorException):
    """Raised when a query is invalid or malformed"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            details=details
        )

class SessionError(TutorException):
    """Raised when there are issues with session management"""
    def __init__(self, message: str, session_id: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            details={"session_id": session_id} if session_id else None
        )

class ToolExecutionError(TutorException):
    """Raised when there are issues executing agent tools"""
    def __init__(self, message: str, tool_name: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            details={"tool_name": tool_name} if tool_name else None
        )

async def tutor_exception_handler(request: Request, exc: TutorException) -> JSONResponse:
    """Handle TutorException and its subclasses"""
    logger.error(f"Tutor error: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )

async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors"""
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": str(exc)
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc) if request.app.debug else "An unexpected error occurred"
        }
    ) 