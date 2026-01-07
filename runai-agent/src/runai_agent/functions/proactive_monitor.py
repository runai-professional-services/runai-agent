"""
Proactive Job Monitoring & Auto-Troubleshooting

Continuously monitors Run:AI workloads and automatically troubleshoots failures.
Sends notifications when issues are detected.
"""

import os
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import _get_secure_runai_config, logger


class RunaiProactiveMonitorConfig(FunctionBaseConfig, name="runai_proactive_monitor"):
    """Configuration for proactive job monitoring and auto-troubleshooting"""
    description: str = (
        "Proactively monitor Run:AI workloads and auto-troubleshoot failures. "
        "Continuously checks job status and alerts on failures."
    )
    
    # Monitoring configuration
    monitored_projects: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Projects to monitor (use ['*'] for all projects)"
    )
    
    poll_interval_seconds: int = Field(
        default=60,
        description="How often to check job status (default: 60 seconds)"
    )
    
    # Notification configuration
    slack_webhook_url: Optional[str] = Field(
        default=None,
        description="Slack webhook URL for failure notifications (optional)"
    )
    
    enable_auto_troubleshoot: bool = Field(
        default=True,
        description="Automatically run troubleshooting when failures detected"
    )
    
    # Filter configuration
    monitor_only_failed: bool = Field(
        default=False,
        description="Only monitor/report failed jobs (ignore running/completed)"
    )
    
    max_alerts_per_job: int = Field(
        default=1,
        description="Maximum alerts to send per job (prevents spam)"
    )


@register_function(config_type=RunaiProactiveMonitorConfig)
async def runai_proactive_monitor(config: RunaiProactiveMonitorConfig, builder: Builder):
    """
    Proactive monitoring and auto-troubleshooting for Run:AI workloads.
    
    This function continuously monitors jobs and:
    1. Polls job status at configured intervals
    2. Detects failures and status changes
    3. Auto-troubleshoots failed jobs
    4. Sends notifications via Slack (optional)
    
    Use cases:
    - "Monitor all jobs in project ml-team"
    - "Watch for failures and alert on Slack"
    - "Continuously check job status and auto-troubleshoot"
    
    Parameters:
    - action: "start" to begin monitoring, "status" to check current monitored jobs
    - project: Optional project name to monitor (defaults to all projects)
    - duration_minutes: How long to monitor (default: continuous until stopped)
    """
    
    # Check if Run:AI SDK is available
    try:
        from runai.configuration import Configuration
        from runai.api_client import ApiClient
        from runai.runai_client import RunaiClient
        SDK_AVAILABLE = True
        logger.debug("✓ Run:AI SDK is available")
    except ImportError:
        SDK_AVAILABLE = False
        logger.warning("⚠️ Run:AI SDK not installed. Monitoring will be limited.")
    
    # Track alerted jobs to prevent spam
    _alerted_jobs: Dict[str, int] = {}  # job_uuid -> alert_count
    
    async def _monitor_fn(
        action: str = "start",
        project: Optional[str] = None,
        duration_minutes: int = 0
    ) -> str:
        """
        Start or check status of proactive monitoring
        
        Args:
            action: "start" to begin monitoring, "status" to check state
            project: Optional specific project to monitor (None = all projects)
            duration_minutes: How long to monitor (0 = continuous)
            
        Returns:
            Status message or monitoring report
        """
        
        if action == "status":
            return f"""
📊 **Monitoring Status**

**Configuration:**
- Projects: {', '.join(config.monitored_projects) if config.monitored_projects else 'All'}
- Poll Interval: {config.poll_interval_seconds} seconds
- Auto-Troubleshoot: {'Enabled ✅' if config.enable_auto_troubleshoot else 'Disabled'}
- Slack Alerts: {'Enabled ✅' if config.slack_webhook_url else 'Disabled'}
- Jobs Alerted: {len(_alerted_jobs)}

**Note:** Monitoring runs in the background. Use action="start" to begin.
"""
        
        if action == "start":
            return await _start_monitoring(project, duration_minutes)
        
        return f"❌ Invalid action '{action}'. Use 'start' or 'status'."
    
    async def _start_monitoring(
        project_filter: Optional[str],
        duration_minutes: int
    ) -> str:
        """Start the monitoring loop"""
        
        if not SDK_AVAILABLE:
            return """
⚠️ **Run:AI SDK Not Available**

Monitoring requires the Run:AI SDK to be installed.

Install with:
```bash
pip install runai-sdk
```
"""
        
        logger.info(f"🚀 Starting proactive monitoring...")
        logger.info(f"   Projects: {project_filter or 'ALL'}")
        logger.info(f"   Poll interval: {config.poll_interval_seconds}s")
        logger.info(f"   Duration: {duration_minutes}m" if duration_minutes else "   Duration: Continuous")
        
        start_time = datetime.now()
        check_count = 0
        failures_detected = 0
        
        try:
            # Initialize Run:AI client
            secure_config = _get_secure_runai_config()
            configuration = Configuration(
                client_id=secure_config['RUNAI_CLIENT_ID'],
                client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                runai_base_url=secure_config['RUNAI_BASE_URL']
            )
            
            api_client = ApiClient(configuration)
            client = RunaiClient(api_client)
            
            # Start monitoring loop
            while True:
                check_count += 1
                logger.info(f"🔄 Monitoring check #{check_count} at {datetime.now().strftime('%H:%M:%S')}")
                
                # Get all workloads
                try:
                    workloads = await _fetch_workloads(client, project_filter)
                    
                    if not workloads:
                        logger.info("   No workloads found")
                    else:
                        logger.info(f"   Found {len(workloads)} workload(s)")
                        
                        # Check each workload
                        for workload in workloads:
                            await _check_workload(workload, client, builder)
                
                except Exception as e:
                    logger.error(f"Error fetching workloads: {e}")
                
                # Check if we should stop (duration limit)
                if duration_minutes > 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        logger.info(f"✅ Monitoring duration reached ({duration_minutes} minutes)")
                        break
                
                # Sleep until next check
                await asyncio.sleep(config.poll_interval_seconds)
            
            return f"""
✅ **Monitoring Session Complete**

**Duration:** {(datetime.now() - start_time).total_seconds() / 60:.1f} minutes
**Checks Performed:** {check_count}
**Failures Detected:** {failures_detected}
**Jobs Alerted:** {len(_alerted_jobs)}
"""
        
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            return f"""
❌ **Monitoring Failed**

**Error:** {str(e)}

**Checks Completed:** {check_count}
**Failures Detected:** {failures_detected}
"""
    
    async def _fetch_workloads(
        client,
        project_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch all workloads from Run:AI API"""
        
        try:
            # Get all workloads (training, workspace, distributed)
            response = client.workloads.workloads.get_workloads()
            workloads_data = response.data if hasattr(response, 'data') else response
            all_workloads = workloads_data.get("workloads", []) if isinstance(workloads_data, dict) else []
            
            # Filter by project if specified
            if project_filter and project_filter != "*":
                # Determine which projects to monitor
                if "*" in config.monitored_projects:
                    # Monitor all projects
                    filtered = all_workloads
                else:
                    # Only monitor whitelisted projects
                    filtered = [
                        w for w in all_workloads 
                        if w.get("projectName") in config.monitored_projects
                    ]
                
                # Further filter by specific project if requested
                if project_filter:
                    filtered = [w for w in filtered if w.get("projectName") == project_filter]
                
                return filtered
            else:
                # Apply project whitelist
                if "*" in config.monitored_projects:
                    return all_workloads
                else:
                    return [
                        w for w in all_workloads 
                        if w.get("projectName") in config.monitored_projects
                    ]
        
        except Exception as e:
            logger.error(f"Error fetching workloads: {e}")
            return []
    
    async def _check_workload(
        workload: Dict[str, Any],
        client,
        builder: Builder
    ):
        """Check a single workload and take action if needed"""
        
        job_name = workload.get("name", "unknown")
        job_uuid = workload.get("id", "")
        job_project = workload.get("projectName", "unknown")
        
        # Use 'phase' field instead of 'actualPhase' (which is not populated in this API version)
        # Fallback to actualPhase if phase is not available (for API compatibility)
        phase = workload.get("phase", workload.get("actualPhase", "Unknown"))
        job_type = workload.get("type", "unknown")
        
        logger.info(f"   Checking: {job_name} (project={job_project}, phase={phase})")
        
        # Skip if we're only monitoring failed jobs and this isn't failed
        if config.monitor_only_failed and phase not in ["Failed", "Error", "ImagePullBackOff", "CrashLoopBackOff", "OOMKilled"]:
            return
        
        # Detect failures - Only detect actual failure states reported by Run:AI API
        # Valid failure phases: Failed, Error, ImagePullBackOff, CrashLoopBackOff, OOMKilled
        is_failure = phase in ["Failed", "Error", "ImagePullBackOff", "CrashLoopBackOff", "OOMKilled"]
        
        if is_failure:
            logger.warning(f"🔴 FAILURE DETECTED: {job_name} in {job_project} - Phase: {phase}")
            
            # Check if we've already alerted for this job
            if job_uuid in _alerted_jobs:
                if _alerted_jobs[job_uuid] >= config.max_alerts_per_job:
                    logger.debug(f"   Skipping alert (already sent {_alerted_jobs[job_uuid]} alerts)")
                    return
                _alerted_jobs[job_uuid] += 1
            else:
                _alerted_jobs[job_uuid] = 1
            
            # Auto-troubleshoot if enabled
            troubleshoot_report = None
            pod_info = {}
            if config.enable_auto_troubleshoot:
                logger.info(f"🔧 Auto-troubleshooting {job_name}...")
                try:
                    troubleshoot_report, pod_info = await _auto_troubleshoot(
                        job_name, 
                        job_project, 
                        builder
                    )
                except Exception as e:
                    logger.error(f"Auto-troubleshoot failed: {e}")
                    troubleshoot_report = f"⚠️ Auto-troubleshoot error: {str(e)}"
            
            # Record failure to database for pattern analysis
            try:
                await _record_failure_to_db(
                    job_name=job_name,
                    job_project=job_project,
                    phase=phase,
                    workload=workload,
                    pod_info=pod_info,
                    troubleshoot_report=troubleshoot_report
                )
            except Exception as e:
                logger.error(f"Failed to record failure to database: {e}")
            
            # Send notification
            await _send_alert(
                job_name=job_name,
                job_project=job_project,
                job_type=job_type,
                phase=phase,
                job_uuid=job_uuid,
                troubleshoot_report=troubleshoot_report
            )
    
    async def _auto_troubleshoot(
        job_name: str,
        job_project: str,
        builder: Builder
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Run auto-troubleshooting using kubectl to get pod logs and events
        
        This provides:
        - Pod status and conditions
        - Container logs (last 50 lines)
        - Kubernetes events
        
        Returns:
            Tuple of (report_string, pod_info_dict)
        """
        
        pod_info = {
            "pod_name": None,
            "node_name": None,
            "container_image": None,
            "logs_snippet": None,
            "events_snippet": None
        }
        
        try:
            import subprocess
            
            namespace = f"runai-{job_project}"
            env = os.environ.copy()
            
            report = f"🔍 Auto-Troubleshoot Report for {job_name}\n\n"
            
            # Get pod name
            try:
                result = subprocess.run(
                    ["kubectl", "get", "pods", "-n", namespace, "-l", f"workloadName={job_name}", "-o", "name"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env
                )
                pod_name = result.stdout.strip().replace("pod/", "")
                pod_info["pod_name"] = pod_name
                
                if pod_name:
                    # Get pod status with JSON output for parsing
                    result_json = subprocess.run(
                        ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "json"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=env
                    )
                    
                    # Parse pod info
                    try:
                        import json
                        pod_data = json.loads(result_json.stdout)
                        pod_info["node_name"] = pod_data.get("spec", {}).get("nodeName")
                        containers = pod_data.get("spec", {}).get("containers", [])
                        if containers:
                            pod_info["container_image"] = containers[0].get("image")
                    except:
                        pass
                    
                    # Get pod status (human-readable)
                    result = subprocess.run(
                        ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "wide"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=env
                    )
                    report += f"## Pod Status:\n```\n{result.stdout}\n```\n\n"
                    
                    # Get logs
                    result = subprocess.run(
                        ["kubectl", "logs", pod_name, "-n", namespace, "--tail=50"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=env
                    )
                    logs_output = result.stdout[:1000]
                    pod_info["logs_snippet"] = logs_output
                    report += f"## Logs (last 50 lines):\n```\n{logs_output}\n```\n\n"
                    
                    # Get events
                    result = subprocess.run(
                        ["kubectl", "get", "events", "-n", namespace, "--field-selector", f"involvedObject.name={pod_name}", "--sort-by='.lastTimestamp'"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=env
                    )
                    events_output = result.stdout[:1000]
                    pod_info["events_snippet"] = events_output
                    report += f"## Events:\n```\n{events_output}\n```\n"
                else:
                    report += "⚠️ No pod found for this workload\n"
            
            except subprocess.TimeoutExpired:
                report += "⚠️ kubectl command timed out\n"
            except Exception as e:
                report += f"⚠️ kubectl error: {str(e)}\n"
            
            return report, pod_info
        
        except Exception as e:
            logger.error(f"Auto-troubleshoot error: {e}")
            return f"⚠️ Troubleshooting failed: {str(e)}", pod_info
    
    async def _record_failure_to_db(
        job_name: str,
        job_project: str,
        phase: str,
        workload: Dict[str, Any],
        pod_info: Dict[str, Any],
        troubleshoot_report: Optional[str] = None
    ):
        """Record failure event to database for pattern analysis"""
        try:
            # Import failure database
            from .failure_analyzer import FailureDatabase
            
            # Get database path from config or use default
            db_path = os.environ.get('RUNAI_FAILURE_DB_PATH', '/tmp/runai_failure_history.db')
            db = FailureDatabase(db_path)
            
            # Extract error message from logs if available
            error_message = None
            if pod_info.get('logs_snippet'):
                # Try to extract error from last few lines
                log_lines = pod_info['logs_snippet'].split('\n')
                for line in reversed(log_lines[-10:]):
                    if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception', 'fatal']):
                        error_message = line.strip()[:500]  # Limit length
                        break
            
            # Prepare failure data
            failure_data = {
                'job_name': job_name,
                'project': job_project,
                'failure_type': phase,
                'phase': phase,
                'pod_name': pod_info.get('pod_name'),
                'node_name': pod_info.get('node_name'),
                'container_image': pod_info.get('container_image'),
                'error_message': error_message,
                'logs_snippet': pod_info.get('logs_snippet', '')[:2000] if pod_info.get('logs_snippet') else None,
                'events_snippet': pod_info.get('events_snippet', '')[:2000] if pod_info.get('events_snippet') else None,
                'gpu_count': workload.get('requestedGPUs', 0),
                'memory_request': workload.get('requestedMemory'),
                'cpu_request': workload.get('requestedCPU')
            }
            
            # Record to database
            failure_id, is_new = db.record_failure(failure_data)
            
            if is_new:
                logger.info(f"✓ Recorded NEW failure #{failure_id} to database for pattern analysis")
                # Update correlations only for new failures
                if pod_info.get('node_name'):
                    db.update_correlation('node', pod_info['node_name'])
                if pod_info.get('container_image'):
                    db.update_correlation('image', pod_info['container_image'])
            else:
                logger.info(f"🔄 Updated existing failure #{failure_id} (still failing, within 1 hour window)")
            
        except Exception as e:
            logger.error(f"Failed to record failure to database: {e}")
            # Don't let database errors break the monitoring
    
    async def _send_alert(
        job_name: str,
        job_project: str,
        job_type: str,
        phase: str,
        job_uuid: str,
        troubleshoot_report: Optional[str] = None
    ):
        """Send alert notification about job failure"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build alert message
        alert_title = f"🔴 Job Failure Alert: {job_name}"
        alert_body = f"""
**Project:** {job_project}
**Job Name:** {job_name}
**Type:** {job_type}
**Status:** {phase}
**Time:** {timestamp}
**UUID:** {job_uuid}
"""
        
        if troubleshoot_report:
            alert_body += f"\n**Auto-Troubleshoot Report:**\n{troubleshoot_report[:1000]}..."  # Truncate for Slack
        
        # Log locally
        logger.warning("=" * 80)
        logger.warning(alert_title)
        logger.warning("=" * 80)
        logger.warning(alert_body)
        logger.warning("=" * 80)
        
        # Send to Slack if configured
        if config.slack_webhook_url:
            await _send_slack_notification(alert_title, alert_body)
    
    async def _send_slack_notification(title: str, message: str):
        """Send notification to Slack webhook"""
        
        if not config.slack_webhook_url:
            logger.debug("Slack webhook not configured, skipping notification")
            return
        
        try:
            payload = {
                "text": title,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": title
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.slack_webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Slack notification sent successfully")
                    else:
                        logger.warning(f"⚠️ Slack notification failed: HTTP {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    # Yield the monitoring function
    yield FunctionInfo.from_fn(
        _monitor_fn,
        description=(
            "Proactively monitor Run:AI workloads and auto-troubleshoot failures. "
            "Continuously checks job status at configured intervals and sends alerts when failures are detected. "
            "\n\n"
            "Required parameters:\n"
            "- action: 'start' to begin monitoring, 'status' to check configuration\n"
            "\n"
            "Optional parameters:\n"
            "- project: Specific project to monitor (default: all monitored projects)\n"
            "- duration_minutes: How long to monitor (default: 0 = continuous)\n"
            "\n"
            "Examples:\n"
            "- Start monitoring all projects: action='start'\n"
            "- Monitor specific project for 30 mins: action='start', project='ml-team', duration_minutes=30\n"
            "- Check monitoring status: action='status'"
        )
    )
    
    # Cleanup
    logger.info("Cleaning up proactive monitor")

