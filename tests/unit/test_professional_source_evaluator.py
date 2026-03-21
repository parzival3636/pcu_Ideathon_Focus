"""Unit tests for ProfessionalSourceEvaluator class"""

import pytest
from src.filtering.professional_source_evaluator import ProfessionalSourceEvaluator


@pytest.fixture
def evaluator():
    """Create ProfessionalSourceEvaluator instance"""
    return ProfessionalSourceEvaluator()


class TestInit:
    """Test ProfessionalSourceEvaluator initialization"""
    
    def test_init_creates_whitelist(self, evaluator):
        """Test that initialization creates source whitelist"""
        assert hasattr(evaluator, '_source_whitelist')
        assert len(evaluator._source_whitelist) > 0
        assert 'arxiv.org' in evaluator._source_whitelist
        assert 'medium.com' in evaluator._source_whitelist
    
    def test_init_creates_professional_indicators(self, evaluator):
        """Test that initialization creates professional indicators"""
        assert hasattr(evaluator, '_professional_indicators')
        assert len(evaluator._professional_indicators) > 0
    
    def test_init_creates_editorial_indicators(self, evaluator):
        """Test that initialization creates editorial indicators"""
        assert hasattr(evaluator, '_editorial_indicators')
        assert len(evaluator._editorial_indicators) > 0


class TestEvaluateAuthorCredentials:
    """Test author credential evaluation"""
    
    def test_no_author_returns_half_source_reputation(self, evaluator):
        """Test that missing author returns half of source reputation"""
        score = evaluator.evaluate_author_credentials("", "arxiv.org")
        expected = evaluator.get_source_reputation("arxiv.org") * 0.5
        assert score == pytest.approx(expected, rel=0.01)
    
    def test_phd_author_gets_higher_score(self, evaluator):
        """Test that PhD authors get higher credential scores"""
        score_phd = evaluator.evaluate_author_credentials("Dr. John Smith, PhD", "medium.com")
        score_regular = evaluator.evaluate_author_credentials("John Smith", "medium.com")
        assert score_phd > score_regular
    
    def test_professor_gets_higher_score(self, evaluator):
        """Test that professors get higher credential scores"""
        score = evaluator.evaluate_author_credentials("Professor Jane Doe", "medium.com")
        assert score > 0.6
    
    def test_senior_engineer_gets_boost(self, evaluator):
        """Test that senior positions get credential boost"""
        score_senior = evaluator.evaluate_author_credentials("Senior Software Engineer", "dev.to")
        score_regular = evaluator.evaluate_author_credentials("Software Engineer", "dev.to")
        assert score_senior > score_regular
    
    def test_mit_affiliation_gets_boost(self, evaluator):
        """Test that MIT affiliation increases score"""
        score = evaluator.evaluate_author_credentials("John Smith, MIT", "medium.com")
        assert score > 0.6
    
    def test_google_affiliation_gets_boost(self, evaluator):
        """Test that Google affiliation increases score"""
        score = evaluator.evaluate_author_credentials("Jane Doe, Google", "dev.to")
        assert score > 0.6
    
    def test_score_capped_at_one(self, evaluator):
        """Test that credential score is capped at 1.0"""
        score = evaluator.evaluate_author_credentials(
            "Dr. Professor John Smith PhD, MIT, Google, Senior Principal Chief Architect",
            "arxiv.org"
        )
        assert score <= 1.0
    
    def test_source_reputation_influences_score(self, evaluator):
        """Test that source reputation influences credential score"""
        score_high_rep = evaluator.evaluate_author_credentials("John Smith", "arxiv.org")
        score_low_rep = evaluator.evaluate_author_credentials("John Smith", "unknown-blog.com")
        assert score_high_rep > score_low_rep


class TestIdentifyProfessionalAffiliation:
    """Test professional affiliation identification"""
    
    def test_no_bio_returns_none(self, evaluator):
        """Test that empty bio returns None"""
        result = evaluator.identify_professional_affiliation("")
        assert result is None
    
    def test_identifies_phd(self, evaluator):
        """Test identification of PhD in bio"""
        bio = "John Smith is a PhD researcher at MIT specializing in machine learning."
        result = evaluator.identify_professional_affiliation(bio)
        assert result is not None
        assert 'PhD' in result or 'Ph.D' in result
    
    def test_identifies_senior_engineer(self, evaluator):
        """Test identification of senior engineer title"""
        bio = "Jane is a Senior Software Engineer with 10 years of experience."
        result = evaluator.identify_professional_affiliation(bio)
        assert result is not None
        assert 'Senior' in result
    
    def test_identifies_professor(self, evaluator):
        """Test identification of professor title"""
        bio = "Dr. Smith is a Professor of Computer Science at Stanford University."
        result = evaluator.identify_professional_affiliation(bio)
        assert result is not None
    
    def test_identifies_company_affiliation(self, evaluator):
        """Test identification of major tech company"""
        bio = "Software engineer at Google working on cloud infrastructure."
        result = evaluator.identify_professional_affiliation(bio)
        assert result is not None
        assert 'Google' in result
    
    def test_identifies_university_affiliation(self, evaluator):
        """Test identification of university affiliation"""
        bio = "Research fellow at MIT working on AI safety."
        result = evaluator.identify_professional_affiliation(bio)
        assert result is not None
    
    def test_no_affiliation_returns_none(self, evaluator):
        """Test that bio without professional indicators returns None"""
        bio = "I like to write about technology and share my thoughts."
        result = evaluator.identify_professional_affiliation(bio)
        assert result is None


class TestEvaluateEditorialStandards:
    """Test editorial standards evaluation"""
    
    def test_arxiv_has_editorial_standards(self, evaluator):
        """Test that arXiv is recognized as having editorial standards"""
        result = evaluator.evaluate_editorial_standards("arxiv.org")
        assert result is True
    
    def test_ieee_has_editorial_standards(self, evaluator):
        """Test that IEEE is recognized as having editorial standards"""
        result = evaluator.evaluate_editorial_standards("ieee.org")
        assert result is True
    
    def test_edu_domain_has_editorial_standards(self, evaluator):
        """Test that .edu domains have editorial standards"""
        result = evaluator.evaluate_editorial_standards("cs.stanford.edu")
        assert result is True
    
    def test_ac_uk_domain_has_editorial_standards(self, evaluator):
        """Test that .ac.uk domains have editorial standards"""
        result = evaluator.evaluate_editorial_standards("ox.ac.uk")
        assert result is True
    
    def test_high_reputation_source_has_standards(self, evaluator):
        """Test that high reputation sources (>=0.85) have editorial standards"""
        result = evaluator.evaluate_editorial_standards("nature.com")
        assert result is True
    
    def test_medium_reputation_source_no_standards(self, evaluator):
        """Test that medium reputation sources don't automatically have standards"""
        result = evaluator.evaluate_editorial_standards("medium.com")
        assert result is False
    
    def test_unknown_source_no_standards(self, evaluator):
        """Test that unknown sources don't have editorial standards"""
        result = evaluator.evaluate_editorial_standards("random-blog.com")
        assert result is False


class TestGetSourceReputation:
    """Test source reputation scoring"""
    
    def test_arxiv_high_reputation(self, evaluator):
        """Test that arXiv has high reputation score"""
        score = evaluator.get_source_reputation("arxiv.org")
        assert score >= 0.90
    
    def test_medium_moderate_reputation(self, evaluator):
        """Test that Medium has moderate reputation score"""
        score = evaluator.get_source_reputation("medium.com")
        assert 0.70 <= score <= 0.80
    
    def test_subdomain_matches_parent(self, evaluator):
        """Test that subdomains match parent domain reputation"""
        score_parent = evaluator.get_source_reputation("medium.com")
        score_subdomain = evaluator.get_source_reputation("towardsdatascience.medium.com")
        # Should match either medium.com or towardsdatascience.com
        assert score_subdomain >= 0.70
    
    def test_edu_domain_high_reputation(self, evaluator):
        """Test that .edu domains get high default reputation"""
        score = evaluator.get_source_reputation("cs.unknown-university.edu")
        assert score == 0.85
    
    def test_gov_domain_high_reputation(self, evaluator):
        """Test that .gov domains get high reputation"""
        score = evaluator.get_source_reputation("research.gov")
        assert score == 0.80
    
    def test_unknown_source_default_reputation(self, evaluator):
        """Test that unknown sources get default reputation"""
        score = evaluator.get_source_reputation("random-blog.com")
        assert score == 0.5
    
    def test_case_insensitive_matching(self, evaluator):
        """Test that source matching is case insensitive"""
        score_lower = evaluator.get_source_reputation("arxiv.org")
        score_upper = evaluator.get_source_reputation("ARXIV.ORG")
        score_mixed = evaluator.get_source_reputation("ArXiv.Org")
        assert score_lower == score_upper == score_mixed


class TestRequirements:
    """Test that implementation meets specific requirements"""
    
    def test_requirement_9_1_author_credentials(self, evaluator):
        """Requirement 9.1: Identify author credentials and professional affiliations"""
        # Test with professional author
        score = evaluator.evaluate_author_credentials("Dr. Jane Smith, PhD, MIT", "medium.com")
        assert score > 0.5
        
        # Test affiliation identification
        bio = "Dr. Smith is a Senior Research Scientist at Google Brain."
        affiliation = evaluator.identify_professional_affiliation(bio)
        assert affiliation is not None
    
    def test_requirement_9_2_professional_priority(self, evaluator):
        """Requirement 9.2: Higher priority for verified industry professionals"""
        score_professional = evaluator.evaluate_author_credentials(
            "Senior Engineer at Google", "dev.to"
        )
        score_regular = evaluator.evaluate_author_credentials(
            "John Doe", "dev.to"
        )
        assert score_professional > score_regular
    
    def test_requirement_9_3_editorial_standards(self, evaluator):
        """Requirement 9.3: Identify sources with editorial standards"""
        # Academic sources should have editorial standards
        assert evaluator.evaluate_editorial_standards("arxiv.org") is True
        assert evaluator.evaluate_editorial_standards("ieee.org") is True
        
        # Random blogs should not
        assert evaluator.evaluate_editorial_standards("random-blog.com") is False
    
    def test_requirement_9_4_fallback_to_reputation(self, evaluator):
        """Requirement 9.4: Fall back to source reputation when credentials unavailable"""
        # No author provided
        score = evaluator.evaluate_author_credentials("", "arxiv.org")
        
        # Should use source reputation
        source_reputation = evaluator.get_source_reputation("arxiv.org")
        assert score == pytest.approx(source_reputation * 0.5, rel=0.01)
