# app/utils/logger.py
import logging
import sys
import time
from typing import Any, Dict, Optional
import json

def setup_logger(name: str = "multi_agent_tutor", level: int = logging.INFO) -> logging.Logger:
    """
    Set up a comprehensive logger for the multi-agent system.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create detailed formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

def get_logger(name: str = "multi_agent_tutor") -> logging.Logger:
    """Get the configured logger."""
    return logging.getLogger(name)

class AgentLogger:
    """
    Specialized logger for agent operations with structured logging and flow tracking.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger(f"agent.{agent_name.lower().replace(' ', '_')}")
        self.flow_id = int(time.time() * 1000)  # Unique ID for tracking the flow
    
    def log_routing_decision(self, query: str, decision: Dict[str, Any]):
        """Log routing decisions made by the coordinator."""
        self.logger.info(f"🎯 ROUTING DECISION [Flow-{self.flow_id}]")
        self.logger.info(f"   Query: '{query}'")
        self.logger.info(f"   Action: {decision.get('action', 'unknown')}")
        self.logger.info(f"   Target: {decision.get('agent_name', 'N/A')}")
        self.logger.info(f"   Reasoning: {decision.get('reasoning', 'N/A')}")
    
    def log_agent_start(self, query: str):
        """Log when an agent starts processing a task."""
        self.logger.info(f"🤖 {self.agent_name.upper()} STARTED [Flow-{self.flow_id}]")
        self.logger.info(f"   Processing: '{query}'")
    
    def log_tool_schemas(self, schemas: list):
        """Log available tool schemas."""
        if schemas:
            tool_names = [schema.get('name', 'unknown') for schema in schemas]
            self.logger.info(f"🔧 Available tools [Flow-{self.flow_id}]: {', '.join(tool_names)}")
        else:
            self.logger.info(f"🔧 No tools available [Flow-{self.flow_id}]")
    
    def log_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any):
        """Log tool function calls."""
        self.logger.info(f"⚡ TOOL CALL: {tool_name} [Flow-{self.flow_id}]")
        self.logger.info(f"   Arguments: {json.dumps(args, ensure_ascii=False) if isinstance(args, (dict, list)) else args}")
        result_str = json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
        self.logger.info(f"   Result: {result_str}")
    
    def log_gemini_request(self, prompt_preview: str):
        """Log Gemini API requests."""
        preview = prompt_preview[:100] + "..." if len(prompt_preview) > 100 else prompt_preview
        self.logger.info(f"🧠 GEMINI REQUEST [Flow-{self.flow_id}]")
        self.logger.info(f"   Prompt preview: {preview}")
    
    def log_gemini_response(self, response_preview: str):
        """Log Gemini API responses."""
        preview = response_preview[:100] + "..." if len(response_preview) > 100 else response_preview
        self.logger.info(f"💬 GEMINI RESPONSE [Flow-{self.flow_id}]")
        self.logger.info(f"   Response preview: {preview}")
    
    def log_function_call_detected(self, function_name: str, args: Dict[str, Any]):
        """Log when Gemini makes a function call."""
        self.logger.info(f"📞 FUNCTION CALL DETECTED [Flow-{self.flow_id}]")
        self.logger.info(f"   Function: {function_name}")
        args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, (dict, list)) else str(args)
        self.logger.info(f"   Arguments: {args_str}")
    
    def log_agent_complete(self, execution_time_ms: float, confidence: float):
        """Log when an agent completes processing."""
        self.logger.info(f"✅ {self.agent_name.upper()} COMPLETED [Flow-{self.flow_id}]")
        self.logger.info(f"   Execution time: {execution_time_ms:.2f}ms")
        self.logger.info(f"   Confidence: {confidence:.2f}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context."""
        self.logger.error(f"❌ ERROR in {self.agent_name} [Flow-{self.flow_id}]")
        if context:
            self.logger.error(f"   Context: {context}")
        self.logger.error(f"   Error: {str(error)}")
    
    def log_delegation(self, from_agent: str, to_agent: str, reasoning: str):
        """Log agent delegation."""
        self.logger.info(f"🔄 DELEGATION [Flow-{self.flow_id}]")
        self.logger.info(f"   From: {from_agent}")
        self.logger.info(f"   To: {to_agent}")
        self.logger.info(f"   Reasoning: {reasoning}")

# Initialize the main logger
setup_logger() 