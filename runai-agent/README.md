# RunAI Agent

A specialized NeMo Agent Toolkit (NAT) agent for RunAI Labs with RAG-enhanced code search and intelligent job generation.

## Features

- **Environment Information**: Get RunAI Labs cluster and project details
- **Environment Creation**: 🆕 Create reusable environment templates with resource configs
- **Job Generation**: Generate complete job submission code for:
  - Interactive Jupyter workspaces
  - Single-GPU training jobs
  - Multi-GPU distributed training
  - Model inference/serving
- **Job Management**: Submit, monitor, and manage lifecycle (suspend, resume, delete) for all workload types
- **REST API Executor**: 🧠 LLM-driven REST API code generator for datasource assets (NFS, PVC, Git - full CRUD operations)
  - Docs-based code generation using `webpage_query`
  - Zero hardcoded templates - dynamically adapts to any resource type
  - OAuth authentication and SSL verification
  - Dry-run and confirmation workflows
- **Code Search**: Semantic search over the Runapy SDK codebase
- **Repository Indexing**: Automatic indexing of the Runapy GitHub repository
- **Code Analysis**: Analyze code patterns and best practices
- **Code Generation**: Generate optimized Runapy SDK code templates
- **Documentation Search**: Search and index Run:ai documentation

## Documentation

### Guides
- **[Environment Creation Guide](docs/environment_creation_guide.md)** - Complete guide for creating Run:AI environment templates
  - Configuration options and field specifications
  - 10+ usage examples and scenarios
  - Validation rules and best practices
  - Error handling and troubleshooting
  - Integration with job submission

### Feature Documentation
- **[Environment Creation Feature Overview](../docs/ENVIRONMENT_CREATION_FEATURE.md)** - Summary of the environment creation feature
  - What was created and why
  - Quick start examples
  - Configuration and safety features
  - Testing instructions

### Examples
- **[Environment Creation Examples](examples/create_environment_example.py)** - 10 practical code examples
  - Basic ML training environment
  - Distributed training setup
  - Production inference environment
  - Complete workflow examples

## Installation

### Prerequisites

**macOS Users:** If you encounter OpenMP library conflicts, set this environment variable:
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
# Add to your ~/.zshrc or ~/.bashrc to make it permanent:
echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.zshrc
```

### Setup

1. **Create a virtual environment:**

```bash
cd /path/to/runai-agent-test
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install the RunAI Agent (includes NAT 1.3.1):**

```bash
cd nemo-agent-toolkit-custom
pip install -e .
```

3. **Install the webpage_query plugin (required for doc search):**

```bash
pip install "git+https://github.com/NVIDIA/NeMo-Agent-Toolkit.git@v1.3.1#subdirectory=examples/getting_started/simple_web_query"
```

> **Note:** The `nat_simple_web_query` plugin is not available on PyPI and must be installed from the NAT GitHub repository. This plugin provides the `webpage_query` tool used by `runai_docs_search` and `runai_api_docs` functions.

### Environment Variables

Set up the required environment variables:

```bash
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="[YOUR_RUNAI_BASE_URL]"
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
```

## Usage

### Run the Agent

```bash
nat run --config_file src/runai_agent/configs/config.yml --input "Show me how to create a Jupyter workspace"
```

### Serve as API

```bash
nat serve --config_file src/runai_agent/configs/config.yml --host 0.0.0.0 --port 8000
```

Then access the API documentation at: http://localhost:8000/docs

## Configuration

The agent is configured via `configs/config.yml`. Key configuration options:

### Functions

#### Environment Management
- `runailabs_environment_info`: Display environment details
- `runai_create_environment`: 🆕 Create reusable environment templates
- `runai_delete_environment`: 🆕 Delete environment templates

#### Job Operations
- `runailabs_job_generator`: Generate job submission code
- `runai_submit_workload`: Submit single-node training jobs
- `runai_submit_distributed_workload`: Submit distributed training jobs
- `runai_submit_workspace`: Submit interactive workspaces
- `runai_job_status`: Check job status
- `runai_manage_workload`: 🎯 Unified lifecycle management (suspend, resume, delete)
- `runai_llm_executor`: 🧠 LLM-driven REST API executor for datasource assets (NFS, PVC, Git - create, list, delete)
- `runai_kubectl_troubleshoot`: Deep troubleshooting with logs and events

#### Code & Documentation
- `runapy_code_search`: Search the Runapy codebase
- `runapy_repo_indexer`: Index the Runapy repository
- `runapy_code_analyzer`: Analyze code patterns
- `runapy_code_generator`: Generate SDK code templates
- `runai_docs_indexer`: Index Run:ai documentation
- `runai_docs_search`: Search Run:ai docs

### LLM Configuration

The agent uses NVIDIA NIM with Llama 3.1 70B by default. You can customize the LLM in the config file.

## Example Queries

### Environment Management
- "Show me the current environment setup"
- "Create a new ML training environment with 4 GPUs"
- "Set up a Jupyter environment template"
- "Create environment named my-env with busybox image for workspace and training" ✅ **Tested & Working!**
- "Delete the environment named test-env"
- "Remove environment busybox-test"

### Job Operations
- "Generate a Jupyter workspace job"
- "Submit a training job with 2 GPUs"
- "Create a distributed training job with 4 workers"
- "Check the status of my training job"

### REST API Executor (Datasources & Projects - LLM-Driven)

**🧠 Hybrid LLM-Driven Code Generator with Teaching Examples**

The `runai_llm_executor` dynamically generates and executes REST API code for datasource and project operations using:
- **5 Core Teaching Patterns** that cover 90% of Run:AI API use cases
- **Swagger for Discovery** - Dynamically finds endpoints and field names
- **LLM Pattern Learning** - Adapts teaching examples to new resource types
- **No Hardcoded Templates** - Pure generalization from patterns

**Architecture:**
- ✅ **Pattern 1**: Org-Unit Resources (Projects, Departments) with cluster lookup
- ✅ **Pattern 2**: Datasource Assets - Flat Spec (NFS, Git, S3)
- ✅ **Pattern 3**: Datasource Assets - Nested Spec (PVC with claimInfo)
- ✅ **Pattern 4**: LIST/GET Operations (simple GET requests)
- ✅ **Pattern 5**: DELETE Operations (resource name in path)

**NFS (Network File System) Operations:**
- "Create an NFS datasource named my-nfs in test-project with server 192.168.1.100 and path /data" ✅ **Tested!**
- "List all NFS datasources" ✅ **Tested!**
- "Show me NFS storage in project test-project" ✅ **Tested!**
- "Delete the NFS datasource named my-nfs"

**PVC (Persistent Volume Claims) Operations:**
- "Create a PVC named test-pvc-storage with 10Gi storage in test-project" ✅ **Tested!**
- "Create a 50Gi volume named training-data in test-project"
- "List all PVC datasources" ✅ **Tested!**
- "Show me all PVC datasources" ✅ **Tested!**
- "Delete the PVC named test-pvc-storage from test-project" ✅ **Tested!**

**Git Datasource Operations:**
- "Create a Git datasource named code-repo with repository https://github.com/nvidia/nemo branch main in test-project" ✅ **Tested!**
- "List all Git datasources"
- "Show me Git storage in test-project"
- "Delete the Git datasource named code-repo"

**Project Operations:**
- "Create a project named test-project with 4 GPU quota" ✅ **Tested!**
- "Create a department named test-dept with 8 GPU quota" ✅ **Tested!**
- "List all projects"

**Features:**
- ✅ **Teaching Examples**: 5 core patterns that LLM adapts to new resources
- ✅ **Swagger Integration**: Dynamic endpoint discovery and field validation
- ✅ **Pattern Learning**: Generalizes from examples (no hardcoding!)
- ✅ **SSL Verification**: Secure HTTPS with certificate checking
- ✅ **OAuth Authentication**: Proper Run:AI API authentication flow
- ✅ **Smart Routing**: Explicit tool descriptions for reliable agent routing
- ✅ **10/10 Tests Passing**: Full CRUD operations validated

### Workload Lifecycle Management
- "Suspend the job named training-job-1"
- "Resume the job named my-training"
- "Delete the completed job"

### Code & Documentation
- "How do I submit a training job with the Runapy SDK?"
- "Search for job submission examples in the Runapy codebase"
- "What are the best practices for RunAI job configuration?"
- "Show me examples of distributed training"

## Architecture

The agent uses a ReAct (Reasoning + Acting) architecture with:

- **Tools**: Specialized functions for different RunAI operations
- **RAG**: Semantic search over Runapy codebase and documentation
- **Query Classification**: Intelligent routing to optimal embedding models
- **Auto-indexing**: Automatic repository indexing on startup

## Development

### Project Structure

```
runai_agent/
├── __init__.py              # Package initialization
├── register.py              # Function registration
├── runai_agent_function.py  # Main function implementations (includes GitHub example fetcher)
├── query_classifier.py      # Query classification for optimal search
├── configs/
│   └── config.yml          # Agent configuration
├── pyproject.toml          # Package metadata
└── README.md               # This file
```

### Adding New Functions

1. Define the function config class in `runai_agent_function.py`
2. Implement the function logic
3. Register with `@register_function` decorator
4. Add to `configs/config.yml` workflow

## Troubleshooting

### GitHub API Rate Limiting

If you encounter GitHub API rate limits when fetching code examples, set a GitHub token:

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

Get a token at: https://github.com/settings/tokens

### Import Errors

Ensure you're using the NAT virtual environment:

```bash
cd /path/to/runai-agent-test
source .venv/bin/activate
```

### Environment Variables

Verify all required environment variables are set:

```bash
echo $RUNAI_CLIENT_ID
echo $RUNAI_CLIENT_SECRET
echo $RUNAI_BASE_URL
echo $NVIDIA_API_KEY
```

## License

Copyright (c) 2024 NVIDIA Corporation. All rights reserved.
