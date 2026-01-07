# 🚀 Failure Analysis Quick Start

Get started with Advanced Failure Analysis in 5 minutes!

## Step 1: Enable the Feature

The failure analyzer is **already enabled** in your agent configuration. No setup required!

## Step 2: Start Collecting Data

Enable proactive monitoring to automatically record failures:

```
Start monitoring all jobs
```

That's it! The agent will now:
- ✅ Monitor for failures continuously
- ✅ Auto-record failures to the database
- ✅ Build pattern recognition over time
- ✅ Improve remediation suggestions automatically

## Step 3: Try It Out

### Get Your First Analysis

Wait for a few failures to occur (or let it run for a day), then ask:

```
Analyze failures from the last 7 days
```

**You'll see:**
- Total failure count and affected projects
- Detected patterns (repeated failures)
- Problematic nodes (hot nodes)
- Image correlations
- Actionable recommendations

### Get Quick Stats

```
Show me failure statistics
```

**You'll see:**
- Failure types distribution
- Project failure counts
- Node failure counts
- Image failure counts

### Get Fix Suggestions

When you encounter a specific failure type:

```
How do I fix OOMKilled failures?
```

**You'll get:**
- Rule-based solutions (pre-configured fixes)
- Historical solutions (what worked for others)
- Success rates for each solution

## Step 4: Act on Insights

### Example Workflow

1. **Morning Check:**
   ```
   Show me failure statistics for the last 24 hours
   ```

2. **Spot a Pattern:**
   ```
   📊 Node Failures:
   - gpu-node-03: 8 failures
   - gpu-node-07: 3 failures
   ```

3. **Investigate:**
   ```
   Analyze failures in the last 7 days
   ```

4. **Get Recommendation:**
   ```
   ⚠️ Node 'gpu-node-03' has 75% failure rate.
   Consider cordoning this node for maintenance.
   ```

5. **Take Action:**
   - Cordon the problematic node
   - Investigate hardware issues
   - Prevent future job losses

## Common Queries

### Pattern Analysis
```
"Analyze failures from the last 7 days"
"Show me failure patterns in project ml-team"
"What are the most common failure types?"
```

### Statistics
```
"Show me failure statistics for the last 30 days"
"How many OOMKilled failures happened this week?"
"Which projects have the most failures?"
```

### Remediation
```
"How do I fix OOMKilled failures?"
"Get remediation suggestions for ImagePullBackOff"
"What's the best solution for CrashLoopBackOff?"
```

### Project-Specific
```
"Analyze failures in project ml-team"
"Show me failures in data-science project"
```

## Configuration (Optional)

Want to customize? Edit `runai-agent/configs/workflow.yaml`:

```yaml
runai_failure_analyzer:
  # How many days of history to analyze
  lookback_days: 7
  
  # Minimum failures to identify a pattern
  pattern_threshold: 3
  
  # Database location (use persistent storage in production!)
  db_path: "/tmp/runai_failure_history.db"
```

## Production Setup

### Mount Persistent Storage

**Important:** The default database location (`/tmp`) is not persistent!

For production, mount a persistent volume:

```yaml
# In your Kubernetes deployment
volumes:
  - name: failure-db
    persistentVolumeClaim:
      claimName: runai-agent-failure-db

volumeMounts:
  - name: failure-db
    mountPath: /data

# Then update workflow.yaml
runai_failure_analyzer:
  db_path: "/data/runai_failure_history.db"
```

### Set Environment Variable

Alternatively, set via environment variable:

```bash
export RUNAI_FAILURE_DB_PATH="/persistent/storage/runai_failure_history.db"
```

## Tips & Best Practices

### 1. Let It Learn
- Give it a few days to collect data
- The more failures it sees, the smarter it gets
- Patterns emerge after 3+ similar failures

### 2. Regular Check-Ins
- Run weekly failure analysis reports
- Monitor trends over time
- Act on recommendations promptly

### 3. Share Knowledge
- When you fix an issue, the system learns from it
- Your solutions help other team members
- Community knowledge grows automatically

### 4. Investigate Hot Nodes
- High failure rates often indicate hardware issues
- Cordon problematic nodes for maintenance
- Prevent cascading failures

### 5. Review Image Compatibility
- Track which images cause failures
- Test new images in dev before production
- Document known compatibility issues

## Troubleshooting

### "No failures detected"

**Cause:** Not enough data yet.

**Solution:** Wait for failures to occur naturally, or the database is empty.

### "No patterns detected"

**Cause:** Failures are too diverse or threshold too high.

**Solution:** Lower `pattern_threshold` in config or wait for more data.

### Database errors

**Cause:** Database path not writable.

**Solution:** Ensure the path exists and has write permissions:
```bash
mkdir -p /tmp
chmod 777 /tmp
```

## Example Session

```
You: Start monitoring all jobs

Agent: 🚀 Starting proactive monitoring...
       Projects: ALL
       Poll interval: 60s
       Duration: Continuous

[Wait for some failures to occur...]

You: Analyze failures from the last 7 days

Agent: 📊 Advanced Failure Analysis Report

       ## 📈 Summary
       - Total Failures: 12
       - Projects Affected: 3
       - Unique Failure Types: 4

       ## 🔍 Detected Patterns
       🔴 Project: ml-team
          - Failures: 8
          - Top failure types: {'OOMKilled': 5, 'ImagePullBackOff': 3}

       ## 🔥 Problematic Nodes
       🔴 Node: gpu-node-03
          - Failures: 6 across 4 jobs
          - Failure Rate: 75.0%

       ## 💡 Recommendations
       ⚠️ Node 'gpu-node-03' has 75% failure rate. Consider cordoning for maintenance.

You: How do I fix OOMKilled failures?

Agent: 🔧 Automated Remediation Suggestions

       Failure Type: OOMKilled
       Description: Out of Memory - Pod exceeded memory limit

       ## 🎯 Rule-Based Solutions
       1. Increase memory request/limit by 2x
       2. Optimize application memory usage

       ## 📊 Historical Solutions (Community Knowledge)
       1. Increase memory limit from 8Gi to 16Gi
          ✅ Success Rate: 85.7% (6 successes, 1 failure)
```

## Next Steps

1. ✅ Enable proactive monitoring
2. ✅ Let it collect data for a few days
3. ✅ Run your first analysis
4. ✅ Act on recommendations
5. ✅ Watch your cluster health improve!

## Learn More

- **Full Documentation:** [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md)
- **Example Script:** `runai-agent/examples/failure_analysis_example.py`
- **Configuration:** `runai-agent/configs/workflow.yaml`

---

**Questions?** Just ask the agent:
```
"How does failure analysis work?"
"What can I do with failure analysis?"
```

🎉 **Happy debugging!**

