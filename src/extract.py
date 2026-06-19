"""Minimal LiteLLM/Gemini extraction: one interview transcript -> PatientLabels (a prediction).

Builds on the canonical call verified in `notebooks/00_setup.ipynb` (litellm.completion,
gemini-2.5-flash-lite, GEMINI_API_KEY loaded from `.env`) and the documented Gemini
structured-output pattern (https://docs.litellm.ai/docs/providers/gemini):

    response_format={"type": "json_object", "response_schema": <json schema>,
                     "enforce_validation": True}

We pass `PatientLabels.model_json_schema()` as `response_schema`, so Pydantic builds the schema
(accurate for our nested models), Gemini is constrained to it, and `enforce_validation` makes
LiteLLM validate the reply — raising `litellm.JSONSchemaValidationError` on a bad output.
`model_validate_json(...)` then materialises the typed object.

The MVP includes a *simple* referral_pathway instruction (in the prompt below); refining the
step vocabulary / journey-type clustering is the big post-MVP task (docs/TODO.md).

TO VERIFY in testing (see docs/RESOURCES.md): whether Gemini 2.5 accepts the `$defs`/`$ref`
Pydantic emits for the nested models, and whether the LiteLLM path matches the OpenAI-SDK path.
"""

import litellm
from dotenv import load_dotenv

from schema import PatientLabels

MODEL = "gemini/gemini-2.5-flash-lite"

SYSTEM_PROMPT = (
    "Extract the structured labels from this Crohn's disease patient interview. "
    "Use the schema's enum values exactly, and leave a field null/empty when the transcript "
    "doesn't support a confident value. Set patient_id to the value given in the message. "
    "For referral_pathway, list the patient's journey as an ordered sequence of the canonical "
    "PathwayStep values."
)


def extract(transcript: str, patient_id: str) -> PatientLabels:
    """Extract one patient's labels from their interview transcript via Gemini (a prediction)."""
    load_dotenv()  # GEMINI_API_KEY -> env; litellm reads it for the gemini/ provider
    response = litellm.completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"patient_id: {patient_id}\n\n{transcript}"},
        ],
        response_format={
            "type": "json_object",
            "response_schema": PatientLabels.model_json_schema(),
            "enforce_validation": True,
        },
    )
    return PatientLabels.model_validate_json(response.choices[0].message.content)
