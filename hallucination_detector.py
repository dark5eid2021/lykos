import re
import requests
import json
from typing import List, Dict, Any
import logging
from datetime import datetime

class HallucinationDetector:
    def __init__(self, confidence_threshold=0.7, fact_check_api_key=None):
        self.confidence_threshold = confidence_threshold
        self.fact_check_api_key = fact_check_api_key
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hallucination_alerts.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_confidence_patterns(self, text: str) -> Dict[str, Any]:
        """Detect low-confidence language patterns"""
        low_confidence_patterns = [
            r'\b(i think|i believe|maybe|perhaps|possibly|likely|probably)\b',
            r'\b(not sure|uncertain|unclear|vague)\b',
            r'\b(might be|could be|seems like|appears to)\b',
            r'\b(approximately|roughly|around|about)\b(?=\s+\d+)',
        ]
        
        hedge_words = [
            'allegedly', 'supposedly', 'reportedly', 'apparently',
            'seemingly', 'presumably', 'ostensibly'
        ]
        
        confidence_score = 1.0
        flags = []
        
        text_lower = text.lower()
        
        # Check for hedge patterns
        for pattern in low_confidence_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                confidence_score -= len(matches) * 0.1
                flags.append(f"Uncertainty pattern: {matches}")
        
        # Check for hedge words
        for word in hedge_words:
            if word in text_lower:
                confidence_score -= 0.05
                flags.append(f"Hedge word detected: {word}")
        
        return {
            'confidence_score': max(0, confidence_score),
            'flags': flags,
            'is_suspicious': confidence_score < self.confidence_threshold
        }
    
    def check_factual_consistency(self, text: str) -> Dict[str, Any]:
        """Check for internal contradictions and impossible facts"""
        flags = []
        
        # Check for contradictory statements
        contradiction_patterns = [
            (r'always', r'never'),
            (r'all', r'none'),
            (r'everyone', r'no one'),
            (r'impossible', r'possible'),
        ]
        
        for pos_pattern, neg_pattern in contradiction_patterns:
            if re.search(pos_pattern, text, re.IGNORECASE) and re.search(neg_pattern, text, re.IGNORECASE):
                flags.append(f"Potential contradiction: {pos_pattern} vs {neg_pattern}")
        
        # Check for impossible dates/numbers
        current_year = datetime.now().year
        future_years = re.findall(r'\b(20\d{2})\b', text)
        for year in future_years:
            if int(year) > current_year + 1:
                flags.append(f"Suspicious future date: {year}")
        
        # Check for unrealistic numbers
        large_numbers = re.findall(r'\b(\d{10,})\b', text)
        if large_numbers:
            flags.append(f"Unusually large numbers: {large_numbers}")
        
        return {
            'consistency_flags': flags,
            'is_suspicious': len(flags) > 0
        }
    
    def check_source_claims(self, text: str) -> Dict[str, Any]:
        """Detect unsupported source claims"""
        flags = []
        
        # Look for specific claims without sources
        claim_patterns = [
            r'according to (studies|research|experts)',
            r'scientists have (found|discovered|proven)',
            r'data shows that',
            r'statistics indicate',
            r'research suggests'
        ]
        
        for pattern in claim_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(f"Unsourced claim pattern: {pattern}")
        
        # Look for specific but unverifiable claims
        specific_patterns = [
            r'\b\d+%\b.*?(of people|of users|of cases)',
            r'in \d{4}, [A-Z].*?(discovered|invented|created)',
            r'the (first|last|only) person to'
        ]
        
        for pattern in specific_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                flags.append(f"Specific unverified claim: {matches}")
        
        return {
            'source_flags': flags,
            'is_suspicious': len(flags) > 2
        }
    
    def external_fact_check(self, text: str) -> Dict[str, Any]:
        """Use external APIs to fact-check claims (placeholder)"""
        # This would integrate with fact-checking APIs like:
        # - Google Fact Check Tools API
        # - ClaimBuster API
        # - Custom knowledge base
        
        if not self.fact_check_api_key:
            return {'external_check': 'API key not provided', 'is_suspicious': False}
        
        # Placeholder for actual API integration
        return {
            'external_check': 'Not implemented - would check against fact-checking APIs',
            'is_suspicious': False
        }
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Main analysis function"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'confidence_analysis': self.check_confidence_patterns(text),
            'consistency_analysis': self.check_factual_consistency(text),
            'source_analysis': self.check_source_claims(text),
            'external_analysis': self.external_fact_check(text)
        }
        
        # Determine overall suspicion level
        suspicion_factors = [
            results['confidence_analysis']['is_suspicious'],
            results['consistency_analysis']['is_suspicious'],
            results['source_analysis']['is_suspicious'],
            results['external_analysis']['is_suspicious']
        ]
        
        results['overall_suspicious'] = sum(suspicion_factors) >= 2
        results['suspicion_score'] = sum(suspicion_factors) / len(suspicion_factors)
        
        return results
    
    def alert_if_suspicious(self, text: str, context: str = ""):
        """Analyze text and create alert if suspicious"""
        analysis = self.analyze_text(text)
        
        if analysis['overall_suspicious']:
            alert_message = f"""
🚨 POTENTIAL HALLUCINATION DETECTED 🚨
Context: {context}
Timestamp: {analysis['timestamp']}
Suspicion Score: {analysis['suspicion_score']:.2f}

Text: {text[:200]}{'...' if len(text) > 200 else ''}

Issues Found:
"""
            
            if analysis['confidence_analysis']['flags']:
                alert_message += f"- Confidence Issues: {analysis['confidence_analysis']['flags']}\n"
            
            if analysis['consistency_analysis']['consistency_flags']:
                alert_message += f"- Consistency Issues: {analysis['consistency_analysis']['consistency_flags']}\n"
            
            if analysis['source_analysis']['source_flags']:
                alert_message += f"- Source Issues: {analysis['source_analysis']['source_flags']}\n"
            
            self.logger.warning(alert_message)
            
            # You could also send email, Slack notification, etc.
            self.send_notification(alert_message)
            
            return True
        
        return False
    
    def send_notification(self, message: str):
        """Send notification (customize based on your needs)"""
        # Example: Send to Slack webhook
        # webhook_url = "YOUR_SLACK_WEBHOOK_URL"
        # requests.post(webhook_url, json={"text": message})
        
        # Example: Send email
        # send_email("alert@yourcompany.com", "Hallucination Alert", message)
        
        print("ALERT SENT:", message)

# Example usage
if __name__ == "__main__":
    detector = HallucinationDetector(confidence_threshold=0.6)
    
    # Test cases
    test_texts = [
        "The Eiffel Tower was built in 1889 and is 324 meters tall.",  # Factual
        "I think the Eiffel Tower might be around 500 meters tall, but I'm not entirely sure.",  # Low confidence
        "The Eiffel Tower was built in 2025 and is impossible to climb.",  # Contradictory/impossible
        "According to recent studies, 97% of people believe the Eiffel Tower is made of cheese.",  # Unsourced claim
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n--- Test {i+1} ---")
        detector.alert_if_suspicious(text, f"Test case {i+1}")