"""
LLM Agent for analyzing schema and generating insights using OpenAI API.
"""
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple
import openai
import os

from ..models.schema import DatabaseSchema
from .base_agent import BaseAgent

class LLMAgent(BaseAgent):
    """
    Agent responsible for analyzing schema and generating insights using LLM.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM agent.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__("LLM", config)
        self.api_key = config.get("openai_api_key") if config else os.getenv("OPENAI_API_KEY")
        self.model = config.get("openai_model", "gpt-4-turbo") if config else "gpt-4-turbo"
        
        # Initialize OpenAI client
        if self.api_key:
            openai.api_key = self.api_key
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze schema and generate insights using LLM.
        
        Args:
            data: Dictionary containing:
                - schema: DatabaseSchema object
                - analysis_type: Type of analysis to perform (e.g., "dependency", "optimization")
                
        Returns:
            Dictionary with analysis results
        """
        schema = data.get("schema")
        if not schema:
            raise ValueError("Schema is required")
            
        analysis_type = data.get("analysis_type", "dependency")
        
        self.logger.info(f"Analyzing schema using LLM: {analysis_type}")
        
        # Convert schema to JSON for LLM input
        schema_json = self._schema_to_json(schema)
        
        # Perform analysis based on type
        if analysis_type == "dependency":
            result = await self._analyze_dependencies(schema_json)
        elif analysis_type == "optimization":
            result = await self._analyze_optimization(schema_json)
        elif analysis_type == "impact":
            result = await self._analyze_impact(schema_json, data.get("target_object"))
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        return {
            "analysis_type": analysis_type,
            "result": result
        }
    
    def _schema_to_json(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """
        Convert schema to JSON for LLM input.
        
        Args:
            schema: DatabaseSchema object
            
        Returns:
            JSON representation of schema
        """
        # Create a simplified JSON representation
        result = {
            "database_name": schema.database_name,
            "database_type": schema.database_type.value,
            "tables": [],
            "procedures": [],
            "dependencies": []
        }
        
        # Add tables
        for table_key, table in schema.tables.items():
            table_json = {
                "name": table.name,
                "schema": table.schema,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "is_nullable": col.is_nullable,
                        "is_primary_key": col.is_primary_key
                    }
                    for col in table.columns
                ],
                "foreign_keys": [
                    {
                        "column_name": fk.column_name,
                        "referenced_table_name": fk.referenced_table_name,
                        "referenced_column_name": fk.referenced_column_name
                    }
                    for fk in table.foreign_keys
                ]
            }
            result["tables"].append(table_json)
        
        # Add procedures
        for proc_key, proc in schema.procedures.items():
            proc_json = {
                "name": proc.name,
                "schema": proc.schema,
                "type": proc.type,
                "parameters": proc.parameters,
                "return_type": proc.return_type
            }
            result["procedures"].append(proc_json)
        
        # Add dependencies
        for dep in schema.dependencies:
            dep_json = {
                "source_type": dep.source_type,
                "source_name": dep.source_name,
                "source_schema": dep.source_schema,
                "target_type": dep.target_type,
                "target_name": dep.target_name,
                "target_schema": dep.target_schema,
                "dependency_type": dep.dependency_type
            }
            result["dependencies"].append(dep_json)
        
        return result
    
    async def _analyze_dependencies(self, schema_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependencies in schema.
        
        Args:
            schema_json: JSON representation of schema
            
        Returns:
            Analysis results
        """
        try:
            # Create prompt for dependency analysis
            prompt = self._create_dependency_prompt(schema_json)
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse and return results
            return self._parse_dependency_response(response)
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependencies: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_optimization(self, schema_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze schema for optimization opportunities.
        
        Args:
            schema_json: JSON representation of schema
            
        Returns:
            Analysis results
        """
        try:
            # Create prompt for optimization analysis
            prompt = self._create_optimization_prompt(schema_json)
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse and return results
            return self._parse_optimization_response(response)
            
        except Exception as e:
            self.logger.error(f"Error analyzing optimization: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_impact(self, schema_json: Dict[str, Any], target_object: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze impact of changing a database object.
        
        Args:
            schema_json: JSON representation of schema
            target_object: Object to analyze impact for
            
        Returns:
            Analysis results
        """
        try:
            # Create prompt for impact analysis
            prompt = self._create_impact_prompt(schema_json, target_object)
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse and return results
            return self._parse_impact_response(response)
            
        except Exception as e:
            self.logger.error(f"Error analyzing impact: {str(e)}")
            return {"error": str(e)}
    
    def _create_dependency_prompt(self, schema_json: Dict[str, Any]) -> str:
        """
        Create prompt for dependency analysis.
        
        Args:
            schema_json: JSON representation of schema
            
        Returns:
            Prompt for OpenAI API
        """
        return f"""
        You are a database expert analyzing schema dependencies. 
        
        Here is the database schema in JSON format:
        {json.dumps(schema_json, indent=2)}
        
        Please analyze the dependencies between database objects and provide the following:
        
        1. A summary of the most critical dependencies in the database
        2. Identify any circular dependencies that might cause issues
        3. Identify the most central/important tables in the schema based on dependency relationships
        4. Suggest a logical order for data migration based on dependencies
        
        Format your response as a JSON object with the following structure:
        {{
            "critical_dependencies": [
                {{
                    "source": "schema.object_name",
                    "target": "schema.object_name",
                    "type": "dependency_type",
                    "description": "Description of the dependency"
                }}
            ],
            "circular_dependencies": [
                [
                    "schema.object_name",
                    "schema.object_name",
                    "schema.object_name"
                ]
            ],
            "central_objects": [
                {{
                    "name": "schema.object_name",
                    "type": "object_type",
                    "importance_score": 0.95,
                    "reason": "Reason for importance"
                }}
            ],
            "migration_order": [
                "schema.object_name",
                "schema.object_name"
            ]
        }}
        """
    
    def _create_optimization_prompt(self, schema_json: Dict[str, Any]) -> str:
        """
        Create prompt for optimization analysis.
        
        Args:
            schema_json: JSON representation of schema
            
        Returns:
            Prompt for OpenAI API
        """
        return f"""
        You are a database expert analyzing schema for optimization opportunities. 
        
        Here is the database schema in JSON format:
        {json.dumps(schema_json, indent=2)}
        
        Please analyze the schema and provide the following:
        
        1. Identify potential indexing opportunities for performance improvement
        2. Suggest denormalization opportunities where appropriate
        3. Identify potential schema design issues or anti-patterns
        4. Suggest query optimization strategies based on the schema structure
        
        Format your response as a JSON object with the following structure:
        {{
            "indexing_opportunities": [
                {{
                    "table": "schema.table_name",
                    "columns": ["column1", "column2"],
                    "reason": "Reason for suggesting this index",
                    "impact": "Expected performance impact"
                }}
            ],
            "denormalization_opportunities": [
                {{
                    "tables": ["schema.table1", "schema.table2"],
                    "suggestion": "Detailed suggestion for denormalization",
                    "trade_offs": "Trade-offs to consider"
                }}
            ],
            "design_issues": [
                {{
                    "issue_type": "Issue type (e.g., 'excessive joins', 'poor key design')",
                    "location": "schema.object_name",
                    "description": "Description of the issue",
                    "recommendation": "Recommendation to address the issue"
                }}
            ],
            "query_optimization": [
                {{
                    "pattern": "Query pattern description",
                    "optimization": "Optimization suggestion",
                    "affected_objects": ["schema.object_name"]
                }}
            ]
        }}
        """
    
    def _create_impact_prompt(self, schema_json: Dict[str, Any], target_object: Dict[str, str]) -> str:
        """
        Create prompt for impact analysis.
        
        Args:
            schema_json: JSON representation of schema
            target_object: Object to analyze impact for
            
        Returns:
            Prompt for OpenAI API
        """
        return f"""
        You are a database expert analyzing the impact of changes to a database object. 
        
        Here is the database schema in JSON format:
        {json.dumps(schema_json, indent=2)}
        
        I want to understand the impact of modifying the following object:
        {json.dumps(target_object, indent=2)}
        
        Please analyze the potential impact and provide the following:
        
        1. Identify all objects that directly depend on this object
        2. Identify all objects that indirectly depend on this object (transitive dependencies)
        3. Assess the risk level of modifying this object
        4. Suggest a safe approach to making changes to this object
        
        Format your response as a JSON object with the following structure:
        {{
            "direct_dependencies": [
                {{
                    "name": "schema.object_name",
                    "type": "object_type",
                    "dependency_type": "type of dependency",
                    "impact": "Description of impact"
                }}
            ],
            "indirect_dependencies": [
                {{
                    "name": "schema.object_name",
                    "type": "object_type",
                    "path": ["schema.object1", "schema.object2"],
                    "impact": "Description of impact"
                }}
            ],
            "risk_assessment": {{
                "level": "HIGH|MEDIUM|LOW",
                "factors": [
                    "Factor 1",
                    "Factor 2"
                ]
            }},
            "change_strategy": [
                "Step 1",
                "Step 2"
            ]
        }}
        """
    
    async def _call_openai_api(self, prompt: str) -> str:
        """
        Call OpenAI API.
        
        Args:
            prompt: Prompt for OpenAI API
            
        Returns:
            API response
        """
        try:
            # Check if API key is set
            if not self.api_key:
                raise ValueError("OpenAI API key is not set")
                
            # Call API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a database expert analyzing schema and generating insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Extract and return content
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def _parse_dependency_response(self, response: str) -> Dict[str, Any]:
        """
        Parse dependency analysis response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            Parsed response
        """
        try:
            # Extract JSON from response
            json_str = self._extract_json(response)
            
            # Parse JSON
            result = json.loads(json_str)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing dependency response: {str(e)}")
            return {"error": str(e), "raw_response": response}
    
    def _parse_optimization_response(self, response: str) -> Dict[str, Any]:
        """
        Parse optimization analysis response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            Parsed response
        """
        try:
            # Extract JSON from response
            json_str = self._extract_json(response)
            
            # Parse JSON
            result = json.loads(json_str)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing optimization response: {str(e)}")
            return {"error": str(e), "raw_response": response}
    
    def _parse_impact_response(self, response: str) -> Dict[str, Any]:
        """
        Parse impact analysis response.
        
        Args:
            response: OpenAI API response
            
        Returns:
            Parsed response
        """
        try:
            # Extract JSON from response
            json_str = self._extract_json(response)
            
            # Parse JSON
            result = json.loads(json_str)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing impact response: {str(e)}")
            return {"error": str(e), "raw_response": response}
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text.
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON string
        """
        # Find JSON in text
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No JSON found in response")
            
        return text[start_idx:end_idx + 1]
