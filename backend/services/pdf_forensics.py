import pikepdf
import subprocess
import json
import logging
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import re
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)

class PDFForensicsService:
    def __init__(self):
        self.suspicious_patterns = {
            "javascript": ["/JS", "/JavaScript", "/AcroForm"],
            "actions": ["/Launch", "/SubmitForm", "/ImportData", "/OpenAction", "/AA"],
            "embedded_files": ["/EmbeddedFile", "/FileAttachment"],
            "annotations": ["/RichMedia", "/3D", "/Movie"],
            "external_links": ["/URI", "/GoTo", "/GoToR"]
        }
        
        # Check if PDFiD is available
        self.pdfid_available = self._check_pdfid_availability()
        if not self.pdfid_available:
            logger.warning("PDFiD not found. PDF analysis will be limited. Install PDFiD for full security analysis.")
    
    def _check_pdfid_availability(self) -> bool:
        """Check if PDFiD binary is available in system PATH"""
        try:
            result = subprocess.run(
                ["pdfid", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    async def analyze_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive PDF forensic analysis
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = datetime.now()
        
        try:
            # Extract file path from storage path
            if file_path.startswith(("s3://", "minio://")):
                # For cloud storage, we need to download first
                from services.storage import storage_service
                file_content = storage_service.get_file(file_path)
                if not file_content:
                    raise Exception("Failed to retrieve file from storage")
                
                # Save to temporary file for analysis
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                    temp_file.write(file_content.read())
                    temp_file_path = temp_file.name
            else:
                temp_file_path = file_path
            
            # Run PDFiD analysis if available
            pdfid_results = self._run_pdfid_analysis(temp_file_path) if self.pdfid_available else {"error": "PDFiD not installed"}
            
            # Run pikepdf analysis
            pikepdf_results = self._run_pikepdf_analysis(temp_file_path)
            
            # Generate visual charts (improved chart types)
            charts_paths = self._generate_visual_charts(pdfid_results, pikepdf_results, file_path)
            
            # Combine and analyze results
            combined_analysis = self._combine_analysis_results(pdfid_results, pikepdf_results, charts_paths)
            
            # Determine verdict and confidence
            verdict, confidence = self._determine_verdict(combined_analysis)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Cleanup temporary file if created
            if file_path.startswith(("s3://", "minio://")) and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            return {
                "verdict": verdict,
                "confidence_score": confidence,
                "evidence": combined_analysis,
                "processing_time": processing_time,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"PDF analysis error: {e}")
            raise

    def _run_pdfid_analysis(self, file_path: str) -> Dict[str, Any]:
        """Run PDFiD analysis on the PDF file"""
        try:
            # Run PDFiD command with more detailed output
            result = subprocess.run(
                ["pdfid", "-f", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"PDFiD analysis failed: {result.stderr}")
                return {"error": f"PDFiD analysis failed: {result.stderr}"}
            
            # Parse PDFiD output
            return self._parse_pdfid_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            logger.error("PDFiD analysis timed out")
            return {"error": "PDFiD analysis timed out"}
        except FileNotFoundError:
            logger.error("PDFiD not found. Please install pdfid.")
            return {"error": "PDFiD not installed"}
        except Exception as e:
            logger.error(f"PDFiD analysis error: {e}")
            return {"error": str(e)}
    
    def _parse_pdfid_output(self, output: str) -> Dict[str, Any]:
        """Parse PDFiD command output with enhanced suspicious object detection"""
        results = {
            "objects": {},
            "suspicious_objects": [],
            "total_objects": 0,
            "security_flags": []
        }
        
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.startswith('obj '):
                # Parse object counts
                parts = line.split()
                if len(parts) >= 2:
                    obj_type = parts[1]
                    count = int(parts[0].split()[1]) if len(parts[0].split()) > 1 else 0
                    results["objects"][obj_type] = count
                    results["total_objects"] += count
                    
                    # Check for suspicious objects with enhanced detection
                    if self._is_suspicious_object(obj_type):
                        risk_level = self._get_risk_level(obj_type)
                        explanation = self._get_suspicious_explanation(obj_type)
                        results["suspicious_objects"].append({
                            "type": obj_type,
                            "count": count,
                            "risk_level": risk_level,
                            "explanation": explanation
                        })
                        
                        # Add security flags for high-risk objects
                        if risk_level == "high":
                            results["security_flags"].append(f"High-risk object detected: {obj_type} (count: {count})")
        
        return results
    
    def _get_suspicious_explanation(self, obj_type: str) -> str:
        """Provide clear explanations for why objects are suspicious"""
        explanations = {
            "/JS": "JavaScript can execute malicious code when PDF is opened",
            "/JavaScript": "JavaScript can execute malicious code when PDF is opened", 
            "/Launch": "Can launch external programs or applications",
            "/SubmitForm": "Can submit form data to external servers",
            "/ImportData": "Can import data from external sources",
            "/OpenAction": "Executes actions automatically when PDF opens",
            "/AA": "Additional actions that execute automatically",
            "/URI": "Can open external websites or URLs",
            "/GoTo": "Can navigate to external destinations",
            "/GoToR": "Can navigate to external destinations with remote go-to",
            "/AcroForm": "Interactive forms can contain malicious scripts",
            "/EmbeddedFile": "Can contain hidden executable files",
            "/FileAttachment": "Can contain hidden executable files",
            "/RichMedia": "Can contain multimedia content with scripts",
            "/3D": "3D content can contain embedded scripts",
            "/Movie": "Movie content can contain embedded scripts"
        }
        return explanations.get(obj_type, f"Unknown suspicious object type: {obj_type}")
    
    def _run_pikepdf_analysis(self, file_path: str) -> Dict[str, Any]:
        """Run pikepdf analysis on the PDF file"""
        try:
            with pikepdf.open(file_path) as pdf:
                results = {
                    "metadata": {},
                    "structure": {},
                    "anomalies": []
                }
                
                # Extract metadata
                if pdf.docinfo:
                    for key, value in pdf.docinfo.items():
                        results["metadata"][str(key)] = str(value)
                
                # Analyze document structure
                results["structure"] = self._analyze_pdf_structure(pdf)
                
                # Check for anomalies with enhanced detection
                results["anomalies"] = self._detect_anomalies(pdf, results["metadata"])
                
                return results
                
        except Exception as e:
            logger.error(f"pikepdf analysis error: {e}")
            return {"error": str(e)}
    
    def _analyze_pdf_structure(self, pdf) -> Dict[str, Any]:
        """Analyze PDF document structure with enhanced security checks"""
        structure = {
            "pages": len(pdf.pages),
            "version": str(pdf.pdf_version),
            "encryption": pdf.is_encrypted,
            "linearized": pdf.is_linearized,
            "object_count": len(pdf.objects),
            "trailer_keys": list(pdf.trailer.keys()) if pdf.trailer else []
        }
        
        # Check for suspicious structure elements
        suspicious_elements = []
        
        # Check for JavaScript
        if "/Names" in pdf.trailer:
            names = pdf.trailer["/Names"]
            if "/JavaScript" in names:
                suspicious_elements.append({
                    "element": "JavaScript found in document names",
                    "risk": "high",
                    "explanation": "JavaScript can execute malicious code automatically"
                })
        
        # Check for forms
        if "/AcroForm" in pdf.trailer:
            suspicious_elements.append({
                "element": "Interactive forms detected",
                "risk": "medium", 
                "explanation": "Forms can contain scripts and submit data to external sources"
            })
        
        # Check for annotations
        annotation_count = 0
        for page in pdf.pages:
            if "/Annots" in page:
                annotation_count += len(page["/Annots"])
        
        if annotation_count > 0:
            structure["annotation_count"] = annotation_count
            if annotation_count > 10:  # Threshold for suspicious
                suspicious_elements.append({
                    "element": f"High number of annotations: {annotation_count}",
                    "risk": "medium",
                    "explanation": "Excessive annotations may indicate document tampering"
                })
        
        structure["suspicious_elements"] = suspicious_elements
        return structure
    
    def _detect_anomalies(self, pdf, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """Detect anomalies in PDF metadata and structure with enhanced logic"""
        anomalies = []
        
        # Check creation vs modification time (CRITICAL FIX)
        if "/CreationDate" in metadata and "/ModDate" in metadata:
            try:
                creation_date = self._parse_pdf_date(metadata["/CreationDate"])
                mod_date = self._parse_pdf_date(metadata["/ModDate"])
                
                if creation_date and mod_date:
                    if mod_date < creation_date:
                        anomalies.append({
                            "type": "time_anomaly",
                            "description": "Modification date is before creation date",
                            "severity": "high",
                            "explanation": "This is logically impossible and indicates metadata tampering. The document timestamps have been forged.",
                            "technical_details": {
                                "creation_date": creation_date.isoformat(),
                                "modification_date": mod_date.isoformat(),
                                "time_difference_hours": (creation_date - mod_date).total_seconds() / 3600
                            }
                        })
                    elif (mod_date - creation_date).total_seconds() < 60:
                        anomalies.append({
                            "type": "time_suspicious",
                            "description": "Creation and modification times are very close",
                            "severity": "medium",
                            "explanation": "Document was created and immediately modified, which may indicate automated generation or tampering",
                            "technical_details": {
                                "creation_date": creation_date.isoformat(),
                                "modification_date": mod_date.isoformat(),
                                "time_difference_seconds": (mod_date - creation_date).total_seconds()
                            }
                        })
            except Exception as e:
                logger.warning(f"Date parsing error: {e}")
        
        # Check for missing producer/creator
        if "/Producer" not in metadata and "/Creator" not in metadata:
            anomalies.append({
                "type": "metadata_missing",
                "description": "Missing producer/creator information",
                "severity": "medium",
                "explanation": "Legitimate documents typically have producer/creator metadata. Missing data may indicate file tampering or creation with malicious tools."
            })
        
        # Check for suspicious producer names with enhanced detection
        producer = metadata.get("/Producer", "").lower()
        suspicious_producers = ["adobe", "acrobat", "pdf", "word", "excel", "libreoffice", "openoffice"]
        if producer and not any(sp in producer for sp in suspicious_producers):
            anomalies.append({
                "type": "suspicious_producer",
                "description": f"Unusual producer: {metadata.get('/Producer', 'Unknown')}",
                "severity": "medium",
                "explanation": f"This producer string '{metadata.get('/Producer')}' does not match known legitimate software. It may indicate file tampering, creation with a malicious tool, or use of obscure/outdated software.",
                "technical_details": {
                    "detected_producer": metadata.get('/Producer'),
                    "expected_producers": suspicious_producers
                }
            })
        
        return anomalies

    def _parse_pdf_date(self, date_str: str) -> datetime:
        """Parse PDF date string with enhanced error handling"""
        try:
            # Remove PDF date prefix if present
            if date_str.startswith("D:"):
                date_str = date_str[2:]
            
            # Parse various date formats
            formats = [
                "%Y%m%d%H%M%S",
                "%Y%m%d%H%M%S%z",
                "%Y%m%d%H%M%S'%z'",
                "%Y%m%d%H%M%S'%z'%Z"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"Date parsing failed for '{date_str}': {e}")
            return None
    
    def _is_suspicious_object(self, obj_type: str) -> bool:
        """Check if object type is suspicious with enhanced patterns"""
        for category, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if pattern.lower() in obj_type.lower():
                    return True
        return False
    
    def _get_risk_level(self, obj_type: str) -> str:
        """Get risk level for suspicious object with enhanced categorization"""
        high_risk = ["/JS", "/JavaScript", "/Launch", "/SubmitForm", "/OpenAction", "/AA", "/URI"]
        medium_risk = ["/AcroForm", "/EmbeddedFile", "/FileAttachment", "/ImportData", "/GoTo", "/GoToR"]
        
        if any(risk in obj_type for risk in high_risk):
            return "high"
        elif any(risk in obj_type for risk in medium_risk):
            return "medium"
        else:
            return "low"
    
    def _combine_analysis_results(self, pdfid_results: Dict, pikepdf_results: Dict, charts_paths: Dict[str, str] = None) -> Dict[str, Any]:
        """Combine results from both analysis methods with enhanced risk scoring"""
        combined = {
            "pdfid_analysis": pdfid_results,
            "pikepdf_analysis": pikepdf_results,
            "charts": charts_paths or {},
            "summary": {
                "total_suspicious_objects": len(pdfid_results.get("suspicious_objects", [])),
                "total_anomalies": len(pikepdf_results.get("anomalies", [])),
                "risk_indicators": [],
                "security_flags": pdfid_results.get("security_flags", []),
                "risk_explanation": ""
            }
        }
        
        # Calculate risk indicators with explanations
        risk_score = 0
        risk_details = []
        
        # PDFiD suspicious objects
        for obj in pdfid_results.get("suspicious_objects", []):
            if obj["risk_level"] == "high":
                risk_score += 3
                risk_details.append(f"High-risk object: {obj['type']} ({obj['count']}) - {obj['explanation']}")
            elif obj["risk_level"] == "medium":
                risk_score += 2
                risk_details.append(f"Medium-risk object: {obj['type']} ({obj['count']}) - {obj['explanation']}")
            else:
                risk_score += 1
                risk_details.append(f"Low-risk object: {obj['type']} ({obj['count']}) - {obj['explanation']}")
        
        # pikepdf anomalies
        for anomaly in pikepdf_results.get("anomalies", []):
            if anomaly["severity"] == "high":
                risk_score += 3
                risk_details.append(f"High-severity anomaly: {anomaly['description']} - {anomaly.get('explanation', 'No explanation provided')}")
            elif anomaly["severity"] == "medium":
                risk_score += 2
                risk_details.append(f"Medium-severity anomaly: {anomaly['description']} - {anomaly.get('explanation', 'No explanation provided')}")
            else:
                risk_score += 1
                risk_details.append(f"Low-severity anomaly: {anomaly['description']} - {anomaly.get('explanation', 'No explanation provided')}")
        
        # Suspicious structure elements
        for element in pikepdf_results.get("structure", {}).get("suspicious_elements", []):
            risk_score += 2
            risk_details.append(f"Structure issue: {element['element']} - {element['explanation']}")
        
        combined["summary"]["risk_score"] = risk_score
        combined["summary"]["risk_indicators"] = risk_details
        
        # Provide clear risk explanation
        if risk_score == 0:
            combined["summary"]["risk_explanation"] = "No security risks detected. Document appears to be clean and legitimate."
        elif risk_score <= 3:
            combined["summary"]["risk_explanation"] = "Low risk. Minor anomalies detected but document appears generally safe."
        elif risk_score <= 6:
            combined["summary"]["risk_explanation"] = "Medium risk. Several suspicious elements detected. Exercise caution and review details."
        else:
            combined["summary"]["risk_explanation"] = "High risk. Multiple security threats detected. Document should be considered potentially malicious."
        
        return combined
    
    def _determine_verdict(self, analysis: Dict[str, Any]) -> tuple:
        """Determine final verdict and confidence score with enhanced logic"""
        risk_score = analysis["summary"]["risk_score"]
        total_indicators = len(analysis["summary"]["risk_indicators"])
        
        # Determine verdict based on risk score with better thresholds
        if risk_score >= 8 or total_indicators >= 5:
            verdict = "suspicious"
            confidence = min(0.95, 0.7 + (risk_score * 0.03))
        elif risk_score >= 4 or total_indicators >= 2:
            verdict = "suspicious"
            confidence = min(0.85, 0.6 + (risk_score * 0.04))
        elif risk_score >= 2:
            verdict = "suspicious"
            confidence = min(0.75, 0.5 + (risk_score * 0.05))
        else:
            verdict = "authentic"
            confidence = max(0.7, 0.9 - (risk_score * 0.1))
        
        return verdict, confidence

    def _generate_visual_charts(self, pdfid_results: Dict, pikepdf_results: Dict, original_path: str) -> Dict[str, str]:
        """Generate visual charts for PDF analysis with IMPROVED chart types"""
        charts = {}
        
        try:
            # Create output directory for charts
            charts_dir = Path("static/pdf_charts")
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract filename for chart naming
            original_name = Path(original_path).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 1. Object Type Distribution Chart (Pie chart - PERFECT for this data)
            if "objects" in pdfid_results and pdfid_results["objects"]:
                charts["object_distribution"] = self._create_object_distribution_chart(
                    pdfid_results["objects"], original_name, timestamp, charts_dir
                )
            
            # 2. Risk Level Chart (Stacked bar chart - PERFECT for this data)
            if "suspicious_objects" in pdfid_results and pdfid_results["suspicious_objects"]:
                charts["risk_levels"] = self._create_risk_level_chart(
                    pdfid_results["suspicious_objects"], original_name, timestamp, charts_dir
                )
            
            # 3. Metadata Timeline Chart (Line chart - PERFECT for dates)
            if "metadata" in pikepdf_results and pikepdf_results["metadata"]:
                charts["metadata_timeline"] = self._create_metadata_timeline_chart(
                    pikepdf_results["metadata"], original_name, timestamp, charts_dir
                )
            
            # 4. Structure Analysis Chart (KPI Cards instead of radar chart)
            if "structure" in pikepdf_results:
                charts["structure_analysis"] = self._create_structure_kpi_chart(
                    pikepdf_results["structure"], original_name, timestamp, charts_dir
                )
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
        
        return charts

    def _create_object_distribution_chart(self, objects: Dict[str, int], filename: str, timestamp: str, charts_dir: Path) -> str:
        """Create pie chart showing distribution of PDF objects - PERFECT for this data"""
        try:
            # Filter out zero-count objects and get top 10
            non_zero_objects = {k: v for k, v in objects.items() if v > 0}
            sorted_objects = dict(sorted(non_zero_objects.items(), key=lambda x: x[1], reverse=True)[:10])
            
            if not sorted_objects:
                return ""
            
            # Create a more informative chart
            plt.figure(figsize=(12, 8))
            
            # Use a better color palette
            colors = plt.cm.Set3(np.linspace(0, 1, len(sorted_objects)))
            
            wedges, texts, autotexts = plt.pie(
                sorted_objects.values(), 
                labels=sorted_objects.keys(), 
                autopct='%1.1f%%', 
                startangle=90,
                colors=colors,
                textprops={'fontsize': 10}
            )
            
            # Enhance text readability
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            plt.title('PDF Object Distribution', fontsize=16, fontweight='bold', pad=20)
            plt.axis('equal')
            
            # Add total count in the center
            total_objects = sum(sorted_objects.values())
            plt.text(0, 0, f'Total: {total_objects}', ha='center', va='center', 
                    fontsize=12, fontweight='bold', transform=plt.gca().transData)
            
            chart_path = charts_dir / f"object_dist_{filename}_{timestamp}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return str(chart_path)
        except Exception as e:
            logger.error(f"Object distribution chart error: {e}")
            return ""
    
    def _create_risk_level_chart(self, suspicious_objects: List[Dict], filename: str, timestamp: str, charts_dir: Path) -> str:
        """Create stacked bar chart showing risk levels - PERFECT for this data"""
        try:
            if not suspicious_objects:
                return ""
            
            # Count risk levels
            risk_counts = Counter(obj["risk_level"] for obj in suspicious_objects)
            risk_levels = ["low", "medium", "high"]
            counts = [risk_counts.get(level, 0) for level in risk_levels]
            
            # Color mapping with better colors
            colors = ['#28a745', '#ffc107', '#dc3545']
            
            plt.figure(figsize=(10, 7))
            bars = plt.bar(risk_levels, counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
            plt.title('Risk Level Distribution', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Risk Level', fontsize=12, fontweight='bold')
            plt.ylabel('Count', fontsize=12, fontweight='bold')
            plt.xticks(risk_levels, [level.title() for level in risk_levels], fontsize=11)
            plt.yticks(fontsize=11)
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                if count > 0:
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            str(count), ha='center', va='bottom', fontweight='bold', fontsize=12)
            
            # Add grid for better readability
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            
            chart_path = charts_dir / f"risk_levels_{filename}_{timestamp}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return str(chart_path)
        except Exception as e:
            logger.error(f"Risk level chart error: {e}")
            return ""
    
    def _create_metadata_timeline_chart(self, metadata: Dict[str, str], filename: str, timestamp: str, charts_dir: Path) -> str:
        """Create timeline chart for metadata dates - PERFECT for this data"""
        try:
            dates = {}
            for key, value in metadata.items():
                if any(date_key in key.lower() for date_key in ['date', 'time']):
                    parsed_date = self._parse_pdf_date(value)
                    if parsed_date:
                        dates[key] = parsed_date
            
            if len(dates) < 2:
                return ""
            
            plt.figure(figsize=(12, 8))
            
            # Sort dates chronologically
            sorted_dates = sorted(dates.items(), key=lambda x: x[1])
            labels = [key.replace('/', '') for key, _ in sorted_dates]
            date_values = [date for _, date in sorted_dates]
            
            # Create timeline with better styling
            plt.plot(range(len(date_values)), date_values, 'o-', linewidth=3, markersize=10, 
                    color='#007bff', markerfacecolor='white', markeredgecolor='#007bff', markeredgewidth=2)
            plt.xticks(range(len(labels)), labels, rotation=45, ha='right', fontsize=11)
            plt.ylabel('Date', fontsize=12, fontweight='bold')
            plt.title('PDF Metadata Timeline', fontsize=16, fontweight='bold', pad=20)
            plt.grid(True, alpha=0.3)
            
            # Format y-axis dates
            plt.gca().yaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
            plt.gca().yaxis.set_major_locator(plt.matplotlib.dates.DayLocator(interval=1))
            
            # Add annotations for each point
            for i, (label, date) in enumerate(zip(labels, date_values)):
                plt.annotate(f'{date.strftime("%Y-%m-%d")}', 
                            xy=(i, date), xytext=(0, 10), textcoords='offset points',
                            ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            
            chart_path = charts_dir / f"metadata_timeline_{filename}_{timestamp}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return str(chart_path)
        except Exception as e:
            logger.error(f"Metadata timeline chart error: {e}")
            return ""
    
    def _create_structure_kpi_chart(self, structure: Dict, filename: str, timestamp: str, charts_dir: Path) -> str:
        """Create KPI cards instead of radar chart - PERFECT for independent metrics"""
        try:
            # Define metrics to visualize
            metrics = ['pages', 'object_count', 'annotation_count']
            values = []
            labels = []
            
            for metric in metrics:
                if metric in structure and structure[metric] is not None:
                    values.append(structure[metric])
                    labels.append(metric.replace('_', ' ').title())
            
            if len(values) < 2:
                return ""
            
            # Create KPI-style visualization
            fig, axes = plt.subplots(1, len(values), figsize=(4*len(values), 6))
            if len(values) == 1:
                axes = [axes]
            
            for i, (label, value) in enumerate(zip(labels, values)):
                ax = axes[i]
                
                # Create a simple, clear KPI display
                ax.text(0.5, 0.6, str(value), ha='center', va='center', fontsize=24, fontweight='bold', color='#007bff')
                ax.text(0.5, 0.3, label, ha='center', va='center', fontsize=14, fontweight='bold', color='#333')
                ax.text(0.5, 0.1, 'Count', ha='center', va='center', fontsize=10, color='#666')
                
                # Remove axes
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                
                # Add border
                for spine in ax.spines.values():
                    spine.set_visible(True)
                    spine.set_color('#ddd')
                    spine.set_linewidth(2)
            
            plt.suptitle('Document Structure Metrics', fontsize=16, fontweight='bold', y=0.95)
            plt.tight_layout()
            
            chart_path = charts_dir / f"structure_kpi_{filename}_{timestamp}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return str(chart_path)
        except Exception as e:
            logger.error(f"Structure KPI chart error: {e}")
            return ""
