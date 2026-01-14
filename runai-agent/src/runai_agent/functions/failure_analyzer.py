"""
Advanced Failure Analysis with Pattern Recognition & Auto-Remediation

This module provides intelligent failure analysis capabilities:
- Historical failure tracking with SQLite database
- Pattern recognition across jobs, projects, and nodes
- Cross-job correlation analysis
- Automated remediation suggestions
- Knowledge graph of failure → solution mappings
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import sanitize_input, _get_secure_runai_config, _search_workload_by_name_helper, logger


class FailureAnalyzerConfig(FunctionBaseConfig, name="runai_failure_analyzer"):
    """Configuration for advanced failure analysis"""
    description: str = (
        "Advanced failure analysis with pattern recognition, cross-job correlation, "
        "and automated remediation suggestions. Analyzes historical failures to provide insights."
    )
    
    # Database configuration
    db_path: str = Field(
        default="/tmp/runai_failure_history.db",
        description="Path to SQLite database for failure history"
    )
    
    # Analysis configuration
    lookback_days: int = Field(
        default=7,
        description="How many days of history to analyze"
    )
    
    pattern_threshold: int = Field(
        default=3,
        description="Minimum occurrences to identify a pattern"
    )
    
    # Remediation configuration
    enable_auto_remediation: bool = Field(
        default=False,
        description="Enable automatic remediation (with confirmation)"
    )
    
    allowed_projects: List[str] = Field(
        default=["*"],
        description="Whitelisted projects (use ['*'] for all)"
    )


class FailureDatabase:
    """SQLite database for storing failure history"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main failure events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                project TEXT NOT NULL,
                failure_type TEXT NOT NULL,
                phase TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pod_name TEXT,
                node_name TEXT,
                container_image TEXT,
                error_message TEXT,
                logs_snippet TEXT,
                events_snippet TEXT,
                gpu_count INTEGER,
                memory_request TEXT,
                cpu_request TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolution_type TEXT,
                resolution_timestamp DATETIME,
                auto_remediated BOOLEAN DEFAULT 0
            )
        """)
        
        # Solutions knowledge base table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_solutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                failure_type TEXT NOT NULL,
                solution_description TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_used DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(failure_type, solution_description)
            )
        """)
        
        # Cross-job correlation table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correlation_type TEXT NOT NULL,
                correlation_value TEXT NOT NULL,
                failure_count INTEGER DEFAULT 1,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(correlation_type, correlation_value)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON failure_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project ON failure_events(project)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_failure_type ON failure_events(failure_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_node ON failure_events(node_name)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ Failure database initialized at {self.db_path}")
    
    def record_failure(self, failure_data: Dict[str, Any]) -> tuple[int, bool]:
        """
        Record a new failure event with deduplication.
        
        Prevents duplicate records by checking if the same failure (same job, project, phase)
        was recorded recently (within 1 hour). If found, updates the timestamp instead of creating
        a new record.
        
        Returns:
            tuple[int, bool]: (failure_id, is_new_record)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        job_name = failure_data.get('job_name')
        project = failure_data.get('project')
        phase = failure_data.get('phase')
        
        # Check for recent duplicate (within last hour)
        cursor.execute("""
            SELECT id, timestamp FROM failure_events
            WHERE job_name = ? AND project = ? AND phase = ?
            AND datetime(timestamp) > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
            LIMIT 1
        """, (job_name, project, phase))
        
        existing = cursor.fetchone()
        
        if existing:
            # Duplicate found - update timestamp instead of creating new record
            failure_id = existing[0]
            cursor.execute("""
                UPDATE failure_events 
                SET timestamp = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (failure_id,))
            conn.commit()
            conn.close()
            logger.debug(f"⚠️  Duplicate failure detected for {job_name} - updated existing record #{failure_id}")
            return failure_id, False  # Existing record, not new
        
        # No recent duplicate - insert new record
        cursor.execute("""
            INSERT INTO failure_events (
                job_name, project, failure_type, phase, pod_name, node_name,
                container_image, error_message, logs_snippet, events_snippet,
                gpu_count, memory_request, cpu_request
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_name,
            project,
            failure_data.get('failure_type'),
            phase,
            failure_data.get('pod_name'),
            failure_data.get('node_name'),
            failure_data.get('container_image'),
            failure_data.get('error_message'),
            failure_data.get('logs_snippet'),
            failure_data.get('events_snippet'),
            failure_data.get('gpu_count'),
            failure_data.get('memory_request'),
            failure_data.get('cpu_request')
        ))
        
        failure_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✓ Recorded failure event #{failure_id} for job {job_name}")
        return failure_id, True  # New record
    
    def get_recent_failures(self, days: int = 7, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent failure events"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Format cutoff date as string for SQLite comparison
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        if project:
            cursor.execute("""
                SELECT * FROM failure_events 
                WHERE timestamp >= ? AND project = ?
                ORDER BY timestamp DESC
            """, (cutoff_date, project))
        else:
            cursor.execute("""
                SELECT * FROM failure_events 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_correlation(self, correlation_type: str, correlation_value: str):
        """Update correlation tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO failure_correlations (correlation_type, correlation_value, failure_count)
            VALUES (?, ?, 1)
            ON CONFLICT(correlation_type, correlation_value) DO UPDATE SET
                failure_count = failure_count + 1,
                last_seen = CURRENT_TIMESTAMP
        """, (correlation_type, correlation_value))
        
        conn.commit()
        conn.close()
    
    def get_pattern_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get pattern statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Format cutoff date as string for SQLite comparison
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        stats = {}
        
        # Failure types distribution
        cursor.execute("""
            SELECT failure_type, COUNT(*) as count 
            FROM failure_events 
            WHERE timestamp >= ?
            GROUP BY failure_type 
            ORDER BY count DESC
        """, (cutoff_date,))
        stats['failure_types'] = dict(cursor.fetchall())
        
        # Project failures
        cursor.execute("""
            SELECT project, COUNT(*) as count 
            FROM failure_events 
            WHERE timestamp >= ?
            GROUP BY project 
            ORDER BY count DESC
        """, (cutoff_date,))
        stats['project_failures'] = dict(cursor.fetchall())
        
        # Node failures
        cursor.execute("""
            SELECT node_name, COUNT(*) as count 
            FROM failure_events 
            WHERE timestamp >= ? AND node_name IS NOT NULL
            GROUP BY node_name 
            ORDER BY count DESC
        """, (cutoff_date,))
        stats['node_failures'] = dict(cursor.fetchall())
        
        # Image failures
        cursor.execute("""
            SELECT container_image, COUNT(*) as count 
            FROM failure_events 
            WHERE timestamp >= ? AND container_image IS NOT NULL
            GROUP BY container_image 
            ORDER BY count DESC
            LIMIT 10
        """, (cutoff_date,))
        stats['image_failures'] = dict(cursor.fetchall())
        
        conn.close()
        return stats
    
    def record_solution(self, failure_type: str, solution: str, success: bool):
        """Record a solution attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO failure_solutions (failure_type, solution_description, success_count, failure_count, last_used)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(failure_type, solution_description) DO UPDATE SET
                success_count = success_count + ?,
                failure_count = failure_count + ?,
                last_used = CURRENT_TIMESTAMP
        """, (
            failure_type,
            solution,
            1 if success else 0,
            0 if success else 1,
            1 if success else 0,
            0 if success else 1
        ))
        
        conn.commit()
        conn.close()
    
    def get_best_solutions(self, failure_type: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Get best solutions for a failure type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                solution_description,
                success_count,
                failure_count,
                (success_count * 1.0 / (success_count + failure_count + 1)) as success_rate
            FROM failure_solutions
            WHERE failure_type = ?
            ORDER BY success_rate DESC, success_count DESC
            LIMIT ?
        """, (failure_type, limit))
        
        results = []
        for row in cursor.fetchall():
            solution, success_count, failure_count, success_rate = row
            results.append((solution, success_rate, success_count, failure_count))
        
        conn.close()
        return results


class FailurePatternAnalyzer:
    """Analyze failure patterns and provide insights"""
    
    def __init__(self, db: FailureDatabase, threshold: int = 3):
        self.db = db
        self.threshold = threshold
    
    def analyze_patterns(self, days: int = 7) -> Dict[str, Any]:
        """Comprehensive pattern analysis"""
        failures = self.db.get_recent_failures(days=days)
        
        if not failures:
            return {"message": "No failures found in the specified time period"}
        
        analysis = {
            "summary": {
                "total_failures": len(failures),
                "time_period_days": days,
                "projects_affected": len(set(f['project'] for f in failures)),
                "unique_failure_types": len(set(f['failure_type'] for f in failures))
            },
            "patterns": [],
            "correlations": [],
            "hot_nodes": [],
            "recommendations": []
        }
        
        # Pattern 1: Repeated failures in same project
        project_failures = defaultdict(list)
        for f in failures:
            project_failures[f['project']].append(f)
        
        for project, proj_failures in project_failures.items():
            if len(proj_failures) >= self.threshold:
                failure_types = Counter(f['failure_type'] for f in proj_failures)
                analysis['patterns'].append({
                    "type": "project_pattern",
                    "project": project,
                    "failure_count": len(proj_failures),
                    "top_failure_types": dict(failure_types.most_common(3)),
                    "severity": "high" if len(proj_failures) >= 5 else "medium"
                })
        
        # Pattern 2: Node failures (hot nodes)
        node_failures = defaultdict(list)
        for f in failures:
            if f['node_name']:
                node_failures[f['node_name']].append(f)
        
        for node, node_fails in node_failures.items():
            if len(node_fails) >= self.threshold:
                total_jobs = len(set(f['job_name'] for f in node_fails))
                failure_rate = len(node_fails) / total_jobs if total_jobs > 0 else 0
                
                analysis['hot_nodes'].append({
                    "node": node,
                    "failure_count": len(node_fails),
                    "jobs_affected": total_jobs,
                    "failure_rate": f"{failure_rate:.1%}",
                    "severity": "critical" if failure_rate > 0.5 else "high"
                })
        
        # Pattern 3: Image-related failures
        image_failures = defaultdict(list)
        for f in failures:
            if f['container_image']:
                image_failures[f['container_image']].append(f)
        
        for image, img_fails in image_failures.items():
            if len(img_fails) >= self.threshold:
                analysis['correlations'].append({
                    "type": "image_correlation",
                    "image": image,
                    "failure_count": len(img_fails),
                    "common_errors": self._extract_common_errors(img_fails)
                })
        
        # Pattern 4: Time-based patterns
        time_patterns = self._analyze_time_patterns(failures)
        if time_patterns:
            analysis['patterns'].extend(time_patterns)
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _extract_common_errors(self, failures: List[Dict]) -> List[str]:
        """Extract common error messages"""
        errors = [f['error_message'] for f in failures if f['error_message']]
        if not errors:
            return []
        
        # Simple frequency analysis
        error_counter = Counter(errors)
        return [error for error, count in error_counter.most_common(3)]
    
    def _analyze_time_patterns(self, failures: List[Dict]) -> List[Dict]:
        """Analyze time-based patterns"""
        patterns = []
        
        # Group by hour
        hour_failures = defaultdict(int)
        for f in failures:
            try:
                timestamp = datetime.fromisoformat(f['timestamp'])
                hour_failures[timestamp.hour] += 1
            except:
                continue
        
        # Find peak hours
        if hour_failures:
            max_hour_failures = max(hour_failures.values())
            if max_hour_failures >= 5:
                peak_hours = [h for h, count in hour_failures.items() if count >= max_hour_failures * 0.8]
                patterns.append({
                    "type": "time_pattern",
                    "description": f"Failures spike during hours {peak_hours}",
                    "peak_hours": peak_hours,
                    "suggestion": "May indicate resource contention or scheduled workloads"
                })
        
        return patterns
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # High-frequency project failures
        for pattern in analysis.get('patterns', []):
            if pattern.get('type') == 'project_pattern' and pattern.get('severity') in ['high', 'critical']:
                recommendations.append(
                    f"🔴 Project '{pattern['project']}' has {pattern['failure_count']} failures. "
                    f"Review project resources and job configurations."
                )
        
        # Hot node recommendations
        for node_info in analysis.get('hot_nodes', [])[:3]:  # Top 3 problematic nodes
            if node_info.get('severity') == 'critical':
                recommendations.append(
                    f"⚠️ Node '{node_info['node']}' has {node_info['failure_rate']} failure rate "
                    f"({node_info['failure_count']} failures). Consider cordoning this node for maintenance."
                )
        
        # Image correlation recommendations
        for corr in analysis.get('correlations', []):
            if corr.get('type') == 'image_correlation' and corr.get('failure_count') >= 5:
                recommendations.append(
                    f"🐳 Image '{corr['image']}' is associated with {corr['failure_count']} failures. "
                    f"Verify image compatibility and dependencies."
                )
        
        if not recommendations:
            recommendations.append("✅ No critical patterns detected. System appears healthy.")
        
        return recommendations


class RemediationEngine:
    """Automated remediation suggestions and execution"""
    
    def __init__(self, db: FailureDatabase):
        self.db = db
        
        # Knowledge base of failure → remediation mappings
        self.remediation_rules = {
            "OOMKilled": {
                "description": "Out of Memory - Pod exceeded memory limit",
                "solutions": [
                    {
                        "action": "increase_memory",
                        "description": "Increase memory request/limit by 2x",
                        "params": {"multiplier": 2.0}
                    },
                    {
                        "action": "optimize_code",
                        "description": "Optimize application memory usage (manual)",
                        "params": {}
                    }
                ]
            },
            "ImagePullBackOff": {
                "description": "Cannot pull container image",
                "solutions": [
                    {
                        "action": "verify_image",
                        "description": "Verify image name, tag, and registry access",
                        "params": {}
                    },
                    {
                        "action": "check_credentials",
                        "description": "Check image pull secrets and registry credentials",
                        "params": {}
                    }
                ]
            },
            "CrashLoopBackOff": {
                "description": "Container crashes immediately after starting",
                "solutions": [
                    {
                        "action": "check_command",
                        "description": "Verify container command and entrypoint",
                        "params": {}
                    },
                    {
                        "action": "check_dependencies",
                        "description": "Check for missing dependencies or environment variables",
                        "params": {}
                    }
                ]
            },
            "Pending": {
                "description": "Job stuck in Pending state - insufficient resources",
                "solutions": [
                    {
                        "action": "reduce_resources",
                        "description": "Reduce GPU/CPU/Memory requests",
                        "params": {"gpu_reduction": 0.5}
                    },
                    {
                        "action": "wait_for_resources",
                        "description": "Wait for cluster resources to become available",
                        "params": {"estimated_wait_minutes": 30}
                    }
                ]
            },
            "Error": {
                "description": "Generic error - requires investigation",
                "solutions": [
                    {
                        "action": "check_logs",
                        "description": "Review pod logs for specific error messages",
                        "params": {}
                    },
                    {
                        "action": "resubmit",
                        "description": "Resubmit job (may be transient error)",
                        "params": {}
                    }
                ]
            }
        }
    
    def suggest_remediation(self, failure_type: str, failure_context: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest remediation based on failure type and context"""
        
        # Get rule-based solutions
        rule_based = self.remediation_rules.get(failure_type, {})
        
        # Get historical solutions
        historical_solutions = self.db.get_best_solutions(failure_type, limit=3)
        
        suggestion = {
            "failure_type": failure_type,
            "description": rule_based.get("description", "Unknown failure type"),
            "rule_based_solutions": rule_based.get("solutions", []),
            "historical_solutions": [
                {
                    "solution": sol[0],
                    "success_rate": f"{sol[1]:.1%}",
                    "success_count": sol[2],
                    "failure_count": sol[3]
                }
                for sol in historical_solutions
            ],
            "context": failure_context
        }
        
        return suggestion
    
    def format_remediation_report(self, suggestion: Dict[str, Any]) -> str:
        """Format remediation suggestion as readable report"""
        
        report = f"""
🔧 **Automated Remediation Suggestions**

**Failure Type:** {suggestion['failure_type']}
**Description:** {suggestion['description']}

---

## 🎯 Rule-Based Solutions

"""
        
        for idx, sol in enumerate(suggestion['rule_based_solutions'], 1):
            report += f"{idx}. **{sol['description']}**\n"
            if sol.get('params'):
                report += f"   Parameters: {json.dumps(sol['params'], indent=2)}\n"
            report += "\n"
        
        if suggestion['historical_solutions']:
            report += """
## 📊 Historical Solutions (Community Knowledge)

These solutions have been tried by other users:

"""
            for idx, sol in enumerate(suggestion['historical_solutions'], 1):
                report += f"{idx}. {sol['solution']}\n"
                report += f"   ✅ Success Rate: {sol['success_rate']} ({sol['success_count']} successes, {sol['failure_count']} failures)\n\n"
        
        return report


@register_function(config_type=FailureAnalyzerConfig)
async def runai_failure_analyzer(config: FailureAnalyzerConfig, builder: Builder):
    """
    Advanced failure analysis with pattern recognition and automated remediation.
    
    Provides:
    - Historical failure tracking
    - Pattern recognition across jobs, projects, and nodes
    - Cross-job correlation analysis
    - Automated remediation suggestions
    - Knowledge graph of failure → solution mappings
    """
    
    # Initialize database and engines
    db = FailureDatabase(config.db_path)
    pattern_analyzer = FailurePatternAnalyzer(db, threshold=config.pattern_threshold)
    remediation_engine = RemediationEngine(db)
    
    async def _analyze_fn(
        action: str = "analyze",
        project: Optional[str] = None,
        job_name: Optional[str] = None,
        failure_type: Optional[str] = None,
        lookback_days: Optional[int] = None
    ) -> str:
        """
        Analyze failures and provide insights.
        
        Actions:
        - analyze: Comprehensive pattern analysis
        - record: Record a new failure event (used by monitoring)
        - remediate: Get remediation suggestions for a specific failure
        - stats: Get failure statistics
        """
        
        # Validate project access
        if project and "*" not in config.allowed_projects and project not in config.allowed_projects:
            return f"❌ Access denied to project '{project}'"
        
        days = lookback_days or config.lookback_days
        
        if action == "analyze":
            return await _analyze_patterns(project, days)
        
        elif action == "stats":
            return await _get_stats(days)
        
        elif action == "remediate":
            if not failure_type:
                return "❌ Please specify failure_type for remediation suggestions"
            return await _get_remediation(failure_type, job_name, project)
        
        else:
            return f"❌ Invalid action '{action}'. Use: analyze, stats, or remediate"
    
    async def _analyze_patterns(project: Optional[str], days: int) -> str:
        """Comprehensive failure pattern analysis"""
        
        logger.info(f"🔍 Analyzing failure patterns (last {days} days, project={project or 'all'})")
        
        failures = db.get_recent_failures(days=days, project=project)
        
        if not failures:
            return f"""
📊 **Failure Analysis Report**

**Time Period:** Last {days} days
**Project Filter:** {project or 'All projects'}

✅ **No failures detected!**

The cluster is running smoothly with no recorded failures in the specified time period.
"""
        
        # Run pattern analysis
        analysis = pattern_analyzer.analyze_patterns(days=days)
        
        # Format report
        report = f"""
📊 **Advanced Failure Analysis Report**

**Time Period:** Last {days} days
**Project Filter:** {project or 'All projects'}

---

## 📈 Summary

- **Total Failures:** {analysis['summary']['total_failures']}
- **Projects Affected:** {analysis['summary']['projects_affected']}
- **Unique Failure Types:** {analysis['summary']['unique_failure_types']}

---

## 🔍 Detected Patterns

"""
        
        if analysis['patterns']:
            for pattern in analysis['patterns']:
                if pattern['type'] == 'project_pattern':
                    severity_emoji = "🔴" if pattern['severity'] == 'high' else "🟡"
                    report += f"{severity_emoji} **Project: {pattern['project']}**\n"
                    report += f"   - Failures: {pattern['failure_count']}\n"
                    report += f"   - Top failure types: {pattern['top_failure_types']}\n\n"
                elif pattern['type'] == 'time_pattern':
                    report += f"⏰ **{pattern['description']}**\n"
                    report += f"   - {pattern['suggestion']}\n\n"
        else:
            report += "✅ No significant patterns detected\n\n"
        
        # Hot nodes
        if analysis['hot_nodes']:
            report += "## 🔥 Problematic Nodes\n\n"
            for node in analysis['hot_nodes'][:5]:
                severity_emoji = "🔴" if node['severity'] == 'critical' else "⚠️"
                report += f"{severity_emoji} **Node: {node['node']}**\n"
                report += f"   - Failures: {node['failure_count']} across {node['jobs_affected']} jobs\n"
                report += f"   - Failure Rate: {node['failure_rate']}\n\n"
        
        # Correlations
        if analysis['correlations']:
            report += "## 🔗 Correlations\n\n"
            for corr in analysis['correlations'][:5]:
                if corr['type'] == 'image_correlation':
                    report += f"🐳 **Image: {corr['image']}**\n"
                    report += f"   - Failure count: {corr['failure_count']}\n"
                    if corr['common_errors']:
                        report += f"   - Common errors: {', '.join(corr['common_errors'][:2])}\n"
                    report += "\n"
        
        # Recommendations
        report += "## 💡 Recommendations\n\n"
        for rec in analysis['recommendations']:
            report += f"{rec}\n\n"
        
        report += """
---

**💡 Tip:** Use `action='remediate'` with a specific failure_type to get automated remediation suggestions.
"""
        
        return report
    
    async def _get_stats(days: int) -> str:
        """Get failure statistics"""
        
        stats = db.get_pattern_stats(days=days)
        
        # Get recent failures to show job names
        all_failures = db.get_recent_failures(days=days)
        
        report = f"""
📊 **Failure Statistics**

**Time Period:** Last {days} days
**Total Failures:** {len(all_failures)} events

---

## Failure Types

"""
        
        for failure_type, count in stats['failure_types'].items():
            report += f"- **{failure_type}**: {count} occurrences\n"
        
        report += "\n## Project Failures\n\n"
        for project, count in list(stats['project_failures'].items())[:10]:
            report += f"- **{project}**: {count} failures\n"
        
        if stats['node_failures']:
            report += "\n## Node Failures\n\n"
            for node, count in list(stats['node_failures'].items())[:10]:
                # Show 'unknown' as a special case with explanation
                if node == 'unknown' or node is None or node == '':
                    report += f"- **Unknown Node** (node name not available in API): {count} failures\n"
                else:
                    report += f"- **{node}**: {count} failures\n"
        
        # Add failed job names section
        if all_failures:
            report += "\n## Failed Jobs\n\n"
            
            # Group failures by job name
            from collections import defaultdict
            jobs_by_project = defaultdict(list)
            for f in all_failures:
                jobs_by_project[f['project']].append({
                    'name': f['job_name'],
                    'phase': f['failure_type'],
                    'timestamp': f['timestamp'],
                    'node': f.get('node_name', 'unknown')
                })
            
            # Display failures grouped by project
            for project in sorted(jobs_by_project.keys()):
                report += f"\n### {project}\n\n"
                # Get unique job names (jobs may have multiple failure events)
                unique_jobs = {}
                for job in jobs_by_project[project]:
                    job_name = job['name']
                    if job_name not in unique_jobs:
                        unique_jobs[job_name] = job
                
                for job_name, job_info in sorted(unique_jobs.items()):
                    node_info = f" on `{job_info['node']}`" if job_info['node'] != 'unknown' else ""
                    report += f"- **{job_name}** - {job_info['phase']}{node_info} (last seen: {job_info['timestamp']})\n"
        
        return report
    
    async def _get_remediation(
        failure_type: str,
        job_name: Optional[str],
        project: Optional[str]
    ) -> str:
        """Get remediation suggestions for a specific failure"""
        
        context = {
            "job_name": job_name,
            "project": project
        }
        
        suggestion = remediation_engine.suggest_remediation(failure_type, context)
        report = remediation_engine.format_remediation_report(suggestion)
        
        return report
    
    # Yield the function
    yield FunctionInfo.from_fn(
        _analyze_fn,
        description=(
            "Advanced failure analysis with pattern recognition and automated remediation. "
            "Analyzes historical failures to identify patterns, correlations, and provide "
            "intelligent remediation suggestions.\n\n"
            "Actions:\n"
            "- analyze: Comprehensive pattern analysis across jobs and projects\n"
            "- stats: Get failure statistics and counts\n"
            "- remediate: Get automated remediation suggestions for a specific failure type\n\n"
            "Parameters:\n"
            "- action: 'analyze', 'stats', or 'remediate' (default: analyze)\n"
            "- project: Optional project filter\n"
            "- lookback_days: Days of history to analyze (default: 7)\n"
            "- failure_type: Required for 'remediate' action (e.g., 'OOMKilled', 'ImagePullBackOff')\n\n"
            "Examples:\n"
            "- Analyze all failures: action='analyze'\n"
            "- Get stats: action='stats', lookback_days=30\n"
            "- Get remediation for OOM: action='remediate', failure_type='OOMKilled'"
        )
    )
    
    logger.info("Failure analyzer initialized")

