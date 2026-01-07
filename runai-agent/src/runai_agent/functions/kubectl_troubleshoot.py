"""Run:AI kubectl-based comprehensive troubleshooting function"""

import os
import subprocess
from datetime import datetime
from typing import List
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import sanitize_input, _get_secure_runai_config, _search_workload_by_name_helper, logger


class RunaiKubectlTroubleshootConfig(FunctionBaseConfig, name="runai_kubectl_troubleshoot"):
    """Comprehensive kubectl-based troubleshooting for Run:AI jobs"""
    description: str = "Deep troubleshooting for failed jobs using kubectl (logs, events, pod status). Use when jobs fail or need diagnosis."
    include_logs: bool = Field(default=True, description="Include pod logs in output")
    include_events: bool = Field(default=True, description="Include Kubernetes events")
    log_tail_lines: int = Field(default=100, description="Number of log lines to fetch")
    allowed_projects: List[str] = Field(default=["*"], description="Whitelisted projects (use ['*'] for all)")


@register_function(config_type=RunaiKubectlTroubleshootConfig)
async def runai_kubectl_troubleshoot(config: RunaiKubectlTroubleshootConfig, builder: Builder):
    """Comprehensive troubleshooting using kubectl for deep job debugging"""
    
    def get_kubectl_env():
        """Get environment variables for kubectl commands, including KUBECONFIG if set"""
        env = os.environ.copy()
        
        # If KUBECONFIG is set, ensure kubectl uses it
        kubeconfig_path = os.getenv('KUBECONFIG')
        if kubeconfig_path:
            logger.debug(f"Using KUBECONFIG: {kubeconfig_path}")
            env['KUBECONFIG'] = kubeconfig_path
        
        return env
    
    async def _troubleshoot_fn(job_name: str, job_project: str) -> str:
        """
        Comprehensive troubleshooting for a Run:AI job using kubectl.
        
        Args:
            job_name: Name of the job to troubleshoot
            job_project: Run:AI project name (without 'runai-' prefix)
        
        Returns:
            Comprehensive troubleshooting report with logs, events, and diagnosis
        """
        try:
            # Sanitize inputs
            job_name = sanitize_input(job_name, max_length=100)
            job_project = sanitize_input(job_project, max_length=100)
            
            # Validate project whitelist (support wildcard "*")
            if "*" not in config.allowed_projects and job_project not in config.allowed_projects:
                return f"""
❌ **Access Denied**

Project `{job_project}` is not in the allowed list.

**Allowed projects:** {', '.join(config.allowed_projects)}
"""
            
            namespace = f"runai-{job_project}"
            
            logger.info(f"🔍 Troubleshooting job: {job_name} in project: {job_project}")
            
            response = f"""
🔍 **Comprehensive Troubleshooting Report**

**Job:** `{job_name}`
**Project:** `{job_project}`
**Namespace:** `{namespace}`
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
            
            # 1. Get Job Status using existing API logic
            response += "## 📊 Job Status\n\n"
            try:
                status_info = await get_job_status_info(job_name, job_project)
                response += status_info + "\n\n---\n\n"
            except Exception as e:
                response += f"⚠️ Could not fetch job status via API: {str(e)}\n\n---\n\n"
            
            # 2. Get Pod Information
            response += "## 🐳 Pod Information\n\n"
            pod_info = await get_pod_info(job_name, namespace)
            response += pod_info + "\n\n---\n\n"
            
            # 3. Get Pod Logs (if enabled and pod exists)
            if config.include_logs:
                response += "## 📝 Pod Logs\n\n"
                logs = await get_pod_logs(job_name, namespace, config.log_tail_lines)
                response += logs + "\n\n---\n\n"
            
            # 4. Get Kubernetes Events (if enabled)
            if config.include_events:
                response += "## 📢 Kubernetes Events\n\n"
                events = await get_pod_events(job_name, namespace)
                response += events + "\n\n---\n\n"
            
            # 5. AI-Powered Diagnosis
            response += "## 🧠 Diagnosis & Recommendations\n\n"
            diagnosis = analyze_job_issues(pod_info, logs if config.include_logs else "", events if config.include_events else "")
            response += diagnosis + "\n\n---\n\n"
            
            # 6. Helpful Commands
            response += f"""
## 🛠️ Useful Commands

```bash
# Get pod details
kubectl get pods -n {namespace} -l workloadName={job_name}

# Describe pod (detailed info)
kubectl describe pod -n {namespace} -l workloadName={job_name}

# Get logs (last 100 lines)
kubectl logs -n {namespace} -l workloadName={job_name} --tail=100

# Get events
kubectl get events -n {namespace} --field-selector involvedObject.name={job_name}

# Delete job (if needed)
kubectl delete -n {namespace} interactiveworkload {job_name}
# OR for training jobs
kubectl delete -n {namespace} training {job_name}
```
"""
            
            return response
            
        except Exception as e:
            logger.error(f"Error during troubleshooting: {str(e)}")
            return f"""
❌ **Troubleshooting Error**

**Job:** `{job_name}`
**Error:** {str(e)}

**Troubleshooting Steps:**
1. Verify kubectl access: `kubectl get pods -n runai-{job_project}`
2. Check Run:AI API credentials
3. Verify job exists: `runai list jobs -p {job_project}`
4. Check Run:AI UI for job details

**Error Type:** {type(e).__name__}
"""
    
    async def get_job_status_info(job_name: str, job_project: str) -> str:
        """Get job status using Run:AI API"""
        # Reuse logic from runai_job_status
        try:
            from runai.configuration import Configuration
            from runai.api_client import ApiClient
            from runai.runai_client import RunaiClient
            
            secure_config = _get_secure_runai_config()
            configuration = Configuration(
                client_id=secure_config['RUNAI_CLIENT_ID'],
                client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                runai_base_url=secure_config['RUNAI_BASE_URL'],
            )
            client = RunaiClient(ApiClient(configuration))
            
            # Search for workload
            workload_uuid, workload_type = _search_workload_by_name_helper(client, job_name)
            
            if not workload_uuid:
                return f"⚠️ Job `{job_name}` not found in Run:AI API"
            
            # Get workload details using type-specific API calls
            # The Run:AI API uses 'actualPhase' for current status
            phase = "Unknown"
            workload_data = None
            
            # Try to get the workload using the specific type
            type_mapping = {
                'training': lambda: client.workloads.trainings.get_training(workload_uuid),
                'workspace': lambda: client.workloads.workspaces.get_workspace(workload_uuid),
                'distributed': lambda: client.workloads.distributed.get_distributed(workload_uuid),
            }
            
            # If we know the type, try that first; otherwise try all types
            types_to_try = [workload_type.lower()] if workload_type else ['training', 'workspace', 'distributed']
            
            for wtype in types_to_try:
                try:
                    get_fn = type_mapping.get(wtype)
                    if get_fn:
                        response = get_fn()
                        workload_data = response.data if hasattr(response, 'data') else response
                        if workload_data:
                            # Extract actualPhase from the workload data
                            phase = workload_data.get("actualPhase", "Unknown")
                            break
                except Exception:
                    continue
            
            return f"""
✅ **Job Found in Run:AI**
- **UUID:** `{workload_uuid}`
- **Phase:** `{phase}`
- **Type:** {workload_type or 'Run:AI Workload'}
"""
        except Exception as e:
            return f"⚠️ API Status Check Failed: {str(e)}"
    
    async def get_pod_info(job_name: str, namespace: str) -> str:
        """Get pod information using kubectl"""
        try:
            # Get kubectl environment (includes KUBECONFIG if set)
            kubectl_env = get_kubectl_env()
            
            # Check if kubectl is available
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                timeout=5,
                env=kubectl_env
            )
            
            if result.returncode != 0:
                logger.warning(f"kubectl version check failed: {result.stderr}")
                return f"⚠️ `kubectl` is not available or not configured\n\nError: {result.stderr.strip()}"
            
            # Get pod by workload label
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", namespace, 
                 f"-l", f"workloadName={job_name}",
                 "-o", "wide"],
                capture_output=True,
                text=True,
                timeout=10,
                env=kubectl_env
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                return f"""
⚠️ **No pods found for job `{job_name}`**

This could mean:
- Job hasn't created pods yet (Pending/Initializing)
- Job completed and pods were cleaned up
- Job failed before pod creation
- Wrong job name or project
"""
            
            return f"""
**Pods for job `{job_name}`:**

```
{result.stdout}
```
"""
        except FileNotFoundError:
            return "⚠️ `kubectl` command not found - install kubectl for pod inspection"
        except subprocess.TimeoutExpired:
            return "⚠️ kubectl command timed out"
        except Exception as e:
            return f"⚠️ Error getting pod info: {str(e)}"
    
    async def get_pod_logs(job_name: str, namespace: str, tail_lines: int) -> str:
        """Get pod logs using kubectl"""
        try:
            # Get kubectl environment (includes KUBECONFIG if set)
            kubectl_env = get_kubectl_env()
            
            # Get logs by workload label
            result = subprocess.run(
                ["kubectl", "logs", "-n", namespace,
                 "-l", f"workloadName={job_name}",
                 f"--tail={tail_lines}",
                 "--all-containers=true"],
                capture_output=True,
                text=True,
                timeout=30,
                env=kubectl_env
            )
            
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "not found" in stderr.lower() or "no resources found" in stderr.lower():
                    return """
⚠️ **No logs available**

Possible reasons:
- Pod hasn't started yet
- Pod was deleted
- No containers running
- Logs were rotated out
"""
                return f"⚠️ Error fetching logs: {stderr}"
            
            logs_output = result.stdout.strip()
            
            if not logs_output:
                return "ℹ️ No logs generated yet (pod may be starting)"
            
            # Truncate very long logs
            if len(logs_output) > 50000:
                logs_output = logs_output[-50000:] + "\n\n... (logs truncated to last 50KB)"
            
            return f"""
**Last {tail_lines} lines of logs:**

```
{logs_output}
```
"""
        except FileNotFoundError:
            return "⚠️ `kubectl` command not found"
        except subprocess.TimeoutExpired:
            return "⚠️ Log fetch timed out (pod may be generating large logs)"
        except Exception as e:
            return f"⚠️ Error fetching logs: {str(e)}"
    
    async def get_pod_events(job_name: str, namespace: str) -> str:
        """Get Kubernetes events for the job"""
        try:
            # Get kubectl environment (includes KUBECONFIG if set)
            kubectl_env = get_kubectl_env()
            
            # Get events for pods with this workload label
            result = subprocess.run(
                ["kubectl", "get", "events", "-n", namespace,
                 "--field-selector", f"involvedObject.name~={job_name}",
                 "--sort-by='.lastTimestamp'"],
                capture_output=True,
                text=True,
                timeout=10,
                env=kubectl_env
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                # Try alternative: get all recent events and filter
                result = subprocess.run(
                    ["kubectl", "get", "events", "-n", namespace,
                     "--sort-by='.lastTimestamp'",
                     "|", "grep", job_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True,
                    env=kubectl_env
                )
            
            if not result.stdout.strip():
                return """
ℹ️ **No recent events found**

This could mean:
- Job is running normally without issues
- Events have expired (older than 1 hour)
- Job hasn't generated any events yet
"""
            
            events_output = result.stdout.strip()
            
            # Highlight important events
            if any(keyword in events_output.lower() for keyword in ['error', 'failed', 'warning', 'backoff', 'crash']):
                prefix = "⚠️ **ATTENTION: Issues detected in events**\n\n"
            else:
                prefix = "✅ **Events look normal**\n\n"
            
            return f"""
{prefix}**Recent Kubernetes Events:**

```
{events_output}
```
"""
        except FileNotFoundError:
            return "⚠️ `kubectl` command not found"
        except subprocess.TimeoutExpired:
            return "⚠️ Events fetch timed out"
        except Exception as e:
            return f"⚠️ Error fetching events: {str(e)}"
    
    def analyze_job_issues(pod_info: str, logs: str, events: str) -> str:
        """Analyze collected information and provide diagnosis"""
        issues = []
        recommendations = []
        
        # Check pod status
        if "ImagePullBackOff" in pod_info or "ErrImagePull" in pod_info:
            issues.append("🔴 **Image Pull Error** - Cannot pull container image")
            recommendations.append("- Verify image name and tag are correct")
            recommendations.append("- Check image registry credentials")
            recommendations.append("- Ensure image exists in registry")
        
        if "CrashLoopBackOff" in pod_info:
            issues.append("🔴 **Crash Loop** - Container keeps crashing")
            recommendations.append("- Check logs for error messages")
            recommendations.append("- Verify command/entrypoint is correct")
            recommendations.append("- Check for missing dependencies")
            recommendations.append("- Verify environment variables are set")
        
        if "Pending" in pod_info and "Insufficient" in events:
            issues.append("🟡 **Resource Shortage** - Not enough cluster resources")
            recommendations.append("- Reduce GPU/CPU/Memory requests")
            recommendations.append("- Wait for resources to become available")
            recommendations.append("- Check cluster capacity")
        
        if "OOMKilled" in logs or "out of memory" in logs.lower():
            issues.append("🔴 **Out of Memory** - Pod killed due to memory limit")
            recommendations.append("- Increase memory limit in job spec")
            recommendations.append("- Optimize application memory usage")
            recommendations.append("- Check for memory leaks")
        
        if "permission denied" in logs.lower() or "403" in logs:
            issues.append("🟡 **Permission Error** - Access denied")
            recommendations.append("- Check file/directory permissions")
            recommendations.append("- Verify service account permissions")
            recommendations.append("- Check Run:AI project permissions")
        
        if "connection refused" in logs.lower() or "connection timeout" in logs.lower():
            issues.append("🟡 **Network Issue** - Connection problems detected")
            recommendations.append("- Verify service endpoints")
            recommendations.append("- Check network policies")
            recommendations.append("- Verify DNS resolution")
        
        if "no such file or directory" in logs.lower():
            issues.append("🟡 **Missing Files** - Required files not found")
            recommendations.append("- Check volume mounts")
            recommendations.append("- Verify working directory")
            recommendations.append("- Ensure files exist in image")
        
        # Build diagnosis
        if not issues:
            return """
✅ **No Critical Issues Detected**

The job appears to be running normally or the issue requires manual investigation.

**Next Steps:**
1. Review the logs above for application-specific errors
2. Check if the job is making progress
3. Monitor resource usage in Run:AI UI
4. Review job configuration for correctness
"""
        
        diagnosis = "**Issues Detected:**\n\n"
        for issue in issues:
            diagnosis += f"{issue}\n"
        
        diagnosis += "\n**Recommended Actions:**\n\n"
        for idx, rec in enumerate(recommendations, 1):
            diagnosis += f"{idx}. {rec}\n"
        
        diagnosis += "\n**General Troubleshooting:**\n"
        diagnosis += "- Review complete logs above\n"
        diagnosis += "- Check Run:AI UI for additional details\n"
        diagnosis += "- Try resubmitting the job if transient issue\n"
        diagnosis += "- Contact support if issue persists\n"
        
        return diagnosis
    
    try:
        yield FunctionInfo.create(
            single_fn=_troubleshoot_fn,
            description="Deep troubleshooting for failed jobs using kubectl (logs, events, pod status). Use when jobs fail or need diagnosis."
        )
    except GeneratorExit:
        logger.info("Kubectl troubleshoot exited")
    finally:
        logger.info("Cleaning up kubectl troubleshoot")

