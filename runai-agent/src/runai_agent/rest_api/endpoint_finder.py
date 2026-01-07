"""
Endpoint Finder - Semantic Search for API Operations

Uses the SwaggerFetcher to find relevant API endpoints for user operations.
Provides intelligent matching based on resource types, actions, and descriptions.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from ..utils.helpers import logger


@dataclass
class EndpointMatch:
    """Represents a matched API endpoint with relevance score"""
    method: str
    path: str
    score: float
    summary: str
    description: str
    endpoint_info: Dict[str, Any]
    
    def __repr__(self):
        return f"<EndpointMatch {self.method} {self.path} (score: {self.score})>"


class EndpointFinder:
    """
    Finds relevant API endpoints for operations using semantic matching.
    
    This class provides intelligent endpoint discovery by:
    - Matching resource types (nfs, pvc, etc.) to API paths
    - Mapping actions (create, list, delete) to HTTP methods
    - Scoring endpoints by relevance
    - Providing comprehensive endpoint information for code generation
    
    Usage:
        from rest_api import SwaggerFetcher, EndpointFinder
        
        swagger = SwaggerFetcher(base_url, client_id, client_secret)
        finder = EndpointFinder(swagger)
        
        # Find endpoint for creating NFS
        match = finder.find_endpoint(
            resource_type="nfs",
            action="create",
            description="Create an NFS datasource with server and path"
        )
        
        if match:
            print(f"Found: {match.method} {match.path}")
            schema = swagger.get_request_schema(match.path, match.method)
    """
    
    # Action to HTTP method mapping
    ACTION_TO_METHOD = {
        "create": "POST",
        "add": "POST",
        "submit": "POST",
        "list": "GET",
        "get": "GET",
        "retrieve": "GET",
        "show": "GET",
        "view": "GET",
        "update": "PUT",
        "modify": "PUT",
        "patch": "PATCH",
        "delete": "DELETE",
        "remove": "DELETE",
    }
    
    # Resource type to API path patterns
    # This mapping allows the endpoint finder to locate the correct API path
    # for any resource type, supporting generic operations across the entire API
    RESOURCE_PATTERNS = {
        # Datasource assets
        "nfs": ["/datasource/nfs", "/asset/datasource/nfs"],
        "pvc": ["/datasource/pvc", "/asset/datasource/pvc"],
        "s3": ["/datasource/s3", "/asset/datasource/s3"],
        "git": ["/datasource/git", "/asset/datasource/git"],
        "hostpath": ["/datasource/host-path", "/asset/datasource/host-path"],
        "host-path": ["/datasource/host-path", "/asset/datasource/host-path"],
        
        # Credentials and configs
        "secret": ["/credentials", "/asset/credentials"],
        "credential": ["/credentials", "/asset/credentials"],
        "configmap": ["/datasource/config-map", "/asset/datasource/config-map"],
        "config-map": ["/datasource/config-map", "/asset/datasource/config-map"],
        
        # Environments and compute
        "environment": ["/environment", "/asset/environment"],
        "compute": ["/compute", "/asset/compute"],
        
        # Organization units
        "department": ["/departments", "/org-unit/departments"],
        "project": ["/projects", "/org-unit/projects"],
        "nodepool": ["/nodepools", "/node-pools"],
        "node-pool": ["/nodepools", "/node-pools"],
        "cluster": ["/clusters"],
        
        # Workloads
        "workspace": ["/workspaces", "/workload/workspaces"],
        "training": ["/trainings", "/workload/trainings"],
        "inference": ["/inferences", "/workload/inferences"],
        "distributed": ["/distributed", "/workload/distributed"],
        "workload": ["/workloads", "/workload"],
        "compute": ["/compute", "/asset/compute"],
        "training": ["/workload/trainings", "/trainings"],
        "workspace": ["/workload/workspaces", "/workspaces"],
        "inference": ["/workload/inferences", "/inferences"],
        "distributed": ["/workload/distributed", "/distributed"],
        "project": ["/projects", "/org-unit/projects"],
        "cluster": ["/clusters"],
        "node": ["/nodes"],
    }
    
    def __init__(self, swagger_fetcher):
        """
        Initialize endpoint finder with a SwaggerFetcher
        
        Args:
            swagger_fetcher: SwaggerFetcher instance with cached OpenAPI spec
        """
        self.swagger = swagger_fetcher
        self._endpoint_cache = None
    
    @staticmethod
    def _normalize_action(action: str) -> str:
        """
        Normalize compound actions to base actions
        
        Examples:
            "create_datasource" -> "create"
            "list_workloads" -> "list"
            "delete_environment" -> "delete"
            "update_project" -> "update"
            "submit_training" -> "submit"
            
        Args:
            action: Raw action string (may include underscores and suffixes)
            
        Returns:
            Normalized base action
        """
        # List of known base actions (in order of priority for matching)
        base_actions = [
            "create", "add", "submit",
            "list", "get", "retrieve", "show", "view",
            "update", "modify", "patch", "edit",
            "delete", "remove"
        ]
        
        # Convert to lowercase for matching
        action_lower = action.lower()
        
        # Check if action starts with any base action
        for base in base_actions:
            if action_lower.startswith(base):
                return base
        
        # If no match, return the action as-is
        return action
    
    def find_endpoint(
        self,
        resource_type: str,
        action: str,
        description: Optional[str] = None,
        min_score: float = 0.5
    ) -> Optional[EndpointMatch]:
        """
        Find the best matching endpoint for a resource operation
        
        Args:
            resource_type: Type of resource (e.g., "nfs", "pvc", "training")
            action: Action to perform (e.g., "create", "list", "delete")
            description: Optional description for better matching
            min_score: Minimum relevance score (0.0 to 1.0)
            
        Returns:
            EndpointMatch if found, None otherwise
        """
        matches = self.find_endpoints(
            resource_type=resource_type,
            action=action,
            description=description,
            limit=1,
            min_score=min_score
        )
        
        return matches[0] if matches else None
    
    def find_endpoints(
        self,
        resource_type: str,
        action: str,
        description: Optional[str] = None,
        limit: int = 5,
        min_score: float = 0.3
    ) -> List[EndpointMatch]:
        """
        Find multiple matching endpoints, sorted by relevance
        
        Args:
            resource_type: Type of resource (e.g., "nfs", "pvc")
            action: Action to perform (e.g., "create", "list")
            description: Optional description for better matching
            limit: Maximum number of results
            min_score: Minimum relevance score (0.0 to 1.0)
            
        Returns:
            List of EndpointMatch objects, sorted by score (highest first)
        """
        logger.debug(f"Finding endpoints for: {action} {resource_type}")
        
        # Normalize the action by extracting the base action
        # Examples: "create_datasource" -> "create", "list_workloads" -> "list"
        normalized_action = self._normalize_action(action)
        
        # Get expected HTTP method for this action
        expected_method = self.ACTION_TO_METHOD.get(normalized_action.lower())
        if not expected_method:
            logger.warning(f"Unknown action: {normalized_action} (from: {action})")
            expected_method = "POST" if "create" in normalized_action.lower() or "add" in normalized_action.lower() else "GET"
        
        # Get path patterns for this resource type
        path_patterns = self.RESOURCE_PATTERNS.get(resource_type.lower(), [resource_type.lower()])
        
        # Get all endpoints from OpenAPI spec
        spec = self.swagger.fetch_swagger()
        all_endpoints = []
        
        for path, methods in spec.get("paths", {}).items():
            for method, endpoint_info in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    continue
                
                all_endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "endpoint_info": endpoint_info
                })
        
        # Score and filter endpoints
        scored_matches = []
        for endpoint in all_endpoints:
            score = self._score_endpoint(
                endpoint=endpoint,
                resource_type=resource_type,
                action=action,
                expected_method=expected_method,
                path_patterns=path_patterns,
                description=description
            )
            
            if score >= min_score:
                scored_matches.append(EndpointMatch(
                    method=endpoint["method"],
                    path=endpoint["path"],
                    score=score,
                    summary=endpoint["endpoint_info"].get("summary", ""),
                    description=endpoint["endpoint_info"].get("description", ""),
                    endpoint_info=endpoint["endpoint_info"]
                ))
        
        # Sort by score (highest first) and limit
        scored_matches.sort(key=lambda x: x.score, reverse=True)
        results = scored_matches[:limit]
        
        logger.info(f"Found {len(results)} endpoint(s) for {action} {resource_type}")
        if results:
            logger.debug(f"Top match: {results[0].method} {results[0].path} (score: {results[0].score:.2f})")
        
        return results
    
    def _score_endpoint(
        self,
        endpoint: Dict[str, Any],
        resource_type: str,
        action: str,
        expected_method: str,
        path_patterns: List[str],
        description: Optional[str]
    ) -> float:
        """
        Calculate relevance score for an endpoint
        
        Scoring criteria:
        - HTTP method match: 0.4
        - Path pattern match: 0.3
        - Summary/description keywords: 0.2
        - Tags match: 0.1
        
        Returns:
            Float score between 0.0 and 1.0
        """
        score = 0.0
        method = endpoint["method"]
        path = endpoint["path"].lower()
        info = endpoint["endpoint_info"]
        
        # 1. HTTP Method match (0.4 points)
        if method == expected_method:
            score += 0.4
        elif method == "POST" and action in ["create", "add"]:
            score += 0.3
        elif method == "GET" and action in ["list", "get"]:
            score += 0.3
        elif method == "DELETE" and action in ["delete", "remove"]:
            score += 0.4
        
        # 2. Path pattern match (0.3 points)
        path_score = 0.0
        for pattern in path_patterns:
            if pattern.lower() in path:
                path_score = 0.3
                break
            elif resource_type.lower() in path:
                path_score = 0.2
        score += path_score
        
        # 3. Summary/Description keywords (0.2 points)
        text_score = 0.0
        summary = info.get("summary", "").lower()
        desc = info.get("description", "").lower()
        combined_text = f"{summary} {desc}"
        
        # Check for action keywords
        if action.lower() in combined_text:
            text_score += 0.1
        
        # Check for resource type keywords
        if resource_type.lower() in combined_text:
            text_score += 0.05
        
        # Check for custom description match
        if description:
            desc_words = description.lower().split()
            matches = sum(1 for word in desc_words if word in combined_text)
            if matches > 0:
                text_score += min(0.05, matches * 0.01)
        
        score += text_score
        
        # 4. Tags match (0.1 points)
        tags = [tag.lower() for tag in info.get("tags", [])]
        if resource_type.lower() in tags:
            score += 0.1
        elif any(pattern.split("/")[-1] in tags for pattern in path_patterns):
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_endpoint_details(
        self,
        endpoint_match: EndpointMatch
    ) -> Dict[str, Any]:
        """
        Get comprehensive details about an endpoint including schemas
        
        Args:
            endpoint_match: EndpointMatch object from find_endpoint()
            
        Returns:
            Dictionary with:
            - method: HTTP method
            - path: API path
            - summary: Operation summary
            - description: Operation description
            - tags: Operation tags
            - parameters: Path/query parameters
            - request_schema: Request body schema (for POST/PUT)
            - response_schema: Response schema
            - request_example: Example request (if available)
            - response_example: Example response (if available)
        """
        path = endpoint_match.path
        method = endpoint_match.method
        info = endpoint_match.endpoint_info
        
        details = {
            "method": method,
            "path": path,
            "summary": info.get("summary", ""),
            "description": info.get("description", ""),
            "tags": info.get("tags", []),
            "parameters": info.get("parameters", []),
        }
        
        # Get request schema (for POST/PUT/PATCH)
        if method in ["POST", "PUT", "PATCH"]:
            request_schema = self.swagger.get_request_schema(path, method)
            details["request_schema"] = request_schema
            
            # Try to get example from schema
            if request_schema and "example" in request_schema:
                details["request_example"] = request_schema["example"]
        
        # Get response schema
        for status_code in ["200", "201", "202"]:  # Try common success codes
            response_schema = self.swagger.get_response_schema(path, method, status_code)
            if response_schema:
                details["response_schema"] = response_schema
                details["response_status_code"] = status_code
                
                # Try to get example
                if "example" in response_schema:
                    details["response_example"] = response_schema["example"]
                break
        
        return details
    
    def list_available_resources(self) -> List[str]:
        """
        List all available resource types that can be managed
        
        Returns:
            List of resource type names
        """
        return list(self.RESOURCE_PATTERNS.keys())
    
    def list_available_actions(self) -> List[str]:
        """
        List all supported actions
        
        Returns:
            List of action names
        """
        return list(self.ACTION_TO_METHOD.keys())

