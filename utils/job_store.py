# utils/job_store.py
"""
Job persistence for async OCR tasks.
Stores job results in SQLite database and output files.
"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import log

# Database path
DB_PATH = Path("models/jobs.db")
OUTPUT_DIR = Path("examples/output")

# Ensure directories exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def init_db():
    """Initialize the jobs database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            filename TEXT,
            result_text TEXT,
            result_json TEXT,
            output_path TEXT,
            error TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    log.info("Job database initialized")


def save_job(job_id: str, filename: str, status: str = "pending") -> bool:
    """
    Save a new job to the database.
    
    Args:
        job_id: Unique job identifier
        filename: Original filename
        status: Job status (pending, processing, completed, failed)
        
    Returns:
        bool: Success status
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO jobs (job_id, status, created_at, updated_at, filename)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, status, now, now, filename))
        
        conn.commit()
        conn.close()
        
        log.info(f"Job {job_id} saved to database")
        return True
    except Exception as e:
        log.error(f"Failed to save job {job_id}: {e}")
        return False


def update_job(job_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> bool:
    """
    Update job status and results.
    
    Args:
        job_id: Job identifier
        status: New status
        result: Job result data
        error: Error message if failed
        
    Returns:
        bool: Success status
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        # Save result to file if provided
        output_path = None
        result_text = None
        result_json = None
        
        if result:
            # Save text result
            if isinstance(result, dict) and "text" in result:
                result_text = result["text"]
                
                # Save to file
                output_file = OUTPUT_DIR / f"{job_id}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result_text)
                output_path = str(output_file)
            
            # Save full JSON result
            result_json = json.dumps(result)
            json_file = OUTPUT_DIR / f"{job_id}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        
        cursor.execute("""
            UPDATE jobs
            SET status = ?, updated_at = ?, result_text = ?, result_json = ?, output_path = ?, error = ?
            WHERE job_id = ?
        """, (status, now, result_text, result_json, output_path, error, job_id))
        
        conn.commit()
        conn.close()
        
        log.info(f"Job {job_id} updated: {status}")
        return True
    except Exception as e:
        log.error(f"Failed to update job {job_id}: {e}")
        return False


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job details from database.
    
    Args:
        job_id: Job identifier
        
    Returns:
        dict: Job details or None if not found
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            job = dict(row)
            # Parse JSON result
            if job.get("result_json"):
                try:
                    job["result"] = json.loads(job["result_json"])
                except:
                    pass
            return job
        return None
    except Exception as e:
        log.error(f"Failed to get job {job_id}: {e}")
        return None


def list_jobs(limit: int = 100, status: Optional[str] = None) -> list:
    """
    List recent jobs.
    
    Args:
        limit: Maximum number of jobs to return
        status: Filter by status (optional)
        
    Returns:
        list: List of job dictionaries
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT job_id, status, created_at, updated_at, filename, error
                FROM jobs
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT job_id, status, created_at, updated_at, filename, error
                FROM jobs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        log.error(f"Failed to list jobs: {e}")
        return []


def delete_job(job_id: str) -> bool:
    """
    Delete a job and its output files.
    
    Args:
        job_id: Job identifier
        
    Returns:
        bool: Success status
    """
    try:
        # Get job to find output files
        job = get_job(job_id)
        
        # Delete output files
        if job and job.get("output_path"):
            try:
                os.remove(job["output_path"])
            except:
                pass
        
        # Delete JSON file
        json_file = OUTPUT_DIR / f"{job_id}.json"
        if json_file.exists():
            json_file.unlink()
        
        # Delete from database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        conn.commit()
        conn.close()
        
        log.info(f"Job {job_id} deleted")
        return True
    except Exception as e:
        log.error(f"Failed to delete job {job_id}: {e}")
        return False


# Initialize database on import
init_db()
