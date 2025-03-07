"""
FastAPI-based REST API for external integrations.
"""
import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..models.schema import DatabaseSchema, DatabaseType
from ..agents.orchestrator_agent import OrchestratorAgent
from ..agents.graph_agent import GraphAgent
from ..agents.llm_agent import LLMAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="VMigrateAgent API",
    description="API for VMigrateAgent - Multi-Agent Database Schema Extraction System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory user database (replace with real database in production)
users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin"),
        "disabled": False,
        "role": "admin"
    }
}

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: str

class UserInDB(User):
    hashed_password: str

class ConnectionRequest(BaseModel):
    connection_string: str
    schema_filter: Optional[List[str]] = None

class AnalysisRequest(BaseModel):
    database_name: str
    analysis_type: str = "dependency"
    target_object: Optional[Dict[str, str]] = None

class SchemaResponse(BaseModel):
    database_name: str
    database_type: str
    tables_count: int
    procedures_count: int
    views_count: int
    dependencies_count: int

# Security functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/extract-schema", response_model=SchemaResponse)
async def extract_schema(
    request: ConnectionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract schema from a database.
    """
    try:
        # Initialize orchestrator agent
        orchestrator = OrchestratorAgent()
        
        # Extract schema
        result = await orchestrator.process({
            "connection_string": request.connection_string,
            "schema_filter": request.schema_filter
        })
        
        schema = result["schema"]
        
        # Store in Neo4j if configured
        try:
            graph_agent = GraphAgent()
            await graph_agent.process({
                "schema": schema,
                "database_name": schema.database_name,
                "database_type": schema.database_type
            })
        except Exception as e:
            logging.error(f"Error storing schema in Neo4j: {str(e)}")
        
        # Return response
        return SchemaResponse(
            database_name=schema.database_name,
            database_type=schema.database_type.value,
            tables_count=len(schema.tables),
            procedures_count=len(schema.procedures),
            views_count=len(schema.views),
            dependencies_count=len(schema.dependencies)
        )
        
    except Exception as e:
        logging.error(f"Error extracting schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/schema/{database_name}", response_model=Dict[str, Any])
async def get_schema(
    database_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get schema for a database.
    """
    try:
        # Initialize graph agent
        graph_agent = GraphAgent()
        
        # Query Neo4j for schema
        # This is a placeholder - in a real implementation, you would query Neo4j
        # and return the schema data
        
        # For now, return a dummy response
        return {
            "database_name": database_name,
            "message": "Schema retrieval from Neo4j not implemented yet"
        }
        
    except Exception as e:
        logging.error(f"Error getting schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/analyze", response_model=Dict[str, Any])
async def analyze_schema(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze schema using LLM.
    """
    try:
        # Initialize LLM agent
        llm_agent = LLMAgent()
        
        # Get schema from Neo4j
        # This is a placeholder - in a real implementation, you would query Neo4j
        # and get the schema data
        
        # For now, return a dummy response
        return {
            "database_name": request.database_name,
            "analysis_type": request.analysis_type,
            "message": "Schema analysis not implemented yet"
        }
        
    except Exception as e:
        logging.error(f"Error analyzing schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/dependencies/{database_name}", response_model=List[Dict[str, Any]])
async def get_dependencies(
    database_name: str,
    object_name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get dependencies for a database or specific object.
    """
    try:
        # Initialize graph agent
        graph_agent = GraphAgent()
        
        # Query Neo4j for dependencies
        # This is a placeholder - in a real implementation, you would query Neo4j
        # and return the dependencies
        
        # For now, return a dummy response
        return [
            {
                "database_name": database_name,
                "message": "Dependency retrieval from Neo4j not implemented yet"
            }
        ]
        
    except Exception as e:
        logging.error(f"Error getting dependencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
