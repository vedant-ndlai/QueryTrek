"""
Data models for representing database schema objects.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    SYBASE = "sybase"
    UNKNOWN = "unknown"


class Column(BaseModel):
    """Represents a database column."""
    name: str
    data_type: str
    is_nullable: bool = True
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_unique: bool = False
    character_maximum_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    ordinal_position: int
    comment: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.name} {self.data_type}"


class ForeignKey(BaseModel):
    """Represents a foreign key relationship."""
    name: str
    table_name: str
    column_name: str
    referenced_table_name: str
    referenced_column_name: str
    update_rule: str = "NO ACTION"
    delete_rule: str = "NO ACTION"
    
    def __str__(self) -> str:
        return f"{self.table_name}.{self.column_name} -> {self.referenced_table_name}.{self.referenced_column_name}"


class Index(BaseModel):
    """Represents a database index."""
    name: str
    table_name: str
    column_names: List[str]
    is_unique: bool = False
    is_primary: bool = False
    
    def __str__(self) -> str:
        return f"{self.name} on {self.table_name}({', '.join(self.column_names)})"


class Table(BaseModel):
    """Represents a database table."""
    name: str
    schema: str
    columns: List[Column] = Field(default_factory=list)
    primary_key: Optional[List[str]] = None
    foreign_keys: List[ForeignKey] = Field(default_factory=list)
    indexes: List[Index] = Field(default_factory=list)
    comment: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.schema}.{self.name}"


class StoredProcedure(BaseModel):
    """Represents a stored procedure or function."""
    name: str
    schema: str
    type: str  # 'PROCEDURE' or 'FUNCTION'
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    return_type: Optional[str] = None
    body: str
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.schema}.{self.name}"


class View(BaseModel):
    """Represents a database view."""
    name: str
    schema: str
    definition: str
    columns: List[Column] = Field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.schema}.{self.name}"


class Trigger(BaseModel):
    """Represents a database trigger."""
    name: str
    schema: str
    table_name: str
    event: str  # 'INSERT', 'UPDATE', 'DELETE'
    timing: str  # 'BEFORE', 'AFTER', 'INSTEAD OF'
    body: str
    
    def __str__(self) -> str:
        return f"{self.schema}.{self.name}"


class Dependency(BaseModel):
    """Represents a dependency between database objects."""
    source_type: str  # 'TABLE', 'VIEW', 'PROCEDURE', 'FUNCTION', 'TRIGGER'
    source_name: str
    source_schema: str
    target_type: str
    target_name: str
    target_schema: str
    dependency_type: str  # 'REFERENCES', 'USES', 'TRIGGERS', etc.
    
    def __str__(self) -> str:
        return f"{self.source_schema}.{self.source_name} {self.dependency_type} {self.target_schema}.{self.target_name}"


class DatabaseSchema(BaseModel):
    """Represents the complete schema of a database."""
    database_name: str
    database_type: DatabaseType
    tables: Dict[str, Table] = Field(default_factory=dict)
    views: Dict[str, View] = Field(default_factory=dict)
    procedures: Dict[str, StoredProcedure] = Field(default_factory=dict)
    triggers: Dict[str, Trigger] = Field(default_factory=dict)
    dependencies: List[Dependency] = Field(default_factory=list)
    
    def add_table(self, table: Table) -> None:
        """Add a table to the schema."""
        self.tables[f"{table.schema}.{table.name}"] = table
    
    def add_view(self, view: View) -> None:
        """Add a view to the schema."""
        self.views[f"{view.schema}.{view.name}"] = view
    
    def add_procedure(self, procedure: StoredProcedure) -> None:
        """Add a stored procedure to the schema."""
        self.procedures[f"{procedure.schema}.{procedure.name}"] = procedure
    
    def add_trigger(self, trigger: Trigger) -> None:
        """Add a trigger to the schema."""
        self.triggers[f"{trigger.schema}.{trigger.name}"] = trigger
    
    def add_dependency(self, dependency: Dependency) -> None:
        """Add a dependency to the schema."""
        self.dependencies.append(dependency)
    
    def get_all_objects(self) -> Dict[str, Any]:
        """Get all database objects."""
        return {
            "tables": self.tables,
            "views": self.views,
            "procedures": self.procedures,
            "triggers": self.triggers
        }
    
    def __str__(self) -> str:
        return (f"Database: {self.database_name} ({self.database_type})\n"
                f"Tables: {len(self.tables)}\n"
                f"Views: {len(self.views)}\n"
                f"Procedures: {len(self.procedures)}\n"
                f"Triggers: {len(self.triggers)}\n"
                f"Dependencies: {len(self.dependencies)}")
