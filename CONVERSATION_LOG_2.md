# Conversation Log 2 - 2026-02-15

## Session Overview

Continued development of the Math Feedback App. This session focused on improving the image processing pipeline — experimenting with OCR.space, image quality checks, crossed-out content detection, and multi-step API call architectures. After extensive experimentation, reverted to a clean, working single Vision call approach.

---

## Request 1

**User:**
> review this folder 'C:\Users\poket\Desktop\math-feedback-app' and run the servers

**Claude:**
Explored the full project structure, read all files, and started both servers:
- Backend: FastAPI on port 8000 (`py -m uvicorn`)
- Frontend: Python HTTP server on port 3000

Hit a Windows path backslash issue in bash on first attempt. Fixed by using forward slashes with `py -m`.

---

## Request 2

**User:**
> can we try now using the ocr.space instead of only claude api? i want to compare results

**Claude:**
Implemented OCR.space alongside Claude Vision for comparison:
- Created `backend/app/services/ocr_space.py` for OCR.space API integration
- Added OCR method selector buttons to frontend (Claude / OCR.space / Compare Both)
- Updated models with `ocr_method` field
- Updated submissions router to support multiple OCR modes

---

## Request 3

**User:**
> are you sure the comparison feature works? i tried it and nothing was different. Make it so you use the ocr.space to identify the text and then you run it through claude

**Claude:**
Simplified the approach: removed comparison UI, made OCR.space the default for text extraction, kept Claude only for evaluation. Removed OCR method selector from frontend.

---

## Request 4

**User:**
> i used an image that previously worked but now it sends an error about file size limit

**Claude:**
Investigated the issue. OCR.space free tier has a 1MB file size limit. User's images were 2-3MB. After investigation, discovered the real issue: Uvicorn's `--reload` had failed to pick up the code changes silently. All previous submissions had been using Claude Vision the entire time — OCR.space was never actually called.

---

## Request 5

**User:**
> will compressing images affect the OCR performance? what do you suggest?

**Claude:**
Suggested combining quality check + OCR into a single Claude Vision call to eliminate OCR.space entirely. Benefits: no file size limit, better accuracy for handwriting, one fewer API dependency.

User approved. Implemented single-call `VisionService` that does quality check + OCR in one prompt.

---

## Request 6

**User:**
> i noticed that in some cases where the solution was messy/blurry claude the ocr ignored it and it affected claude's feedback. I want to add a step before the ocr to evaluate image quality

**Claude:**
Added image quality gate before OCR. If the image is blurry, poorly lit, messy, etc., the system returns a quality failure message instead of proceeding to OCR.

Initially the quality check was too lenient (prompt said "Be lenient"). Made it stricter with "When in doubt, reject." Confirmed working: blurry images were correctly rejected.

---

## Request 7

**User:**
> i just tried an image where a part of the solution has a line deleting it yet the quality check doesn't fail it

**Claude:**
The image had a diagonal slash through `2x = 8` (crossed-out content). Multiple prompt engineering attempts to make Sonnet detect it:
1. Added strikethrough detection instructions — didn't work
2. Made it a separate step in the prompt — didn't work
3. Added `crossed_out_content` as required JSON field — still missed it
4. Tried per-line analysis — user rejected before applying

**Key discovery:** Claude Opus 4.6 (the CLI model) detected the strikethrough immediately, but Claude Sonnet 4 (the API model) consistently missed it. This is a model capability difference.

---

## Request 8

**User:**
> i want to return to the simple approach we had before

**Claude:**
Reverted to clean version with quality check + OCR in a single Vision call, plus evaluation. Committed to git as `1c0f0c9`.

---

## Request 9

**User:**
> when i sent you the problematic image you identified the crossed text yet when we sent the same image to the api it didn't, can you explain that?

**Claude:**
Explained the model capability difference:
- Claude Opus 4.6 (CLI) has stronger visual reasoning and detected the strikethrough
- Claude Sonnet 4 (API) is optimized for speed/cost and missed it
- Additionally, the CLI had context priming (discussion about strikethroughs) while the API call was cold

---

## Request 10

**User:**
> i wanted to try separating the requests. Instead of one request for quality check + ocr, what if we separate it to 3 calls?

**Claude:**
Agreed that dedicated single-task calls could improve model focus. Implemented 3-step pipeline:
1. **QualityCheckService** — dedicated quality-only call (blur, lighting, crossed-out detection)
2. **OCRService** — dedicated text extraction-only call
3. **EvaluatorService** — evaluation (unchanged)

Updated submissions router, health endpoint, restarted backend. All 3 services confirmed healthy.

---

## Request 11

**User:**
> it seems like our new solution worked, however it didn't work around the crossed line — it just ruled the image as bad

**Claude:**
The quality check detected the crossed-out content (progress!) but rejected the entire image instead of passing it through. Attempted to change the behavior: keep crossed-out detection but report it instead of rejecting.

However, when the prompt was changed from "reject if crossed out" to "just report crossed-out content," Sonnet stopped detecting it entirely. The "reject" framing made the model more vigilant — softer framing reduced urgency.

Multiple prompt iterations tried:
- Soft "report it" framing — model ignored crossed-out content
- Strong "you MUST report" framing — still ignored
- "Unfair to the student" urgency — still ignored

---

## Request 12

**User:**
> lets make 4 checks: quality, crossed-out detection, OCR, evaluation

**Claude:**
Implemented 4-step pipeline:
1. **Quality check** — blur, lighting, readability (reject if bad)
2. **Crossed-out detection** — dedicated call with "reject" framing (backend intercepts and extracts the list instead of actually rejecting)
3. **OCR** — text extraction (runs in parallel with step 2)
4. **Evaluation** — receives OCR text + crossed-out list

The "reject" framing trick: the prompt tells the model to reject for crossed-out content (which makes it vigilant), but the backend code catches the "rejection" and just extracts the crossed-out content list, passing the image through anyway.

---

## Request 13

**User:**
> now it rejected it. i think we should just get back to the original version

**Claude:**
Checked logs — the quality check itself rejected the image for "Poor lighting, Messy or chaotic layout, Partially erased or overwritten" (not the crossed-out service). The quality check was being too strict on this particular image.

User decided to abandon crossed-out detection entirely and revert.

---

## Request 14

**User:**
> can you create a new log of today's conversation, update the readme, commit, and push to github

**Claude:**
Created this conversation log, updated README, committed changes, and pushed to GitHub.

---

## Current Status

**Architecture:** Single Vision call (quality + OCR) + Evaluation call
- `VisionService` — one Claude Vision call that checks quality and extracts text
- `EvaluatorService` — one Claude text call that evaluates the solution

**What works:**
- Image quality detection (blurry/bad images correctly rejected)
- OCR text extraction from clear handwritten images
- AI-powered math evaluation with step-by-step feedback
- Frontend quality warning UI

**Known limitation:**
- Crossed-out content detection does not work reliably with Sonnet 4. The model can detect it when told to "reject" for it, but cannot simply report it without rejecting. This would require either a more capable model (Opus) or a different approach entirely.

**Git:** Reverted to commit `1c0f0c9` state (clean single Vision + Evaluator approach).

**Untracked files (not committed):**
- `QUICKSTART.txt`
- `backend/app/services/ocr_space.py` (unused, from OCR.space experiment)
- `claude api results.txt`
- `ocr results.txt`

---

## Lessons Learned

1. **Uvicorn `--reload` is unreliable** — changes sometimes don't get picked up silently. Always manually restart the server after code changes.
2. **Model capability matters** — Opus 4.6 can detect visual details (strikethroughs) that Sonnet 4 misses. Choose the right model for the task.
3. **Prompt framing affects vigilance** — telling a model to "reject if found" makes it look harder than "just report if found." High-stakes framing increases detection sensitivity.
4. **Single-task prompts outperform multi-task prompts** — separating quality check from OCR improved both tasks, though the crossed-out detection remains a model limitation.
5. **OCR.space free tier** is not suitable for handwritten math (1MB limit, unreliable handwriting support).

---

## Project Location
`C:\Users\poket\Desktop\math-feedback-app`
