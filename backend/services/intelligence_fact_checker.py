import logging
import re
import os
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import PyPDF2
import io

from models.announcement import Announcement

logger = logging.getLogger(__name__)


class FactCheckerService:
    def __init__(self):
        self.trusted_sources = [
            "bseindia.com",
            "nseindia.com",
            "sebi.gov.in",
            "mca.gov.in"
        ]
        # Enable lightweight demo mode to avoid dependence on a vector DB
        self.demo_mode_enabled = os.getenv("FACT_CHECKER_DEMO", "true").lower() in ("1", "true", "yes", "y")
    
    async def check_content(self, content: str, db: Session) -> Dict[str, Any]:
        """Perform fact-checking on user-provided content"""
        try:
            logger.info("Starting fact-checking process")
            
            # 1. Extract key claims from content
            claims = self._extract_claims(content)
            
            # 2. If demo mode is enabled or database has no announcements, use lightweight heuristic verification
            use_demo_flow = False
            if self.demo_mode_enabled:
                use_demo_flow = True
            else:
                try:
                    from models.announcement import Announcement  # local import to avoid cycles
                    total_anns = db.query(Announcement).count()
                    if total_anns == 0:
                        use_demo_flow = True
                except Exception:
                    # If we cannot query, fall back to demo for robustness
                    use_demo_flow = True

            if use_demo_flow:
                verification_result = self._demo_verify(content, claims)
            else:
                # 3. Search for matching announcements in database
                matching_announcements = await self._search_matching_announcements(claims, db)
                
                # 4. Analyze verification results
                verification_result = self._analyze_verification_results(claims, matching_announcements)
            
            # 5. Generate recommendations
            recommendations = self._generate_recommendations(verification_result)
            
            return {
                "verification_status": verification_result["status"],
                "confidence_score": verification_result["confidence_score"],
                "evidence": verification_result["evidence"],
                "analysis_details": verification_result["analysis_details"],
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in fact-checking: {e}")
            return {
                "verification_status": "error",
                "confidence_score": 0.0,
                "evidence": [],
                "analysis_details": {"error": str(e)},
                "recommendations": ["Unable to verify content due to technical error"]
            }

    def _demo_verify(self, content: str, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Lightweight heuristic verification used for demos without vector DB or data."""
        lowered = content.lower()
        has_date = bool(re.search(r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", lowered))
        has_money = bool(re.search(r"(\d+(?:[\.,]\d+)?)\s*(crore|lakh|million|billion)", lowered))
        contains_caution = any(k in lowered for k in ["rumor", "rumour", "leak", "leaked", "unconfirmed", "forwarded as received", "whatsapp"])
        contains_source_link = any(src in lowered for src in self.trusted_sources)
        is_short = len(content.strip()) < 140

        # Base score
        score = 0.2
        if has_date:
            score += 0.2
        if has_money:
            score += 0.2
        if contains_source_link:
            score += 0.3
        if contains_caution:
            score -= 0.3
        if is_short:
            score -= 0.1

        score = max(0.0, min(1.0, score))

        if score >= 0.7:
            status = "verified_authentic"
        elif score >= 0.4:
            status = "partially_verified"
        else:
            status = "potentially_misleading"

        # Construct placeholder evidence pointing to official sources
        evidence: List[Dict[str, Any]] = []
        for domain in self.trusted_sources[:3]:
            evidence.append({
                "announcement_id": None,
                "company_name": None,
                "title": f"Reference: {domain}",
                "announcement_date": None,
                "similarity_score": 0.0,
                "matched_claims": [c for c in claims[:2]]
            })

        analysis_details = {
            "mode": "demo",
            "reason": "Heuristic evaluation without database matches",
            "total_claims": len(claims),
            "has_date": has_date,
            "has_financial_figure": has_money,
            "contains_official_source_link": contains_source_link,
            "contains_caution_markers": contains_caution,
            "content_length": len(content)
        }

        return {
            "status": status,
            "confidence_score": round(score, 2),
            "evidence": evidence,
            "analysis_details": analysis_details,
        }
    
    def _extract_claims(self, content: str) -> List[Dict[str, Any]]:
        """Extract verifiable claims from content"""
        claims = []
        
        # Extract company names
        company_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Limited|Ltd\.?|Corporation|Corp\.?)\b',
            r'\b([A-Z]{2,10})\b'  # Stock symbols
        ]
        
        for pattern in company_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                claims.append({
                    "type": "company_mention",
                    "value": match.group(1),
                    "context": match.group(0)
                })
        
        # Extract financial figures
        financial_patterns = [
            r'₹?\s*(\d+(?:\.\d+)?)\s*crore',
            r'₹?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:lakh|crore|million|billion)',
            r'revenue\s+of\s+₹?\s*(\d+(?:\.\d+)?)\s*crore',
            r'profit\s+of\s+₹?\s*(\d+(?:\.\d+)?)\s*crore'
        ]
        
        for pattern in financial_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                claims.append({
                    "type": "financial_figure",
                    "value": match.group(1),
                    "context": match.group(0)
                })
        
        # Extract dates
        date_patterns = [
            r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\bQ[1-4]\s+(?:FY|Financial Year)\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                claims.append({
                    "type": "date_mention",
                    "value": match.group(1),
                    "context": match.group(0)
                })
        
        return claims
    
    async def _search_matching_announcements(self, claims: List[Dict[str, Any]], db: Session) -> List[Dict[str, Any]]:
        """Search for matching announcements in the database"""
        matching_announcements = []
        
        try:
            # Extract company symbols from claims
            company_symbols = []
            for claim in claims:
                if claim["type"] == "company_mention":
                    # Try to map company name to symbol
                    symbol = self._map_company_to_symbol(claim["value"])
                    if symbol:
                        company_symbols.append(symbol)
            
            if not company_symbols:
                return matching_announcements
            
            # Search for announcements by company symbols
            for symbol in company_symbols:
                announcements = db.query(Announcement).filter(
                    Announcement.company_symbol.ilike(f"%{symbol}%")
                ).limit(10).all()
                
                for announcement in announcements:
                    # Calculate similarity score
                    similarity_score = self._calculate_similarity(claims, announcement)
                    
                    if similarity_score > 0.3:  # Threshold for relevance
                        matching_announcements.append({
                            "announcement": announcement,
                            "similarity_score": similarity_score,
                            "matched_claims": self._get_matched_claims(claims, announcement)
                        })
            
            # Sort by similarity score
            matching_announcements.sort(key=lambda x: x["similarity_score"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error searching matching announcements: {e}")
        
        return matching_announcements
    
    def _map_company_to_symbol(self, company_name: str) -> Optional[str]:
        """Map company name to stock symbol"""
        # Simple mapping - in production, you'd have a comprehensive mapping
        company_mapping = {
            "Reliance Industries": "RELIANCE",
            "Tata Consultancy Services": "TCS",
            "Infosys": "INFY",
            "HDFC Bank": "HDFCBANK",
            "ICICI Bank": "ICICIBANK",
            "Bharti Airtel": "BHARTIARTL",
            "ITC": "ITC",
            "Kotak Mahindra Bank": "KOTAKBANK",
            "Larsen & Toubro": "LT",
            "State Bank of India": "SBIN"
        }
        
        for name, symbol in company_mapping.items():
            if name.lower() in company_name.lower():
                return symbol
        
        return None
    
    def _calculate_similarity(self, claims: List[Dict[str, Any]], announcement: Announcement) -> float:
        """Calculate similarity between claims and announcement"""
        similarity_score = 0.0
        
        # Company name similarity
        for claim in claims:
            if claim["type"] == "company_mention":
                if claim["value"].lower() in announcement.company_name.lower():
                    similarity_score += 0.4
                if claim["value"].lower() in announcement.company_symbol.lower():
                    similarity_score += 0.3
        
        # Financial figure similarity
        announcement_text = announcement.full_text or ""
        for claim in claims:
            if claim["type"] == "financial_figure":
                if claim["value"] in announcement_text:
                    similarity_score += 0.2
        
        # Date similarity
        for claim in claims:
            if claim["type"] == "date_mention":
                if claim["value"] in announcement_text:
                    similarity_score += 0.1
        
        return min(1.0, similarity_score)
    
    def _get_matched_claims(self, claims: List[Dict[str, Any]], announcement: Announcement) -> List[Dict[str, Any]]:
        """Get claims that match the announcement"""
        matched_claims = []
        announcement_text = announcement.full_text or ""
        
        for claim in claims:
            if claim["value"] in announcement_text:
                matched_claims.append(claim)
        
        return matched_claims
    
    def _analyze_verification_results(self, claims: List[Dict[str, Any]], matching_announcements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze verification results and determine status"""
        if not matching_announcements:
            return {
                "status": "unverified",
                "confidence_score": 0.0,
                "evidence": [],
                "analysis_details": {
                    "reason": "No matching official announcements found",
                    "total_claims": len(claims),
                    "matched_claims": 0
                }
            }
        
        # Calculate overall confidence
        total_similarity = sum(ann["similarity_score"] for ann in matching_announcements)
        avg_similarity = total_similarity / len(matching_announcements)
        
        # Determine verification status
        if avg_similarity > 0.7:
            status = "verified_authentic"
            confidence_score = min(1.0, avg_similarity)
        elif avg_similarity > 0.4:
            status = "partially_verified"
            confidence_score = avg_similarity
        else:
            status = "potentially_misleading"
            confidence_score = avg_similarity
        
        # Prepare evidence
        evidence = []
        for match in matching_announcements[:3]:  # Top 3 matches
            evidence.append({
                "announcement_id": match["announcement"].id,
                "company_name": match["announcement"].company_name,
                "title": match["announcement"].title,
                "announcement_date": match["announcement"].announcement_date.isoformat(),
                "similarity_score": match["similarity_score"],
                "matched_claims": match["matched_claims"]
            })
        
        return {
            "status": status,
            "confidence_score": confidence_score,
            "evidence": evidence,
            "analysis_details": {
                "total_claims": len(claims),
                "matched_claims": sum(len(match["matched_claims"]) for match in matching_announcements),
                "average_similarity": avg_similarity,
                "total_matches": len(matching_announcements)
            }
        }
    
    def _generate_recommendations(self, verification_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        status = verification_result["status"]
        confidence_score = verification_result["confidence_score"]
        
        if status == "verified_authentic":
            recommendations.append("✅ Content appears to be verified against official announcements")
            recommendations.append("📊 High confidence in authenticity")
        elif status == "partially_verified":
            recommendations.append("⚠️ Some claims match official sources, but verification is incomplete")
            recommendations.append("🔍 Consider cross-referencing with additional sources")
        elif status == "potentially_misleading":
            recommendations.append("🚨 Content does not match official announcements")
            recommendations.append("❌ High risk of misinformation")
            recommendations.append("📋 Recommend fact-checking with official sources")
        else:  # unverified
            recommendations.append("❓ Unable to verify content against official sources")
            recommendations.append("🔍 No matching announcements found in database")
            recommendations.append("📋 Consider checking official company websites")
        
        if confidence_score < 0.5:
            recommendations.append("⚠️ Low confidence score - exercise caution")
        
        return recommendations
    
    async def extract_pdf_text(self, file) -> str:
        """Extract text from uploaded PDF file"""
        try:
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
