"""Professional source evaluation for content quality assessment"""

from typing import Optional
import re


class ProfessionalSourceEvaluator:
    """Evaluates content sources for professional credentials and reputation"""
    
    def __init__(self):
        """Initialize the professional source evaluator with trusted source whitelist"""
        # Whitelist of trusted professional sources with reputation scores
        self._source_whitelist = {
            # Academic and research platforms
            'arxiv.org': 0.95,
            'scholar.google.com': 0.95,
            'researchgate.net': 0.90,
            'ieee.org': 0.95,
            'acm.org': 0.95,
            'springer.com': 0.90,
            'sciencedirect.com': 0.90,
            'nature.com': 0.95,
            'science.org': 0.95,
            
            # Professional tech blogs and platforms
            'medium.com': 0.75,
            'dev.to': 0.75,
            'hackernoon.com': 0.70,
            'towardsdatascience.com': 0.80,
            'freecodecamp.org': 0.80,
            'stackoverflow.blog': 0.85,
            
            # Industry-specific professional sources
            'martinfowler.com': 0.90,
            'thoughtworks.com': 0.85,
            'infoq.com': 0.80,
            'dzone.com': 0.75,
            
            # Educational institutions
            'mit.edu': 0.95,
            'stanford.edu': 0.95,
            'berkeley.edu': 0.95,
            'harvard.edu': 0.95,
            'ox.ac.uk': 0.95,
            'cambridge.org': 0.95,
        }
        
        # Professional affiliation indicators
        self._professional_indicators = [
            r'\b(?:PhD|Ph\.D\.|Doctor|Professor|Dr\.)\b',
            r'\b(?:Senior|Lead|Principal|Staff|Chief)\s+(?:Engineer|Developer|Scientist|Architect)\b',
            r'\b(?:Software|Data|Machine Learning|AI)\s+Engineer\b',
            r'\b(?:Research|Teaching)\s+(?:Fellow|Associate|Assistant)\b',
            r'\b(?:CTO|CEO|VP|Director)\b',
            r'\b(?:Google|Microsoft|Amazon|Meta|Apple|IBM|Oracle)\b',
            r'\b(?:MIT|Stanford|Harvard|Berkeley|Cambridge|Oxford)\b',
        ]
        
        # Editorial standards indicators
        self._editorial_indicators = {
            'peer-reviewed', 'editorial board', 'reviewed by',
            'fact-checked', 'editorial standards', 'editorial policy',
            'submission guidelines', 'review process'
        }
    
    def evaluate_author_credentials(self, author: str, source: str) -> float:
        """
        Evaluate author credentials based on name and source.
        
        Args:
            author: Author name or identifier
            source: Source domain/hostname
            
        Returns:
            Credential score between 0.0 and 1.0
        """
        if not author:
            # No author information, rely on source reputation
            return self.get_source_reputation(source) * 0.5
        
        # Start with base score
        score = 0.5
        
        # Check for professional titles or affiliations in author name
        author_lower = author.lower()
        
        # PhD or doctorate
        if any(indicator in author_lower for indicator in ['phd', 'ph.d', 'dr.', 'doctor', 'professor']):
            score += 0.3
        
        # Senior/lead positions
        if any(indicator in author_lower for indicator in ['senior', 'lead', 'principal', 'chief', 'staff']):
            score += 0.2
        
        # Academic institutions
        if any(inst in author_lower for inst in ['mit', 'stanford', 'harvard', 'berkeley', 'cambridge', 'oxford']):
            score += 0.2
        
        # Major tech companies
        if any(company in author_lower for company in ['google', 'microsoft', 'amazon', 'meta', 'apple', 'ibm']):
            score += 0.15
        
        # Boost score based on source reputation
        source_reputation = self.get_source_reputation(source)
        score = score * 0.7 + source_reputation * 0.3
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def identify_professional_affiliation(self, author_bio: str) -> Optional[str]:
        """
        Identify professional affiliation from author bio text.
        
        Args:
            author_bio: Author biography or description text
            
        Returns:
            Professional affiliation string if found, None otherwise
        """
        if not author_bio:
            return None
        
        # Check each professional indicator pattern
        for pattern in self._professional_indicators:
            match = re.search(pattern, author_bio, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def evaluate_editorial_standards(self, source: str) -> bool:
        """
        Evaluate whether a source has editorial standards.
        
        Args:
            source: Source domain/hostname
            
        Returns:
            True if source has known editorial standards, False otherwise
        """
        # Academic and research sources have editorial standards
        academic_domains = [
            'arxiv.org', 'scholar.google.com', 'researchgate.net',
            'ieee.org', 'acm.org', 'springer.com', 'sciencedirect.com',
            'nature.com', 'science.org'
        ]
        
        # Educational institutions have editorial standards
        edu_tlds = ['.edu', '.ac.uk', '.ac.in', '.edu.au']
        
        # Check if source is in academic domains
        source_lower = source.lower()
        if any(domain in source_lower for domain in academic_domains):
            return True
        
        # Check if source is educational institution
        if any(tld in source_lower for tld in edu_tlds):
            return True
        
        # High-reputation sources in whitelist (>= 0.85) are assumed to have standards
        if source_lower in self._source_whitelist:
            if self._source_whitelist[source_lower] >= 0.85:
                return True
        
        return False
    
    def get_source_reputation(self, source: str) -> float:
        """
        Get reputation score for a content source.
        
        Args:
            source: Source domain/hostname
            
        Returns:
            Reputation score between 0.0 and 1.0
        """
        source_lower = source.lower()
        
        # Check exact match in whitelist
        if source_lower in self._source_whitelist:
            return self._source_whitelist[source_lower]
        
        # Check for partial matches (e.g., subdomain.medium.com matches medium.com)
        for whitelisted_source, reputation in self._source_whitelist.items():
            if whitelisted_source in source_lower:
                return reputation
        
        # Educational institutions get high default reputation
        edu_tlds = ['.edu', '.ac.uk', '.ac.in', '.edu.au']
        if any(tld in source_lower for tld in edu_tlds):
            return 0.85
        
        # Government sources get moderate-high reputation
        gov_tlds = ['.gov', '.gov.uk', '.gov.au']
        if any(tld in source_lower for tld in gov_tlds):
            return 0.80
        
        # Default reputation for unknown sources
        return 0.5
