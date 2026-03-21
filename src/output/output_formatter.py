"""Output formatter for study content recommendations"""

import json
from typing import Dict
from pathlib import Path

from .recommendation_generator import TopicRecommendations, Recommendation


class OutputFormatter:
    """Formats recommendations in various output formats"""
    
    @staticmethod
    def format_json(recommendations: Dict[str, TopicRecommendations]) -> str:
        """
        Format recommendations as JSON with complete metadata.
        
        Args:
            recommendations: Dictionary mapping topic to TopicRecommendations
            
        Returns:
            JSON string with complete recommendation metadata
        """
        output = {}
        
        for topic, topic_recs in recommendations.items():
            output[topic] = {
                "topic": topic_recs.topic,
                "total_count": topic_recs.total_count,
                "recommendations": [
                    {
                        "title": rec.title,
                        "url": rec.url,
                        "source": rec.source,
                        "author": rec.author,
                        "content_type": rec.content_type,
                        "quality_score": rec.quality_score,
                        "publication_date": rec.publication_date.isoformat() if rec.publication_date else None
                    }
                    for rec in topic_recs.recommendations
                ]
            }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    @staticmethod
    def format_markdown(recommendations: Dict[str, TopicRecommendations]) -> str:
        """
        Format recommendations as Markdown for readability.
        
        Args:
            recommendations: Dictionary mapping topic to TopicRecommendations
            
        Returns:
            Markdown formatted string
        """
        lines = ["# Study Content Recommendations\n"]
        
        for topic, topic_recs in recommendations.items():
            lines.append(f"## {topic_recs.topic}\n")
            lines.append(f"**Total Recommendations:** {topic_recs.total_count}\n")
            
            if not topic_recs.recommendations:
                lines.append("*No recommendations available for this topic.*\n")
                continue
            
            for idx, rec in enumerate(topic_recs.recommendations, 1):
                lines.append(f"### {idx}. {rec.title}\n")
                lines.append(f"- **URL:** {rec.url}")
                lines.append(f"- **Source:** {rec.source}")
                lines.append(f"- **Author:** {rec.author or 'Unknown'}")
                lines.append(f"- **Type:** {rec.content_type}")
                lines.append(f"- **Quality Score:** {rec.quality_score:.2f}")
                
                if rec.publication_date:
                    lines.append(f"- **Published:** {rec.publication_date.isoformat()}")
                
                lines.append("")  # Empty line between recommendations
            
            lines.append("")  # Empty line between topics
        
        return "\n".join(lines)
    
    @staticmethod
    def save_to_file(
        recommendations: Dict[str, TopicRecommendations],
        filepath: str,
        format: str = "json"
    ) -> None:
        """
        Save recommendations to a file with format selection.
        
        Args:
            recommendations: Dictionary mapping topic to TopicRecommendations
            filepath: Path where the file should be saved
            format: Output format - "json" or "markdown" (default: "json")
            
        Raises:
            ValueError: If format is not "json" or "markdown"
            IOError: If file cannot be written
        """
        if format not in ["json", "markdown"]:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'markdown'.")
        
        # Format the content
        if format == "json":
            content = OutputFormatter.format_json(recommendations)
        else:  # markdown
            content = OutputFormatter.format_markdown(recommendations)
        
        # Ensure parent directory exists
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write to file {filepath}: {e}")
