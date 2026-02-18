# RunAI CLI

A lightweight TypeScript CLI for interacting with the RunAI Agent backend.

## 🌟 NEW: Natural Language Job Submission!

Submit jobs using plain English - just like ChatGPT!

```bash
runai-cli submit "Create a training job with 2 GPUs using PyTorch"
```

No JSON files, no complex flags - just tell it what you need! 🎉

**[📖 Read the Complete Natural Language Guide →](docs/NATURAL_LANGUAGE_GUIDE.md)**  
**[⚡ Quick Examples →](docs/QUICKSTART_EXAMPLES.md)**

## Features

- 🚀 **Natural Language Submit**: GenAI-style job submission (NEW!)
- 📊 **Cluster Resource Summary**: Ask "How is my cluster doing?" for GPU/CPU/memory quota and usage by project (NEW!)
- 📊 **NIM Benchmarking**: NVIDIA NIM LLM benchmarking on H100, H200, A100 (NEW!)
- 🌐 **Remote Agent Support**: Connect to remote agents for team collaboration (NEW!)
- 💬 **Interactive REPL**: Chat-style interface for multi-turn conversations
- 🔧 **Server Management**: Start, stop, and monitor the agent server
- 📊 **Job Operations**: Submit, monitor, and manage training jobs
- 🌍 **Environment Management**: Create and manage RunAI environments
- ⚙️ **Configurable**: Persistent configuration with sensible defaults
- 🎨 **Beautiful Output**: Colored output with spinners and formatting

## Quick Start

### Prerequisites

**For the CLI (TypeScript)**:
- Node.js >= 18.0.0
- npm (comes with Node.js)

**For the Agent Backend (Python)**:
- Python >= 3.11
- Virtual environment (recommended)
- NeMo Agent Toolkit (NAT) >= 1.3.0
- RunAI SDK (runapy) - optional but recommended

**Required Environment Variables**:
```bash
export RUNAI_CLIENT_ID="your_client_id"
export RUNAI_CLIENT_SECRET="your_client_secret"
export RUNAI_BASE_URL="https://your-runai-cluster.example.com"
export NVIDIA_API_KEY="your_nvidia_api_key"
```

### Installation

#### Step 1: Install Python Agent Backend (NAT)

```bash
# Navigate to project root
cd /path/to/runai-agent

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the RunAI Agent (includes NAT 1.3.1)
cd nemo-agent-toolkit-custom
pip install -e .

# Optional: Install webpage_query plugin for doc search
pip install "git+https://github.com/NVIDIA/NeMo-Agent-Toolkit.git@v1.3.1#subdirectory=examples/getting_started/simple_web_query"

# Optional: Install RunAI SDK for direct API access
pip install runapy==1.223.0
```

**macOS Users**: If you encounter OpenMP library conflicts:
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.zshrc
```

#### Step 2: Install TypeScript CLI

```bash
# Navigate to CLI directory
cd ../runai-cli

# Install dependencies
npm install

# Build TypeScript
npm run build

# Link CLI globally
npm link
```

This creates a global `runai-cli` command.

### Basic Usage

**Important**: The CLI requires the NAT agent server to be running. The server provides the AI-powered backend.

```bash
# Set environment variables (required for agent backend)
export RUNAI_CLIENT_ID="your_client_id"
export RUNAI_CLIENT_SECRET="your_client_secret"
export RUNAI_BASE_URL="https://your-cluster.example.com"
export NVIDIA_API_KEY="your_api_key"

# Check if the agent server is running
runai-cli server status

# Start the agent server (in background)
runai-cli server start --background

# Wait a few seconds for server to start, then test
runai-cli ask "Show me all projects"

# Or use interactive mode
runai-cli chat

# Try the NEW natural language submit!
runai-cli submit "Create a training job with 2 GPUs"
```

## 🌐 Remote Agent Support (NEW!)

Connect to remote agents for team collaboration and production use!

### Quick Start - Remote Agent

```bash
# Connect to a remote agent
runai-cli connect https://runai-agent.example.com:8000

# Verify connection
runai-cli server status

# Use all CLI commands as normal!
runai-cli ask "Show me all projects"
runai-cli submit "Create a training job with 2 GPUs"

# Switch back to local mode
runai-cli connect local
```

### Benefits

- ✅ **Team Collaboration** - Share a single agent across your team
- ✅ **Zero Setup** - No need to run the agent locally
- ✅ **Production Ready** - Connect to HA deployments in Kubernetes
- ✅ **Same Commands** - All CLI commands work with remote agents (except `server start/stop`)

**[📖 Complete Remote Agent Guide →](docs/REMOTE_AGENT.md)**

## Commands

### 🆕 Natural Language Submit

**`submit [prompt]`** - Submit jobs using natural language (GenAI-style)

```bash
# Simple submission
runai-cli submit "Create a training job with 2 GPUs using PyTorch"

# With project context
runai-cli submit "Training job with 4 GPUs" --project ml-team

# Interactive mode
runai-cli submit

# Stream the response
runai-cli submit "Distributed training with 8 workers" --stream

# Skip confirmations (for automation)
runai-cli submit "Quick training job" --no-confirm
```

**Examples:**
```bash
# Simple
runai-cli submit "Training job with 2 GPUs"

# Specific
runai-cli submit "PyTorch distributed training with 4 workers and 2 GPUs per worker"

# Workspace
runai-cli submit "Jupyter workspace with 8GB memory in project data-science"

# Batch
runai-cli submit "Create 5 training jobs with different learning rates"
```

**[📖 See complete examples and guide →](docs/NATURAL_LANGUAGE_GUIDE.md)**

Options:
- `-s, --stream` - Stream the response in real-time  
- `-p, --project <name>` - Target project name
- `--no-confirm` - Skip confirmation prompts

### Agent Queries

**`ask <query>`** - Send a one-shot query to the agent

```bash
runai-cli ask "Show me all projects in the cluster"
runai-cli ask "Show me cluster resource summary"
runai-cli ask "How is my cluster doing?"
runai-cli ask "Generate a training job with 2 GPUs" --stream
```

Options:
- `-s, --stream` - Stream the response in real-time

**`chat`** - Start interactive REPL mode

```bash
runai-cli chat
```

Interactive commands:
- Type any query and press Enter
- `exit` or `quit` - Exit the REPL
- `clear` - Clear the screen
- `help` - Show help message

### Server Management

**`server status`** - Check if the agent server is running

```bash
runai-cli server status
```

**`server start`** - Start the agent server

```bash
# Start in foreground (press Ctrl+C to stop)
runai-cli server start

# Start in background
runai-cli server start --background
```

**`server stop`** - Stop the background agent server

```bash
runai-cli server stop
```

**`server logs`** - View server logs (coming soon)

```bash
runai-cli server logs
```

### Job Operations

**`job submit <spec>`** - Submit a job from a JSON spec file

```bash
runai-cli job submit ./my-job.json
```

Example job spec (`my-job.json`):
```json
{
  "name": "training-job-1",
  "project": "project-01",
  "image": "nvcr.io/nvidia/pytorch:24.01-py3",
  "gpu": 2,
  "command": "python",
  "args": ["train.py", "--epochs", "100"]
}
```

**`job status <name>`** - Check the status of a job

```bash
runai-cli job status my-training-job
runai-cli job status my-training-job --project project-01
```

**`job list`** - List all jobs

```bash
runai-cli job list
runai-cli job list --project project-01
```

**`job delete <name>`** - Delete a job

```bash
runai-cli job delete my-training-job
runai-cli job delete my-training-job --project project-01 --force
```

Options:
- `-p, --project <project>` - Specify project name
- `-f, --force` - Skip confirmation prompt

### Environment Operations

**`env info`** - Show environment information

```bash
runai-cli env info
```

**`env create <spec>`** - Create an environment from a JSON spec file

```bash
runai-cli env create ./my-env.json
```

Example environment spec (`my-env.json`):
```json
{
  "name": "ml-training-env",
  "scope": "project",
  "scopeId": "project-01-id",
  "description": "ML training environment with GPU support",
  "image": "nvcr.io/nvidia/pytorch:24.01-py3",
  "compute": {
    "gpu": 2,
    "cpuCores": 8,
    "memory": "64Gi"
  },
  "environmentVariables": {
    "NCCL_DEBUG": "INFO"
  }
}
```

**`env list`** - List all environments

```bash
runai-cli env list
```

**`env delete <name>`** - Delete an environment

```bash
runai-cli env delete my-env
runai-cli env delete my-env --force
```

### NIM Benchmarking

**`benchmark run`** - Run a NIM benchmark job on a specific GPU and scenario

```bash
runai-cli benchmark run --gpu h100 --scenario throughput
runai-cli benchmark run --gpu h200 --scenario latency --monitor
runai-cli benchmark run --gpu a100 --scenario concurrency --monitor --export csv
```

**`benchmark status`** - Check benchmark job status

```bash
runai-cli benchmark status nim-bench-h100-throughput-202602061200 --project benchmark
```

**`benchmark logs`** - Fetch benchmark logs

```bash
runai-cli benchmark logs nim-bench-h100-throughput-202602061200
```

**`benchmark export`** - Export results to JSON or CSV

```bash
runai-cli benchmark export nim-bench-h100-throughput-202602061200 --format csv
```

**`benchmark list-gpus`** / **`benchmark list-scenarios`** - Show available options

```bash
runai-cli benchmark list-gpus
runai-cli benchmark list-scenarios
```

**[📖 Full Benchmark Documentation →](docs/BENCHMARK.md)**

### Connection Management

**`connect <target>`** - Connect to a remote agent or switch to local mode

```bash
# Connect to remote agent
runai-cli connect https://agent.example.com:8000

# Connect using IP address
runai-cli connect http://192.168.1.50:8000

# Skip connection verification (if agent is temporarily offline)
runai-cli connect https://agent.example.com:8000 --no-verify

# Switch back to local mode
runai-cli connect local
```

Options:
- `--no-verify` - Skip connection verification

**[📖 Full Remote Agent Guide →](docs/REMOTE_AGENT.md)**

### Configuration

**`config show`** - Show current configuration

```bash
runai-cli config show
```

**`config set <key> <value>`** - Set a configuration value

```bash
runai-cli config set agentUrl http://localhost:8000
runai-cli config set timeout 30000
runai-cli config set stream true
runai-cli config set debug true
```

Valid configuration keys:
- `agentUrl` - Agent server URL (default: `http://localhost:8000`) - Use `connect` command instead
- `timeout` - Request timeout in milliseconds (default: `60000`)
- `stream` - Enable streaming responses (default: `false`)
- `debug` - Enable debug output (default: `false`)

### Conversation memory (user ID)

When the agent uses Redis-backed conversation memory, each request is scoped by a **user ID** so the agent can recall context per user. The CLI sends this from the **`RUNAI_USER_ID`** environment variable; if unset, it uses **`default_user`**.

- **Single user / dev:** Leaving it unset is fine; your context is stored under `default_user`.
- **Multi-user or shared agent:** Set a unique ID per user so memories don’t mix (e.g. `RUNAI_USER_ID=alice runai-cli ask "..."`). Otherwise everyone without `RUNAI_USER_ID` shares the same `default_user` memory. See [Conversation Memory](../docs/CONVERSATION_MEMORY.md).

**`config reset`** - Reset configuration to defaults

```bash
runai-cli config reset
```

## Configuration File

Configuration is stored in `~/.runai-cli/config.json`:

```json
{
  "agentUrl": "http://localhost:8000",
  "timeout": 60000,
  "stream": false,
  "debug": false
}
```

## Development

### Project Structure

```
runai-cli/
├── bin/
│   └── runai-cli.js           # Executable entry point
├── src/
│   ├── index.ts               # Main CLI entry point
│   ├── commands/              # Command implementations
│   │   ├── agent.ts           # Agent query commands
│   │   ├── benchmark.ts       # NIM benchmark commands (NEW)
│   │   ├── job.ts             # Job operations
│   │   ├── environment.ts     # Environment operations
│   │   ├── server.ts          # Server management
│   │   ├── submit.ts          # Natural-language submit
│   │   └── repl.ts            # Interactive REPL mode
│   ├── benchmark/             # NVIDIA NIM benchmark module (NEW)
│   │   ├── index.ts           # Barrel export
│   │   ├── types.ts           # Benchmark types & interfaces
│   │   ├── configs.ts         # GPU profiles & scenario configs
│   │   ├── env.ts             # .env loader & validation
│   │   ├── runner.ts          # Job builder, submit & monitor
│   │   └── results.ts         # JSON/CSV export & summary
│   ├── api/
│   │   └── client.ts          # NAT REST API client
│   ├── utils/
│   │   ├── config.ts          # Config file management
│   │   ├── logger.ts          # Pretty logging
│   │   └── validation.ts      # Input validation
│   └── types/
│       └── index.ts           # Shared types
├── docs/
│   ├── BENCHMARK.md           # Benchmark documentation (NEW)
│   ├── NATURAL_LANGUAGE_GUIDE.md
│   ├── QUICKSTART_EXAMPLES.md
│   └── REMOTE_CONNECTION.md
├── package.json
├── tsconfig.json
└── README.md
```

### Build & Run

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run in development mode (no build needed)
npm run dev -- ask "Show me all projects"

# Run compiled version
npm start -- ask "Show me all projects"

# Watch mode (auto-rebuild on changes)
npm run watch
```

### Clean Build

```bash
npm run clean
npm run build
```

## Examples

### Example 1: Quick Status Check

```bash
$ runai-cli ask "Show me all projects"

✓ Processing complete

Here are the available projects:

- **project-01**
  - Project ID: prj-123
  - Namespace: runai-project-01
  - Cluster: my-cluster
  - GPU Quota: 8 GPU(s)
```

### Example 2: Interactive Session

```bash
$ runai-cli chat

🤖 RunAI Agent CLI - Interactive Mode
────────────────────────────────────────
ℹ Connected to: http://localhost:8000
Type your query and press Enter. Type "exit" or "quit" to leave.

> Show me all projects

Here are the available projects:
- project-01 (8 GPUs)
- project-02 (4 GPUs)

> Submit a training job to project-01 with 2 GPUs

✓ Training job submitted successfully!
Job Details:
- Name: training-job-1234
- Project: project-01
- GPUs: 2

> exit

👋 Goodbye!
```

### Example 3: Job Submission

Create a job spec file `job.json`:

```json
{
  "name": "pytorch-training",
  "project": "project-01",
  "image": "nvcr.io/nvidia/pytorch:24.01-py3",
  "gpu": 2,
  "cpuCores": 8,
  "memory": "32Gi",
  "command": "python",
  "args": ["train.py", "--dataset", "imagenet", "--epochs", "100"],
  "environmentVariables": {
    "NCCL_DEBUG": "INFO"
  }
}
```

Submit the job:

```bash
$ runai-cli job submit job.json

✓ Job submitted successfully!

Job Details:
- Name: pytorch-training
- Project: project-01
- GPUs: 2
- Status: Pending
```

### Example 4: Server Management

```bash
# Start server in background
$ runai-cli server start --background
✓ Server started in background
ℹ Process ID: 12345
ℹ Server URL: http://localhost:8000

# Check status
$ runai-cli server status
✓ Agent server is running at http://localhost:8000
ℹ Process ID: 12345

# Stop server
$ runai-cli server stop
ℹ Stopping server (PID: 12345)...
✓ Server stopped
```

## Testing & Verification

### Automated Verification Script

A comprehensive test script is available to verify your CLI installation:

```bash
# Run the verification script
./scripts/verify-cli.sh
```

This script will:
- ✅ Check Node.js and npm versions
- ✅ Verify TypeScript compilation
- ✅ Test all CLI commands
- ✅ Validate configuration management
- ✅ Check server connectivity

## Troubleshooting

### Server Not Running

```bash
$ runai-cli ask "test"
✗ Agent server is not running at http://localhost:8000
ℹ Start the server with: runai-cli server start
```

**Solution**: Start the server with `runai-cli server start`

### Connection Timeout

```bash
✗ Request timed out. The agent might be processing a complex query.
```

**Solution**: Increase timeout with `runai-cli config set timeout 120000`

### Invalid Configuration

```bash
✗ Failed to parse config file, using defaults
```

**Solution**: Reset configuration with `runai-cli config reset`

### Command Not Found

```bash
bash: runai-cli: command not found
```

**Solution**: Run `npm link` from the `runai-cli` directory

## Architecture

The CLI follows a clean architecture:

1. **Command Parser** (Commander.js) - Parses CLI arguments and routes to handlers
2. **Command Handlers** (`src/commands/*.ts`) - Implement business logic for each command
3. **API Client** (`src/api/client.ts`) - Handles HTTP communication with NAT server
4. **Utilities** (`src/utils/*.ts`) - Shared functionality (logging, config, validation)

### Data Flow

```
User Input
   ↓
Command Parser (Commander.js)
   ↓
Command Handler (src/commands/*.ts)
   ↓
API Client (src/api/client.ts)
   ↓
HTTP Request → NAT Server (Python)
   ↓
Agent Processing (LLM + Tools)
   ↓
HTTP Response ← NAT Server
   ↓
Response Formatter (logger, colors)
   ↓
Terminal Output
```

## API Reference

### RunAIAgentClient

The core API client for communicating with the NAT server.

```typescript
import { RunAIAgentClient } from './api/client.js';

const client = new RunAIAgentClient('http://localhost:8000', 60000);

// Send a query
const response = await client.query('Show me all projects');

// Stream a query
for await (const chunk of client.queryStream('Generate a job')) {
  console.log(chunk);
}

// Health check
const health = await client.healthCheck();
console.log(health.running); // true/false
```

## License

Copyright (c) 2024 NVIDIA Corporation. All rights reserved.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the NAT agent logs
3. Ensure environment variables are set correctly
4. Verify the NAT server is running and accessible

