"""
Query Classification and Multi-Model Embedding System

This module provides intelligent query classification to determine the best
embedding model for different types of queries in the RunAI agent system.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries for specialized embedding model selection."""
    CODE_SEARCH = "code_search"           # Looking for specific code, functions, APIs
    DOCUMENTATION = "documentation"       # Seeking explanations, tutorials, how-tos
    QUESTION_ANSWERING = "qa"            # Direct questions needing answers
    TROUBLESHOOTING = "troubleshooting"  # Error resolution, debugging
    EXAMPLE_REQUEST = "example"          # Requesting code examples
    GENERAL = "general"                  # General/unclear intent

@dataclass
class QueryClassification:
    """Result of query classification."""
    query_type: QueryType
    confidence: float
    reasoning: str
    suggested_model: str

class QueryClassifier:
    """Classifies queries to determine the optimal embedding model."""
    
    def __init__(self):
        # Query patterns for different types
        self.patterns = {
            QueryType.CODE_SEARCH: [
                # Looking for specific functions/APIs
                r'\b(function|method|api|class|import)\b',
                r'\b(find|search|locate).+(function|method|code|api)\b',
                r'\b(how to use|usage of).+(api|function|method)\b',
                r'\b(client\.|api\.|\.)\w+',  # API calls like client.jobs.submit
                r'\b(submit|create|delete|update|list)_\w+',  # API method patterns
                
                # Code-specific terms
                r'\b(authentication|configuration|client|endpoint)\b',
                r'\b(async|await|def |class |import )\b',
                r'\b(python|code|script|implementation)\b',
            ],
            
            QueryType.DOCUMENTATION: [
                # Explanatory queries
                r'\b(what is|what does|explain|describe)\b',
                r'\b(how does.+work|how.+works)\b',
                r'\b(overview|introduction|getting started)\b',
                r'\b(concept|architecture|design)\b',
                r'\b(guide|tutorial|documentation)\b',
                r'\b(difference between|compare)\b',
            ],
            
            QueryType.QUESTION_ANSWERING: [
                # Direct questions
                r'^\s*(what|how|why|when|where|which|who)',
                r'\b(can i|should i|is it|are there)\b',
                r'\?\s*$',  # Ends with question mark
                r'\b(tell me|show me|help me)\b',
            ],
            
            QueryType.TROUBLESHOOTING: [
                # Error and problem resolution
                r'\b(error|exception|failed|failure|problem|issue)\b',
                r'\b(not working|doesn\'t work|broken|fix)\b',
                r'\b(debug|troubleshoot|solve|resolve)\b',
                r'\b(401|403|404|500)\b',  # HTTP error codes
                r'\b(unauthorized|forbidden|timeout)\b',
            ],
            
            QueryType.EXAMPLE_REQUEST: [
                # Requesting examples
                r'\b(example|sample|demo|template)\b',
                r'\b(show me how|give me an example)\b',
                r'\b(code example|usage example)\b',
                r'\b(how to.+(submit|create|run|execute))\b',
                r'\b(step by step|walkthrough)\b',
            ]
        }
        
        # Model recommendations for each query type
        self.model_recommendations = {
            QueryType.CODE_SEARCH: "microsoft/codebert-base",
            QueryType.DOCUMENTATION: "sentence-transformers/all-mpnet-base-v2", 
            QueryType.QUESTION_ANSWERING: "sentence-transformers/multi-qa-mpnet-base-dot-v1",
            QueryType.TROUBLESHOOTING: "sentence-transformers/multi-qa-mpnet-base-dot-v1",
            QueryType.EXAMPLE_REQUEST: "microsoft/codebert-base",
            QueryType.GENERAL: "sentence-transformers/all-mpnet-base-v2"
        }
    
    def classify_query(self, query: str) -> QueryClassification:
        """
        Classify a query and recommend the best embedding model.
        
        Args:
            query: The user's search query
            
        Returns:
            QueryClassification with type, confidence, and model recommendation
        """
        query_lower = query.lower().strip()
        
        if not query_lower:
            return QueryClassification(
                query_type=QueryType.GENERAL,
                confidence=1.0,
                reasoning="Empty query",
                suggested_model=self.model_recommendations[QueryType.GENERAL]
            )
        
        # Score each query type
        type_scores = {}
        
        for query_type, patterns in self.patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                matches = re.findall(pattern, query_lower, re.IGNORECASE)
                if matches:
                    # Weight based on pattern specificity and match count
                    pattern_weight = len(pattern) / 100  # More specific patterns get higher weight
                    match_count = len(matches)
                    score += pattern_weight * match_count
                    matched_patterns.append(pattern)
            
            if score > 0:
                type_scores[query_type] = {
                    'score': score,
                    'patterns': matched_patterns
                }
        
        # Determine best match
        if not type_scores:
            return QueryClassification(
                query_type=QueryType.GENERAL,
                confidence=0.5,
                reasoning="No specific patterns matched",
                suggested_model=self.model_recommendations[QueryType.GENERAL]
            )
        
        # Get highest scoring type
        best_type = max(type_scores.keys(), key=lambda t: type_scores[t]['score'])
        best_score = type_scores[best_type]['score']
        
        # Calculate confidence (normalize score)
        max_possible_score = len(self.patterns[best_type]) * 0.5  # Rough estimate
        confidence = min(best_score / max_possible_score, 1.0)
        
        # Ensure minimum confidence
        confidence = max(confidence, 0.3)
        
        # Create reasoning
        pattern_count = len(type_scores[best_type]['patterns'])
        reasoning = f"Matched {pattern_count} {best_type.value} patterns (score: {best_score:.2f})"
        
        return QueryClassification(
            query_type=best_type,
            confidence=confidence,
            reasoning=reasoning,
            suggested_model=self.model_recommendations[best_type]
        )
    
    def get_model_for_query(self, query: str) -> Tuple[str, QueryClassification]:
        """
        Get the recommended embedding model for a query.
        
        Args:
            query: The user's search query
            
        Returns:
            Tuple of (model_name, classification_details)
        """
        classification = self.classify_query(query)
        return classification.suggested_model, classification
    
    def explain_classification(self, query: str) -> str:
        """
        Provide a human-readable explanation of query classification.
        
        Args:
            query: The user's search query
            
        Returns:
            Explanation string
        """
        classification = self.classify_query(query)
        
        return f"""
Query Classification Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Query: "{query}"
🎯 Type: {classification.query_type.value.replace('_', ' ').title()}
📊 Confidence: {classification.confidence:.1%}
🧠 Model: {classification.suggested_model}
💭 Reasoning: {classification.reasoning}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# Global classifier instance
query_classifier = QueryClassifier()

# Convenience functions
def classify_query(query: str) -> QueryClassification:
    """Classify a query using the global classifier."""
    return query_classifier.classify_query(query)

def get_optimal_model(query: str) -> str:
    """Get the optimal embedding model for a query."""
    model, _ = query_classifier.get_model_for_query(query)
    return model

def explain_query_classification(query: str) -> str:
    """Explain how a query was classified."""
    return query_classifier.explain_classification(query)

if __name__ == "__main__":
    # Test the classifier
    test_queries = [
        "Find examples of submitting RunAI jobs",
        "What is the difference between training and inference?",
        "How do I authenticate with the RunAI API?",
        "client.jobs.submit is not working",
        "Show me how to create a distributed training job",
        "Error 401 unauthorized when calling API"
    ]
    
    print("🧠 Query Classification Test Results:")
    print("=" * 50)
    
    for query in test_queries:
        classification = classify_query(query)
        print(f"\n📝 '{query}'")
        print(f"   🎯 Type: {classification.query_type.value}")
        print(f"   🧠 Model: {classification.suggested_model}")
        print(f"   📊 Confidence: {classification.confidence:.1%}")
