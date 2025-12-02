"""
Supabase logger for batch simulation results.
Handles batch inserts to avoid API rate limits.
Supports time-series data and distributed job queue management.
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://lfktihxrcaqxzbcoiruj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Initialize Supabase client
supabase: Client = None

def init_supabase():
    """Initialize Supabase client."""
    global supabase
    if not supabase:
        if not SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY environment variable is not set")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_batch_result(data: Dict[str, Any]) -> Optional[str]:
    """Log a single simulation result."""
    init_supabase()
    try:
        result = supabase.table("simulation_batch_runs").insert(data).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]['id']
        return None
    except Exception as e:
        print(f"Error logging batch result: {e}")
        return None

def log_time_series(data: List[Dict[str, Any]]):
    """Log time-series data snapshots."""
    init_supabase()
    if not data:
        return
    try:
        # Insert in batches
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            supabase.table("simulation_time_series").insert(batch).execute()
    except Exception as e:
        print(f"Error logging time series data: {e}")

def log_human_match(data: Dict[str, Any]):
    """Log a human vs AI match result."""
    init_supabase()
    try:
        supabase.table("human_matches").insert(data).execute()
    except Exception as e:
        print(f"Error logging human match: {e}")

# --- JOB QUEUE MANAGEMENT ---

def fetch_pending_job(machine_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and lock a pending job from the queue.
    
    Args:
        machine_id: ID of the worker machine
        
    Returns:
        Job dictionary or None if no jobs available
    """
    init_supabase()
    try:
        # 1. Find a pending job (RPC would be better for atomicity, but this works for simple cases)
        # We fetch one pending job
        response = supabase.table("simulation_queue") \
            .select("*") \
            .eq("status", "pending") \
            .limit(1) \
            .execute()
        
        if not response.data:
            return None
            
        job = response.data[0]
        job_id = job['id']
        
        # 2. Try to lock it
        update_response = supabase.table("simulation_queue") \
            .update({
                "status": "processing",
                "assigned_to": machine_id,
                "started_at": datetime.now(timezone.utc).isoformat()
            }) \
            .eq("id", job_id) \
            .eq("status", "pending") \
            .select() \
            .execute()
            
        # If update returned data, we successfully locked it
        if update_response.data:
            return update_response.data[0]
        else:
            # Someone else grabbed it, try again (recursive or return None)
            return None
            
    except Exception as e:
        print(f"Error fetching job: {e}")
        return None

def complete_job(job_id: str, result_data: Dict[str, Any] = None):
    """Mark a job as completed."""
    init_supabase()
    try:
        supabase.table("simulation_queue") \
            .update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }) \
            .eq("id", job_id) \
            .execute()
            
    except Exception as e:
        print(f"Error completing job: {e}")

def fail_job(job_id: str, error_msg: str):
    """Mark a job as failed."""
    init_supabase()
    try:
        supabase.table("simulation_queue") \
            .update({
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }) \
            .eq("id", job_id) \
            .execute()
    except Exception as e:
        print(f"Error failing job: {e}")

# --- GENETIC ALGORITHM ---

def fetch_genome_weights(genome_id: str) -> Optional[Dict[str, Any]]:
    """Fetch weights for a specific genome."""
    init_supabase()
    try:
        response = supabase.table("simulation_genomes") \
            .select("weights") \
            .eq("id", genome_id) \
            .single() \
            .execute()
        
        if response.data:
            return response.data['weights']
        return None
    except Exception as e:
        print(f"Error fetching genome: {e}")
        return None

def update_genome_fitness(genome_id: str, fitness: float):
    """Update the fitness score of a genome."""
    init_supabase()
    try:
        supabase.table("simulation_genomes") \
            .update({"fitness_score": fitness}) \
            .eq("id", genome_id) \
            .execute()
    except Exception as e:
        print(f"Error updating genome fitness: {e}")
