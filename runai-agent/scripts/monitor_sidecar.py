#!/usr/bin/env python3
"""
Monitoring Sidecar for Run:AI Agent

This script runs continuously in a sidecar container alongside the main agent,
monitoring Run:AI workloads and recording failures to a shared database.

Usage:
    python monitor_sidecar.py [--poll-interval 60] [--project PROJECT]
"""

# Suppress SyntaxWarnings from Run:AI SDK docstrings (invalid escape sequences in Python 3.13+)
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="runai")

import os
import sys
import asyncio
import argparse
import signal
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from runai_agent.utils import logger, _workload_image

# Phases that indicate a job has finished (success or failure). Recording these to job_run_history
# enables job performance analytics in Kubernetes without requiring "Start proactive monitoring" in chat.
TERMINAL_PHASES = {
    'Succeeded', 'Failed', 'Error', 'Completed',
    'OOMKilled', 'ImagePullBackOff', 'CrashLoopBackOff',
}


class MonitoringSidecar:
    """Manages the monitoring sidecar lifecycle"""
    
    def __init__(self, poll_interval: int = 60, project: str = None):
        self.poll_interval = poll_interval
        self.project = project
        self.running = True
        
        # Handle graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _get_secure_runai_config(self) -> dict:
        """Get Run:AI credentials from environment"""
        return {
            'RUNAI_CLIENT_ID': os.environ.get('RUNAI_CLIENT_ID'),
            'RUNAI_CLIENT_SECRET': os.environ.get('RUNAI_CLIENT_SECRET'),
            'RUNAI_BASE_URL': os.environ.get('RUNAI_BASE_URL')
        }
    
    async def _fetch_workloads(self, client, project: str = None):
        """Fetch workloads from Run:AI"""
        try:
            # Get all workloads (trainings, workspaces, distributed)
            response = await asyncio.to_thread(
                client.workloads.workloads.get_workloads
            )
            
            workloads_data = response.data if hasattr(response, 'data') else response
            workloads = workloads_data.get("workloads", []) if isinstance(workloads_data, dict) else []
            
            # Filter by project if specified
            if project and workloads:
                workloads = [w for w in workloads if w.get('project') == project]
            
            return workloads
        except Exception as e:
            logger.error(f"Error fetching workloads: {e}")
            return []
    
    def _record_job_run_to_history(self, workload, db):
        """Record a completed job (any terminal phase) to job_run_history for performance analytics."""
        job_id = workload.get('id') or workload.get('name', '')
        if not job_id:
            return
        phase = workload.get('phase', workload.get('actualPhase', 'Unknown'))
        ended_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        started_at = workload.get('createdAt')
        image = _workload_image(workload)
        gpu_count = workload.get('requestedGPUs', workload.get('gpuRequestedGPUs', workload.get('gpuCount')))
        try:
            db.record_job_run(
                job_id=str(job_id),
                job_name=workload.get('name', 'unknown'),
                project=workload.get('projectName', workload.get('project', 'unknown')),
                status=phase,
                ended_at=ended_at,
                started_at=started_at,
                image=image,
                gpu_count=int(gpu_count) if gpu_count is not None else None,
            )
        except Exception as e:
            logger.debug(f"Could not record job run history: {e}")

    async def _check_workload(self, workload, client, db):
        """Check a workload for failures and record them"""
        try:
            # Get workload details
            workload_name = workload.get('name', 'unknown')
            project = workload.get('projectName', workload.get('project', 'unknown'))
            
            # Use 'phase' field instead of 'actualPhase' (which is not populated in this API version)
            # Fallback to actualPhase if phase is not available (for API compatibility)
            phase = workload.get('phase', workload.get('actualPhase', 'Unknown'))
            
            logger.info(f"   Checking workload: {workload_name}, phase: '{phase}'")
            
            # Only process actual failure states
            # Valid failure phases from Run:AI API: Failed, Error, ImagePullBackOff, CrashLoopBackOff, OOMKilled
            if phase not in ['Failed', 'Error', 'ImagePullBackOff', 'CrashLoopBackOff', 'OOMKilled']:
                return
            
            # Try to get failure reason (check multiple possible fields)
            failure_reason = workload.get('message') or workload.get('reason') or workload.get('statusMessage') or "Unknown failure"
            
            # Extract node and image for correlation tracking
            node_name = workload.get('nodeName', workload.get('node', 'unknown'))
            container_image = _workload_image(workload) or 'unknown'
            gpu_count = workload.get('gpuRequestedGPUs', workload.get('gpuCount', 0))
            
            # Record failure to database (use correct field names matching schema)
            failure_data = {
                'job_name': workload_name,
                'project': project,
                'failure_type': phase,
                'error_message': failure_reason,
                'node_name': node_name,
                'container_image': container_image,
                'gpu_count': gpu_count,
                'phase': phase,
                'pod_name': workload.get('podName', workload.get('pod', 'unknown'))
            }
            
            failure_id, is_new = db.record_failure(failure_data)
            
            # Update correlations for pattern analysis (only for new failures)
            if is_new:
                if node_name and node_name != 'unknown':
                    db.update_correlation('node', node_name)
                if container_image and container_image != 'unknown':
                    db.update_correlation('image', container_image)
                logger.info(f"   📝 Recorded NEW failure #{failure_id}: {workload_name} ({phase}) on {node_name}")
            else:
                logger.info(f"   🔄 Updated existing failure #{failure_id}: {workload_name} ({phase}) - still failing")
            
        except Exception as e:
            logger.error(f"Error checking workload: {e}")
    
    async def run(self):
        """Run the monitoring loop"""
        logger.info("=" * 80)
        logger.info("Run:AI Monitoring Sidecar Starting")
        logger.info("=" * 80)
        logger.info(f"Configuration:")
        logger.info(f"  - Poll Interval: {self.poll_interval} seconds")
        logger.info(f"  - Project Filter: {self.project or 'All projects'}")
        logger.info(f"  - Database: {os.environ.get('RUNAI_FAILURE_DB_PATH', '/tmp/runai_failure_history.db')}")
        logger.info(f"  - Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # Verify credentials
        required_vars = ['RUNAI_CLIENT_ID', 'RUNAI_CLIENT_SECRET', 'RUNAI_BASE_URL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Sidecar cannot start without Run:AI credentials")
            sys.exit(1)
        
        logger.info(f"✓ Run:AI credentials configured")
        logger.info(f"✓ Cluster: {os.environ.get('RUNAI_BASE_URL')}")
        
        # Check kubeconfig
        if os.environ.get('KUBECONFIG'):
            logger.info(f"✓ Kubeconfig: {os.environ.get('KUBECONFIG')}")
        else:
            logger.info("ℹ️  No KUBECONFIG set (will use in-cluster config)")
        
        try:
            # Import monitoring dependencies
            from runai.configuration import Configuration
            from runai.api_client import ApiClient
            from runai.runai_client import RunaiClient
            from runai_agent.functions.failure_analyzer import FailureDatabase
            
            logger.info("🚀 Starting continuous monitoring...")
            
            # Initialize Run:AI client
            secure_config = self._get_secure_runai_config()
            configuration = Configuration(
                client_id=secure_config['RUNAI_CLIENT_ID'],
                client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                runai_base_url=secure_config['RUNAI_BASE_URL']
            )
            
            api_client = ApiClient(configuration)
            client = RunaiClient(api_client)
            
            # Initialize failure database
            db_path = os.environ.get('RUNAI_FAILURE_DB_PATH', '/data/runai_failure_history.db')
            db = FailureDatabase(db_path)
            logger.info(f"✓ Failure database initialized at {db_path}")
            
            # Monitoring loop
            check_count = 0
            while True:
                check_count += 1
                logger.info(f"🔄 Monitoring check #{check_count} at {datetime.now().strftime('%H:%M:%S')}")
                
                try:
                    # Get all workloads (simplified - just get trainings for now)
                    workloads = await self._fetch_workloads(client, self.project)
                    
                    if not workloads:
                        logger.info("   No workloads found")
                    else:
                        logger.info(f"   Found {len(workloads)} workload(s)")
                        for workload in workloads:
                            phase = workload.get('phase', workload.get('actualPhase', 'Unknown'))
                            # Record all terminal phases to job_run_history (for job performance analytics)
                            if phase in TERMINAL_PHASES:
                                self._record_job_run_to_history(workload, db)
                            # Record failures to failure_events and run auto-troubleshoot
                            if phase in ['Failed', 'Error', 'ImagePullBackOff', 'CrashLoopBackOff', 'OOMKilled']:
                                await self._check_workload(workload, client, db)
                
                except asyncio.CancelledError:
                    logger.info("Monitoring cancelled")
                    break
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    logger.info("Continuing monitoring...")
                
                # Sleep until next check
                await asyncio.sleep(self.poll_interval)
        
        except Exception as e:
            logger.error(f"Fatal error in monitoring sidecar: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
        
        finally:
            logger.info("=" * 80)
            logger.info("Monitoring Sidecar Stopped")
            logger.info(f"Stop Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run:AI Monitoring Sidecar - Continuous workload monitoring'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=60,
        help='Polling interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default=None,
        help='Specific project to monitor (default: all projects)'
    )
    
    args = parser.parse_args()
    
    # Create and run sidecar
    sidecar = MonitoringSidecar(
        poll_interval=args.poll_interval,
        project=args.project
    )
    
    # Run async loop
    asyncio.run(sidecar.run())


if __name__ == '__main__':
    main()

