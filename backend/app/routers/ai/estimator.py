"""Room photo estimate through Gemini Vision."""

import json

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from google.genai import types as genai_types

from app.utils.gemini import generate_with_fallback

router = APIRouter()


# ── Vision Estimator ──────────────────────────────────────────────────────────

_VISION_PROMPT = """
You are a logistics AI that analyzes room/space images for moving estimates.

Analyze the image and return ONLY valid JSON (no markdown, no explanation) in this exact format:
{
  "detected_space": "e.g. Master Bedroom / Living Room",
  "confidence": 92,
  "items": [
    {"name": "Item name", "qty": 1, "fragile": false},
    {"name": "Another item", "qty": 2, "fragile": true}
  ],
  "metrics": {
    "boxes_needed": 12,
    "laborers": 2,
    "bubble_wrap_rolls": 3,
    "heavy_items": 2,
    "estimated_volume_cubic_feet": 95
  },
  "vehicle_recommendation": {
    "type": "tempo",
    "display_name": "Tata Ace / 1.5 Ton Tempo",
    "reason": "Brief reason for vehicle choice"
  },
  "estimated_base_cost_inr": 4500
}

Rules:
- List actual visible furniture/items (beds, wardrobes, TVs, sofas, etc.)
- Mark item as fragile:true if it's glass, electronics, mirrors, crockery etc.
- boxes_needed = estimate based on item volume
- vehicle type must be one of: mini-truck, tempo, lcv, hcv
- estimated_base_cost_inr = rough cost in Indian Rupees (without distance)
- If image is not of a room/space, still return valid JSON but with detected_space: "Unknown / Not a room"
"""


@router.post(
    "/estimate-image",
    summary="Analyze a room photo for moving estimate",
    description="Upload an image. Gemini Vision detects items and returns a moving estimate.",
)
async def estimate_image(
    file: UploadFile = File(..., description="Room photo — JPG or PNG, max 15 MB"),
):
    """Analyze a room photo with Gemini Vision and return a moving estimate."""
    # Validate
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, or WebP images are accepted.",
        )

    raw = await file.read()
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be smaller than 15 MB.",
        )

    # Build inline image part using the new SDK
    image_part = genai_types.Part.from_bytes(data=raw, mime_type=file.content_type)
    text_part  = genai_types.Part.from_text(text=_VISION_PROMPT)

    try:
        response = await generate_with_fallback(
            contents=[genai_types.Content(role="user", parts=[image_part, text_part])],
            config=genai_types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        result_text = response.text.strip()
        # Strip markdown fences if model wraps despite mime type setting
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        return json.loads(result_text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an unexpected response. Please try again.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini Vision error: {str(e)}",
        ) from e
