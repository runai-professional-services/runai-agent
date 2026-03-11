"""
Job Performance Analytics

Provides historical performance insights: execution time trends, failure rates,
recommendations, and anomaly detection (jobs running longer than usual).
Uses the same SQLite DB as failure analysis (job_run_history table).
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Union
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import (
    _get_secure_runai_config,
    _coerce_optional_int,
    _normalize_optional_str_none,
    _workload_image,
    logger,
)


class JobAnalyticsConfig(FunctionBaseConfig, name="runai_job_analytics"):
    """Configuration for job performance analytics."""

    description: str = (
        "Job performance analytics: execution time trends, failure rates by project/image, "
        "recommendations, and anomaly detection (jobs running 3x longer than usual)."
    )
    db_path: str = Field(
        default="/tmp/runai_failure_history.db",
        description="Path to SQLite database (same as failure analyzer)",
    )
    lookback_days: int = Field(default=7, description="Days of history to analyze")
    allowed_projects: List[str] = Field(
        default_factory=lambda: ["*"], description="Projects to include"
    )


def _format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


@register_function(config_type=JobAnalyticsConfig)
async def runai_job_analytics(config: JobAnalyticsConfig, builder: Builder):
    """
    Job performance analytics: execution trends, failure rates, recommendations, anomalies.
    Uses run history (populated by proactive monitor) and failure data from the same DB.
    """
    from .failure_analyzer import FailureDatabase

    def _db_path() -> str:
        return os.environ.get("RUNAI_FAILURE_DB_PATH", config.db_path)

    async def _analytics_fn(
        lookback_days: Optional[Union[int, str]] = None,
        project: Optional[str] = None,
    ) -> str:
        days = _coerce_optional_int(lookback_days, config.lookback_days)
        project = _normalize_optional_str_none(project)
        if (
            project
            and "*" not in config.allowed_projects
            and project not in config.allowed_projects
        ):
            return f"❌ Access denied to project '{project}'"

        try:
            db = FailureDatabase(_db_path())
        except Exception as e:
            logger.exception("Job analytics: failed to open database")
            return f"❌ Could not open analytics database: {e}. Check RUNAI_FAILURE_DB_PATH or permissions."

        sections: List[str] = []

        try:
            # 1. Execution time trends (from job_run_history)
            agg = db.get_run_aggregates(days=days, project=project)
        except Exception as e:
            logger.exception("Job analytics: get_run_aggregates failed")
            return f"❌ Analytics error reading run history: {e}. Try specifying a project (e.g. 'for project-03') or check the database path."

        if agg.get("runs_with_duration", 0) == 0:
            sections.append(
                "## 📈 Execution time trends\n\n"
                "No run history with duration yet.\n\n"
                "**How data is collected:** In Kubernetes, the monitoring sidecar records job completions automatically. "
                'Otherwise, say **"Start monitoring all jobs"** in chat to record completions. Trends will appear once data is recorded.'
            )
        else:
            lines = [
                f"- **Total runs (with duration):** {agg['runs_with_duration']} (last {days} days)",
                f"- **Overall avg duration:** {_format_duration(agg['avg_duration_seconds'])}",
            ]
            if agg.get("by_project"):
                lines.append("\n**By project:**")
                for proj, avg_sec in sorted(
                    agg["by_project"].items(), key=lambda x: -x[1]
                )[:10]:
                    lines.append(f"- {proj}: {_format_duration(avg_sec)} avg")
            if agg.get("by_image"):
                lines.append("\n**By image (top 5):**")
                for img, avg_sec in sorted(
                    agg["by_image"].items(), key=lambda x: -x[1]
                )[:5]:
                    short_img = (img[:60] + "…") if len(img) > 60 else img
                    lines.append(f"- {short_img}: {_format_duration(avg_sec)} avg")
            sections.append("## 📈 Execution time trends\n\n" + "\n".join(lines))

        try:
            # 2. Failure rate analysis (from failure_events)
            stats = db.get_pattern_stats(days=days)
            fail_types = stats.get("failure_types") or {}
            proj_failures = stats.get("project_failures") or {}
            image_failures = stats.get("image_failures") or {}
            if project:
                proj_failures = {k: v for k, v in proj_failures.items() if k == project}
            if not fail_types and not proj_failures:
                sections.append(
                    "## 🔴 Failure rates\n\nNo failures recorded in this period."
                )
            else:
                lines = [f"- **Failure types:** {dict(fail_types)}", "**By project:**"]
                for p, c in sorted(proj_failures.items(), key=lambda x: -x[1])[:10]:
                    lines.append(f"- {p}: {c}")
                if image_failures:
                    lines.append("\n**By image (top 5):**")
                    for img, c in sorted(image_failures.items(), key=lambda x: -x[1])[
                        :5
                    ]:
                        short_img = (img[:50] + "…") if len(img) > 50 else img
                        lines.append(f"- {short_img}: {c}")
                sections.append("## 🔴 Failure rates\n\n" + "\n".join(lines))

            # 3. Recommendations
            recs = []
            if agg.get("by_project"):
                for proj, avg_sec in sorted(
                    agg["by_project"].items(), key=lambda x: -x[1]
                )[:3]:
                    recs.append(
                        f"- **{proj}**: Training jobs typically take ~{_format_duration(avg_sec)} — schedule accordingly."
                    )
            if not recs:
                recs.append(
                    '- Execution trends appear once completions are recorded (by the monitoring sidecar in Kubernetes or by saying **"Start monitoring all jobs"** in chat).'
                )
            sections.append("## 💡 Recommendations\n\n" + "\n".join(recs))

            # 4. Anomaly: running jobs taking much longer than usual (with timeout so request cannot hang)
            secure = _get_secure_runai_config()
            if all(
                [
                    secure.get("RUNAI_CLIENT_ID"),
                    secure.get("RUNAI_CLIENT_SECRET"),
                    secure.get("RUNAI_BASE_URL"),
                ]
            ):

                def _anomaly_sync() -> str:
                    from runai.configuration import Configuration
                    from runai.api_client import ApiClient
                    from runai.runai_client import RunaiClient

                    configuration = Configuration(
                        client_id=secure["RUNAI_CLIENT_ID"],
                        client_secret=secure["RUNAI_CLIENT_SECRET"],
                        runai_base_url=secure["RUNAI_BASE_URL"],
                    )
                    client = RunaiClient(ApiClient(configuration))
                    response = client.workloads.workloads.get_workloads()
                    data = response.data if hasattr(response, "data") else response
                    workloads = (
                        data.get("workloads", []) if isinstance(data, dict) else []
                    )
                    running = [
                        w
                        for w in workloads
                        if w.get("phase") == "Running"
                        or w.get("actualPhase") == "Running"
                    ]
                    by_image = agg.get("by_image") or {}
                    anomalies = []
                    now = datetime.utcnow()
                    for w in running:
                        created = w.get("createdAt")
                        if not created:
                            continue
                        try:
                            if "Z" in created or "+" in created:
                                created_dt = datetime.fromisoformat(
                                    created.replace("Z", "+00:00")
                                )
                            else:
                                created_dt = datetime.fromisoformat(created)
                            if created_dt.tzinfo:
                                created_dt = created_dt.replace(tzinfo=None)
                            elapsed = int((now - created_dt).total_seconds())
                        except (ValueError, TypeError):
                            continue
                        img = _workload_image(w) or "unknown"
                        avg_sec = (
                            by_image.get(img) or agg.get("avg_duration_seconds") or 3600
                        )
                        if avg_sec and elapsed > 3 * avg_sec:
                            anomalies.append(
                                f"- **{w.get('name')}** ({w.get('projectName')}): running {_format_duration(elapsed)} "
                                f"(avg for this image: {_format_duration(avg_sec)}) — consider checking."
                            )
                    if anomalies:
                        return (
                            "## ⚠️ Possible anomalies (running 3× longer than usual)\n\n"
                            + "\n".join(anomalies[:10])
                        )
                    return "## ⚠️ Anomalies\n\nNo running jobs are significantly longer than their usual duration."

                try:
                    section = await asyncio.wait_for(
                        asyncio.to_thread(_anomaly_sync),
                        timeout=15.0,
                    )
                    sections.append(section)
                except asyncio.TimeoutError:
                    logger.warning("Anomaly check timed out (Run:AI API)")
                    sections.append(
                        "## ⚠️ Anomalies\n\nAnomaly check timed out (Run:AI API slow or unreachable)."
                    )
                except Exception as e:
                    logger.debug(f"Anomaly check skipped: {e}")
                    sections.append(
                        "## ⚠️ Anomalies\n\nCould not fetch running jobs for anomaly check (Run:AI API)."
                    )
            else:
                sections.append(
                    "## ⚠️ Anomalies\n\nRun:AI credentials not set; anomaly detection skipped."
                )

            return (
                "📊 **Job Performance Analytics**\n\n"
                f"**Period:** Last {days} days | **Project:** {project or 'All'}\n\n"
                + "\n\n".join(sections)
            )
        except Exception as e:
            logger.exception("Job analytics failed")
            return f"❌ Job performance analytics failed: {e}. Try specifying a project (e.g. 'for project-03')."

    yield FunctionInfo.from_fn(
        _analytics_fn,
        description=(
            "Job performance analytics: execution time trends, failure rates by project/image, "
            "recommendations (e.g. typical job duration), and anomaly detection for jobs running "
            "much longer than usual. Use when the user asks about job duration, failure rates, "
            "or 'jobs taking too long'."
        ),
    )
    logger.info("Job analytics initialized")
