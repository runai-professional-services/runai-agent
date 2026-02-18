# Conversation Memory (Redis)

The Run:AI agent can keep **conversation context across prompts** using NVIDIA NeMo Agent Toolkit (NAT) memory with a Redis backend. This enables follow-up questions (“cancel that job”, “show logs for the one we just looked at”) and session defaults (“I’m working in project X”) without repeating yourself.

## How It Works

- **NAT auto_memory_agent** wraps the main agent and automatically:
  - Saves user messages and agent responses to Redis
  - Retrieves relevant past context before each response
- **User/session isolation**: Context is scoped by **user ID**. NAT reads user ID from the **`nat-session` cookie** (and `X-User-ID` header). The CLI and Web UI send both so each user or conversation can have its own memory.

### Default user and multi-user

When no user ID is provided (no `nat-session` cookie, no `X-User-ID` header), the backend uses **`default_user`** for memory. **Everyone using `default_user` shares the same memory.** In a shared or multi-user deployment, one person’s "Remember: my favorite project is X" could be recalled by another user who also didn’t set a user ID—contexts can mix and preferences can leak.

**Recommendations:**

- **CLI:** Set a unique `RUNAI_USER_ID` per user or session (e.g. `RUNAI_USER_ID=alice runai-cli ask "..."`). If unset, the CLI sends `default_user` and memory is shared with anyone else not setting it.
- **Web UI:** Ensure the frontend sends a unique session or conversation ID as the `nat-session` cookie so each browser session or conversation has its own memory.
- **Shared deployment:** Treat `default_user` as "anonymous shared"; for real multi-user use, require or encourage unique user IDs (e.g. SSO id, conversation id, or `RUNAI_USER_ID`).

## Prerequisites

- **Redis** running and reachable by the agent (e.g. `localhost:6379` or your Redis host/port).
- **NAT Redis plugin**: `nvidia-nat-redis` is included in the runai-agent dependencies.
- **NAT version**: This feature uses **NAT 1.4+** and `auto_memory_agent`. The project pins `nvidia-nat>=1.4.0` and `nvidia-nat-redis>=1.4.0`. If PyPI only has pre-release 1.4.x, use `pip install --pre` or pin a specific version.

## Configuration

### Environment Variables

| Variable      | Default     | Description                |
|---------------|-------------|----------------------------|
| `REDIS_HOST`  | `localhost` | Redis server host          |
| `REDIS_PORT`  | `6379`      | Redis server port          |
| `REDIS_DB`    | `0`         | Redis database index       |

For the CLI, you can optionally set:

| Variable          | Default        | Description                                      |
|-------------------|----------------|--------------------------------------------------|
| `RUNAI_USER_ID`   | `default_user` | User/session ID sent as `X-User-ID` for memory  |

### Workflow

With **NAT 1.4+**, the default `runai-agent/configs/workflow.yaml` includes:

- **memory:** `redis_memory` (NAT Redis backend, `embedder: nv-embedqa-e5-v5`)
- **workflow:** `auto_memory_agent` wrapping the Run:AI react agent (`runai_react_agent`)

Ensure Redis is running (or start it via `docker compose -f deploy/docker-compose.yml up -d`) so the backend can connect at `REDIS_HOST`/`REDIS_PORT`.

## Running Redis

### Docker Compose (Redis + Agent together)

From the project root, build and run both Redis and the agent:

```bash
# Build the agent image (if not already built)
./deploy/build-docker.sh

# Start Redis and the agent (agent connects to Redis as hostname "redis")
docker compose -f deploy/docker-compose.yml up -d

# View logs
docker compose -f deploy/docker-compose.yml logs -f agent

# Stop
docker compose -f deploy/docker-compose.yml down
```

Set `NVIDIA_API_KEY`, `RUNAI_CLIENT_ID`, `RUNAI_CLIENT_SECRET`, and `RUNAI_BASE_URL` in your environment (or in a `.env` file in the project root) before `up`. The agent container gets `REDIS_HOST=redis` so it connects to the Redis container.

### Local (Redis only)

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Then run the agent locally (e.g. `nat serve` or your own agent container) with `REDIS_HOST=localhost`.

### Kubernetes / Helm

The **runai-agent Helm chart** deploys **Redis Stack** in-cluster by default (`redis.enabled: true`), so conversation memory works without extra setup. The agent receives `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB` automatically. To use an external Redis instead, set `redis.enabled: false` and `redis.host` (e.g. `my-redis.other-namespace.svc`) in your values. See `deploy/helm/runai-agent/README.md` for Redis options.

## CLI

- **User ID** is taken from `RUNAI_USER_ID` or defaults to `default_user`.
- Every request sends the `nat-session` cookie (and `X-User-ID` header) so the agent can store and retrieve context for that user/session.
- Use different `RUNAI_USER_ID` values for different users or sessions, e.g.:

  ```bash
  RUNAI_USER_ID=alice runai-cli ask "List my jobs in project ml-team"
  RUNAI_USER_ID=alice runai-cli ask "Cancel the pending one"  # agent can use prior context
  ```

## Web UI

- The frontend sends the **nat-session** cookie (and X-User-ID) using the current conversation ID (or “web-user” if none).
- Each chat thread gets its own memory scope so follow-ups in that thread use the same context.

## Testing conversation memory

Use these checks to confirm Redis-backed memory is working.

### CLI (same user/session)

1. **Establish context** (one user ID):
   ```bash
   RUNAI_USER_ID=memtest runai-cli ask "Remember: I am testing memory. My favorite project is project-alpha."
   ```
   Expect a normal reply (e.g. acknowledgment or summary).

2. **Recall context** (same user ID):
   ```bash
   RUNAI_USER_ID=memtest runai-cli ask "What project did I say was my favorite?"
   ```
   **Pass:** The response mentions "project-alpha" (or the agent clearly used the prior message).  
   **Fail:** The agent says it doesn't know or doesn't have that context.

3. **Isolation** (different user ID):
   ```bash
   RUNAI_USER_ID=otheruser runai-cli ask "What project did I say was my favorite?"
   ```
   **Pass:** The agent does *not* say "project-alpha" (different user has no memory of memtest's message).

### Web UI (same conversation)

1. In one **conversation**, send: *"Remember: we're testing memory. The test code word is banana."*
2. In the **same** conversation, send: *"What was the test code word I just asked you to remember?"*
3. **Pass:** The response includes "banana" or clearly refers to it.  
4. **Fail:** The agent doesn't recall the code word.

Optional: open a **new** conversation and ask the same recall question; the agent should not see the other conversation's memory (different Conversation-Id → different X-User-ID).

### Quick curl (backend only)

The `/generate` endpoint expects `input_message` (not `message`). Use the same cookie for store and recall:

```bash
# Store (use a stable user id via cookie)
curl -s -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -H "Cookie: nat-session=memtest" \
  -d '{"input_message":"Remember: I am testing memory. My favorite project is project-alpha."}'

# Recall (same cookie = same user)
curl -s -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -H "Cookie: nat-session=memtest" \
  -d '{"input_message":"What project did I say was my favorite?"}'
```

**Pass:** The second response mentions "project-alpha". **Fail:** Agent says it doesn't have that context.

### Verify the patch is in the image

After `docker compose build agent` and `up -d`, confirm the memory user_id patch is in the running container:

```bash
# Should print "Patch present" if the image was rebuilt with the Dockerfile patch
docker compose -f deploy/docker-compose.yml exec agent grep -q "Priority 2.5" /app/.venv/lib/python3.13/site-packages/nat/agent/auto_memory_wrapper/agent.py && echo "Patch present" || echo "Patch MISSING"
```

Then run the store + recall curls and watch agent logs in another terminal. You should see the same user_id on both requests:

```bash
# Terminal 1: stream logs
docker compose -f deploy/docker-compose.yml logs -f agent

# Terminal 2: store then recall (same cookie)
curl -s -X POST http://localhost:3000/generate -H "Content-Type: application/json" -H "Cookie: nat-session=memtest" -d '{"input_message":"Remember: my favorite project is project-alpha."}'
curl -s -X POST http://localhost:3000/generate -H "Content-Type: application/json" -H "Cookie: nat-session=memtest" -d '{"input_message":"What project did I say was my favorite?"}'
```

Look for **Memory user_id from context (cookie): memtest** or **Memory user_id from X-User-ID header: memtest** in the logs for both requests. If you see "Patch MISSING" or no such log line, rebuild with `--no-cache` and redeploy: `docker compose -f deploy/docker-compose.yml build --no-cache agent && docker compose -f deploy/docker-compose.yml up -d`.

**Where backend logs go:** The NAT backend is run by supervisord; its logs are in the container at `/var/log/supervisor/backend.out.log` and `backend.err.log`, not in `docker compose logs`. To check memory user_id after running the curls:
```bash
docker compose -f deploy/docker-compose.yml exec agent grep "Memory user_id" /var/log/supervisor/backend.err.log
```

### Debugging memory (store/retrieve)

If recall fails even with the same cookie/header:

1. **Logs:** After rebuilding the agent image, check backend logs for:
   - `Memory user_id from context (cookie): <user_id>` or `Memory user_id from X-User-ID header: <user_id>`
   - Same user id on both the "Remember" request and the "What did I say" request. If you see `default_user` or no line, the cookie/header may not be reaching the agent.

2. **Redis:** Confirm that memory is stored. From the host (or a pod that can reach Redis):
   ```bash
   # Docker Compose
   docker compose -f deploy/docker-compose.yml exec redis redis-cli KEYS "runai_agent*"
   ```
   After the first "Remember" request you should see keys under the `runai_agent` prefix (exact pattern depends on NAT Redis plugin). If no keys appear, storage may be failing (e.g. embedder, index creation).

3. **Config:** In `workflow.yaml`, `search_params.top_k` (e.g. 20) controls how many memories are retrieved per request; increasing it can help recall of preference-style facts.

4. **Embedding patch:** The NAT Redis plugin only stores an embedding when `memory_item.memory` is set; the auto_memory_agent often stores items with only `conversation` (and empty `memory`). Our Dockerfile applies a patch so an embedding is computed from the conversation content when `memory` is empty, making those items findable by KNN search.

5. **Inject patch:** The auto_memory_agent only injects each retrieved item’s `memory` field into the prompt. Stored items often have `memory: ""` and content in `conversation`. We patch the agent so that when `memory` is empty, conversation content is used for the injected context, so the LLM can actually see what was stored.

6. **"No such index memory_idx" / "Auto-memory agent failed":** If you ran `FLUSHDB` or Redis is empty, the RediSearch index is gone. **Restart the agent** so the memory client re-initializes and recreates the index: `docker compose -f deploy/docker-compose.yml restart agent`.

## References

- [NAT Memory (NVIDIA Docs)](https://docs.nvidia.com/nemo/agent-toolkit/latest/build-workflows/memory.html)
- [NAT Auto Memory Wrapper](https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/develop/examples/agents/auto_memory_wrapper)
