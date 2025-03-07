"""
Base Agent class that all specialized agents will inherit from.
"""
from abc import ABC, abstractmethod
import logging
import asyncio
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseAgent(ABC):
    """Base agent class that defines the interface for all agents."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name: The name of the agent
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"Agent.{name}")
        self.logger.info(f"Initializing {name} agent")
        
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return the results.
        
        Args:
            data: Input data for the agent to process
            
        Returns:
            Processed data
        """
        pass
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's process method with logging and error handling.
        
        Args:
            data: Input data for the agent to process
            
        Returns:
            Processed data
        """
        self.logger.info(f"{self.name} agent starting execution")
        try:
            result = await self.process(data)
            self.logger.info(f"{self.name} agent completed execution")
            return result
        except Exception as e:
            self.logger.error(f"{self.name} agent encountered an error: {str(e)}", exc_info=True)
            raise
            
    def __str__(self) -> str:
        return f"{self.name} Agent"
