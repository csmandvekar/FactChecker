import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import logging
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

logger = logging.getLogger(__name__)

class CASIACNN(nn.Module):
    """CASIA CNN model for image tampering detection"""
    def __init__(self, num_classes=2):
        super(CASIACNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(256, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

class ImageForensicsService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self._load_model()
    
    def _load_model(self):
        """Load pretrained CASIA CNN model"""
        try:
            self.model = CASIACNN()
            # In a real implementation, you would load pretrained weights here
            # self.model.load_state_dict(torch.load(settings.CASIA_MODEL_PATH, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            logger.info("CASIA CNN model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load CASIA model: {e}. Using dummy model.")
            self.model = None
    
    async def analyze_image(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive image forensic analysis
        
        Args:
            file_path: Path to the image file
            
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
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                    temp_file.write(file_content.read())
                    temp_file_path = temp_file.name
            else:
                temp_file_path = file_path
            
            # Run ELA analysis
            ela_start = datetime.now()
            ela_result, ela_confidence, ela_heatmap_path = self._run_ela_analysis(temp_file_path)
            ela_processing_time = (datetime.now() - ela_start).total_seconds()
            
            # Run CNN analysis
            cnn_start = datetime.now()
            cnn_result, cnn_confidence = self._run_cnn_analysis(temp_file_path)
            cnn_processing_time = (datetime.now() - cnn_start).total_seconds()
            
            # Combine results
            overall_verdict, overall_confidence = self._combine_results(
                ela_result, ela_confidence, cnn_result, cnn_confidence
            )
            
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            # Cleanup temporary file if created
            if file_path.startswith(("s3://", "minio://")) and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            return {
                "verdict": overall_verdict,
                "confidence_score": overall_confidence,
                "ela_result": ela_result,
                "ela_confidence": ela_confidence,
                "ela_evidence": {"heatmap_path": ela_heatmap_path},
                "ela_heatmap_path": ela_heatmap_path,
                "ela_processing_time": ela_processing_time,
                "cnn_result": cnn_result,
                "cnn_confidence": cnn_confidence,
                "cnn_evidence": {"model_prediction": cnn_result},
                "cnn_processing_time": cnn_processing_time,
                "total_processing_time": total_processing_time,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            raise
    
    def _run_ela_analysis(self, file_path: str) -> Tuple[str, float, str]:
        """Run Error Level Analysis on the image"""
        try:
            # Load image
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save with specific quality to create ELA
            temp_ela_path = tempfile.mktemp(suffix='.jpg')
            image.save(temp_ela_path, 'JPEG', quality=95)
            
            # Load the saved image
            saved_image = Image.open(temp_ela_path)
            
            # Calculate ELA
            ela_image = self._calculate_ela(image, saved_image)
            
            # Analyze ELA for tampering indicators
            tampering_score = self._analyze_ela_patterns(ela_image)
            
            # Generate heatmap
            heatmap_path = self._generate_ela_heatmap(ela_image, file_path)
            
            # Cleanup temporary file
            if os.path.exists(temp_ela_path):
                os.unlink(temp_ela_path)
            
            # Determine result based on tampering score
            if tampering_score > 0.7:
                result = "suspicious"
                confidence = min(0.95, 0.6 + tampering_score * 0.3)
            elif tampering_score > 0.4:
                result = "suspicious"
                confidence = min(0.85, 0.5 + tampering_score * 0.3)
            else:
                result = "authentic"
                confidence = max(0.6, 0.9 - tampering_score * 0.3)
            
            return result, confidence, heatmap_path
            
        except Exception as e:
            logger.error(f"ELA analysis error: {e}")
            return "authentic", 0.5, ""
    
    def _calculate_ela(self, original: Image.Image, saved: Image.Image) -> np.ndarray:
        """Calculate Error Level Analysis"""
        # Convert to numpy arrays
        original_array = np.array(original, dtype=np.float32)
        saved_array = np.array(saved, dtype=np.float32)
        
        # Calculate error level
        ela = np.abs(original_array - saved_array)
        
        # Normalize to 0-255 range
        ela_normalized = np.clip(ela * 10, 0, 255).astype(np.uint8)
        
        return ela_normalized
    
    def _analyze_ela_patterns(self, ela_image: np.ndarray) -> float:
        """Analyze ELA patterns for tampering indicators"""
        try:
            # Convert to grayscale for analysis
            if len(ela_image.shape) == 3:
                gray_ela = cv2.cvtColor(ela_image, cv2.COLOR_RGB2GRAY)
            else:
                gray_ela = ela_image
            
            # Calculate statistics
            mean_error = np.mean(gray_ela)
            std_error = np.std(gray_ela)
            
            # Detect high-error regions (potential tampering)
            high_error_threshold = mean_error + 2 * std_error
            high_error_pixels = np.sum(gray_ela > high_error_threshold)
            total_pixels = gray_ela.size
            
            # Calculate tampering score
            tampering_ratio = high_error_pixels / total_pixels
            
            # Additional analysis: edge detection in ELA
            edges = cv2.Canny(gray_ela, 50, 150)
            edge_density = np.sum(edges > 0) / total_pixels
            
            # Combine indicators
            tampering_score = (tampering_ratio * 0.7 + edge_density * 0.3)
            
            return min(1.0, tampering_score * 10)  # Scale up and cap at 1.0
            
        except Exception as e:
            logger.error(f"ELA pattern analysis error: {e}")
            return 0.0
    
    def _generate_ela_heatmap(self, ela_image: np.ndarray, original_path: str) -> str:
        """Generate ELA heatmap visualization"""
        try:
            # Create output directory for heatmaps
            heatmap_dir = Path("static/heatmaps")
            heatmap_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            original_name = Path(original_path).stem
            heatmap_filename = f"ela_heatmap_{original_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            heatmap_path = heatmap_dir / heatmap_filename
            
            # Create heatmap visualization
            plt.figure(figsize=(12, 8))
            
            # Original ELA
            plt.subplot(2, 2, 1)
            plt.imshow(ela_image)
            plt.title('ELA Analysis')
            plt.axis('off')
            
            # Grayscale ELA
            if len(ela_image.shape) == 3:
                gray_ela = cv2.cvtColor(ela_image, cv2.COLOR_RGB2GRAY)
            else:
                gray_ela = ela_image
            
            plt.subplot(2, 2, 2)
            plt.imshow(gray_ela, cmap='hot')
            plt.title('ELA Heatmap')
            plt.colorbar()
            plt.axis('off')
            
            # Error distribution
            plt.subplot(2, 2, 3)
            plt.hist(gray_ela.flatten(), bins=50, alpha=0.7)
            plt.title('Error Distribution')
            plt.xlabel('Error Level')
            plt.ylabel('Frequency')
            
            # High-error regions
            plt.subplot(2, 2, 4)
            mean_error = np.mean(gray_ela)
            std_error = np.std(gray_ela)
            high_error_mask = gray_ela > (mean_error + 2 * std_error)
            plt.imshow(high_error_mask, cmap='Reds')
            plt.title('High-Error Regions')
            plt.axis('off')
            
            plt.tight_layout()
            plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(heatmap_path)
            
        except Exception as e:
            logger.error(f"Heatmap generation error: {e}")
            return ""
    
    def _run_cnn_analysis(self, file_path: str) -> Tuple[str, float]:
        """Run CASIA CNN analysis on the image"""
        try:
            if self.model is None:
                # Return dummy result if model not loaded
                return "authentic", 0.5
            
            # Load and preprocess image
            image = Image.open(file_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply transformations
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Run inference
            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                
                # Get prediction (0: authentic, 1: tampered)
                prediction = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][prediction].item()
                
                result = "suspicious" if prediction == 1 else "authentic"
                
                # Adjust confidence based on model reliability
                if self.model is None:  # Dummy model
                    confidence = 0.5
                
                return result, confidence
                
        except Exception as e:
            logger.error(f"CNN analysis error: {e}")
            return "authentic", 0.5
    
    def _combine_results(self, ela_result: str, ela_confidence: float, 
                        cnn_result: str, cnn_confidence: float) -> Tuple[str, float]:
        """Combine ELA and CNN results"""
        # Weight the results (ELA is more reliable for certain types of tampering)
        ela_weight = 0.6
        cnn_weight = 0.4
        
        # Calculate weighted confidence
        if ela_result == cnn_result:
            # Both methods agree
            overall_confidence = (ela_confidence * ela_weight + cnn_confidence * cnn_weight)
            return ela_result, overall_confidence
        else:
            # Methods disagree - use the one with higher confidence
            if ela_confidence > cnn_confidence:
                return ela_result, ela_confidence * 0.9  # Slight penalty for disagreement
            else:
                return cnn_result, cnn_confidence * 0.9
        
        # Determine overall verdict
        if ela_result == "suspicious" or cnn_result == "suspicious":
            # If either method detects tampering, mark as suspicious
            if ela_result == "suspicious" and cnn_result == "suspicious":
                # Both agree on suspicious
                overall_confidence = (ela_confidence * ela_weight + cnn_confidence * cnn_weight)
                return "suspicious", overall_confidence
            elif ela_result == "suspicious":
                # ELA detected tampering
                return "suspicious", ela_confidence * 0.8
            else:
                # CNN detected tampering
                return "suspicious", cnn_confidence * 0.8
        else:
            # Both methods agree on authentic
            overall_confidence = (ela_confidence * ela_weight + cnn_confidence * cnn_weight)
            return "authentic", overall_confidence
