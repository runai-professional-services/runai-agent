"""
Run:AI LLM-Driven REST API Executor - Dynamic Code Generation

Dynamically generates and executes REST API code for Run:AI datasource assets.
Supports NFS and PVC operations without hardcoded templates.
"""

import os
from typing import List, Literal, Optional, Dict, Any
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils.helpers import _get_secure_runai_config, logger
from ..rest_api import SwaggerFetcher, EndpointFinder


def _simplify_schema_for_llm(schema: Dict[str, Any], max_depth: int = 4, current_depth: int = 0) -> Dict[str, Any]:
    """
    Simplify a Swagger schema for LLM consumption by keeping only essential fields
    
    Args:
        schema: Full resolved Swagger schema
        max_depth: Maximum nesting depth to traverse (increased to 4 for spec details)
        current_depth: Current recursion depth
        
    Returns:
        Simplified schema with only: type, required fields, examples, enum values
    """
    if not isinstance(schema, dict) or current_depth >= max_depth:
        return schema
    
    simplified = {}
    
    # Keep essential top-level fields
    for key in ['type', 'required', 'enum', 'example']:
        if key in schema:
            simplified[key] = schema[key]
    
    # Keep description only for root level (not nested)
    if current_depth == 0 and 'description' in schema:
        simplified['description'] = schema['description']
    
    # Simplify properties recursively
    if 'properties' in schema:
        simplified['properties'] = {}
        for prop_name, prop_schema in schema['properties'].items():
            if isinstance(prop_schema, dict):
                # For each property, keep only: type, example, enum, format, nested properties
                simplified_prop = {}
                for key in ['type', 'example', 'enum', 'format']:
                    if key in prop_schema:
                        simplified_prop[key] = prop_schema[key]
                
                # Recursively simplify nested properties (important for spec!)
                if 'properties' in prop_schema:
                    nested_simplified = _simplify_schema_for_llm(prop_schema, max_depth, current_depth + 1)
                    if 'properties' in nested_simplified:
                        simplified_prop['properties'] = nested_simplified['properties']
                    if 'required' in nested_simplified:
                        simplified_prop['required'] = nested_simplified['required']
                
                # Keep required fields if they exist at this level
                if 'required' in prop_schema:
                    simplified_prop['required'] = prop_schema['required']
                
                simplified['properties'][prop_name] = simplified_prop
    
    return simplified


def _validate_generated_code(code: str) -> Optional[str]:
    """
    Validate generated code for common issues
    
    Args:
        code: Generated Python code string
        
    Returns:
        Error message if validation fails, None if code is valid
    """
    if not code or not code.strip():
        return "Generated code is empty"
    
    # Check minimum length (realistic API code should be at least 200 chars)
    if len(code) < 200:
        return f"Generated code is suspiciously short ({len(code)} chars). Expected at least 200 characters."
    
    # Check for basic syntax errors (try to compile)
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        return f"Syntax error in generated code: {e}"
    
    # Check for required imports
    if 'import requests' not in code:
        return "Generated code missing required 'import requests'"
    
    # Check for result variable (expected in all patterns)
    if 'result =' not in code and 'result=' not in code:
        return "Generated code doesn't set 'result' variable (required for output)"
    
    # Check for unterminated strings (common truncation issue)
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        # Count quotes (ignoring escaped quotes)
        cleaned = line.replace(r'\"', '').replace(r"\'", '')
        single_quotes = cleaned.count("'")
        double_quotes = cleaned.count('"')
        
        # Basic check: odd number of quotes likely means unterminated string
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            # Last line might be incomplete if truncated
            if i == len(lines):
                return f"Generated code appears truncated (line {i} has unterminated string)"
    
    return None  # Validation passed


class RunaiLLMSmartExecutorConfig(FunctionBaseConfig, name="runai_llm_executor"):
    """Configuration for LLM-Driven Smart Executor - UNRESTRICTED MODE"""
    description: str = (
        "Manage datasources and projects ONLY (NFS, PVC, Git, S3, HostPath storage + project create/list/delete). "
        "Use for: creating/listing/deleting NFS, PVC, Git datasources; creating projects with GPU quotas. "
        "Do NOT use for: workloads, training jobs, distributed jobs, workspace submissions, job status, "
        "environments, kubectl troubleshooting, or code generation."
    )
    allowed_projects: List[str] = Field(
        default_factory=lambda: ["*"],  # ✅ Allow ALL projects
        description="List of projects where smart execution is allowed ('*' = all)"
    )
    require_confirmation: bool = Field(
        default=False,  # ✅ No confirmation needed
        description="Require explicit confirmation before executing generated code"
    )
    dry_run_default: bool = Field(
        default=False,  # ✅ Execute by default
        description="Show generated code by default before execution"
    )
    allowed_resource_types: List[str] = Field(
        default_factory=lambda: ["*"],  # ✅ Allow ALL resource types
        description="List of resource types that can be managed ('*' = all)"
    )


@register_function(config_type=RunaiLLMSmartExecutorConfig)
async def runai_llm_executor(config: RunaiLLMSmartExecutorConfig, builder: Builder):
    """
    Manage datasources and projects ONLY (NFS, PVC, Git, S3 storage + project create/list/delete).
    
    ✅ USE THIS TOOL FOR:
    - Datasource operations: NFS, PVC, Git, S3, HostPath storage (create/list/delete)
    - Project operations: Create projects with GPU quotas, list projects, delete projects
    
    ❌ DO NOT USE FOR:
    - Workloads, training jobs, distributed jobs, workspace submissions
    - Job status or job lifecycle operations
    - Environments or kubectl troubleshooting
    
    SPECIFIC USE CASES:
    - "Create an NFS datasource named X"
    - "List all PVC datasources"
    - "Delete Git datasource named Y"
    - "Create a project with 8 GPU quota"
    
    Parameters:
    - action: "create", "list", or "delete"
    - project: Project name (required for all operations)
    - resource_type: "nfs" for Network File System, "pvc" for Persistent Volume Claims
    - resource_name: Name of the resource (required for create/delete)
    - server: NFS server IP or hostname (required for NFS create, e.g., "192.168.1.100")
    - path: NFS export path (required for NFS create, e.g., "/data" or "/exports/shared")
    - size: Storage size for PVC (required for PVC create, e.g., "10Gi", "100Gi")
    - dry_run: True to preview code, False to execute (default: True)
    - confirmed: True to skip confirmation (default: False)
    
    Examples:
    User: "Create an NFS datasource named ml-data in project-01 with server 10.0.1.50 and path /data"
    User: "List all NFS resources in project-01"
    User: "Create a 50Gi PVC named training-data in project-01"
    User: "Show me all storage volumes in project-01"
    """
    
    async def _execute_llm_operation(
        action: str,
        resource_type: str = "nfs",
        project: str = "",
        resource_name: str = "",
        server: str = "",
        path: str = "",
        size: str = "",
        repository: str = "",
        branch: str = "",
        bucket: str = "",
        endpoint: str = "",
        dry_run: bool = True,
        confirmed: bool = False
    ) -> str:
        """
        Execute a Run:AI REST API operation using dynamically generated code
        
        Args:
            action: Action to perform (create, delete, list)
            resource_type: Type of resource (nfs, pvc, git, project, etc.)
            project: Project name (required for datasources, optional for top-level resources like projects)
            resource_type: Type of resource (e.g., "nfs", "pvc", "git")
            resource_name: Name of the resource
            server: NFS server address (for NFS create)
            path: NFS export path (for NFS create) or Git container mount path
            size: Storage size (for PVC create, e.g., "10Gi", "100Gi")
            repository: Git repository URL (for Git create, e.g., "https://github.com/user/repo")
            branch: Git branch name (for Git create, e.g., "main", "develop")
            dry_run: If True, show generated code without executing
            confirmed: If True, execute the operation
            
        Returns:
            Status message with operation results or generated code
        """
        
        logger.info(f"LLM Smart Executor: {action} {resource_type} in project {project}")
        logger.info(f"Parameters received - repository: '{repository}', branch: '{branch}', server: '{server}', path: '{path}', size: '{size}', bucket: '{bucket}', endpoint: '{endpoint}'")
        
        # === VALIDATION ===
        errors = []
        
        # Resource type validation (skip if wildcard "*" is in allowed list)
        if "*" not in config.allowed_resource_types and resource_type not in config.allowed_resource_types:
            errors.append(f"Resource type '{resource_type}' not allowed. Supported: {config.allowed_resource_types}")
        
        # Project validation (skip for project creation - we're creating the project itself!)
        # Skip validation if wildcard "*" is in allowed list
        if (resource_type != "project" and project and 
            "*" not in config.allowed_projects and 
            project not in config.allowed_projects):
            errors.append(f"Project '{project}' not in allowed list: {config.allowed_projects}")
        
        # Action-specific validation
        if action in ["create", "delete"]:
            if not resource_name or not resource_name.strip():
                errors.append(f"resource_name is required for {action} operations")
        
        if action == "create" and resource_type == "nfs":
            if not server or not server.strip():
                errors.append("server is required for NFS creation (e.g., 'nfs-server.example.com')")
            if not path or not path.strip():
                errors.append("path is required for NFS creation (e.g., '/exports/data')")
        
        if action == "create" and resource_type == "pvc":
            if not size or not size.strip():
                errors.append("size is required for PVC creation (e.g., '10Gi', '100Gi')")
        
        if action == "create" and resource_type == "git":
            if not repository or not repository.strip():
                errors.append("repository is required for Git creation (e.g., 'https://github.com/user/repo')")
            if not branch or not branch.strip():
                errors.append("branch is required for Git creation (e.g., 'main', 'develop')")
        
        if errors:
            error_msg = "\n".join([f"  • {err}" for err in errors])
            return f"""
❌ **LLM Smart Executor Validation Failed**

{error_msg}

Please fix these issues and try again.
"""
        
        # === CONFIRMATION FLOW ===
        if config.require_confirmation and not dry_run and not confirmed:
            return f"""
⚠️  **Confirm Dynamic LLM Execution**

You are about to execute LLM-generated code:
- **Resource Type:** {resource_type}
- **Action:** {action}
- **Project:** {project}
{f"- **Resource Name:** {resource_name}" if resource_name else ""}
{f"- **Server:** {server}" if server else ""}
{f"- **Path:** {path}" if path else ""}

**To see the generated code first, call with `dry_run=True`**
**To execute, call again with `confirmed=True` and `dry_run=False`**
"""
        
        # === LLM CODE GENERATION ===
        try:
            # Generate code using LLM (pass builder to access LLM)
            generated_code = await _generate_code_with_llm(
                builder=builder,
                resource_type=resource_type,
                action=action,
                project=project,
                resource_name=resource_name,
                server=server,
                path=path,
                size=size,
                repository=repository,
                branch=branch,
                bucket=bucket,
                endpoint=endpoint
            )
            
            # DRY RUN: Show code without executing
            if dry_run:
                return f"""
🤖 **LLM-Generated Code (Dry Run Mode)**

The LLM has dynamically generated the following code:

```python
{generated_code}
```

**To execute this code:**
Call the function again with:
- `dry_run=False`
- `confirmed=True`

**This code was generated by AI** based on SDK patterns and documentation.
Please review carefully before execution.
"""
            
            # EXECUTE: Run the LLM-generated code
            logger.info(f"Executing LLM-generated code for {action} {resource_type}")
            
            # Get secure configuration
            secure_config = _get_secure_runai_config()
            
            if not all([secure_config['RUNAI_CLIENT_ID'], 
                       secure_config['RUNAI_CLIENT_SECRET'], 
                       secure_config['RUNAI_BASE_URL']]):
                return "❌ Error: Run:AI credentials not configured. Please set RUNAI_CLIENT_ID, RUNAI_CLIENT_SECRET, and RUNAI_BASE_URL environment variables."
            
            # Create execution environment with REST API support
            import requests
            exec_globals = {
                'requests': requests,
                'client_id': secure_config['RUNAI_CLIENT_ID'],
                'client_secret': secure_config['RUNAI_CLIENT_SECRET'],
                'base_url': secure_config['RUNAI_BASE_URL'],
                # User-provided parameters for code generation
                'resource_name': resource_name,
                'project': project,
                'server': server,
                'path': path,
                'size': size,
                'repository': repository,
                'branch': branch,
                'bucket': bucket,
                'endpoint': endpoint,
            }
            exec_locals = {}
            
            # Execute the LLM-generated code with detailed error capture
            try:
                exec(generated_code, exec_globals, exec_locals)
            except requests.exceptions.HTTPError as http_err:
                # Capture detailed API error response
                error_details = "No response body available"
                status_code = "Unknown"
                if hasattr(http_err, 'response') and http_err.response is not None:
                    status_code = http_err.response.status_code
                    try:
                        error_details = http_err.response.text
                        logger.error(f"❌ HTTP {status_code} Error Response: {error_details}")
                    except:
                        pass
                raise Exception(f"API Error: HTTP {status_code} - {str(http_err)}\nResponse: {error_details}")
            except Exception as e:
                # Log any other execution errors with context
                logger.error(f"❌ Code execution error: {type(e).__name__}: {str(e)}")
                # Try to extract response info if available in locals
                if 'response' in exec_locals:
                    resp = exec_locals['response']
                    logger.error(f"📋 Response Status: {resp.status_code if hasattr(resp, 'status_code') else 'N/A'}")
                    logger.error(f"📋 Response Headers: {dict(resp.headers) if hasattr(resp, 'headers') else 'N/A'}")
                    logger.error(f"📋 Response Text (first 500 chars): {resp.text[:500] if hasattr(resp, 'text') else 'N/A'}")
                raise
            
            # Get the result
            result = exec_locals.get('result', 'Operation completed successfully')
            
            return f"""
✅ **LLM-Generated Code Executed Successfully!**

**Action:** {action.title()} {resource_type.upper()}
**Project:** {project}
{f"**Resource:** {resource_name}" if resource_name else ""}

**Result:**
{result}

**LLM-Generated Code:**
```python
{generated_code}
```

🤖 **This code was dynamically generated by AI** - no templates used!
"""
        
        except Exception as e:
            logger.error(f"LLM execution error: {e}")
            return f"""
❌ **LLM Execution Failed**

**Error:** {str(e)}

**Context:**
- Resource Type: {resource_type}
- Action: {action}
- Project: {project}

The LLM-generated code encountered an error during execution.
This may indicate:
1. API structure has changed
2. Invalid parameters
3. Missing required fields

Try reviewing the generated code in dry-run mode first.
"""
    
    async def _generate_code_from_api_docs(
        builder,
        resource_type: str,
        action: str,
        project: str,
        resource_name: str,
        server: str = "",
        path: str = "",
        size: str = "",
        repository: str = "",
        branch: str = "",
        bucket: str = "",
        endpoint: str = ""
    ) -> Optional[str]:
        """
        ✨ SIMPLIFIED APPROACH: Generate code by reading API docs with webpage_query
        
        Much simpler than parsing OpenAPI specs:
        1. Use webpage_query to search API docs for examples
        2. LLM reads human-readable docs with working examples
        3. LLM generates code based on real docs
        4. Execute!
        
        Returns:
            Generated Python code string or None if generation fails
        """
        logger.info("📚 Searching API docs for endpoint examples...")
        
        # Get Run:AI credentials
        secure_config = _get_secure_runai_config()
        base_url = secure_config['RUNAI_BASE_URL']
        client_id = secure_config['RUNAI_CLIENT_ID']
        client_secret = secure_config['RUNAI_CLIENT_SECRET']
        
        if not all([base_url, client_id, client_secret]):
            logger.error("Missing Run:AI credentials")
            return None
        
        try:
            api_docs_context = ""
            import json
            
            # For GET/DELETE, skip Swagger entirely (teaching examples are sufficient)
            if action.lower() in ['list', 'get', 'delete', 'remove']:
                logger.info(f"Step 1: Skipping Swagger for '{action}' operation (using teaching examples)")
                api_docs_context = f"""
OPERATION: {action.upper()} {resource_type}
NOTE: Use Pattern 4 (for list/get) or Pattern 5 (for delete) from the teaching examples.
"""
            else:
                # For CREATE/UPDATE, fetch actual API schema from Swagger
                logger.info(f"Step 1: Fetching Swagger schema for '{action} {resource_type}'...")
                
                # Initialize Swagger fetcher
                swagger_fetcher = SwaggerFetcher(base_url, client_id, client_secret)
                endpoint_finder = EndpointFinder(swagger_fetcher)
                
                # Find the correct endpoint for this resource type and action
                logger.info(f"Searching for endpoint: {resource_type} {action}")
                endpoint_match = endpoint_finder.find_endpoint(
                    resource_type=resource_type,
                    action=action,
                    description=f"{action} {resource_type} with provided parameters"
                )
                
                if endpoint_match:
                    logger.info(f"✓ Found endpoint: {endpoint_match.method} {endpoint_match.path} (score: {endpoint_match.score:.2f})")
                    
                    # Get detailed endpoint information including schema
                    endpoint_details = endpoint_finder.get_endpoint_details(endpoint_match)
                    
                    # Include request body schema
                    request_schema = endpoint_details.get('request_schema', {})
                    
                    # Build a simplified schema with only essential info
                    simplified = _simplify_schema_for_llm(request_schema)
                    schema_json = json.dumps(simplified, indent=2) if simplified else "No schema available"
                    
                    api_docs_context = f"""
ENDPOINT: {endpoint_details['method']} {endpoint_details['path']}
DESCRIPTION: {endpoint_details.get('description', 'N/A')}

REQUEST BODY SCHEMA (simplified):
{schema_json}
"""
                else:
                    logger.warning(f"⚠️  No endpoint found for {resource_type} {action}, using teaching examples only")
                    api_docs_context = f"No specific endpoint found. Use teaching examples for {action} {resource_type}."
            
            # DEBUG: Log the actual schema being passed to LLM
            logger.info("=" * 80)
            logger.info("SCHEMA PASSED TO LLM:")
            logger.info("=" * 80)
            lines = api_docs_context.split('\n')
            for i, line in enumerate(lines[:50], 1):
                logger.info(f"  {i}: {line}")
            if len(lines) > 50:
                logger.info(f"  ... ({len(lines) - 50} more lines)")
            logger.info("=" * 80)
            
            # Step 2: Generate code using LLM with API docs context
            logger.info(f"Step 2: Generating Python code with LLM...")
            
            # Get LLM
            llm = await builder.get_llm("demo_llm", wrapper_type=LLMFrameworkEnum.LANGCHAIN)
            
            # Build comprehensive prompt with API docs
            prompt = f"""You are a Python expert generating Run:AI REST API code.

TASK: Generate Python code to {action} a {resource_type} resource in Run:AI.

USER PARAMETERS:
- Resource Name: {resource_name}
{f"- Project: {project}" if project else ""}
{f"- Server: {server}" if server else ""}
{f"- Path: {path}" if path else ""}
{f"- Size: {size}" if size else ""}
{f"- Repository: {repository}" if repository else ""}
{f"- Branch: {branch}" if branch else ""}
{f"- Bucket: {bucket}" if bucket else ""}
{f"- Endpoint: {endpoint}" if endpoint else ""}

SWAGGER API SCHEMA:
{api_docs_context}

PRE-INJECTED VARIABLES (DO NOT DEFINE THESE):
- base_url: Already provided in execution context
- client_id: Already provided in execution context
- client_secret: Already provided in execution context

TEACHING EXAMPLES (Learn these patterns and adapt to Swagger schema):

=== PATTERN 1: ORG-UNIT RESOURCES (Projects, Departments) ===
Example: Create Project with GPU quota
```python
import requests

# Auth
token_url = f"{{{{base_url}}}}/api/v1/token"
token_response = requests.post(token_url, json={{{{
    "grantType": "client_credentials",
    "clientId": client_id,
    "clientSecret": client_secret
}}}}, verify=True)
access_token = token_response.json()["accessToken"]
headers = {{"Authorization": f"Bearer {{{{access_token}}}}", "Content-Type": "application/json"}}

# Get cluster ID (required for projects/departments)
clusters_response = requests.get(f"{{{{base_url}}}}/api/v1/clusters", headers=headers, verify=True)
clusters_response.raise_for_status()
clusters = clusters_response.json()
cluster_id = clusters[0]["uuid"] if isinstance(clusters, list) and clusters else None

if not cluster_id:
    result = {{"error": "Unable to retrieve cluster ID"}}
else:
    # Create project (no meta wrapper!)
    payload = {{
        "name": "{resource_name}",
        "clusterId": cluster_id,
        "resources": [{{
            "gpu": {{"deserved": {size}}}  # or other resource quotas
        }}]
    }}
    response = requests.post(f"{{{{base_url}}}}/api/v1/org-unit/projects", headers=headers, json=payload, verify=True)
    response.raise_for_status()
    result = response.json() if response.text else {{"status": "success"}}
```

=== PATTERN 2: DATASOURCE ASSETS - FLAT SPEC (NFS, Git, HostPath) ===
Example: Create NFS datasource
```python
import requests

# Auth
token_url = f"{{{{base_url}}}}/api/v1/token"
token_response = requests.post(token_url, json={{{{
    "grantType": "client_credentials",
    "clientId": client_id,
    "clientSecret": client_secret
}}}}, verify=True)
access_token = token_response.json()["accessToken"]
headers = {{"Authorization": f"Bearer {{{{access_token}}}}", "Content-Type": "application/json"}}

# Get project info (datasources need projectId + clusterId)
projects_response = requests.get(f"{{{{base_url}}}}/api/v1/org-unit/projects", headers=headers, verify=True)
project_obj = next((p for p in projects_response.json()["projects"] if p["name"] == "{project}"), None)
project_id = int(project_obj["id"])
cluster_id = project_obj["clusterId"]

# Create datasource (meta + flat spec)
payload = {{
    "meta": {{
        "name": "{resource_name}",
        "scope": "project",
        "projectId": project_id,
        "clusterId": cluster_id
    }},
    "spec": {{
        "server": "{server}",  # or repository/path per resource type
        "path": "{path}"
    }}
}}
response = requests.post(f"{{{{base_url}}}}/api/v1/asset/datasource/nfs", headers=headers, json=payload, verify=True)
response.raise_for_status()
result = response.json()
```

=== PATTERN 2B: S3 DATASOURCE (Bucket + Credentials) ===
Example: Create S3 datasource with bucket and endpoint
```python
import requests

# Auth
token_url = f"{{{{base_url}}}}/api/v1/token"
token_response = requests.post(token_url, json={{{{
    "grantType": "client_credentials",
    "clientId": client_id,
    "clientSecret": client_secret
}}}}, verify=True)
access_token = token_response.json()["accessToken"]
headers = {{"Authorization": f"Bearer {{{{access_token}}}}", "Content-Type": "application/json"}}

# Get project info (datasources need projectId + clusterId)
projects_response = requests.get(f"{{{{base_url}}}}/api/v1/org-unit/projects", headers=headers, verify=True)
project_obj = next((p for p in projects_response.json()["projects"] if p["name"] == "{project}"), None)
project_id = int(project_obj["id"])
cluster_id = project_obj["clusterId"]

# Create S3 datasource (meta + spec with bucket/url)
payload = {{
    "meta": {{
        "name": "{resource_name}",
        "scope": "project",
        "projectId": project_id,
        "clusterId": cluster_id
    }},
    "spec": {{
        "bucket": "{bucket}",  # S3 bucket name
        "path": "/container/{bucket}",  # Container path
        "url": "{endpoint}"  # S3 endpoint URL, e.g., https://s3.amazonaws.com
        # Note: Credentials (accessKeyAssetId) typically managed separately
    }}
}}
response = requests.post(f"{{{{base_url}}}}/api/v1/asset/datasource/s3", headers=headers, json=payload, verify=True)
response.raise_for_status()
result = response.json()
```

=== PATTERN 3: DATASOURCE ASSETS - NESTED SPEC (PVC, DataVolumes) ===
Example: Create PVC with nested claimInfo
```python
import requests

# Auth
token_url = f"{{{{base_url}}}}/api/v1/token"
token_response = requests.post(token_url, json={{{{
    "grantType": "client_credentials",
    "clientId": client_id,
    "clientSecret": client_secret
}}}}, verify=True)
access_token = token_response.json()["accessToken"]
headers = {{"Authorization": f"Bearer {{{{access_token}}}}", "Content-Type": "application/json"}}

# Get project info
projects_response = requests.get(f"{{{{base_url}}}}/api/v1/org-unit/projects", headers=headers, verify=True)
project_obj = next((p for p in projects_response.json()["projects"] if p["name"] == "{project}"), None)
project_id = int(project_obj["id"])
cluster_id = project_obj["clusterId"]

# Create PVC (NOTE: nested claimInfo structure!)
payload = {{
    "meta": {{
        "name": "{resource_name}",
        "scope": "project",
        "projectId": project_id,
        "clusterId": cluster_id
    }},
    "spec": {{
        "path": "/mnt/pvc",
        "existingPvc": False,
        "claimName": "{resource_name}",
        "claimInfo": {{  # NESTED object for size/storage/access
            "size": "{size}",
            "storageClass": "default",
            "accessModes": {{
                "readWriteOnce": True,
                "readOnlyMany": False,
                "readWriteMany": False
            }}
        }}
    }}
}}
response = requests.post(f"{{{{base_url}}}}/api/v1/asset/datasource/pvc", headers=headers, json=payload, verify=True)
response.raise_for_status()
result = response.json()
```

=== PATTERN 4: LIST/GET OPERATIONS (Read datasources) ===
Example: List all datasources of a type
```python
import requests

# Auth
token_url = f"{{{{base_url}}}}/api/v1/token"
token_response = requests.post(token_url, json={{{{
    "grantType": "client_credentials",
    "clientId": client_id,
    "clientSecret": client_secret
}}}}, verify=True)
access_token = token_response.json()["accessToken"]
headers = {{"Authorization": f"Bearer {{{{access_token}}}}", "Content-Type": "application/json"}}

# GET request (no body needed)
response = requests.get(f"{{{{base_url}}}}/api/v1/asset/datasource/{resource_type}", headers=headers, verify=True)
response.raise_for_status()
result = response.json()
```

=== PATTERN 5: DELETE OPERATIONS (Remove datasources) ===
Example: Delete a specific datasource
```python
import requests

# Auth
token_url = f"{{{{base_url}}}}/api/v1/token"
token_response = requests.post(token_url, json={{{{
    "grantType": "client_credentials",
    "clientId": client_id,
    "clientSecret": client_secret
}}}}, verify=True)
access_token = token_response.json()["accessToken"]
headers = {{"Authorization": f"Bearer {{{{access_token}}}}", "Content-Type": "application/json"}}

# DELETE request (resource name in URL path)
response = requests.delete(f"{{{{base_url}}}}/api/v1/asset/datasource/{resource_type}/{resource_name}", headers=headers, verify=True)
response.raise_for_status()
result = {{"status": "deleted", "resource": "{resource_name}"}} if not response.text else response.json()
```

YOUR TASK: Adapt the pattern above that matches your action (create/list/delete) and resource type, using the Swagger schema for field names and structure.

HOW TO GENERATE CODE:
1. **Identify the pattern based on action:**
   - CREATE org-unit (project/department) → Pattern 1
   - CREATE datasource with flat spec → Pattern 2  
   - CREATE datasource with nested spec → Pattern 3
   - LIST/GET datasources → Pattern 4
   - DELETE datasources → Pattern 5
2. **Adapt the example:** Use the teaching example as a template
3. **Apply Swagger schema:** Replace field names/structure per the SCHEMA above (if provided)
4. **Keep the auth flow:** Always use the same auth code from examples

CRITICAL OUTPUT RULES:
✗ NO thinking, reasoning, explanations, or markdown fences
✗ NO <think> tags or natural language
✗ NO defining base_url, client_id, client_secret (pre-injected!)
✓ OUTPUT MUST START WITH: import requests
✓ Every line must be executable Python code
✓ Use verify=True for all requests
✓ Store final result in 'result' variable

YOUR ENTIRE OUTPUT = PURE PYTHON CODE. NO EXCEPTIONS.

Generate Python code NOW (starting with "import requests"):
"""
            
            # Generate code
            logger.info("Calling LLM to generate code...")
            generated_code_obj = await llm.ainvoke(prompt)
            generated_code = str(generated_code_obj.content if hasattr(generated_code_obj, 'content') else generated_code_obj)
            
            # Strip thinking/reasoning and markdown
            import re
            
            # Remove markdown fences
            generated_code = generated_code.replace("```python", "").replace("```", "").strip()
            
            # Remove thinking tags
            generated_code = re.sub(r'<think>.*?</think>', '', generated_code, flags=re.DOTALL).strip()
            
            # Simple extraction: Start from "import requests" and take everything after
            lines = generated_code.split('\n')
            code_lines = []
            found_import = False
            
            # Only filter out obviously wrong lines at the start/end
            for line in lines:
                # Skip until we find the import statement
                if not found_import:
                    if line.strip().startswith('import '):
                        found_import = True
                        code_lines.append(line)
                    continue
                
                # Check if this line is CLEARLY reasoning (be conservative!)
                # Only skip lines that are OBVIOUSLY not code
                stripped = line.strip()
                if (stripped.startswith('CRITICAL INSTRUCTIONS') or 
                    stripped.startswith('OUTPUT RULES') or
                    stripped.startswith('SWAGGER SCHEMA')):
                    logger.debug(f"Skipping non-code line: {line[:60]}...")
                    continue
                
                code_lines.append(line)
            
            generated_code = '\n'.join(code_lines).strip()
            logger.info(f"✅ Generated {len(generated_code)} characters of clean Python code")
            
            # Validate generated code before returning
            validation_error = _validate_generated_code(generated_code)
            if validation_error:
                raise Exception(f"Code validation failed: {validation_error}")
            
            return generated_code
                
        except Exception as e:
            logger.error(f"Modular code generation failed: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def _generate_code_with_llm(
        builder,
        resource_type: str,
        action: str,
        project: str,
        resource_name: str,
        server: str = "",
        path: str = "",
        size: str = "",
        repository: str = "",
        branch: str = "",
        bucket: str = "",
        endpoint: str = ""
    ) -> str:
        """
        ✨ SIMPLIFIED: Generate code by reading API docs with webpage_query
        
        Much simpler than complex schema parsing:
        1. Search API docs for examples
        2. LLM reads and generates code
        3. Done!
        """
        logger.info(f"📚 Docs-based generation: {action} {resource_type} in {project}")
        
        try:
            docs_driven_code = await _generate_code_from_api_docs(
                builder=builder,
                resource_type=resource_type,
                action=action,
                project=project,
                resource_name=resource_name,
                server=server,
                path=path,
                size=size,
                repository=repository,
                branch=branch,
                bucket=bucket,
                endpoint=endpoint
            )
            
            if not docs_driven_code:
                raise Exception("Docs-driven generation returned empty code")
            
            # Log the generated code for debugging
            logger.info("=" * 80)
            logger.info("GENERATED CODE TO EXECUTE:")
            logger.info("=" * 80)
            code_lines = docs_driven_code.split('\n')
            for i, line in enumerate(code_lines, 1):
                logger.info(f"{i:3}: {line}")
            logger.info("=" * 80)
            
            return docs_driven_code
        
        except Exception as e:
            import traceback
            logger.error(f"❌ Docs-driven code generation failed: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise Exception(f"Code generation failed for {action} {resource_type}: {str(e)}")
    
    def _get_api_endpoint_hint(resource_type: str, action: str) -> str:
        """Provide API endpoint hints for the LLM (from Swagger docs)"""
        endpoints = {
            ("nfs", "create"): "POST /api/v1/asset/datasource/nfs",
            ("nfs", "list"): "GET /api/v1/asset/datasource/nfs",
            ("nfs", "delete"): "DELETE /api/v1/asset/datasource/nfs/{{AssetId}}",
            ("nfs", "update"): "PUT /api/v1/asset/datasource/nfs/{{AssetId}}",
            ("pvc", "create"): "POST /api/v1/asset/datasource/pvc",
            ("pvc", "list"): "GET /api/v1/asset/datasource/pvc",
            ("pvc", "delete"): "DELETE /api/v1/asset/datasource/pvc/{{AssetId}}",
        }
        return endpoints.get((resource_type, action), f"{action.upper()} /api/v1/asset/datasource/{resource_type}")

    
    # Yield the function wrapped in FunctionInfo
    try:
        yield FunctionInfo.create(
            single_fn=_execute_llm_operation,
            description=(
                "Manage datasources and projects ONLY (NFS, PVC, Git, S3, HostPath storage + project create/list/delete). "
                "Use for: creating/listing/deleting NFS, PVC, Git datasources; creating projects with GPU quotas. "
                "Do NOT use for: workloads, training jobs, distributed jobs, workspace submissions, job status, "
                "environments, kubectl troubleshooting, or code generation."
            )
        )
    except GeneratorExit:
        logger.info("LLM smart executor exited")
    finally:
        logger.info("Cleaning up LLM smart executor")

