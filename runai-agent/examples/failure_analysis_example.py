"""
Example: Advanced Failure Analysis

This example demonstrates how to use the failure analyzer to:
1. Analyze failure patterns across the cluster
2. Get remediation suggestions for specific failure types
3. Query failure statistics
4. Access the knowledge graph
"""

import asyncio
from runai_agent.functions.failure_analyzer import (
    FailureDatabase,
    FailurePatternAnalyzer,
    RemediationEngine
)


async def main():
    """Run failure analysis examples"""
    
    # Initialize components
    db_path = "/tmp/runai_failure_history_example.db"
    db = FailureDatabase(db_path)
    analyzer = FailurePatternAnalyzer(db, threshold=2)
    remediation = RemediationEngine(db)
    
    print("=" * 80)
    print("Advanced Failure Analysis Example")
    print("=" * 80)
    
    # Example 1: Record some sample failures
    print("\n1️⃣ Recording Sample Failures...")
    print("-" * 80)
    
    sample_failures = [
        {
            'job_name': 'training-job-1',
            'project': 'ml-team',
            'failure_type': 'OOMKilled',
            'phase': 'OOMKilled',
            'pod_name': 'training-job-1-0-0',
            'node_name': 'gpu-node-03',
            'container_image': 'pytorch/pytorch:latest',
            'error_message': 'Container killed due to memory limit exceeded',
            'logs_snippet': 'CUDA out of memory. Tried to allocate 2.00 GiB',
            'events_snippet': 'OOMKilled: Memory limit exceeded',
            'gpu_count': 4,
            'memory_request': '16Gi',
            'cpu_request': '8'
        },
        {
            'job_name': 'training-job-2',
            'project': 'ml-team',
            'failure_type': 'OOMKilled',
            'phase': 'OOMKilled',
            'pod_name': 'training-job-2-0-0',
            'node_name': 'gpu-node-05',
            'container_image': 'pytorch/pytorch:latest',
            'error_message': 'Container killed due to memory limit exceeded',
            'logs_snippet': 'RuntimeError: CUDA out of memory',
            'events_snippet': 'OOMKilled: Memory limit exceeded',
            'gpu_count': 2,
            'memory_request': '8Gi',
            'cpu_request': '4'
        },
        {
            'job_name': 'training-job-3',
            'project': 'data-science',
            'failure_type': 'ImagePullBackOff',
            'phase': 'ImagePullBackOff',
            'pod_name': 'training-job-3-0-0',
            'node_name': 'gpu-node-03',
            'container_image': 'custom-registry.io/ml-model:v2.0',
            'error_message': 'Failed to pull image: unauthorized',
            'logs_snippet': 'Error response from daemon: pull access denied',
            'events_snippet': 'Failed to pull image: unauthorized',
            'gpu_count': 1,
            'memory_request': '4Gi',
            'cpu_request': '2'
        },
        {
            'job_name': 'training-job-4',
            'project': 'ml-team',
            'failure_type': 'OOMKilled',
            'phase': 'OOMKilled',
            'pod_name': 'training-job-4-0-0',
            'node_name': 'gpu-node-03',
            'container_image': 'tensorflow/tensorflow:latest-gpu',
            'error_message': 'Container killed due to memory limit exceeded',
            'logs_snippet': 'ResourceExhaustedError: OOM when allocating tensor',
            'events_snippet': 'OOMKilled: Memory limit exceeded',
            'gpu_count': 4,
            'memory_request': '16Gi',
            'cpu_request': '8'
        }
    ]
    
    for failure in sample_failures:
        failure_id = db.record_failure(failure)
        print(f"✓ Recorded failure #{failure_id}: {failure['job_name']} ({failure['failure_type']})")
        
        # Update correlations
        if failure.get('node_name'):
            db.update_correlation('node', failure['node_name'])
        if failure.get('container_image'):
            db.update_correlation('image', failure['container_image'])
    
    # Example 2: Analyze patterns
    print("\n2️⃣ Analyzing Failure Patterns...")
    print("-" * 80)
    
    analysis = analyzer.analyze_patterns(days=7)
    
    print(f"\n📈 Summary:")
    print(f"   Total Failures: {analysis['summary']['total_failures']}")
    print(f"   Projects Affected: {analysis['summary']['projects_affected']}")
    print(f"   Unique Failure Types: {analysis['summary']['unique_failure_types']}")
    
    if analysis['patterns']:
        print(f"\n🔍 Detected Patterns:")
        for pattern in analysis['patterns']:
            if pattern['type'] == 'project_pattern':
                print(f"   🔴 Project '{pattern['project']}': {pattern['failure_count']} failures")
                print(f"      Top types: {pattern['top_failure_types']}")
    
    if analysis['hot_nodes']:
        print(f"\n🔥 Problematic Nodes:")
        for node in analysis['hot_nodes']:
            print(f"   ⚠️  {node['node']}: {node['failure_count']} failures ({node['failure_rate']})")
    
    if analysis['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations'][:3]:
            print(f"   {rec}")
    
    # Example 3: Get remediation suggestions
    print("\n3️⃣ Getting Remediation Suggestions...")
    print("-" * 80)
    
    # Record some successful solutions
    db.record_solution('OOMKilled', 'Increase memory limit from 16Gi to 32Gi', success=True)
    db.record_solution('OOMKilled', 'Increase memory limit from 16Gi to 32Gi', success=True)
    db.record_solution('OOMKilled', 'Enable gradient checkpointing', success=True)
    db.record_solution('OOMKilled', 'Reduce batch size', success=False)
    db.record_solution('ImagePullBackOff', 'Add imagePullSecrets to job spec', success=True)
    
    # Get suggestions for OOMKilled
    suggestion = remediation.suggest_remediation('OOMKilled', {
        'job_name': 'training-job-1',
        'project': 'ml-team'
    })
    
    print(f"\n🔧 Remediation for {suggestion['failure_type']}:")
    print(f"   Description: {suggestion['description']}")
    
    print(f"\n   Rule-Based Solutions:")
    for idx, sol in enumerate(suggestion['rule_based_solutions'], 1):
        print(f"   {idx}. {sol['description']}")
    
    if suggestion['historical_solutions']:
        print(f"\n   Historical Solutions (Community Knowledge):")
        for idx, sol in enumerate(suggestion['historical_solutions'], 1):
            print(f"   {idx}. {sol['solution']}")
            print(f"      Success Rate: {sol['success_rate']} ({sol['success_count']} successes)")
    
    # Example 4: Get statistics
    print("\n4️⃣ Failure Statistics...")
    print("-" * 80)
    
    stats = db.get_pattern_stats(days=7)
    
    print(f"\n📊 Failure Types:")
    for failure_type, count in stats['failure_types'].items():
        print(f"   - {failure_type}: {count} occurrences")
    
    print(f"\n📊 Project Failures:")
    for project, count in stats['project_failures'].items():
        print(f"   - {project}: {count} failures")
    
    if stats['node_failures']:
        print(f"\n📊 Node Failures:")
        for node, count in list(stats['node_failures'].items())[:5]:
            print(f"   - {node}: {count} failures")
    
    # Example 5: Query recent failures
    print("\n5️⃣ Recent Failures...")
    print("-" * 80)
    
    recent = db.get_recent_failures(days=7)
    print(f"\nFound {len(recent)} recent failures:")
    for failure in recent[:3]:
        print(f"   - {failure['job_name']} ({failure['project']}): {failure['failure_type']}")
        print(f"     Node: {failure['node_name']}, Image: {failure['container_image']}")
    
    print("\n" + "=" * 80)
    print("✅ Example Complete!")
    print("=" * 80)
    print(f"\nDatabase location: {db_path}")
    print("You can inspect the database with: sqlite3 " + db_path)


if __name__ == "__main__":
    asyncio.run(main())

