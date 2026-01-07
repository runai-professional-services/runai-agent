# Template System - Quick Start Guide

**5-minute guide to testing the new template-based executor**

---

## 🚀 Start the Agent

```bash
cd runai-agent
source .venv/bin/activate

# Set environment variables
# Set your Run:AI cluster URL and credentials
export RUNAI_BASE_URL=https://your-runai-cluster.com
export RUNAI_CLIENT_ID=[YOUR_CLIENT_ID]
export RUNAI_CLIENT_SECRET=[YOUR_CLIENT_SECRET]
export NVIDIA_API_KEY=[YOUR_NVIDIA_API_KEY]  # Get from build.nvidia.com
export KUBECONFIG=/path/to/your/kubeconfig.yaml
export KMP_DUPLICATE_LIB_OK=TRUE

# Start the agent
nat serve --config_file configs/workflow.yaml --host 0.0.0.0 --port 8000
```

---

## 🧪 Test Operations

### 1. Create NFS Datasource

**Chat:**
```
Create an NFS datasource named test-template-nfs in project-01 with server 10.0.1.50 and path /data
```

**Expected:**
- Agent uses `runai_template_executor` (not `runai_llm_executor`)
- Shows confirmation prompt or dry-run code
- Creates NFS datasource successfully
- Response time < 1 second (vs 2-5 seconds with LLM)

---

### 2. List Datasources

**Chat:**
```
List all NFS datasources in project-01
```

**Expected:**
- Fast response (< 1 second)
- Shows all NFS datasources including the one we just created
- Consistent output format

---

### 3. Create PVC

**Chat:**
```
Create a PVC datasource named test-template-pvc in project-01 with size 10Gi
```

**Expected:**
- Uses template executor
- Creates PVC successfully
- Fast response

---

### 4. Delete Datasource

**Chat:**
```
Delete the NFS datasource named test-template-nfs from project-01
```

**Expected:**
- Finds datasource by name
- Deletes successfully
- Fast response

---

## 🔍 What to Look For

### Performance
- ⚡ **Template operations should be 20-50x faster** than LLM operations
- Look for response times < 1 second vs 2-5 seconds

### Consistency
- ✅ **Same input should always produce same output**
- Try creating the same datasource twice (should get consistent errors)

### Tool Selection
- 🎯 **Agent should prefer `runai_template_executor`** over `runai_llm_executor`
- Check agent reasoning logs to confirm tool selection

### Error Handling
- 🐛 **Errors should be clear and actionable**
- Try invalid operations (missing server, wrong project name)
- Error messages should suggest fixes

---

## 📊 Compare with LLM Executor

To compare performance, you can force the agent to use the old LLM executor:

**Temporarily disable template executor in `workflow.yaml`:**
```yaml
workflow:
  tool_names:
    # - runai_template_executor  # Comment out
    - runai_llm_executor
```

Then restart and test the same operations. You should see:
- Slower response times (2-5 seconds)
- More variability in output
- Higher token usage in logs

---

## 🎯 Success Criteria

✅ **Template executor is used** for datasource operations  
✅ **Operations complete in < 1 second** (vs 2-5 seconds)  
✅ **Results are consistent** across multiple runs  
✅ **Error messages are clear** and helpful  
✅ **All CRUD operations work** (create, list, delete)  

---

## 🐛 Troubleshooting

### Enable Debug Mode

For detailed troubleshooting, enable debug mode to see all API calls and responses:

```bash
export RUNAI_TEMPLATE_DEBUG=true
```

This will show:
- Input parameters for each operation
- Generated API code
- Full API responses
- Any errors with context

See [DEBUG_MODE.md](../runai-agent/DEBUG_MODE.md) for complete documentation.

### Agent uses LLM executor instead of template executor
**Fix:** Check `workflow.yaml` - ensure `runai_template_executor` is listed BEFORE `runai_llm_executor`

### Template not found error
**Fix:** Check template files exist in `src/runai_agent/templates/`

### Authentication error
**Fix:** Verify environment variables are set correctly

### Project not found
**Fix:** Ensure project name exists in your cluster (use `kubectl get projects` or check Run:AI UI)

### Operation seems to succeed but resource not found
**Fix:** Enable debug mode (`RUNAI_TEMPLATE_DEBUG=true`) to see actual API response

---

## 📈 Performance Benchmarking

To measure performance improvements:

```bash
# Time an LLM operation (disable template executor first)
time echo "Create an NFS datasource..." | # send to agent

# Time a template operation (enable template executor)
time echo "Create an NFS datasource..." | # send to agent

# Compare the times
```

Expected improvement: **20-50x faster**

---

## 📝 What to Test

### Priority 1 (Critical)
- [x] NFS create
- [x] NFS list
- [x] NFS delete
- [ ] PVC create
- [ ] PVC list
- [ ] PVC delete

### Priority 2 (Important)
- [ ] Git datasource create
- [ ] S3 datasource create
- [ ] Project create with GPU quota
- [ ] Error handling (invalid inputs)

### Priority 3 (Nice to have)
- [ ] HostPath datasource
- [ ] Department create
- [ ] Performance benchmarks
- [ ] Consistency tests (same operation 10x)

---

## 🎉 Next Steps After Testing

1. **If everything works:**
   - Commit changes
   - Push to remote
   - Update documentation
   - Consider deprecating LLM executor for datasources

2. **If issues found:**
   - Document the issue
   - Check logs for errors
   - Review template code
   - Fix and re-test

3. **Future enhancements:**
   - Add more resource types (NodePools, Credentials)
   - Add template validation
   - Add metrics collection
   - Consider templating job submissions

---

**Ready to test!** 🚀

Open your browser to `http://localhost:8000` and start chatting with the agent.

