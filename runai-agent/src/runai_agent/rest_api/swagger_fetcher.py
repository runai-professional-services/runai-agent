"""
Swagger/OpenAPI Specification Fetcher

Fetches and caches Swagger/OpenAPI specs from Run:AI deployments.
This ensures API documentation matches the exact version deployed.
"""

import requests
from typing import Dict, Any, Optional, List, Tuple
import json
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
from ..utils.helpers import logger


class SwaggerFetcher:
    """
    Fetches and parses OpenAPI/Swagger specifications from Run:AI API.
    
    This class handles:
    - Discovering Swagger endpoints from Run:AI deployment
    - Caching specs to avoid repeated fetches
    - Extracting endpoint information (paths, methods, schemas)
    - Resolving $ref pointers in OpenAPI specs
    
    Usage:
        fetcher = SwaggerFetcher(base_url, client_id, client_secret)
        spec = fetcher.fetch_swagger()
        endpoints = fetcher.list_endpoints()
        endpoint_info = fetcher.get_endpoint_info("/api/v1/asset/datasource/nfs", "POST")
    """
    
    def __init__(self, base_url: str, client_id: str = None, client_secret: str = None):
        """
        Initialize Swagger fetcher
        
        Args:
            base_url: Run:AI cluster base URL (e.g., "https://runcluster.example.com")
            client_id: Optional OAuth client ID (for authenticated endpoints)
            client_secret: Optional OAuth client secret (for authenticated endpoints)
        """
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self._cached_spec: Optional[Dict[str, Any]] = None
        self._access_token: Optional[str] = None
    
    def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token if credentials are provided"""
        if not self.client_id or not self.client_secret:
            return None
        
        if self._access_token:
            return self._access_token
        
        try:
            token_url = f"{self.base_url}/api/v1/token"
            payload = {
                "grantType": "client_credentials",
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            }
            response = requests.post(token_url, json=payload, timeout=10)
            response.raise_for_status()
            self._access_token = response.json()["accessToken"]
            return self._access_token
        except Exception as e:
            logger.warning(f"Failed to get access token: {e}")
            return None
    
    def _try_parse_swagger_from_html(self, html_url: str, headers: dict) -> Optional[Dict[str, Any]]:
        """
        Try to fetch Swagger UI HTML page and extract the spec URL
        
        Args:
            html_url: URL to Swagger UI HTML page (e.g., /api/docs)
            headers: Request headers
            
        Returns:
            Parsed spec or None if not found
        """
        try:
            response = requests.get(html_url, headers=headers, timeout=10, verify=True)
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Look for common Swagger UI patterns
            # Pattern 1: SwaggerUIBundle({ url: "spec.json" })
            import re
            
            # Try to find spec URL in JavaScript
            patterns = [
                r'url:\s*["\']([^"\']+)["\']',  # url: "spec.json"
                r'spec-url["\']?\s*[:=]\s*["\']([^"\']+)["\']',  # spec-url="spec.json"
                r'swagger\.json',  # Direct reference
                r'openapi\.json',  # Direct reference
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, str) and ('json' in match.lower() or 'yaml' in match.lower()):
                        # Construct full URL
                        if match.startswith('http'):
                            spec_url = match
                        elif match.startswith('/'):
                            spec_url = f"{self.base_url}{match}"
                        else:
                            # Relative to current path
                            base = html_url.rsplit('/', 1)[0]
                            spec_url = f"{base}/{match}"
                        
                        logger.debug(f"Found potential spec URL in HTML: {spec_url}")
                        
                        # Try to fetch it
                        try:
                            spec_response = requests.get(spec_url, headers=headers, timeout=10, verify=True)
                            if spec_response.status_code == 200:
                                spec = spec_response.json()
                                if "paths" in spec or "swagger" in spec or "openapi" in spec:
                                    logger.info(f"✓ Found spec by parsing HTML at {spec_url}")
                                    return spec
                        except:
                            continue
            
            return None
        except Exception as e:
            logger.debug(f"Failed to parse HTML at {html_url}: {e}")
            return None
    
    def fetch_swagger(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch OpenAPI/Swagger spec from Run:AI deployment
        
        Args:
            force_refresh: If True, ignore cached spec and fetch fresh
            
        Returns:
            Parsed OpenAPI/Swagger specification as a dictionary
            
        Raises:
            Exception: If spec cannot be fetched from any known endpoint
        """
        if self._cached_spec and not force_refresh:
            logger.debug("Using cached Swagger spec")
            return self._cached_spec
        
        # Try common Swagger/OpenAPI endpoints
        # Based on Run:AI docs: "access the documentation at https://<control-plane-url>/api/docs"
        # Run:AI uses redoc-runai.swagger.yaml for their OpenAPI spec
        possible_endpoints = [
            f"{self.base_url}/api/redoc-runai.swagger.yaml",  # Run:AI specific YAML spec
            f"{self.base_url}/api/redoc-runai.swagger.json",  # Try JSON variant
            f"{self.base_url}/api/docs/swagger.json",         # Swagger JSON at docs path
            f"{self.base_url}/api/docs/openapi.json",         # OpenAPI JSON at docs path
            f"{self.base_url}/api/docs/swagger.yaml",         # YAML at docs path
            f"{self.base_url}/api/docs/openapi.yaml",         # YAML OpenAPI
            f"{self.base_url}/api/docs/v1/swagger.json",      # Versioned Swagger
            f"{self.base_url}/api/docs/swagger",              # Without extension
            f"{self.base_url}/swagger.json",                  # Root level
            f"{self.base_url}/swagger.yaml",                  # Root YAML
            f"{self.base_url}/api/swagger.json",              # API level
            f"{self.base_url}/openapi.json",                  # Root OpenAPI
            f"{self.base_url}/openapi.yaml",                  # Root OpenAPI YAML
            f"{self.base_url}/api/v1/swagger.json",           # Versioned API
            f"{self.base_url}/docs/swagger.json",             # Docs directory
        ]
        
        # Prepare headers (with auth token if available)
        headers = {}
        token = self._get_access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        for url in possible_endpoints:
            try:
                logger.debug(f"Trying Swagger endpoint: {url}")
                response = requests.get(url, headers=headers, timeout=10, verify=True)
                
                if response.status_code == 200:
                    # Try to parse as JSON or YAML
                    spec = None
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # Try JSON first
                    if 'json' in content_type or url.endswith('.json'):
                        try:
                            spec = response.json()
                        except json.JSONDecodeError:
                            logger.debug(f"Failed to parse {url} as JSON")
                    
                    # Try YAML if JSON failed or if it's a YAML file
                    if spec is None and ('yaml' in content_type or url.endswith('.yaml') or url.endswith('.yml')):
                        if YAML_AVAILABLE:
                            try:
                                spec = yaml.safe_load(response.text)
                            except yaml.YAMLError:
                                logger.debug(f"Failed to parse {url} as YAML")
                        else:
                            logger.warning("YAML file detected but PyYAML not installed. Install with: pip install pyyaml")
                    
                    # If still no spec, try both formats as fallback
                    if spec is None:
                        try:
                            spec = response.json()
                        except:
                            if YAML_AVAILABLE:
                                try:
                                    spec = yaml.safe_load(response.text)
                                except:
                                    pass
                    
                    # Validate it's a proper OpenAPI spec
                    if spec and ("paths" in spec or "swagger" in spec or "openapi" in spec):
                        self._cached_spec = spec
                        logger.info(f"✓ Successfully fetched Swagger spec from {url}")
                        logger.info(f"  OpenAPI Version: {spec.get('openapi') or spec.get('swagger', 'Unknown')}")
                        logger.info(f"  API Title: {spec.get('info', {}).get('title', 'Unknown')}")
                        logger.info(f"  Total Paths: {len(spec.get('paths', {}))}")
                        return spec
                    else:
                        logger.debug(f"Response from {url} doesn't look like OpenAPI spec")
                        
            except requests.exceptions.Timeout:
                logger.debug(f"Timeout fetching from {url}")
            except requests.exceptions.RequestException as e:
                logger.debug(f"Request error for {url}: {e}")
            except json.JSONDecodeError:
                logger.debug(f"Invalid JSON from {url}")
            except Exception as e:
                logger.debug(f"Unexpected error fetching {url}: {e}")
        
        # Last resort: Try parsing HTML docs page
        logger.info("Direct JSON endpoints failed, trying to parse HTML docs page...")
        html_endpoints = [
            f"{self.base_url}/api/docs",
            f"{self.base_url}/api/docs/",
            f"{self.base_url}/docs",
        ]
        
        for html_url in html_endpoints:
            spec = self._try_parse_swagger_from_html(html_url, headers)
            if spec:
                self._cached_spec = spec
                return spec
        
        raise Exception(
            f"Could not fetch Swagger spec from Run:AI deployment at {self.base_url}. "
            f"Tried endpoints: {', '.join(possible_endpoints + html_endpoints)}"
        )
    
    def get_endpoint_info(self, path: str, method: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific API endpoint
        
        Args:
            path: API path (e.g., "/api/v1/asset/datasource/nfs")
            method: HTTP method (e.g., "GET", "POST", "DELETE")
            
        Returns:
            Endpoint information including parameters, request body, responses
        """
        spec = self.fetch_swagger()
        endpoint = spec.get("paths", {}).get(path, {}).get(method.lower(), {})
        
        if not endpoint:
            logger.warning(f"Endpoint not found: {method} {path}")
        
        return endpoint
    
    def list_endpoints(self, filter_path: str = None) -> List[Tuple[str, str]]:
        """
        List all available API endpoints
        
        Args:
            filter_path: Optional substring to filter paths (e.g., "nfs", "pvc")
            
        Returns:
            List of tuples: [(method, path), ...]
            Example: [("GET", "/api/v1/asset/datasource/nfs"), ...]
        """
        spec = self.fetch_swagger()
        endpoints = []
        
        for path, methods in spec.get("paths", {}).items():
            # Filter by path if specified
            if filter_path and filter_path.lower() not in path.lower():
                continue
            
            for method in methods.keys():
                # Skip non-operation keys like "parameters", "servers", etc.
                if method.lower() in ["get", "post", "put", "patch", "delete", "options", "head"]:
                    endpoints.append((method.upper(), path))
        
        return sorted(endpoints)
    
    def get_schema(self, schema_ref: str) -> Dict[str, Any]:
        """
        Resolve a $ref pointer to get the actual schema
        
        Args:
            schema_ref: Reference string (e.g., "#/components/schemas/NFSCreationRequest")
            
        Returns:
            Resolved schema definition
        """
        spec = self.fetch_swagger()
        
        # Handle $ref pointers like "#/components/schemas/NFSCreationRequest"
        if schema_ref.startswith("#/"):
            parts = schema_ref[2:].split("/")
            current = spec
            
            for part in parts:
                current = current.get(part, {})
            
            return current
        
        # If it's not a reference, return empty dict
        return {}
    
    def resolve_schema_refs(self, schema: Any, max_depth: int = 20, _depth: int = 0, _visited: set = None) -> Any:
        """
        Recursively resolve $ref references in a schema with cycle detection
        
        Args:
            schema: Schema object (dict, list, or primitive)
            max_depth: Maximum recursion depth (default: 20 for deeply nested schemas)
            _depth: Current recursion depth (internal use)
            _visited: Set of visited $ref paths to detect cycles (internal use)
            
        Returns:
            Schema with $ref references resolved
        """
        # Initialize visited set on first call
        if _visited is None:
            _visited = set()
            logger.debug(f"🔄 Starting schema resolution (max_depth={max_depth})...")
        
        # Prevent infinite recursion
        if _depth >= max_depth:
            logger.info(f"⚠️  Max depth {max_depth} reached at depth {_depth}")
            return schema  # Return as-is at max depth
        
        # Handle dictionaries
        if isinstance(schema, dict):
            # Handle $ref
            if "$ref" in schema:
                ref_path = schema["$ref"]
                logger.debug(f"  {'  ' * _depth}└─ Resolving $ref: {ref_path} (depth={_depth})")
                
                # Detect circular references
                if ref_path in _visited:
                    logger.debug(f"  {'  ' * _depth}   ⚠️ Circular reference detected!")
                    return {"type": "object", "description": f"Circular ref to {ref_path}"}
                
                # Add to visited and resolve
                _visited.add(ref_path)
                resolved = self.get_schema(ref_path)
                logger.debug(f"  {'  ' * _depth}   ✓ Fetched schema, now resolving nested refs...")
                result = self.resolve_schema_refs(resolved, max_depth, _depth + 1, _visited)
                _visited.remove(ref_path)  # Remove after resolving
                return result
            
            # Handle allOf (merge multiple schemas)
            if "allOf" in schema:
                merged = {}
                for sub_schema in schema["allOf"]:
                    resolved_sub = self.resolve_schema_refs(sub_schema, max_depth, _depth + 1, _visited)
                    # Merge properties
                    if isinstance(resolved_sub, dict):
                        if "properties" in resolved_sub:
                            if "properties" not in merged:
                                merged["properties"] = {}
                            merged["properties"].update(resolved_sub.get("properties", {}))
                        # Merge other fields
                        for key, value in resolved_sub.items():
                            if key not in ["properties", "allOf"]:
                                merged[key] = value
                
                # Keep non-allOf fields from original schema
                for key, value in schema.items():
                    if key != "allOf":
                        merged[key] = value
                
                return merged
            
            # Otherwise, recursively resolve all values in the dict
            result = {}
            for key, value in schema.items():
                result[key] = self.resolve_schema_refs(value, max_depth, _depth + 1, _visited)
            return result
        
        # Handle lists
        elif isinstance(schema, list):
            return [self.resolve_schema_refs(item, max_depth, _depth + 1, _visited) for item in schema]
        
        # Handle primitives (strings, numbers, booleans, None)
        else:
            return schema
    
    def search_endpoints(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for endpoints matching a query (simple keyword search)
        
        Args:
            query: Search query (e.g., "nfs create", "pvc list")
            limit: Maximum number of results
            
        Returns:
            List of endpoint information dictionaries
        """
        spec = self.fetch_swagger()
        results = []
        query_lower = query.lower()
        
        for path, methods in spec.get("paths", {}).items():
            path_lower = path.lower()
            
            for method, endpoint_info in methods.items():
                if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                    continue
                
                # Score based on query matches
                score = 0
                
                # Check path
                if query_lower in path_lower:
                    score += 10
                
                # Check operation summary/description
                summary = endpoint_info.get("summary", "").lower()
                description = endpoint_info.get("description", "").lower()
                
                if query_lower in summary:
                    score += 5
                if query_lower in description:
                    score += 3
                
                # Check tags
                tags = endpoint_info.get("tags", [])
                for tag in tags:
                    if query_lower in tag.lower():
                        score += 2
                
                if score > 0:
                    results.append({
                        "score": score,
                        "method": method.upper(),
                        "path": path,
                        "summary": endpoint_info.get("summary", ""),
                        "description": endpoint_info.get("description", ""),
                        "endpoint_info": endpoint_info
                    })
        
        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def get_request_schema(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """
        Extract the request body schema for an endpoint with all $ref resolved
        
        Args:
            path: API path
            method: HTTP method
            
        Returns:
            Fully resolved request schema or None if not found
        """
        endpoint = self.get_endpoint_info(path, method)
        request_body = endpoint.get("requestBody", {})
        content = request_body.get("content", {})
        
        # Try JSON content type
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        
        if not schema:
            logger.debug(f"No schema found for {method} {path}")
            return None
        
        logger.info(f"🔍 Resolving request schema for {method} {path}...")
        logger.debug(f"Raw schema before resolution: {schema}")
        
        # Recursively resolve all $ref references
        resolved_schema = self.resolve_schema_refs(schema)
        
        logger.info(f"✅ Resolved schema has {len(str(resolved_schema))} chars")
        logger.debug(f"Resolved schema: {resolved_schema}")
        
        return resolved_schema if resolved_schema else None
    
    def get_response_schema(self, path: str, method: str, status_code: str = "200") -> Optional[Dict[str, Any]]:
        """
        Extract the response schema for an endpoint with all $ref resolved
        
        Args:
            path: API path
            method: HTTP method
            status_code: HTTP status code (default: "200")
            
        Returns:
            Fully resolved response schema or None if not found
        """
        endpoint = self.get_endpoint_info(path, method)
        responses = endpoint.get("responses", {})
        response = responses.get(status_code, {})
        content = response.get("content", {})
        
        # Try JSON content type
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        
        if not schema:
            return None
        
        # Recursively resolve all $ref references
        resolved_schema = self.resolve_schema_refs(schema)
        
        return resolved_schema if resolved_schema else None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the API spec
        
        Returns:
            Dictionary with stats (total paths, methods, schemas, etc.)
        """
        spec = self.fetch_swagger()
        
        paths = spec.get("paths", {})
        total_endpoints = 0
        methods_count = {}
        
        for path, methods in paths.items():
            for method in methods.keys():
                if method.lower() in ["get", "post", "put", "patch", "delete"]:
                    total_endpoints += 1
                    methods_count[method.upper()] = methods_count.get(method.upper(), 0) + 1
        
        schemas = spec.get("components", {}).get("schemas", {})
        
        return {
            "openapi_version": spec.get("openapi") or spec.get("swagger"),
            "title": spec.get("info", {}).get("title", "Unknown"),
            "version": spec.get("info", {}).get("version", "Unknown"),
            "total_paths": len(paths),
            "total_endpoints": total_endpoints,
            "methods": methods_count,
            "total_schemas": len(schemas)
        }

