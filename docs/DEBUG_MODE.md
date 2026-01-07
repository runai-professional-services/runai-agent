# Template Executor Debug Mode

## Overview

Debug mode provides verbose logging for the `runai_template_executor` to help troubleshoot API calls and diagnose issues.

## Enabling Debug Mode

### Option 1: Environment Variable (Recommended for Production)

Set the `RUNAI_TEMPLATE_DEBUG` environment variable before starting the agent:

```bash
export RUNAI_TEMPLATE_DEBUG=true
nat serve --config_file configs/workflow.yaml
```

Or inline:

```bash
RUNAI_TEMPLATE_DEBUG=true nat serve --config_file configs/workflow.yaml
```

Accepted values: `true`, `1`, `yes`, `on` (case-insensitive)

### Option 2: Configuration File (For Persistent Testing)

Edit `configs/workflow.yaml`:

```yaml
runai_template_executor:
  debug_mode: true  # Enable debug logging
```

**Note:** Environment variable overrides config file setting.

## What Debug Mode Shows

When enabled, you'll see detailed logs for every template executor call:

### 1. Input Parameters
```
🔍 DEBUG MODE ENABLED - Template Executor Call
================================================================================
Action: delete
Resource Type: pvc
Resource Name: my-pvc
Project: project-01
Parameters: dry_run=None, confirmed=False
Config: require_confirmation=True, dry_run_default=True
Additional params: server=, path=, size=, repository=, branch=
================================================================================
```

### 2. Template Execution
```
🔧 DEBUG: Executing Template
================================================================================
Base URL: https://your-cluster.run.ai
Template Variables:
  - name: my-pvc
  - project: project-01
  - server: 
  - path: 
  - size: 
Generated Code (first 500 chars):
import requests

# Step 1: Authenticate with Run:AI API
token_response = requests.post(
    f"{base_url}/api/v1/token",
...
================================================================================
```

### 3. API Response
```
✅ DEBUG: Execution Result
================================================================================
Result: {'status': 'deleted', 'datasource': 'my-pvc', 'type': 'pvc', 'code': 202}
================================================================================
```

## Use Cases

### Production Troubleshooting

When users report issues, ask them to reproduce with debug mode:

```bash
# In production environment
export RUNAI_TEMPLATE_DEBUG=true
# Restart the agent
```

### Development Testing

Leave debug mode on during development:

```yaml
# configs/workflow.yaml
runai_template_executor:
  debug_mode: true
```

### Verifying API Calls

Use debug mode to confirm:
- Correct API endpoint is being called
- Parameters are being passed correctly
- API response structure
- Authentication is working

## Examples

### Example 1: Debugging Failed Delete

```bash
$ export RUNAI_TEMPLATE_DEBUG=true
$ nat run --input "Delete PVC my-data from project-01"

# Output shows:
# - Name passed to template: my-data
# - Project ID lookup: 4500002
# - API call: DELETE /api/v1/asset/datasource/pvc/abc-123
# - Response: 404 Not Found
# - Error: PVC datasource 'my-data' not found in project 'project-01'
```

**Diagnosis:** PVC doesn't exist or name is wrong.

### Example 2: Debugging Slow Operations

```bash
$ export RUNAI_TEMPLATE_DEBUG=true
$ time nat run --input "List all PVCs in project-01"

# Output shows timestamps for:
# - Authentication (0.5s)
# - Cluster ID lookup (0.2s)  
# - Project ID lookup (0.3s)
# - PVC list call (1.2s)
# Total: ~2.2s
```

**Diagnosis:** Most time spent in PVC list API call.

## Disabling Debug Mode

### Temporary (Environment Variable)

```bash
unset RUNAI_TEMPLATE_DEBUG
# Or restart without the variable
```

### Permanent (Configuration File)

```yaml
# configs/workflow.yaml
runai_template_executor:
  debug_mode: false
```

## Performance Impact

Debug mode has **minimal performance impact**:
- Extra logging to console/file
- No impact on API call speed
- Recommended to disable in production unless troubleshooting

## Security Considerations

⚠️ **Debug logs contain sensitive information:**
- API base URLs
- Project names and IDs
- Resource details

**Do not share debug logs publicly without redacting:**
- Remove or mask URLs
- Remove project/resource names
- Remove any identifiable information

## See Also

- [Template Executor Documentation](../docs/QUICKSTART_TEMPLATES.md)
- [API Template Analysis](../docs/API_TEMPLATE_ANALYSIS.md)
- [Troubleshooting Guide](../TESTING.md)

