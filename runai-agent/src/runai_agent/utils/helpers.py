"""Shared helper functions and utilities for Run:AI agent"""

import logging
import os
import asyncio
import subprocess
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import requests for GitHub API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("Requests not available. Repository indexing will be disabled.")
    REQUESTS_AVAILABLE = False


def get_secure_config() -> Dict[str, str]:
    """Get secure configuration from environment variables."""
    required_vars = {
        'RUNAI_CLIENT_ID': os.getenv('RUNAI_CLIENT_ID'),
        'RUNAI_CLIENT_SECRET': os.getenv('RUNAI_CLIENT_SECRET'),
        'RUNAI_BASE_URL': os.getenv('RUNAI_BASE_URL'),
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return required_vars


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not isinstance(input_str, str):
        raise ValueError("Input must be a string")
    
    # Remove potentially dangerous characters
    sanitized = input_str.replace('<script>', '').replace('</script>', '')
    sanitized = sanitized.replace('javascript:', '').replace('data:', '')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def _get_secure_runai_config():
    """Get Run:AI credentials from environment (shared helper)"""
    return {
        'RUNAI_CLIENT_ID': os.environ.get('RUNAI_CLIENT_ID', ''),
        'RUNAI_CLIENT_SECRET': os.environ.get('RUNAI_CLIENT_SECRET', ''),
        'RUNAI_BASE_URL': os.environ.get('RUNAI_BASE_URL', ''),
    }


def _search_workload_by_name_helper(client, job_name_to_search: str, project_id: str = None, cluster_id: str = None):
    """
    Shared helper function to search for workload by name using kubectl or Run:AI API.
    Can be used by multiple functions that need to look up workloads.
    """
    # Get kubectl environment (includes KUBECONFIG if set)
    kubectl_env = os.environ.copy()
    kubeconfig_path = os.getenv('KUBECONFIG')
    if kubeconfig_path:
        kubectl_env['KUBECONFIG'] = kubeconfig_path
        logger.debug(f"Using KUBECONFIG: {kubeconfig_path}")
    
    # First, try kubectl if available (faster)
    try:
        cmd = [
            "kubectl", "get", "pods",
            "--all-namespaces",
            "-l", f"workloadName={job_name_to_search}",
            "-o", "jsonpath={.items[0].metadata.labels['run\\.ai/top-owner-uid']}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=kubectl_env)
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"✓ Found workload via kubectl: {result.stdout.strip()}")
            return result.stdout.strip(), None  # Return UUID, None for type
        logger.debug("kubectl not available or job not found via kubectl")
    except Exception as e:
        logger.debug(f"kubectl lookup failed: {e}")
    
    # Fallback: Query Run:AI API to list all workloads and filter by name
    try:
        logger.info(f"Querying Run:AI API for workload '{job_name_to_search}'")
        
        # Use the workloads API to list all workloads (across all types)
        response = client.workloads.workloads.get_workloads(
            search=job_name_to_search  # This helps narrow down results
        )
        
        workloads_data = response.data if hasattr(response, 'data') else response
        workloads = workloads_data.get("workloads", []) if isinstance(workloads_data, dict) else []
        
        logger.info(f"Found {len(workloads)} workloads from API")
        
        # Search for exact name match
        for workload in workloads:
            workload_name = workload.get("name", "")
            workload_id = workload.get("id")
            workload_type = workload.get("type", "").lower()
            
            logger.debug(f"Checking workload: {workload_name} (type: {workload_type}, id: {workload_id})")
            
            if workload_name == job_name_to_search:
                logger.info(f"✓ Found exact match: '{job_name_to_search}' (ID: {workload_id}, Type: {workload_type})")
                return workload_id, workload_type
        
        logger.warning(f"No exact match found for '{job_name_to_search}' among {len(workloads)} workloads")
        return None, None
        
    except Exception as e:
        logger.error(f"Error listing workloads via API: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return None, None


class RunapyExamplesFetcher:
    """Fetch and cache runapy examples from official GitHub repository"""
    
    def __init__(self):
        self.examples = {}
        self.last_fetch = None
        self.cache_duration = 3600  # 1 hour cache
        self._fetching = False
        
    def _cache_valid(self) -> bool:
        """Check if cached examples are still valid"""
        if not self.examples or not self.last_fetch:
            return False
        
        return datetime.now() - self.last_fetch < timedelta(seconds=self.cache_duration)
    
    async def get_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Get cached or fetch fresh examples"""
        if self._cache_valid():
            logger.debug("Using cached runapy examples")
            return self.examples
        
        if self._fetching:
            logger.debug("Example fetch already in progress, waiting...")
            await asyncio.sleep(1)
            return self.examples if self.examples else {}
        
        try:
            self._fetching = True
            return await self._fetch_examples()
        finally:
            self._fetching = False
    
    async def _fetch_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Fetch examples from GitHub API (both root examples/ and examples/generated/)"""
        examples = {
            "training": [],
            "workspace": [],
            "distributed": [],
            "projects": [],
            "general": []
        }
        
        try:
            logger.info("🔍 Fetching runapy examples from GitHub...")
            
            # GitHub API URLs for examples directories
            github_api_urls = [
                "https://api.github.com/repos/runai-professional-services/runapy/contents/examples",
                "https://api.github.com/repos/runai-professional-services/runapy/contents/examples/generated"
            ]
            
            # Add GitHub token to headers if available (avoids rate limiting)
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'RunAI-Agent'
            }
            github_token = os.environ.get('GITHUB_TOKEN')
            if github_token:
                # Classic tokens use 'token', fine-grained use 'Bearer'
                # Try 'token' format first (works for most PATs)
                headers['Authorization'] = f'token {github_token}'
                logger.info(f"✓ Using GitHub token for authentication (length: {len(github_token)}, prefix: {github_token[:4]}...)")
            else:
                logger.warning("No GITHUB_TOKEN found - may hit rate limits")
            
            async with aiohttp.ClientSession(headers=headers) as session:
                # Fetch from both directories
                for github_api_url in github_api_urls:
                    dir_name = github_api_url.split('/')[-1]
                    logger.debug(f"Fetching from {dir_name}...")
                    
                    try:
                        async with session.get(github_api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status != 200:
                                error_body = await response.text()
                                logger.warning(f"Failed to fetch {dir_name} from GitHub: {response.status}")
                                logger.debug(f"Response body: {error_body}")
                                continue
                            
                            files = await response.json()
                            
                            # Filter for .py files and fetch their content
                            for file in files:
                                if file.get("type") == "file" and file.get("name", "").endswith(".py"):
                                    try:
                                        file_url = file.get("download_url")
                                        if not file_url:
                                            continue
                                        
                                        async with session.get(file_url, timeout=aiohttp.ClientTimeout(total=10)) as file_response:
                                            if file_response.status == 200:
                                                content = await file_response.text()
                                                
                                                # Categorize example based on filename
                                                filename = file.get("name", "").lower()
                                                category = self._categorize_example(filename)
                                                
                                                examples[category].append({
                                                    "filename": file.get("name"),
                                                    "code": content,
                                                    "description": self._extract_description(content),
                                                    "source": dir_name  # Track which directory it came from
                                                })
                                                
                                                logger.debug(f"Fetched example: {file.get('name')} from {dir_name}")
                                    except Exception as e:
                                        logger.warning(f"Failed to fetch example {file.get('name')}: {e}")
                                        continue
                    except Exception as e:
                        logger.warning(f"Failed to fetch from {dir_name}: {e}")
                        continue
            
            # If we got no examples at all, fall back
            total_examples = sum(len(v) for v in examples.values())
            if total_examples == 0:
                logger.warning("No examples fetched from GitHub, using fallback")
                return self._get_fallback_examples()
            
            self.examples = examples
            self.last_fetch = datetime.now()
            
            logger.info(f"✅ Fetched {total_examples} runapy examples from GitHub (root + generated)")
            
            return examples
            
        except Exception as e:
            logger.error(f"Error fetching examples from GitHub: {e}")
            return self._get_fallback_examples()
    
    def _categorize_example(self, filename: str) -> str:
        """Categorize example based on filename"""
        if "training" in filename or "train" in filename:
            return "training"
        elif "workspace" in filename or "jupyter" in filename:
            return "workspace"
        elif "distributed" in filename or "dist" in filename:
            return "distributed"
        elif "project" in filename or "department" in filename:
            return "projects"
        else:
            return "general"
    
    def _extract_description(self, code: str) -> str:
        """Extract description from code comments"""
        lines = code.split('\n')
        description_lines = []
        
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('#') and not line.startswith('#!'):
                # Remove the # and clean up
                desc = line[1:].strip()
                if desc and len(desc) > 10:  # Meaningful comment
                    description_lines.append(desc)
        
        return ' '.join(description_lines) if description_lines else "Run:AI example"
    
    def _get_fallback_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Fallback examples if GitHub fetch fails"""
        logger.warning("Using fallback examples - GitHub fetch failed")
        
        return {
            "training": [{
                "filename": "training_basic.py",
                "code": """from runai import models

# Get project details
projects_response = client.organizations.projects.get_projects()
projects_data = projects_response.data
project = [p for p in projects_data.get("projects", []) if p["name"] == "my-project"][0]

# Create training job
training_request = models.TrainingCreationRequest(
    name="my-training-job",
    project_id=project["id"],
    cluster_id=project["clusterId"],
    spec=models.TrainingSpecSpec(
        image="pytorch/pytorch:latest",
        compute=models.SupersetSpecAllOfCompute(
            gpu_devices_request=2,
            gpu_portion_request=1,
            cpu_core_request=1,
            cpu_memory_request="8Gi",
            gpu_request_type="portion"
        )
    )
)

job = client.workloads.trainings.create_training1(training_request)
print(f"Job created: {job.data.get('name')}")
""",
                "description": "Basic training job creation with GPU allocation"
            }],
            "workspace": [],
            "distributed": [],
            "projects": [],
            "general": []
        }
    
    def find_relevant_example(self, query: str, category: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Find the most relevant example based on query"""
        if not self.examples:
            return None
        
        # If category specified, search in that category first
        if category and category in self.examples and self.examples[category]:
            return self.examples[category][0]
        
        # Otherwise, search across all categories
        query_lower = query.lower()
        
        # Try training first (most common)
        if any(word in query_lower for word in ["training", "train", "gpu", "job"]):
            if self.examples.get("training"):
                return self.examples["training"][0]
        
        # Try workspace
        if any(word in query_lower for word in ["workspace", "jupyter", "interactive"]):
            if self.examples.get("workspace"):
                return self.examples["workspace"][0]
        
        # Try distributed
        if any(word in query_lower for word in ["distributed", "dist", "multi-node"]):
            if self.examples.get("distributed"):
                return self.examples["distributed"][0]
        
        # Return first available example
        for category_examples in self.examples.values():
            if category_examples:
                return category_examples[0]
        
        return None


# Global instance
examples_fetcher = RunapyExamplesFetcher()

