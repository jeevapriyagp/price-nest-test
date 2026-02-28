import json
from google import genai
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List
from google.genai import types
from ..core.config import GEMINI_API_KEY

# -----------------------------------------------
# Pydantic Schema for LLM output
# -----------------------------------------------

class ProductSummary(BaseModel):
    title: str = Field(..., min_length=1, max_length=120, description="Short product title")
    overview: str = Field(..., min_length=20, max_length=600, description="2–3 sentence product overview")
    highlights: List[str] = Field(..., min_length=2, max_length=6, description="Key specs or features")
    who_its_for: str = Field(..., min_length=10, max_length=300, description="Who the product suits best")
    buying_tip: str = Field(..., min_length=10, max_length=300, description="Practical buying advice")

    @field_validator("highlights")
    @classmethod
    def highlights_must_be_non_empty_strings(cls, v: List[str]) -> List[str]:
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Each highlight must be a non-empty string.")
        return [item.strip() for item in v]

    @field_validator("title", "overview", "who_its_for", "buying_tip", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


# -----------------------------------------------
# Configure Gemini
# -----------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def get_product_summary(query: str) -> dict:
    """
    Given a product search query,
    returns a Pydantic-validated AI overview similar to Google's AI Overview.
    """

    if not client:
        return {"error": "GEMINI_API_KEY is not set in environment variables."}

    prompt = f"""You are a helpful product overview assistant. The user searched for: "{query}".

Give a concise, factual AI overview of this product — exactly like Google's AI Overview panel.

Structure your response in this exact JSON format:
{{
  "title": "Short product title",
  "overview": "2–3 sentence summary of what this product is, its latest generation/version, and what it's known for.",
  "highlights": [
    "Key spec or feature 1",
    "Key spec or feature 2",
    "Key spec or feature 3",
    "Key spec or feature 4"
  ],
  "who_its_for": "1-2 sentences on who this product suits best.",
  "buying_tip": "1-2 sentences practical tip for buyers — e.g. best variant to buy, what to watch for in pricing, or when deals typically occur."
}}

Rules:
- Only use your training knowledge about the product. Do not invent specs.
- Keep it factual, neutral, and informative — no marketing language.
- If the query is vague or not a real product, still return the JSON with a helpful general overview.
- Return ONLY the raw JSON. No markdown, no explanation, no code blocks."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        raw = response.text.strip()

        # Strip accidental markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        # Parse JSON
        parsed = json.loads(raw)

        # Enforce Pydantic schema — raises ValidationError if LLM output is malformed
        validated: ProductSummary = ProductSummary.model_validate(parsed)

        return {"success": True, "data": validated.model_dump()}

    except json.JSONDecodeError as e:
        return {"error": f"LLM returned invalid JSON: {e}"}

    except ValidationError as e:
        return {
            "error": "LLM output failed schema validation.",
            "details": e.errors()
        }

    except Exception as e:
        return {"error": str(e)}