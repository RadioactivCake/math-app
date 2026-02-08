import os
import json
import anthropic
from dataclasses import dataclass
from typing import Optional

from ..models import Feedback, StepAnalysis


@dataclass
class EvaluationResult:
    """Result from LLM evaluation."""
    success: bool
    is_correct: Optional[bool] = None
    feedback: Optional[Feedback] = None
    error: Optional[str] = None


class EvaluatorService:
    """Service for evaluating student math solutions using Claude."""

    EVALUATION_PROMPT = """You are a supportive math tutor evaluating a student's handwritten work.

PROBLEM: {question}
CORRECT ANSWER: {correct_answer}

STUDENT'S WORK (extracted from their handwriting):
{extracted_text}

Analyze the student's solution and provide helpful feedback. Focus on:
1. Whether their final answer is correct
2. The reasoning and steps shown in their work
3. Any errors in their process (even if the final answer happens to be correct)
4. What they did well

Important guidelines:
- Be encouraging but honest
- If work is minimal or unclear, note that showing steps helps catch errors
- Point to specific steps, not vague comments
- Frame errors as learning opportunities
- If you can't determine what the student did, say so and provide general guidance

Respond ONLY with valid JSON in this exact format (no other text):
{{
  "is_correct": true or false,
  "summary": "Brief 1-2 sentence summary of their work",
  "steps_analysis": [
    {{
      "step": "Description of what the student did",
      "evaluation": "correct" or "incorrect" or "unclear",
      "comment": "Specific feedback on this step"
    }}
  ],
  "suggestions": ["Improvement suggestions if any, empty array if none"],
  "encouragement": "Brief positive closing note"
}}"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def is_configured(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.api_key)

    async def evaluate(
        self,
        question: str,
        correct_answer: str,
        extracted_text: str
    ) -> EvaluationResult:
        """
        Evaluate a student's solution using Claude.

        Args:
            question: The math problem
            correct_answer: The expected answer
            extracted_text: OCR-extracted student work

        Returns:
            EvaluationResult with feedback
        """
        if not self.is_configured():
            return EvaluationResult(
                success=False,
                error="Anthropic API key not configured"
            )

        if not extracted_text or extracted_text.strip() == "":
            return EvaluationResult(
                success=False,
                error="No student work to evaluate"
            )

        prompt = self.EVALUATION_PROMPT.format(
            question=question,
            correct_answer=correct_answer,
            extracted_text=extracted_text
        )

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response if wrapped in other text
                import re
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    return EvaluationResult(
                        success=False,
                        error="Failed to parse evaluation response"
                    )

            # Build feedback object
            steps_analysis = [
                StepAnalysis(
                    step=step.get("step", ""),
                    evaluation=step.get("evaluation", "unclear"),
                    comment=step.get("comment", "")
                )
                for step in data.get("steps_analysis", [])
            ]

            feedback = Feedback(
                summary=data.get("summary", ""),
                steps_analysis=steps_analysis,
                suggestions=data.get("suggestions", []),
                encouragement=data.get("encouragement")
            )

            return EvaluationResult(
                success=True,
                is_correct=data.get("is_correct", False),
                feedback=feedback
            )

        except anthropic.AuthenticationError:
            return EvaluationResult(
                success=False,
                error="Invalid Anthropic API key"
            )
        except anthropic.RateLimitError:
            return EvaluationResult(
                success=False,
                error="Rate limit exceeded. Please try again later."
            )
        except anthropic.APIError as e:
            return EvaluationResult(
                success=False,
                error=f"API error: {str(e)}"
            )
        except Exception as e:
            return EvaluationResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )


# Singleton instance
evaluator_service = EvaluatorService()
