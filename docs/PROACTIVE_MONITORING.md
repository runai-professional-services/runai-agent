# Proactive Monitoring & Auto-Troubleshooting

## Overview

The **Proactive Monitoring** feature continuously monitors Run:AI workloads and automatically troubleshoots failures in real-time. It provides:

- ✅ **Continuous Job Monitoring**: Polls job status at configurable intervals
- 🔧 **Auto-Troubleshooting**: Automatically diagnoses failed jobs with detailed reports
- 🔔 **Slack Notifications**: Optional alerts sent to Slack webhooks
- 🎯 **Smart Filtering**: Monitor all jobs or only failures
- 🚫 **Anti-Spam**: Configurable alert limits per job

## Configuration

### Basic Setup (workflow.yaml)

```yaml
runai_proactive_monitor:
  _type: runai_proactive_monitor
  description: "Proactively monitor Run:AI workloads and auto-troubleshoot failures"
  
  # Projects to monitor (* = all)
  monitored_projects: ["*"]
  
  # How often to check (seconds)
  poll_interval_seconds: 60
  
  # Auto-troubleshoot failures
  enable_auto_troubleshoot: true
  
  # Monitor all jobs or only failures
  monitor_only_failed: false
  
  # Max alerts per job (prevent spam)
  max_alerts_per_job: 1
  
  # Optional Slack webhook
  # slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Environment Variables

The monitoring function uses the same Run:AI credentials as other functions:

```bash
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="https://your-cluster.run.ai"
export KUBECONFIG="/path/to/kubeconfig"  # For kubectl troubleshooting
```

## Usage Examples

### Start Monitoring All Jobs

```bash
# Through the agent
"Start monitoring all jobs in the cluster"
```

**What happens:**
- Polls all workloads every 60 seconds (configurable)
- Detects failures (Failed, Error, ImagePullBackOff, OOMKilled, etc.)
- Automatically troubleshoots failed jobs
- Logs alerts and sends to Slack (if configured)

### Monitor Specific Project

```bash
"Monitor jobs in project ml-team"
```

**What happens:**
- Only monitors workloads in the `ml-team` project
- Same auto-troubleshooting and alerting

### Monitor for Limited Time

```bash
"Monitor all jobs for 30 minutes"
```

**What happens:**
- Runs monitoring for 30 minutes then stops
- Useful for temporary monitoring sessions

### Check Monitoring Status

```bash
"What is the monitoring status?"
```

**Returns:**
- Current configuration
- Number of alerts sent
- Active monitoring state

## How It Works

### Monitoring Loop

```
1. Fetch all workloads from Run:AI API
   ↓
2. Filter by project whitelist
   ↓
3. Check each workload's status
   ↓
4. Detect failures (Failed, Error, ImagePullBackOff, etc.)
   ↓
5. Auto-troubleshoot (if enabled)
   ↓
6. Send alerts (Slack + logs)
   ↓
7. Sleep for poll_interval_seconds
   ↓
8. Repeat from step 1
```

### Auto-Troubleshooting

When a failure is detected, the monitor automatically:

1. **Fetches job status** from Run:AI API
2. **Gets pod information** via kubectl
3. **Collects logs** (last 100 lines)
4. **Analyzes Kubernetes events**
5. **Generates diagnosis** with recommendations

### Alert System

**Alert Contents:**
- Job name, project, type
- Failure status (Failed, OOMKilled, ImagePullBackOff, etc.)
- Timestamp and UUID
- Truncated troubleshooting report

**Alert Destinations:**
- **Console logs**: Always logged
- **Slack**: If `slack_webhook_url` is configured

**Anti-Spam:**
- Max alerts per job (`max_alerts_per_job: 1`)
- Prevents repeated alerts for same failure

## Slack Integration

### Setup Slack Webhook

1. Create a Slack app: https://api.slack.com/apps
2. Enable "Incoming Webhooks"
3. Add webhook to workspace
4. Copy webhook URL (e.g., `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)

### Configure in workflow.yaml

```yaml
runai_proactive_monitor:
  slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Slack Alert Format

```
🔴 Job Failure Alert: my-training-job

**Project:** ml-team
**Job Name:** my-training-job
**Type:** training
**Status:** OOMKilled
**Time:** 2025-12-04 10:30:15
**UUID:** a1b2c3d4-e5f6-7890-abcd-ef1234567890

**Auto-Troubleshoot Report:**
🔍 Comprehensive Troubleshooting Report
...
```

## Example Scenarios

### Scenario 1: Monitor ML Training Pipeline

```python
# User query
"Start monitoring ml-team project jobs"

# Agent calls
runai_proactive_monitor(
    action="start",
    project="ml-team",
    duration_minutes=0  # Continuous
)

# Result
# - Monitors all ml-team workloads
# - Auto-troubleshoots failures
# - Alerts on Slack when jobs fail
```

### Scenario 2: Temporary Monitoring Session

```python
# User query
"Monitor all jobs for the next hour"

# Agent calls
runai_proactive_monitor(
    action="start",
    duration_minutes=60
)

# Result
# - Monitors for 60 minutes
# - Stops automatically after 1 hour
```

### Scenario 3: Only Monitor Failures

```yaml
# Configuration
runai_proactive_monitor:
  monitor_only_failed: true  # Only check failed jobs
```

```python
# User query
"Monitor for job failures"

# Agent calls
runai_proactive_monitor(action="start")

# Result
# - Only processes failed/error jobs
# - Ignores running/completed jobs (faster)
```

## Advanced Configuration

### Multiple Projects

```yaml
monitored_projects: ["ml-team", "data-science", "research"]
```

### High-Frequency Monitoring

```yaml
poll_interval_seconds: 30  # Check every 30 seconds
```

### Disable Auto-Troubleshoot

```yaml
enable_auto_troubleshoot: false  # Only alert, don't troubleshoot
```

### Multiple Alerts Per Job

```yaml
max_alerts_per_job: 3  # Allow up to 3 alerts per job
```

## Troubleshooting

### Monitor Not Starting

**Check:**
1. Run:AI credentials are set (`RUNAI_CLIENT_ID`, `RUNAI_CLIENT_SECRET`, `RUNAI_BASE_URL`)
2. Run:AI SDK is installed (`pip install runai-sdk`)
3. Function is registered in `workflow.yaml`

### Slack Notifications Not Sending

**Check:**
1. Webhook URL is correct
2. Slack app has permissions
3. Check logs for HTTP errors

### No Jobs Detected

**Check:**
1. Project whitelist (`monitored_projects`)
2. Jobs actually exist in Run:AI
3. Check logs for API errors

## Performance Considerations

- **Poll Interval**: Lower intervals = more API calls (use 60s for production)
- **Project Filtering**: Narrow scope reduces API load
- **Auto-Troubleshoot**: Adds kubectl overhead (disable if not needed)
- **Slack Webhooks**: Minimal overhead (~10ms per alert)

## Security Best Practices

1. **Store credentials in environment variables** (never hardcode)
2. **Use project whitelisting** (`monitored_projects`) to limit scope
3. **Rotate Slack webhook URLs** periodically
4. **Review alert logs** for sensitive information

## Comparison with Manual Monitoring

| Feature | Manual | Proactive Monitor |
|---------|--------|-------------------|
| Detection Speed | Hours/days | Seconds/minutes |
| Troubleshooting | Manual | Automatic |
| Alerts | Manual check | Slack + logs |
| Coverage | Partial | All jobs |
| Overnight/Weekends | ❌ | ✅ |

## Future Enhancements

Potential improvements:
- Email notifications
- PagerDuty integration
- Historical failure analytics
- Predictive failure detection
- Custom alert rules
- Dashboard UI

## Related Functions

- `runai_job_status`: Manual status checks
- `runai_kubectl_troubleshoot`: Manual troubleshooting
- `runai_manage_workload`: Suspend/resume/delete jobs

---

**Need help?** Check the main [README](../README.md) or ask the agent: "How do I use proactive monitoring?"

