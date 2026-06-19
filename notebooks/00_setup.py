# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python (chronicity)
#     language: python
#     name: chronicity
# ---

# %% [markdown]
# # Chronicity Project Setup
#
# This notebook runs the setup for all the tools we need.

# %%
# Imports

import litellm
import os
from dotenv import load_dotenv
from google import genai
import pandas as pd
from pathlib import Path

# %% [markdown]
# ## Google Gemini API
#
# Let's get Google Gemini API working first, to test my API key works, before getting `LiteLLM` working.
#
# Google GenAI Python SDK
#
# `gemini-3.5-flash` got this error on first try: 
#
# ```
# ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 
# 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
# ```
#
# So I tried a smaller/cheaper previous model for testing: 
#
# [Gemini 2.5 Flash Lite](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite?_gl=1*b87crc*_up*MQ..*_ga*MjAyMjcxMjk5MC4xNzgxNzA2ODEy*_ga_P1DBVKWT6V*czE3ODE3MDY4MTEkbzEkZzAkdDE3ODE3MDcxNzEkajYwJGwwJGgxMzYxOTQ0ODQy)
#
# This worked and returned Markdown formatted text.

# %%
load_dotenv()  # reads variables from a .env file and sets them in os.environ
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

#print(GEMINI_API_KEY)

client = genai.Client(api_key=GEMINI_API_KEY)

google_response = client.models.generate_content(
     model="gemini-2.5-flash-lite", 
     contents="Explain Crohn's Disease in a few words"
 )


# %%
print(google_response)

# %%
type(google_response)

# %%
print(google_response.text)

# %% [markdown]
# # LiteLLM
#
# I followed the setup at [LiteLLM](https://docs.litellm.ai/docs/providers/gemini) which also has the API parameters for calling the model.
#
# I read the API doc for using Gemini.
#
# The LiteLLM API includes parameters relevant to the spec (e.g. `temperature` is automatically set to 1.0, `response_format`, `reasoning_effort` or `thinking_level` - I found a gap in the LiteLLM API doc which mislabelled that parameter - send them a PR if I've got time?, and `thinking`) and parameters useful for debugging (e.g. `logprobs`, `reasoning_content`) which will be useful later.
#
# You can set the `response_format` to JSON:
#
# ```python
# completion(
#     model="gemini/gemini-1.5-pro", 
#     messages=messages, 
#     response_format={"type": "json_object"} # 👈 KEY CHANGE
# )
# ```
#
# There's a really relevant bit on `response_schema`: LiteLLM supports sending `response_schema` as a param for Gemini-1.5-Pro on Google AI Studio which passes a Python dict to the `response_schema` value of the `response_format` API parameter. You then can validate the schema by setting `enforce_validation: true` in the API call. This might be really useful depending on how we do the Pydantic validation!
#
# There's a section on caching and cache control which is relevant to the spec in the time-to-live section ([TTL](https://docs.litellm.ai/docs/providers/gemini#custom-ttl-support)).
#
# There's also a tool calling ability, so we could connect the model to a Google web search, as an extra feature.
#
#
#
#

# %%

litellm_response = litellm.completion(
    model="gemini/gemini-2.5-flash-lite", # note the parameter is gemini/model
    messages=[{"role": "user", "content": "Explain Crohn's Disease in a few words"}]
)

# %%
print(litellm_response)

# %%
# Python ModelResponse object
type(litellm_response)

# %%
print(litellm_response.choices[0].message.content)


# %% [markdown]
# # LiteLLM `ModelResponse` Python Object
#
# I read the SDK [Quickstart](https://docs.litellm.ai/docs/learn/sdk_quickstart) to find out about the `ModelResponse` type.
#
# There's lots of interesting outputs from the `ModelResponse` object.
#
# The relevant ones for us as the token and caching diagnostics in `usage`.
#
# I was curious what `thinking_blocks` is but it looks like Anthropic-only reasoning output, though this [doc](https://docs.litellm.ai/docs/reasoning_content) is contradictory.
#
# Turns out there's a `.model_dump_json()` function that "Generates a JSON representation of the model using Pydantic's `to_json` method"
#

# %%
help(litellm.ModelResponse)

# %%
# ModelResponse has a .json() function
litellm_response.json()

# %%
litellm.ModelResponse.json

# %% [markdown]
# # Exception Handling
#
# I found helpful sections in the LiteLLM docs on [exception handling](https://docs.litellm.ai/docs/#exception-handling), [logging and observability](https://docs.litellm.ai/docs/#logging--observability), and [cost and usage tracking](https://docs.litellm.ai/docs/#track-costs--usage) relevant to the spec.
#
# There's even a [proxy server](https://docs.litellm.ai/docs/#litellm-proxy-server-llm-gateway) (LLM gateway) with a dash I could use for monitoring!

# %% [markdown]
# # Compare Models
#
# Now I've got LiteLLM working and a high-level sense of the API, I looked at the model candidates for a baseline for this use case.
#
# I decided to stick with [Gemini 2.5 Flash-lite](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite?_gl=1*1yw8qfg*_up*MQ..*_ga*Mjg4MTUwNzIwLjE3ODE3NzUwMzU.*_ga_P1DBVKWT6V*czE3ODE3NzUwMzUkbzEkZzAkdDE3ODE3NzUwMzUkajYwJGwwJGg3NzU2OTI3NjI.) for local testing and quick iteration. We can always scale up if necessary.
#
# This model supports caching and thinking according to the docs.
#
# I checked if this model does actually support "thinking" via LiteLLM, which was ambiguous in the docs. Here's how to do that: [Checking if a model supports reasoning](https://docs.litellm.ai/docs/reasoning_content#checking-if-a-model-supports-reasoning). Looks like it does! We might or might not need this.

# %%
litellm.supports_reasoning(model="gemini/gemini-2.5-flash-lite")
