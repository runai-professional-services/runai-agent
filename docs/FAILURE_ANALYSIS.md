# Advanced Failure Analysis 🔬

The Run:AI Agent includes an **Advanced Failure Analysis** system that goes beyond simple logs to provide intelligent pattern recognition, cross-job correlation, and automated remediation suggestions.

## 🎯 Overview

The failure analyzer continuously learns from every failure in your cluster, building a knowledge graph of failure patterns and proven solutions. It can detect systemic issues like problematic nodes, image compatibility problems, and resource bottlenecks before they become critical.

## ✨ Key Features

### 1. **Failure Pattern Recognition**
- Detects repeated failures across projects
- Identifies failure clusters by type (OOMKilled, ImagePullBackOff, etc.)
- Tracks failure trends over time
- Highlights anomalies and spikes

### 2. **Cross-Job Correlation**
- **Hot Node Detection**: "Node gpu-node-03 has 90% failure rate across 15 jobs"
- **Image Problems**: "This container image failed 8 times in the last hour"
- **Project Issues**: "Project ml-team has 5 OOMKilled failures today"
- **Time-Based Patterns**: "Failures spike between 2-4pm (resource contention)"

### 3. **Automated Remediation Suggestions**
- **Rule-Based Solutions**: Pre-configured fixes for common issues
- **Historical Solutions**: "3 other users fixed this by increasing memory 2x"
- **Success Rate Tracking**: Solutions ranked by effectiveness
- **Community Knowledge**: Learn from what works across your organization

### 4. **Knowledge Graph**
- Persistent SQLite database tracks all failures
- Maps failure types → proven solutions
- Builds institutional knowledge over time
- Survives restarts and updates

### 5. **Related: Job Performance Analytics**
The same database is used for **job performance analytics**. Ask the agent for execution time trends, failure rates by project/image, recommendations (e.g. typical job duration), and anomaly detection (jobs running 3× longer than usual). Example: *"How long do my training jobs usually take?"* or *"Any jobs running longer than usual?"* Run history is populated when proactive monitoring is enabled.

## 🚀 Usage

### Analyze Failure Patterns

Get a comprehensive analysis of recent failures:

```
Analyze failures from the last 7 days
```

**Agent Response:**
```
📊 Advanced Failure Analysis Report

Time Period: Last 7 days
Project Filter: All projects

---

## 📈 Summary

- Total Failures: 23
- Projects Affected: 4
- Unique Failure Types: 5

---

## 🔍 Detected Patterns

🔴 Project: ml-team
   - Failures: 8
   - Top failure types: {'OOMKilled': 5, 'ImagePullBackOff': 3}

⏰ Failures spike during hours [14, 15, 16]
   - May indicate resource contention or scheduled workloads

---

## 🔥 Problematic Nodes

🔴 Node: gpu-node-03
   - Failures: 12 across 8 jobs
   - Failure Rate: 75.0%

⚠️ Node: gpu-node-07
   - Failures: 6 across 4 jobs
   - Failure Rate: 60.0%

---

## 🔗 Correlations

🐳 Image: pytorch/pytorch:2.0-cuda11.8
   - Failure count: 5
   - Common errors: CUDA version mismatch, Missing libcudnn.so

---

## 💡 Recommendations

🔴 Project 'ml-team' has 8 failures. Review project resources and job configurations.

⚠️ Node 'gpu-node-03' has 75.0% failure rate (12 failures). Consider cordoning this node for maintenance.

🐳 Image 'pytorch/pytorch:2.0-cuda11.8' is associated with 5 failures. Verify image compatibility and dependencies.
```

### Get Failure Statistics

Quick stats overview:

```
Show me failure statistics for the last 30 days
```

**Agent Response:**
```
📊 Failure Statistics

Time Period: Last 30 days

---

## Failure Types

- OOMKilled: 45 occurrences
- ImagePullBackOff: 23 occurrences
- CrashLoopBackOff: 12 occurrences
- Pending: 8 occurrences
- Error: 5 occurrences

## Project Failures

- ml-team: 38 failures
- data-science: 22 failures
- research: 18 failures
- production: 15 failures

## Node Failures

- gpu-node-03: 25 failures
- gpu-node-07: 18 failures
- gpu-node-12: 12 failures
```

### Get Remediation Suggestions

Get intelligent fix suggestions for specific failure types:

```
How do I fix OOMKilled failures?
```

**Agent Response:**
```
🔧 Automated Remediation Suggestions

Failure Type: OOMKilled
Description: Out of Memory - Pod exceeded memory limit

---

## 🎯 Rule-Based Solutions

1. Increase memory request/limit by 2x
   Parameters: {"multiplier": 2.0}

2. Optimize application memory usage (manual)

---

## 📊 Historical Solutions (Community Knowledge)

These solutions have been tried by other users:

1. Increase memory limit from 8Gi to 16Gi
   ✅ Success Rate: 85.7% (6 successes, 1 failures)

2. Add memory profiling and optimize data loading
   ✅ Success Rate: 75.0% (3 successes, 1 failures)

3. Enable gradient checkpointing to reduce memory usage
   ✅ Success Rate: 66.7% (2 successes, 1 failures)
```

### Project-Specific Analysis

Focus on a specific project:

```
Analyze failures in project ml-team
```

### Custom Time Ranges

```
Show me failure patterns from the last 30 days
```

## 🔄 Integration with Proactive Monitoring

The failure analyzer **automatically integrates** with the proactive monitor. Every failure detected during monitoring is:

1. ✅ Recorded to the failure database with full context
2. ✅ Analyzed for patterns and correlations
3. ✅ Used to improve future remediation suggestions
4. ✅ Tracked for success/failure of applied solutions

**No manual setup required** - just enable proactive monitoring and the analyzer starts learning!

```
Start monitoring all jobs
```

This will:
- Monitor for failures continuously
- Auto-record failures to the database
- Build pattern recognition over time
- Improve remediation suggestions automatically

## 📊 Database Schema

The failure analyzer uses SQLite for persistence:

### Tables

**failure_events** - Main failure tracking
- Job details (name, project, type)
- Failure context (phase, error message, logs snippet)
- Infrastructure (pod name, node name, container image)
- Resources (GPU count, memory, CPU)
- Resolution tracking

**failure_solutions** - Knowledge graph
- Failure type → solution mappings
- Success/failure counts
- Success rate tracking
- Last used timestamp

**failure_correlations** - Pattern tracking
- Correlation type (node, image, project)
- Failure counts
- First/last seen timestamps

### Database Location

Default: `/tmp/runai_failure_history.db`

**Customize in workflow.yaml:**
```yaml
runai_failure_analyzer:
  db_path: "/persistent/storage/runai_failure_history.db"
```

**For production:** Mount a persistent volume to preserve history across restarts.

## 🛠️ Configuration

Edit `runai-agent/configs/workflow.yaml`:

```yaml
runai_failure_analyzer:
  _type: runai_failure_analyzer
  
  # Access control
  allowed_projects: ["*"]  # Or ["project-01", "project-02"]
  
  # Database
  db_path: "/tmp/runai_failure_history.db"
  
  # Analysis parameters
  lookback_days: 7  # Days of history to analyze
  pattern_threshold: 3  # Min occurrences to identify pattern
  
  # Remediation
  enable_auto_remediation: false  # Enable automatic fixes (with confirmation)
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `allowed_projects` | `["*"]` | Projects that can be analyzed |
| `db_path` | `/tmp/runai_failure_history.db` | SQLite database location |
| `lookback_days` | `7` | Days of history to analyze |
| `pattern_threshold` | `3` | Minimum failures to identify a pattern |
| `enable_auto_remediation` | `false` | Enable automated fixes |

## 🧠 How It Works

### 1. Data Collection

When a failure occurs (detected by proactive monitor):

```python
failure_data = {
    'job_name': 'training-job-123',
    'project': 'ml-team',
    'failure_type': 'OOMKilled',
    'phase': 'OOMKilled',
    'pod_name': 'training-job-123-0-0',
    'node_name': 'gpu-node-03',
    'container_image': 'pytorch/pytorch:latest',
    'error_message': 'Container killed due to memory limit',
    'logs_snippet': '...',
    'events_snippet': '...',
    'gpu_count': 4,
    'memory_request': '16Gi',
    'cpu_request': '8'
}
```

### 2. Pattern Analysis

The analyzer runs multiple algorithms:

**Frequency Analysis:**
- Count failures by type, project, node, image
- Identify outliers and hotspots

**Temporal Analysis:**
- Detect time-based patterns (hourly, daily)
- Identify failure spikes and trends

**Correlation Analysis:**
- Cross-reference failures by node, image, project
- Calculate failure rates and probabilities

**Severity Scoring:**
- Rank issues by impact (failure count × jobs affected)
- Prioritize critical problems

### 3. Remediation Matching

For each failure type, the system:

1. **Checks rule-based solutions** (pre-configured fixes)
2. **Queries historical solutions** (what worked before)
3. **Ranks by success rate** (proven effectiveness)
4. **Provides context** (similar failures, related issues)

### 4. Knowledge Graph Building

Over time, the system learns:

```
OOMKilled → "Increase memory 2x" (Success Rate: 85%)
ImagePullBackOff → "Check registry credentials" (Success Rate: 92%)
CrashLoopBackOff → "Verify entrypoint command" (Success Rate: 78%)
```

## 📈 Benefits

### Before Failure Analysis

- ❌ Manual investigation of each failure
- ❌ No visibility into systemic issues
- ❌ Repeated mistakes across teams
- ❌ Slow incident response
- ❌ Knowledge loss when team members leave

### After Failure Analysis

- ✅ Automatic pattern detection
- ✅ Proactive identification of problematic nodes/images
- ✅ Institutional knowledge preservation
- ✅ Fast remediation with proven solutions
- ✅ Continuous learning and improvement

## 🎯 Use Cases

### 1. **Infrastructure Health Monitoring**

**Scenario:** A GPU node is failing frequently but no one notices.

**Solution:** Failure analyzer detects:
```
⚠️ Node 'gpu-node-03' has 75% failure rate (12 failures).
Consider cordoning this node for maintenance.
```

**Action:** DevOps team investigates and finds hardware issue.

---

### 2. **Image Compatibility Issues**

**Scenario:** New PyTorch image causes failures across multiple projects.

**Solution:** Analyzer correlates:
```
🐳 Image 'pytorch/pytorch:2.1-cuda12.0' is associated with 8 failures.
Common errors: CUDA version mismatch, Missing libcudnn.so
```

**Action:** Teams switch to compatible image version.

---

### 3. **Resource Optimization**

**Scenario:** ML team keeps hitting OOM errors.

**Solution:** Historical analysis shows:
```
📊 Historical Solutions for OOMKilled:
1. Increase memory from 8Gi to 16Gi - Success Rate: 85%
2. Enable gradient checkpointing - Success Rate: 75%
```

**Action:** Team applies proven solution, saves time.

---

### 4. **Time-Based Issues**

**Scenario:** Jobs fail more during business hours.

**Solution:** Pattern detection reveals:
```
⏰ Failures spike during hours [9, 10, 11, 14, 15, 16]
May indicate resource contention or scheduled workloads
```

**Action:** Adjust scheduling or increase cluster capacity.

---

### 5. **Knowledge Preservation**

**Scenario:** Senior engineer who knows all the "tricks" leaves the company.

**Solution:** Knowledge graph preserves institutional knowledge:
```
📊 Community Solutions:
- "For ImagePullBackOff on ECR, add imagePullSecrets" (92% success)
- "For OOM on BERT training, use gradient accumulation" (88% success)
```

**Action:** New team members benefit from accumulated expertise.

## 🔮 Future Enhancements

Planned features:

- **ML-Powered Predictions**: Predict failures before they happen
- **Auto-Remediation Execution**: Automatically resubmit with fixes (with approval)
- **Slack/Email Digests**: Weekly failure analysis reports
- **Grafana Integration**: Visualize failure trends over time
- **Multi-Cluster Analysis**: Aggregate patterns across clusters
- **Cost Impact Analysis**: Calculate GPU hours wasted due to failures

## 🤝 Contributing Solutions

When you find a solution that works, the system learns from it:

1. **Automatic Tracking**: When a job succeeds after failure, the system records it
2. **Success Rate Calculation**: Solutions are ranked by effectiveness
3. **Community Benefit**: Other users get your proven solutions

**Example:**
```
User A: Fixes OOMKilled by increasing memory 2x → Success
User B: Gets same error → System suggests "Increase memory 2x (85% success rate)"
User B: Applies solution → Success → Success rate increases to 90%
```

## 📚 API Reference

### Actions

**analyze** - Comprehensive pattern analysis
```python
{
    "action": "analyze",
    "project": "ml-team",  # Optional
    "lookback_days": 7
}
```

**stats** - Quick statistics overview
```python
{
    "action": "stats",
    "lookback_days": 30
}
```

**remediate** - Get fix suggestions
```python
{
    "action": "remediate",
    "failure_type": "OOMKilled",
    "job_name": "my-job",  # Optional
    "project": "ml-team"  # Optional
}
```

## 🐛 Troubleshooting

### Database Not Found

**Issue:** `sqlite3.OperationalError: unable to open database file`

**Solution:** Ensure the database path is writable:
```bash
mkdir -p /tmp
chmod 777 /tmp
```

### No Patterns Detected

**Issue:** "No significant patterns detected"

**Possible Causes:**
- Not enough failures recorded yet (need 3+ for patterns)
- Lookback period too short
- Failures are too diverse (no common patterns)

**Solution:** 
- Wait for more data to accumulate
- Increase `lookback_days`
- Lower `pattern_threshold`

### Database Growing Too Large

**Issue:** Database file is very large

**Solution:** Implement retention policy:
```sql
-- Delete failures older than 90 days
DELETE FROM failure_events WHERE timestamp < datetime('now', '-90 days');
VACUUM;
```

## 🎓 Best Practices

1. **Mount Persistent Storage**: Don't use `/tmp` in production
2. **Regular Analysis**: Run weekly failure analysis reports
3. **Act on Recommendations**: Address hot nodes and problematic images
4. **Share Knowledge**: Encourage teams to document solutions
5. **Monitor Trends**: Watch for increasing failure rates
6. **Correlate with Changes**: Link failures to deployments/updates

## 📊 Metrics to Track

- **Total Failures**: Overall cluster health
- **Failure Rate**: Failures per 100 jobs
- **MTTR** (Mean Time To Resolution): How fast issues are fixed
- **Top Failure Types**: Most common issues
- **Hot Nodes**: Nodes with high failure rates
- **Solution Success Rate**: Effectiveness of remediations

---

**Built with ❤️ to make debugging less painful**

