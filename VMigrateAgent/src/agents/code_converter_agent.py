"""
Agent for converting database queries between different database languages.
"""
import logging
from typing import Optional
import openai
from .base_agent import BaseAgent

class CodeConverterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def validate_query_language(self, language: str) -> bool:
        """
        Validate if the language is a supported database query language.
        
        Args:
            language (str): The database query language to validate
            
        Returns:
            bool: True if supported, False otherwise
        """
        supported_languages = {
            'sql': ['mysql', 'postgresql', 'oracle', 'sql server', 'sqlite'],
            'nosql': ['mongodb', 'cassandra', 'couchdb', 'neo4j'],
            'others': ['graphql', 'sparql']
        }
        
        return any(language.lower() in langs for langs in supported_languages.values())
    
    async def convert_code(self, source_code: str, source_language: str, target_language: str) -> str:
        """
        Convert database query from source language to target language using LLM.
        
        Args:
            source_code (str): The source database query to convert
            source_language (str): The source database query language
            target_language (str): The target database query language
            
        Returns:
            str: The converted query in the target language
        """
        try:
            # Validate languages
            if not self.validate_query_language(source_language):
                raise ValueError(f"Unsupported source database language: {source_language}")
            if not self.validate_query_language(target_language):
                raise ValueError(f"Unsupported target database language: {target_language}")
            
            # Create a prompt for the query conversion
            prompt = f"""
            Convert the following {source_language} query to {target_language}.
            Maintain the same data retrieval/manipulation logic and ensure equivalent functionality.
            Add appropriate comments to explain the query conversion and any specific database features used.
            
            Source query ({source_language}):
            ```{source_language}
            {source_code}
            ```
            
            Convert to {target_language} query:
            """

            # Get response from LLM
            response = await self.llm.agenerate(prompt)
            
            # Extract the converted query
            converted_code = response.strip()
            
            # Log success
            self.logger.info(f"Successfully converted query from {source_language} to {target_language}")
            
            return converted_code
            
        except Exception as e:
            self.logger.error(f"Error converting code: {str(e)}")
            raise Exception(f"Failed to convert code: {str(e)}")
