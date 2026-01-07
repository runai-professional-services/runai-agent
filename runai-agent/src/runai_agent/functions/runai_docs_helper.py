"""
Run:AI Documentation Helper - Direct links to common topics.
This complements webpage_query by providing direct access to known documentation pages.
"""

from typing import Dict, List
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from pydantic import Field


class RunaiDocsHelperConfig(FunctionBaseConfig, name="runai_docs_helper"):
    """Configuration for Run:AI documentation helper."""
    description: str = Field(
        default="Get direct links to Run:AI documentation topics. Use this when webpage_query doesn't find results or for well-known Run:AI concepts like nodePools, projects, workloads, etc.",
    )


# Known documentation topics and their direct URLs
# NOTE: Update these URLs to match your actual Run:AI documentation site
DOCS_INDEX = {
    "nodepool": {
        "title": "Node Pools",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/aiinitiatives/resources/node-pools",
        "description": "Node pools allow you to assign specific nodes to projects/departments for workload scheduling."
    },
    "node pool": {
        "title": "Node Pools",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/aiinitiatives/resources/node-pools",
        "description": "Node pools allow you to assign specific nodes to projects/departments for workload scheduling."
    },
    "project": {
        "title": "Projects",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/aiinitiatives/organization/projects",
        "description": "Projects are the fundamental organizational unit in Run:AI for resource allocation and access control."
    },
    "department": {
        "title": "Departments",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/aiinitiatives/organization/departments",
        "description": "Departments group multiple projects for hierarchical resource management."
    },
    "workload": {
        "title": "Workloads",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/workloads/workloads",
        "description": "Workloads are compute jobs (training, interactive, inference) running in Run:AI."
    },
    "gpu": {
        "title": "GPU Allocation & Scheduling",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/scheduling-and-resource-optimization/the-runai-scheduler",
        "description": "How Run:AI allocates and schedules GPU resources across workloads."
    },
    "quota": {
        "title": "GPU Quotas",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/aiinitiatives/organization/projects",
        "description": "Setting GPU quotas and limits for projects and departments (see Projects documentation)."
    },
    "scheduler": {
        "title": "Scheduler",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/scheduling-and-resource-optimization/the-runai-scheduler",
        "description": "How the Run:AI scheduler prioritizes and allocates resources."
    },
    "pvc": {
        "title": "Storage & Data Sources",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/workloads/workload-assets",
        "description": "Persistent Volume Claims and storage configuration for workloads in Run:AI."
    },
    "datasource": {
        "title": "Data Sources & Workload Assets",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/workloads/workload-assets",
        "description": "Managing data sources (NFS, PVC, S3, Git) and workload assets in Run:AI."
    },
    "network topology": {
        "title": "Network Topology-Aware Scheduling",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/aiinitiatives/resources/topology-aware-scheduling",
        "description": "Accelerating workloads by optimizing pod placement based on network topology to keep nodes as close as possible."
    },
    "topology": {
        "title": "Network Topology-Aware Scheduling",
        "url": "https://run-ai-docs.nvidia.com/self-hosted/platform-management/aiinitiatives/resources/topology-aware-scheduling",
        "description": "Accelerating workloads by optimizing pod placement based on network topology to keep nodes as close as possible."
    }
}


@register_function(config_type=RunaiDocsHelperConfig)
async def runai_docs_helper(config: RunaiDocsHelperConfig, builder: Builder):
    """
    Get direct links to Run:AI documentation topics.
    
    This function provides direct access to known Run:AI documentation pages,
    serving as a fallback when webpage_query doesn't find results.
    
    Args:
        config: Function configuration
        builder: NAT builder instance
        
    Yields:
        FunctionInfo with the documentation lookup function
    """
    
    async def _lookup_docs(query: str) -> str:
        """
        Look up documentation for a Run:AI topic.
        
        Args:
            query: The topic to search for (e.g., "node pool", "project", "gpu quota")
            
        Returns:
            Formatted documentation references with direct links
        """
        query_lower = query.lower().strip()
        
        # Try exact match first
        if query_lower in DOCS_INDEX:
            doc = DOCS_INDEX[query_lower]
            return f"""
📚 **{doc['title']}**

{doc['description']}

🔗 **Documentation:** {doc['url']}

For more details, visit the link above or search the Run:AI documentation site.
"""
        
        # Try partial match
        matches = []
        for key, doc in DOCS_INDEX.items():
            if query_lower in key or key in query_lower or query_lower in doc['title'].lower():
                matches.append(doc)
        
        if matches:
            result = f"📚 Found {len(matches)} documentation page(s) related to '{query}':\n\n"
            for doc in matches:
                result += f"**{doc['title']}**\n"
                result += f"{doc['description']}\n"
                result += f"🔗 {doc['url']}\n\n"
            return result
        
        # No matches found - provide general guidance
        return f"""
ℹ️ No direct documentation link found for '{query}'.

**Available topics with direct links:**
- Node Pools: Node assignment and scheduling
- Projects & Departments: Resource organization
- Workloads: Training, interactive, and inference jobs
- GPU Allocation: Resource scheduling and quotas
- Data Sources: NFS, PVC, S3, Git integration
- Scheduler: How Run:AI prioritizes workloads

💡 **Tip:** Try:
1. Asking about a more general topic (e.g., "projects" instead of "project configuration")
2. Searching the main documentation site: https://run-ai-docs.nvidia.com
3. Using different keywords related to your question

Would you like me to help you find information about any of these topics?
"""
    
    try:
        yield FunctionInfo.create(
            single_fn=_lookup_docs,
            description="Get direct links to Run:AI documentation topics (nodePools, projects, workloads, GPU quotas, datasources, scheduler). Fast and reliable for well-known concepts."
        )
    except GeneratorExit:
        pass
    finally:
        pass

