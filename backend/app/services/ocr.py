import os
import anthropic
from dataclasses import dataclass
from typing import Optional


@dataclass
class OCRResult:
    """Result from Claude Vision OCR."""
    success: bool
    text: Optional[str] = None
    latex: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class OCRService:
    """Service for extracting math from images using Claude Vision."""

    EXTRACTION_PROMPT = """Look at this image of handwritten math work. Extract ALL the mathematical content you can see.

Return ONLY the mathematical work as plain text, preserving the student's steps line by line.

If the image is blurry, unclear, or contains no mathematical content, respond with exactly: NONE"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def is_configured(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.api_key)

    def _parse_image_data(self, image_base64: str) -> tuple[str, str]:
        """Parse base64 image data and return (media_type, raw_base64)."""
        if image_base64.startswith("data:"):
            header, data = image_base64.split(",", 1)
            media_type = header.split(":")[1].split(";")[0]
            return media_type, data
        else:
            return "image/jpeg", image_base64

    async def extract_math(self, image_base64: str) -> OCRResult:
        """
        Extract mathematical content from a base64-encoded image using Claude Vision.

        Args:
            image_base64: Base64-encoded image string (with or without data URI prefix)

        Returns:
            OCRResult with extracted text
        """
        if not self.is_configured():
            return OCRResult(
                success=False,
                error="Anthropic API key not configured"
            )

        try:
            media_type, raw_base64 = self._parse_image_data(image_base64)
            print(f"[OCR] Using Claude Vision, media_type={media_type}, data_length={len(raw_base64)}")

            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": raw_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": self.EXTRACTION_PROMPT,
                        }
                    ],
                }]
            )

            text = message.content[0].text.strip()
            print(f"[OCR] Claude response: {text[:200]}")

            if not text or text.upper() == "NONE":
                return OCRResult(
                    success=False,
                    error="No mathematical content detected in image"
                )

            return OCRResult(
                success=True,
                text=text,
            )

        except anthropic.AuthenticationError:
            return OCRResult(
                success=False,
                error="Invalid Anthropic API key"
            )
        except anthropic.RateLimitError:
            return OCRResult(
                success=False,
                error="Rate limit exceeded. Please try again later."
            )
        except anthropic.APIError as e:
            return OCRResult(
                success=False,
                error=f"API error: {str(e)}"
            )
        except Exception as e:
            print(f"[OCR] Unexpected error: {type(e).__name__}: {e}")
            return OCRResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


# Singleton instance
ocr_service = OCRService()
