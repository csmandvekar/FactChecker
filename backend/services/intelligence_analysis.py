import logging
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.announcement import Announcement
from models.company_financial import CompanyFinancial

logger = logging.getLogger(__name__)


class IntelligenceAnalysisService:
    def __init__(self):
        self.zero_shot_classifier = None
        self.sentiment_analyzer = None
        self._load_models()
    
    def _load_models(self):
        """Load Hugging Face models for analysis"""
        try:
            from transformers import pipeline
            
            # Load zero-shot classification model for red flag detection
            self.zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # Use CPU for now
            )
            
            # Load sentiment analysis model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1  # Use CPU for now
            )
            
            logger.info("Hugging Face models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            # Fallback to simple rule-based analysis
            self.zero_shot_classifier = None
            self.sentiment_analyzer = None
    
    async def analyze_announcement(self, announcement: Announcement, db: Session):
        """Perform comprehensive analysis on an announcement"""
        try:
            logger.info(f"Starting analysis for announcement {announcement.id}")
            
            # Update status to analyzing
            announcement.status = 'analyzing'
            db.commit()
            
            analysis_results = {}
            
            # 1. Red flag analysis
            red_flags = await self._analyze_red_flags(announcement.full_text or "")
            analysis_results['red_flags'] = red_flags
            
            # 2. Sentiment analysis
            sentiment = await self._analyze_sentiment(announcement.full_text or "")
            analysis_results['sentiment'] = sentiment
            
            # 3. Historical anomaly check
            anomaly = await self._check_historical_anomaly(announcement, db)
            analysis_results['anomaly_detected'] = anomaly
            
            # 4. Calculate credibility score
            credibility_score = self._calculate_credibility_score(analysis_results)
            
            # 5. Generate analysis summary
            analysis_summary = self._generate_analysis_summary(analysis_results, credibility_score)
            
            # Update announcement with results
            announcement.credibility_score = credibility_score
            announcement.analysis_summary = analysis_summary
            announcement.status = 'analyzed'
            announcement.updated_at = datetime.now()
            
            db.commit()
            
            logger.info(f"Analysis completed for announcement {announcement.id}. Score: {credibility_score}")
            
        except Exception as e:
            logger.error(f"Error analyzing announcement {announcement.id}: {e}")
            announcement.status = 'failed'
            db.commit()
            raise
    
    async def _analyze_red_flags(self, text: str) -> List[str]:
        """Analyze text for red flags using zero-shot classification"""
        if not text or not self.zero_shot_classifier:
            return self._fallback_red_flag_analysis(text)
        
        try:
            # Define red flag categories
            red_flag_categories = [
                "promotional hype",
                "unrealistic projections",
                "vague language",
                "conflicting information",
                "suspicious timing",
                "lack of details",
                "overly optimistic claims"
            ]
            
            # Use zero-shot classification
            result = self.zero_shot_classifier(text, red_flag_categories)
            
            # Extract high-confidence red flags
            red_flags = []
            for i, score in enumerate(result['scores']):
                if score > 0.7:  # High confidence threshold
                    red_flags.append(result['labels'][i])
            
            return red_flags
            
        except Exception as e:
            logger.error(f"Error in red flag analysis: {e}")
            return self._fallback_red_flag_analysis(text)
    
    def _fallback_red_flag_analysis(self, text: str) -> List[str]:
        """Fallback rule-based red flag analysis"""
        red_flags = []
        text_lower = text.lower()
        
        # Promotional language patterns
        promotional_patterns = [
            r'\b(guaranteed|guarantee|promise|assure|certain|definite)\b',
            r'\b(revolutionary|breakthrough|game-changing|unprecedented)\b',
            r'\b(limited time|act now|don\'t miss|exclusive)\b'
        ]
        
        for pattern in promotional_patterns:
            if re.search(pattern, text_lower):
                red_flags.append("promotional_hype")
                break
        
        # Vague language patterns
        vague_patterns = [
            r'\b(significant|substantial|considerable|major)\s+(increase|growth|improvement)\b',
            r'\b(we expect|anticipated|projected|forecasted)\b',
            r'\b(approximately|around|about|roughly)\b'
        ]
        
        for pattern in vague_patterns:
            if re.search(pattern, text_lower):
                red_flags.append("vague_language")
                break
        
        return red_flags
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of the text"""
        if not text or not self.sentiment_analyzer:
            return {"label": "neutral", "score": 0.5}
        
        try:
            result = self.sentiment_analyzer(text[:512])  # Limit text length
            return {
                "label": result[0]['label'],
                "score": result[0]['score']
            }
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {"label": "neutral", "score": 0.5}
    
    async def _check_historical_anomaly(self, announcement: Announcement, db: Session) -> Dict[str, Any]:
        """Check for historical anomalies in financial claims"""
        try:
            # Extract numerical claims from text
            numerical_claims = self._extract_numerical_claims(announcement.full_text or "")
            
            if not numerical_claims:
                return {"anomaly_detected": False, "details": "No numerical claims found"}
            
            # Get company financial data
            company_financial = db.query(CompanyFinancial).filter(
                CompanyFinancial.company_symbol == announcement.company_symbol
            ).first()
            
            if not company_financial:
                return {"anomaly_detected": False, "details": "No historical data available"}
            
            # Check for anomalies
            anomalies = []
            for claim in numerical_claims:
                if claim['type'] == 'revenue' and company_financial.last_quarter_revenue_cr:
                    # Check if claimed revenue is significantly different from historical
                    historical_revenue = company_financial.last_quarter_revenue_cr
                    claimed_revenue = claim['value']
                    
                    # Calculate percentage difference
                    if historical_revenue > 0:
                        diff_percentage = abs(claimed_revenue - historical_revenue) / historical_revenue * 100
                        if diff_percentage > 50:  # 50% threshold
                            anomalies.append({
                                "type": "revenue_anomaly",
                                "claimed": claimed_revenue,
                                "historical": historical_revenue,
                                "difference_percentage": diff_percentage
                            })
            
            return {
                "anomaly_detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "details": f"Found {len(anomalies)} anomalies" if anomalies else "No anomalies detected"
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly check: {e}")
            return {"anomaly_detected": False, "details": f"Error: {str(e)}"}
    
    def _extract_numerical_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract numerical financial claims from text"""
        claims = []
        
        # Revenue patterns (in crores)
        revenue_patterns = [
            r'revenue\s+of\s+₹?\s*(\d+(?:\.\d+)?)\s*crore',
            r'₹?\s*(\d+(?:\.\d+)?)\s*crore\s+revenue',
            r'quarterly\s+revenue\s+₹?\s*(\d+(?:\.\d+)?)\s*crore'
        ]
        
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claims.append({
                    "type": "revenue",
                    "value": float(match.group(1)),
                    "context": match.group(0)
                })
        
        # Profit patterns
        profit_patterns = [
            r'profit\s+of\s+₹?\s*(\d+(?:\.\d+)?)\s*crore',
            r'₹?\s*(\d+(?:\.\d+)?)\s*crore\s+profit',
            r'net\s+profit\s+₹?\s*(\d+(?:\.\d+)?)\s*crore'
        ]
        
        for pattern in profit_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claims.append({
                    "type": "profit",
                    "value": float(match.group(1)),
                    "context": match.group(0)
                })
        
        return claims
    
    def _calculate_credibility_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate credibility score based on analysis results"""
        base_score = 10.0  # Start with perfect score
        
        # Red flags penalty
        red_flags = analysis_results.get('red_flags', [])
        red_flag_penalty = len(red_flags) * 1.5
        base_score -= red_flag_penalty
        
        # Sentiment penalty
        sentiment = analysis_results.get('sentiment', {})
        sentiment_score = sentiment.get('score', 0.5)
        if sentiment['label'] == 'NEGATIVE':
            base_score -= 2.0
        elif sentiment['label'] == 'POSITIVE' and sentiment_score > 0.8:
            base_score -= 1.0  # Overly positive might be suspicious
        
        # Anomaly penalty
        anomaly = analysis_results.get('anomaly_detected', {})
        if anomaly.get('anomaly_detected', False):
            base_score -= 3.0
        
        # Ensure score is between 0 and 10
        return max(0.0, min(10.0, base_score))
    
    def _generate_analysis_summary(self, analysis_results: Dict[str, Any], credibility_score: float) -> Dict[str, Any]:
        """Generate human-readable analysis summary"""
        summary = {
            "credibility_score": credibility_score,
            "red_flags": analysis_results.get('red_flags', []),
            "sentiment": analysis_results.get('sentiment', {}),
            "anomaly_detected": analysis_results.get('anomaly_detected', {}).get('anomaly_detected', False),
            "analysis_timestamp": datetime.now().isoformat(),
            "recommendations": []
        }
        
        # Generate recommendations based on analysis
        if summary['red_flags']:
            summary['recommendations'].append("Review flagged content for promotional language")
        
        if summary['anomaly_detected']:
            summary['recommendations'].append("Verify financial claims against historical data")
        
        if credibility_score < 5.0:
            summary['recommendations'].append("High risk: Consider additional verification")
        elif credibility_score < 7.0:
            summary['recommendations'].append("Medium risk: Review flagged issues")
        else:
            summary['recommendations'].append("Low risk: Content appears credible")
        
        return summary
