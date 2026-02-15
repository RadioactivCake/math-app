import os
import json
import re
import anthropic
from dataclasses import dataclass
from typing import Optional


@dataclass
class VisionResult:
    """Result from Claude Vision: quality check + OCR in one call."""
    readable: bool
    # Quality fields (populated when readable=False)
    issues: Optional[list[str]] = None
    suggestion: Optional[str] = None
    # OCR fields (populated when readable=True)
    extracted_text: Optional[str] = None
    # Error field (populated on API/parse failure)
    error: Optional[str] = None


class VisionService:
    """Single Claude Vision call that checks image quality and extracts math."""

    PROMPT = """You are analyzing a photo of a student's handwritten math work. Do TWO things in order:

**STEP 1 — Quality Check**
Decide if this image is readable enough to extract math from. Mark it as NOT readable if ANY of these are true:
- Blurry or out of focus — digits or symbols could be misread
- Poor lighting — too dark, too bright, heavy shadows, or glare obscuring writing
- Messy or chaotic layout — writing scribbled over, written in random directions, overlapping, or no clear top-to-bottom flow
- Partially erased or overwritten — lines or numbers half-deleted, smudged, or layered on top of each other
- Cropped or cut off — math work is not fully visible
- No math content — the image has no mathematical writing
- Low resolution — too small or pixelated to confidently read all characters
- Distracting background — math blends into a cluttered surface

When in doubt, mark it as NOT readable. It is better to ask the student to retake the photo than to extract incorrect text.

**STEP 2 — Extract Math (only if readable)**
If the image IS readable, extract ALL mathematical content exactly as the student wrote it. Preserve their steps line by line. Do NOT solve, correct, or reformat — just transcribe what you see.

Respond ONLY with valid JSON (no other text):

If NOT readable:
{
  "readable": false,
  "issues": ["list every specific issue found"],
  "suggestion": "A short, friendly tip to help retake the photo",
  "extracted_text": null
}

If readable:
{
  "readable": true,
  "issues": [],
  "suggestion": null,
  "extracted_text": "the student's math work transcribed line by line"
}"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _parse_image_data(self, image_base64: str) -> tuple[str, str]:
        if image_base64.startswith("data:"):
            header, data = image_base64.split(",", 1)
            media_type = header.split(":")[1].split(";")[0]
            return media_type, data
        else:
            return "image/jpeg", image_base64

    async def analyze(self, image_base64: str) -> VisionResult:
        """
        Single Claude Vision call: checks quality, and if readable, extracts math.
        """
        if not self.is_configured():
            return VisionResult(
                readable=False,
                error="Anthropic API key not configured"
            )

        try:
            media_type, raw_base64 = self._parse_image_data(image_base64)
            print(f"[Vision] Analyzing image, media_type={media_type}, data_length={len(raw_base64)}")

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
                            "text": self.PROMPT,
                        }
                    ],
                }]
            )

            response_text = message.content[0].text.strip()
            print(f"[Vision] Claude response: {response_text}")

            # Parse JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    print("[Vision] Could not parse response")
                    return VisionResult(
                        readable=False,
                        error="Failed to parse image analysis response"
                    )

            readable = data.get("readable", False)
            issues = data.get("issues", [])
            suggestion = data.get("suggestion")
            extracted_text = data.get("extracted_text")

            if not readable:
                return VisionResult(
                    readable=False,
                    issues=issues if issues else ["Image not readable"],
                    suggestion=suggestion,
                )

            # Readable but no text extracted
            if not extracted_text or extracted_text.strip() == "" or extracted_text.upper() == "NONE":
                return VisionResult(
                    readable=False,
                    issues=["No mathematical content detected"],
                    suggestion="Make sure your math work is visible in the photo.",
                )

            return VisionResult(
                readable=True,
                extracted_text=extracted_text.strip(),
            )

        except anthropic.AuthenticationError:
            return VisionResult(readable=False, error="Invalid Anthropic API key")
        except anthropic.RateLimitError:
            return VisionResult(readable=False, error="Rate limit exceeded. Please try again later.")
        except anthropic.APIError as e:
            return VisionResult(readable=False, error=f"API error: {str(e)}")
        except Exception as e:
            print(f"[Vision] Unexpected error: {type(e).__name__}: {e}")
            return VisionResult(readable=False, error=f"Unexpected error: {str(e)}")


# Singleton instance
vision_service = VisionService()
