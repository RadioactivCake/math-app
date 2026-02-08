import httpx
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OCRResult:
    """Result from Mathpix OCR."""
    success: bool
    text: Optional[str] = None
    latex: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class MathpixService:
    """Service for extracting math from images using Mathpix API."""

    API_URL = "https://api.mathpix.com/v3/text"

    def __init__(self):
        self.app_id = os.getenv("MATHPIX_APP_ID")
        self.app_key = os.getenv("MATHPIX_APP_KEY")

    def is_configured(self) -> bool:
        """Check if Mathpix credentials are configured."""
        return bool(self.app_id and self.app_key)

    async def extract_math(self, image_base64: str) -> OCRResult:
        """
        Extract mathematical content from a base64-encoded image.

        Args:
            image_base64: Base64-encoded image string (without data URI prefix)

        Returns:
            OCRResult with extracted text and LaTeX
        """
        if not self.is_configured():
            return OCRResult(
                success=False,
                error="Mathpix API credentials not configured"
            )

        # Ensure proper data URI format
        if not image_base64.startswith("data:"):
            # Assume JPEG if no prefix
            image_base64 = f"data:image/jpeg;base64,{image_base64}"

        headers = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "Content-Type": "application/json"
        }

        payload = {
            "src": image_base64,
            "formats": ["text", "latex_styled"],
            "data_options": {
                "include_asciimath": True
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 401:
                    return OCRResult(
                        success=False,
                        error="Invalid Mathpix API credentials"
                    )

                if response.status_code == 429:
                    return OCRResult(
                        success=False,
                        error="Mathpix rate limit exceeded"
                    )

                if response.status_code != 200:
                    return OCRResult(
                        success=False,
                        error=f"Mathpix API error: {response.status_code}"
                    )

                data = response.json()

                # Check for errors in response
                if "error" in data:
                    return OCRResult(
                        success=False,
                        error=data.get("error_info", {}).get("message", "Unknown error")
                    )

                text = data.get("text", "").strip()
                latex = data.get("latex_styled", "").strip()
                confidence = data.get("confidence", 0)

                # Check if we got any meaningful content
                if not text and not latex:
                    return OCRResult(
                        success=False,
                        error="No mathematical content detected in image"
                    )

                return OCRResult(
                    success=True,
                    text=text,
                    latex=latex,
                    confidence=confidence
                )

        except httpx.TimeoutException:
            return OCRResult(
                success=False,
                error="Mathpix API request timed out"
            )
        except httpx.RequestError as e:
            return OCRResult(
                success=False,
                error=f"Network error: {str(e)}"
            )
        except Exception as e:
            return OCRResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


# Singleton instance
mathpix_service = MathpixService()
