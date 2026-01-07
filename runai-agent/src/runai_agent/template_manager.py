"""
Template Manager for Run:AI API Code Generation

Replaces LLM-driven code generation with deterministic Jinja2 templates.
Provides consistent, fast, and debuggable API code generation.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import jinja2

from .utils.helpers import logger


class TemplateManager:
    """Manages Jinja2 templates for Run:AI API code generation"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the template manager
        
        Args:
            template_dir: Path to templates directory. If None, uses default location.
        """
        if template_dir is None:
            # Default to templates/ directory next to this file
            current_file = Path(__file__).resolve()
            template_dir = current_file.parent / "templates"
        
        self.template_dir = Path(template_dir)
        
        if not self.template_dir.exists():
            raise ValueError(f"Template directory not found: {self.template_dir}")
        
        # Initialize Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False
        )
        
        logger.info(f"✓ TemplateManager initialized with templates from: {self.template_dir}")
    
    def get_template_path(self, resource_type: str, action: str) -> str:
        """
        Determine the correct template file path for a resource and action
        
        Args:
            resource_type: Type of resource (nfs, pvc, git, project, etc.)
            action: Operation to perform (create, list, delete, get)
            
        Returns:
            Template file path relative to template_dir
        """
        # Normalize resource type
        resource_type = resource_type.lower().replace("-", "")
        action = action.lower()
        
        # Map resource types to categories
        datasource_types = ['nfs', 'pvc', 'git', 's3', 'hostpath', 'configmap', 'secret']
        org_unit_types = ['project', 'department', 'nodepool', 'cluster']
        
        if resource_type in datasource_types:
            if action == 'create':
                if resource_type == 'pvc':
                    return 'datasource/create_pvc.j2'
                else:
                    return 'datasource/create_flat_spec.j2'
            elif action == 'list':
                return 'datasource/list.j2'
            elif action == 'delete':
                return 'datasource/delete.j2'
        
        elif resource_type in org_unit_types:
            if action == 'create':
                if resource_type == 'project':
                    return 'org_unit/create_project.j2'
                elif resource_type == 'department':
                    return 'org_unit/create_department.j2'
            elif action == 'list':
                return 'generic/list.j2'
            elif action == 'delete':
                return 'org_unit/delete.j2'
        
        # Fallback to generic templates
        if action == 'list':
            return 'generic/list.j2'
        elif action == 'get':
            return 'generic/get_by_id.j2'
        elif action == 'delete':
            return 'generic/delete_by_id.j2'
        
        raise ValueError(f"No template found for {resource_type} {action}")
    
    def get_api_category(self, resource_type: str) -> str:
        """
        Determine the API category path for a resource type
        
        Args:
            resource_type: Type of resource
            
        Returns:
            API category (e.g., 'asset/datasource', 'org-unit', 'workload')
        """
        datasource_types = ['nfs', 'pvc', 'git', 's3', 'hostpath', 'configmap', 'secret']
        org_unit_types = ['project', 'department', 'nodepool', 'cluster']
        
        if resource_type in datasource_types:
            return 'asset/datasource'
        elif resource_type in org_unit_types:
            return 'org-unit'
        else:
            return 'unknown'
    
    def get_api_resource_type(self, resource_type: str, action: str = None) -> str:
        """
        Get the API-compatible resource type (with hyphens and pluralization for API endpoints)
        
        Args:
            resource_type: Normalized resource type (e.g., 'hostpath', 'project')
            action: Operation type (e.g., 'list', 'get', 'delete') - some need pluralization
            
        Returns:
            API-compatible resource type (e.g., 'host-path', 'projects')
        """
        # Map normalized types to API types (only for those that differ)
        api_type_mapping = {
            'hostpath': 'host-path'
        }
        
        base_type = api_type_mapping.get(resource_type.lower(), resource_type.lower())
        
        # Org-unit resources need pluralization for list operations ONLY
        # The delete template handles its own pluralization for the response key
        org_unit_types = ['project', 'department', 'nodepool', 'cluster']
        if resource_type in org_unit_types and action in ['list', 'get']:
            # Pluralize org-unit resources for list/get operations
            return base_type + 's'
        
        return base_type
    
    def render(self, resource_type: str, action: str, **kwargs) -> str:
        """
        Render a template with provided parameters
        
        Args:
            resource_type: Type of resource (nfs, pvc, git, project, etc.)
            action: Operation to perform (create, list, delete)
            **kwargs: Template variables
            
        Returns:
            Rendered Python code as string
        """
        try:
            # Get template path
            template_path = self.get_template_path(resource_type, action)
            logger.info(f"Loading template: {template_path}")
            
            # Load template
            template = self.env.get_template(template_path)
            
            # Get API-compatible resource type
            api_resource_type = self.get_api_resource_type(resource_type, action)
            
            # Add resource_type to context
            context = {
                'resource_type': api_resource_type,  # Use API-compatible version
                'action': action,
                'category': self.get_api_category(resource_type),
                **kwargs
            }
            
            # Render template
            code = template.render(**context)
            
            logger.info(f"✓ Template rendered successfully: {len(code)} chars")
            return code
            
        except jinja2.TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise ValueError(f"Template not found for {resource_type} {action}: {e}")
        except jinja2.TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise ValueError(f"Template syntax error in {resource_type} {action}: {e}")
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise
    
    def execute(self, code: str, context: Dict[str, Any]) -> Any:
        """
        Execute rendered Python code with provided context
        
        Args:
            code: Python code to execute
            context: Execution context with variables (base_url, credentials, etc.)
            
        Returns:
            The 'result' variable from executed code
        """
        try:
            # Prepare execution namespace
            exec_namespace = {
                'requests': __import__('requests'),
                **context
            }
            
            # Execute the code
            exec(code, exec_namespace)
            
            # Return the result
            if 'result' not in exec_namespace:
                raise ValueError("Executed code did not produce 'result' variable")
            
            return exec_namespace['result']
            
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            logger.error(f"Code that failed:\n{code}")
            raise
    
    def render_and_execute(
        self,
        resource_type: str,
        action: str,
        context: Dict[str, Any],
        **template_kwargs
    ) -> Any:
        """
        Render template and execute in one operation
        
        Args:
            resource_type: Type of resource (nfs, pvc, etc.)
            action: Operation (create, list, delete)
            context: Execution context (base_url, credentials)
            **template_kwargs: Template variables
            
        Returns:
            Result from executed code
        """
        # Render template
        code = self.render(resource_type, action, **template_kwargs)
        
        # Log generated code for debugging
        logger.debug("=" * 80)
        logger.debug("TEMPLATE-GENERATED CODE:")
        logger.debug("=" * 80)
        for i, line in enumerate(code.split('\n'), 1):
            logger.debug(f"{i:3}: {line}")
        logger.debug("=" * 80)
        
        # Execute
        result = self.execute(code, context)
        
        return result
    
    def list_templates(self) -> Dict[str, list]:
        """
        List all available templates organized by category
        
        Returns:
            Dictionary of categories and their template files
        """
        templates = {}
        
        for category_dir in self.template_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                category_name = category_dir.name
                templates[category_name] = []
                
                for template_file in category_dir.glob('*.j2'):
                    templates[category_name].append(template_file.name)
        
        return templates

