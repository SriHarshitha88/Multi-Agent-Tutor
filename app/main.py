# app/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import os
import logging
import uuid
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional, Dict, Any, List

# Import our multi-agent system
from .agents.tutor_agent import TutorAgent
from .agents.base_agent import TaskRequest

# Import utilities
from .utils.logger import setup_logger, get_logger
from .utils.session_manager import SessionManager
from .utils.error_handlers import (
    TutorException,
    AgentNotFoundError,
    InvalidQueryError,
    SessionError,
    ToolExecutionError,
    tutor_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

load_dotenv()

# Set up logging for the application
log_level = logging.INFO if os.getenv("ENVIRONMENT") != "production" else logging.WARNING
setup_logger(level=log_level)
logger = get_logger("main")

# Get port from environment variable (for Railway)
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(
    title="Multi-Agent AI Tutor", 
    description="AI Tutoring system with specialized agents for different subjects",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
    debug=os.getenv("ENVIRONMENT") != "production"
)

# Add CORS middleware with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://multi-agent-tutor.vercel.app",  # Vercel deployment
        os.getenv("FRONTEND_URL", "")  # Railway environment variable
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(TutorException, tutor_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the multi-agent system and session manager
logger.info("Initializing Multi-Agent AI Tutor System")
tutor_agent = TutorAgent()
session_manager = SessionManager(max_history=5, expiry_seconds=3600)  # 1 hour session timeout
logger.info(f"System initialized with {len(tutor_agent.registry.agents)} specialist agents")

# API Models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = Field(None, max_length=2000)
    user_id: Optional[str] = Field(None, max_length=100)
    session_id: Optional[str] = Field(None, max_length=100)
    use_context_history: Optional[bool] = True

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise InvalidQueryError("Query cannot be empty")
        return v

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    agent_used: str
    sources: list
    execution_time_ms: float
    session_id: str
    metadata: Dict[str, Any] = {}
    
class SessionInfo(BaseModel):
    session_id: str
    turn_count: int
    agents_used: List[str]
    duration_seconds: float

@app.get("/")
async def read_root():
    return {
        "message": "Multi-Agent AI Tutor is running!", 
        "version": "2.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "agents_loaded": len(tutor_agent.registry.agents)
    }

@app.post("/ask", response_model=QueryResponse)
async def ask_tutor(request: QueryRequest):
    """Process questions using the AI tutor system with tool capabilities and session history"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation history if enabled
        context = request.context or ""
        if request.use_context_history:
            try:
                session_context = session_manager.get_context(session_id)
                if session_context:
                    # Combine provided context with session history
                    if context:
                        context = f"{context}\n\nConversation History:\n{session_context}"
                    else:
                        context = f"Conversation History:\n{session_context}"
                    logger.info(f"Using conversation history for session {session_id} ({len(session_context)} chars)")
            except Exception as e:
                raise SessionError(f"Error retrieving session context: {str(e)}", session_id)
        
        # Create and process task
        task = TaskRequest(
            query=request.query,
            context=context,
            user_id=request.user_id,
            session_id=session_id
        )
        
        try:
            response = tutor_agent.process_task(task)
        except Exception as e:
            raise ToolExecutionError(f"Error processing task: {str(e)}")
        
        # Determine agent used
        agent_used = "AI Tutor Coordinator"
        if "delegated_to" in response.metadata:
            delegated_agent = tutor_agent.registry.get_agent(response.metadata["delegated_to"])
            if delegated_agent:
                agent_used = f"{delegated_agent.name}"
        
        # Add to session history
        try:
            session_manager.add_interaction(
                session_id=session_id,
                query=request.query,
                response=response.content,
                agent_used=agent_used
            )
        except Exception as e:
            raise SessionError(f"Error updating session history: {str(e)}", session_id)
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=agent_used,
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
            session_id=session_id,
            metadata=response.metadata
        )
    except TutorException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ask_tutor: {str(e)}", exc_info=True)
        raise

@app.post("/ask/{agent_type}", response_model=QueryResponse)
async def ask_specific_agent(agent_type: str, request: QueryRequest):
    """Directly ask a specific agent (math, physics) with session history"""
    try:
        # Check if agent exists
        agent = tutor_agent.registry.get_agent(agent_type)
        if not agent:
            valid_agents = list(tutor_agent.registry.agents.keys())
            raise AgentNotFoundError(agent_type, valid_agents)
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get conversation history if enabled
        context = request.context or ""
        if request.use_context_history:
            try:
                session_context = session_manager.get_context(session_id)
                if session_context:
                    # Combine provided context with session history
                    if context:
                        context = f"{context}\n\nConversation History:\n{session_context}"
                    else:
                        context = f"Conversation History:\n{session_context}"
                    logger.info(f"Using conversation history for session {session_id} ({len(session_context)} chars)")
            except Exception as e:
                raise SessionError(f"Error retrieving session context: {str(e)}", session_id)
        
        # Create task with context
        task = TaskRequest(
            query=request.query,
            context=context,
            user_id=request.user_id,
            session_id=session_id
        )
        
        try:
            response = agent.process_task(task)
        except Exception as e:
            raise ToolExecutionError(f"Error processing task with {agent_type} agent: {str(e)}", agent_type)
        
        # Add to session history
        try:
            session_manager.add_interaction(
                session_id=session_id,
                query=request.query,
                response=response.content,
                agent_used=agent.name
            )
        except Exception as e:
            raise SessionError(f"Error updating session history: {str(e)}", session_id)
        
        return QueryResponse(
            answer=response.content,
            confidence=response.confidence,
            agent_used=agent.name,
            sources=response.sources,
            execution_time_ms=response.execution_time_ms,
            session_id=session_id,
            metadata=response.metadata
        )
    except TutorException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ask_specific_agent: {str(e)}", exc_info=True)
        raise

@app.get("/agents")
async def get_available_agents():
    """Get information about available specialist agents"""
    try:
        agents_info = {}
        for key, agent in tutor_agent.registry.agents.items():
            agents_info[key] = {
                "name": agent.name,
                "available_tools": agent.get_available_tools() if hasattr(agent, "get_available_tools") else []
            }
            
        return {
            "total_agents": len(agents_info),
            "agents": agents_info
        }
    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}", exc_info=True)
        raise

@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get information about a specific session"""
    try:
        session_info = session_manager.get_session_info(session_id)
        if not session_info["exists"]:
            raise SessionError(f"Session '{session_id}' not found or expired", session_id)
            
        return SessionInfo(
            session_id=session_id,
            turn_count=session_info["turn_count"],
            agents_used=session_info["agents_used"],
            duration_seconds=session_info["duration_seconds"]
        )
    except TutorException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}", exc_info=True)
        raise

@app.post("/session/clear/{session_id}")
async def clear_session(session_id: str):
    """Clear session history for a specific session"""
    try:
        success = session_manager.clear_session(session_id)
        if not success:
            raise SessionError(f"Session '{session_id}' not found or already cleared", session_id)
        return {"message": f"Session {session_id} cleared successfully"}
    except TutorException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)