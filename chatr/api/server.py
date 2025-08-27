"""FastAPI web server for ChatR R package integration."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import traceback

from ..core.config import ChatRConfig
from ..core.assistant import ChatRAssistant

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatR API",
    description="API server for ChatR R package integration",
    version="0.1.0"
)

# Global assistant instance
assistant: Optional[ChatRAssistant] = None


class ChatRequest(BaseModel):
    query: str


class AnalyzeRequest(BaseModel):
    code: str


class ChatResponse(BaseModel):
    status: str
    response: Optional[str] = None
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    status: str
    analysis: Optional[str] = None
    error: Optional[str] = None


class DataAnalysisRequest(BaseModel):
    dataset_name: Optional[str] = None
    user_goal: Optional[str] = ""


class DataSummaryRequest(BaseModel):
    dataset_name: str


class CodeGenerationRequest(BaseModel):
    query: str
    mode: str = "interactive"  # "interactive", "script", "execute"
    execute_code: bool = False
    environment_context: Optional[str] = None


class CodeGenerationResponse(BaseModel):
    status: str
    response: Optional[str] = None
    generated_code: Optional[str] = None
    explanation: Optional[str] = None
    error: Optional[str] = None


class DataAnalysisResponse(BaseModel):
    status: str
    response: Optional[str] = None
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize ChatR assistant on startup."""
    global assistant
    
    try:
        config = ChatRConfig.load_config()
        config.setup_directories()
        
        assistant = ChatRAssistant(config)
        assistant.initialize()
        
        logger.info("ChatR API server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize ChatR assistant: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ChatR API"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for R package."""
    
    logger.info(f"Chat request received: {request.query[:100]}...")
    
    if assistant is None:
        logger.error("Assistant not initialized")
        raise HTTPException(status_code=500, detail="Assistant not initialized")
    
    try:
        logger.info("Processing query with assistant...")
        response = assistant.process_query(request.query)
        logger.info(f"Query processed successfully, response length: {len(response)}")
        return ChatResponse(status="success", response=response)
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return ChatResponse(
            status="error", 
            error=str(e)
        )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_code(request: AnalyzeRequest):
    """Code analysis endpoint."""
    
    if assistant is None:
        raise HTTPException(status_code=500, detail="Assistant not initialized")
    
    try:
        result = assistant.process_code_analysis(request.code)
        return AnalyzeResponse(
            status="success", 
            analysis=result.get('analysis', '')
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return AnalyzeResponse(
            status="error",
            error=str(e)
        )


@app.post("/analyze_data", response_model=DataAnalysisResponse)
async def analyze_data(request: DataAnalysisRequest):
    """Data analysis endpoint for smart analysis plans."""
    
    if assistant is None:
        raise HTTPException(status_code=500, detail="Assistant not initialized")
    
    try:
        response = assistant.analyze_my_data(
            dataset_name=request.dataset_name,
            user_goal=request.user_goal or ""
        )
        return DataAnalysisResponse(status="success", response=response)
        
    except Exception as e:
        logger.error(f"Data analysis error: {e}")
        logger.error(traceback.format_exc())
        return DataAnalysisResponse(
            status="error", 
            error=str(e)
        )


@app.post("/data_summary", response_model=DataAnalysisResponse)
async def data_summary(request: DataSummaryRequest):
    """Quick data summary endpoint."""
    
    if assistant is None:
        raise HTTPException(status_code=500, detail="Assistant not initialized")
    
    try:
        response = assistant.quick_data_summary(request.dataset_name)
        return DataAnalysisResponse(status="success", response=response)
        
    except Exception as e:
        logger.error(f"Data summary error: {e}")
        return DataAnalysisResponse(
            status="error", 
            error=str(e)
        )


@app.get("/list_data", response_model=DataAnalysisResponse)
async def list_data():
    """List available data objects endpoint."""
    
    if assistant is None:
        raise HTTPException(status_code=500, detail="Assistant not initialized")
    
    try:
        env_data = assistant.get_environment_data()
        
        if not env_data:
            response = "No data objects found in your R environment."
        else:
            dataset_list = []
            for obj_name, obj_info in env_data.items():
                obj_type = obj_info.get('class', 'unknown')
                if obj_info.get('dimensions'):
                    if isinstance(obj_info['dimensions'], list):
                        dims = f"{obj_info['dimensions'][0]} × {obj_info['dimensions'][1]}"
                    else:
                        dims = f"length {obj_info['dimensions']}"
                else:
                    dims = "unknown size"
                
                dataset_list.append(f"  - **{obj_name}** ({obj_type}, {dims})")
            
            response = f"""# 📊 Available Data Objects

Found {len(env_data)} data object(s) in your R environment:

{chr(10).join(dataset_list)}

Use chatr_analyze("dataset_name") to get analysis plans!"""
        
        return DataAnalysisResponse(status="success", response=response)
        
    except Exception as e:
        logger.error(f"List data error: {e}")
        return DataAnalysisResponse(
            status="error", 
            error=str(e)
        )


@app.post("/generate_code", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Advanced code generation endpoint."""
    
    if assistant is None:
        raise HTTPException(status_code=500, detail="Assistant not initialized")
    
    try:
        result = assistant.generate_advanced_code(
            query=request.query,
            mode=request.mode,
            environment_context=request.environment_context or ""
        )
        
        return CodeGenerationResponse(
            status="success", 
            response=result.get('response', ''),
            generated_code=result.get('code', None),
            explanation=result.get('explanation', None)
        )
        
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        logger.error(traceback.format_exc())
        return CodeGenerationResponse(
            status="error", 
            error=str(e)
        )


@app.get("/status")
async def get_status():
    """Get assistant status."""
    
    if assistant is None:
        return {"status": "not_initialized"}
    
    return assistant.get_status()