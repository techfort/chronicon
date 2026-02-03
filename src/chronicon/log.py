"""
Execution log: append-only storage for workflow executions.

Schema (SQLite):
- executions: High-level execution metadata
- steps: Individual step invocations within executions
- llm_calls: LLM-specific metadata for effectful steps

Design:
- Append-only (no updates, no deletes)
- Explicit schema versioning
- Local SQLite database
- One database per project (or configurable)
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Any
from pathlib import Path
from dataclasses import dataclass

from chronicon.serialization import serialize, deserialize
from chronicon.step import StepInvocation, StepKind


# Schema version for migrations
SCHEMA_VERSION = 1


@dataclass
class ExecutionRecord:
    """High-level execution metadata."""
    execution_id: str
    workflow_id: str
    workflow_version: str
    inputs: dict[str, Any]
    output: Optional[Any]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    status: str  # "running", "completed", "failed"


class ExecutionLog:
    """
    Append-only execution log backed by SQLite.
    
    Thread-safe for single-process usage.
    """
    
    def __init__(self, db_path: str = "chronicon.db"):
        """
        Initialize execution log.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threaded access
                isolation_level="IMMEDIATE",  # Prevent locking issues
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_db(self) -> None:
        """Initialize database schema if needed."""
        conn = self._get_conn()
        
        # Create schema version table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)
        
        # Check current version
        cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = cursor.fetchone()
        current_version = row[0] if row else 0
        
        if current_version < SCHEMA_VERSION:
            self._migrate(current_version)
    
    def _migrate(self, from_version: int) -> None:
        """Apply schema migrations."""
        conn = self._get_conn()
        
        if from_version < 1:
            # Initial schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_version TEXT NOT NULL,
                    inputs TEXT NOT NULL,
                    output TEXT,
                    error TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    
                    CHECK (status IN ('running', 'completed', 'failed'))
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_workflow
                ON executions(workflow_id, started_at DESC)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    step_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    step_version TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    inputs TEXT NOT NULL,
                    output TEXT,
                    error TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    
                    FOREIGN KEY (execution_id) REFERENCES executions(execution_id),
                    CHECK (kind IN ('pure', 'effectful'))
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_steps_execution
                ON steps(execution_id, step_index)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_calls (
                    llm_call_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_record_id INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    temperature REAL,
                    max_tokens INTEGER,
                    system TEXT,
                    response_raw TEXT NOT NULL,
                    
                    FOREIGN KEY (step_record_id) REFERENCES steps(step_record_id)
                )
            """)
            
            conn.execute("""
                INSERT INTO schema_version (version, applied_at)
                VALUES (?, ?)
            """, (SCHEMA_VERSION, datetime.utcnow().isoformat()))
            
            conn.commit()
    
    def start_execution(
        self,
        workflow_id: str,
        workflow_version: str,
        inputs: dict[str, Any],
    ) -> str:
        """
        Start a new execution.
        
        Args:
            workflow_id: Workflow identifier
            workflow_version: Workflow version hash
            inputs: Workflow inputs (must be serializable)
            
        Returns:
            execution_id: Unique execution identifier
        """
        execution_id = str(uuid.uuid4())
        conn = self._get_conn()
        
        conn.execute("""
            INSERT INTO executions (
                execution_id,
                workflow_id,
                workflow_version,
                inputs,
                output,
                error,
                started_at,
                completed_at,
                status
            ) VALUES (?, ?, ?, ?, NULL, NULL, ?, NULL, 'running')
        """, (
            execution_id,
            workflow_id,
            workflow_version,
            serialize(inputs),
            datetime.utcnow().isoformat(),
        ))
        
        conn.commit()
        return execution_id
    
    def complete_execution(
        self,
        execution_id: str,
        output: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Mark an execution as completed or failed.
        
        Args:
            execution_id: Execution identifier
            output: Workflow output (if successful)
            error: Error message (if failed)
        """
        conn = self._get_conn()
        
        status = "failed" if error else "completed"
        
        conn.execute("""
            UPDATE executions
            SET output = ?,
                error = ?,
                completed_at = ?,
                status = ?
            WHERE execution_id = ?
        """, (
            serialize(output) if output is not None else None,
            error,
            datetime.utcnow().isoformat(),
            status,
            execution_id,
        ))
        
        conn.commit()
    
    def log_step(
        self,
        execution_id: str,
        step_index: int,
        invocation: StepInvocation,
    ) -> int:
        """
        Log a step invocation.
        
        Args:
            execution_id: Execution identifier
            step_index: Sequential step index in execution
            invocation: Step invocation data
            
        Returns:
            step_record_id: Database record ID for this step
        """
        conn = self._get_conn()
        
        cursor = conn.execute("""
            INSERT INTO steps (
                execution_id,
                step_id,
                step_version,
                kind,
                step_index,
                inputs,
                output,
                error,
                started_at,
                completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            invocation.step_id,
            invocation.step_version,
            invocation.kind.value,
            step_index,
            serialize(invocation.inputs),
            serialize(invocation.output) if invocation.output is not None else None,
            invocation.error,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
        ))
        
        step_record_id = cursor.lastrowid
        
        # Log LLM metadata if present
        if invocation.llm_model:
            conn.execute("""
                INSERT INTO llm_calls (
                    step_record_id,
                    model,
                    prompt,
                    temperature,
                    max_tokens,
                    system,
                    response_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                step_record_id,
                invocation.llm_model,
                invocation.llm_prompt,
                invocation.llm_temperature,
                invocation.llm_max_tokens,
                invocation.llm_prompt,  # system prompt (reusing prompt col for now)
                invocation.llm_response_raw,
            ))
        
        conn.commit()
        return step_record_id
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionRecord]:
        """Get execution metadata by ID."""
        conn = self._get_conn()
        
        cursor = conn.execute("""
            SELECT * FROM executions WHERE execution_id = ?
        """, (execution_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return ExecutionRecord(
            execution_id=row["execution_id"],
            workflow_id=row["workflow_id"],
            workflow_version=row["workflow_version"],
            inputs=deserialize(row["inputs"]),
            output=deserialize(row["output"]) if row["output"] else None,
            error=row["error"],
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            status=row["status"],
        )
    
    def get_steps(self, execution_id: str) -> list[StepInvocation]:
        """Get all step invocations for an execution, in order."""
        conn = self._get_conn()
        
        cursor = conn.execute("""
            SELECT 
                s.*,
                l.model as llm_model,
                l.prompt as llm_prompt,
                l.temperature as llm_temperature,
                l.max_tokens as llm_max_tokens,
                l.response_raw as llm_response_raw
            FROM steps s
            LEFT JOIN llm_calls l ON s.step_record_id = l.step_record_id
            WHERE s.execution_id = ?
            ORDER BY s.step_index ASC
        """, (execution_id,))
        
        invocations = []
        for row in cursor.fetchall():
            invocations.append(StepInvocation(
                step_id=row["step_id"],
                step_version=row["step_version"],
                kind=StepKind(row["kind"]),
                inputs=deserialize(row["inputs"]),
                output=deserialize(row["output"]) if row["output"] else None,
                error=row["error"],
                llm_model=row["llm_model"],
                llm_prompt=row["llm_prompt"],
                llm_temperature=row["llm_temperature"],
                llm_max_tokens=row["llm_max_tokens"],
                llm_response_raw=row["llm_response_raw"],
            ))
        
        return invocations
    
    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
