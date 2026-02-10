import httpx
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OCRResult:
    """Result from OCR.space API."""
    success: bool
    text: Optional[str] = None
    latex: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class OCRService:
    """Service for extracting math from images using OCR.space API (Engine 3 - Handwriting)."""

    API_URL = "https://api.ocr.space/parse/image"

    def __init__(self):
        self.api_key = os.getenv("OCR_SPACE_API_KEY")

    def is_configured(self) -> bool:
        """Check if OCR.space API key is configured."""
        return bool(self.api_key)

    async def extract_math(self, image_base64: str) -> OCRResult:
        """
        Extract mathematical content from a base64-encoded image.

        Args:
            image_base64: Base64-encoded image string (with or without data URI prefix)

        Returns:
            OCRResult with extracted text
        """
        if not self.is_configured():
            return OCRResult(
                success=False,
                error="OCR.space API key not configured"
            )

        # Ensure proper data URI format for ocr.space
        if not image_base64.startswith("data:"):
            image_base64 = f"data:image/jpeg;base64,{image_base64}"

        payload = {
            "apikey": self.api_key,
            "base64Image": image_base64,
            "OCREngine": "3",
            "scale": "true",
            "isTable": "true",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.API_URL,
                    data=payload,
                )

                if response.status_code != 200:
                    return OCRResult(
                        success=False,
                        error=f"OCR.space API error: HTTP {response.status_code}"
                    )

                data = response.json()

                # Check for processing errors
                if data.get("IsErroredOnProcessing", False):
                    error_msg = "OCR processing failed"
                    if data.get("ParsedResults"):
                        error_msg = data["ParsedResults"][0].get("ErrorMessage", error_msg)
                    return OCRResult(
                        success=False,
                        error=error_msg
                    )

                exit_code = data.get("OCRExitCode", 0)
                if exit_code not in (1, 2):
                    return OCRResult(
                        success=False,
                        error=f"OCR failed with exit code {exit_code}"
                    )

                # Extract text from parsed results
                parsed_results = data.get("ParsedResults", [])
                if not parsed_results:
                    return OCRResult(
                        success=False,
                        error="No results returned from OCR"
                    )

                text = parsed_results[0].get("ParsedText", "").strip()

                if not text:
                    return OCRResult(
                        success=False,
                        error="No mathematical content detected in image"
                    )

                return OCRResult(
                    success=True,
                    text=text,
                )

        except httpx.TimeoutException:
            return OCRResult(
                success=False,
                error="OCR request timed out"
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
ocr_service = OCRService()
