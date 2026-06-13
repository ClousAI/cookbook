# 06 · Earnings Q&A

Ask natural-language questions about a company's filings and get **grounded,
cited** answers — two ways.

## A. `POST /v1/answer` (purpose-built)

Returns an answer synthesized **strictly from filing text**, with `citations` to
the source filings and a `basis` (confidence + reasoning).

Body (`AnswerIn`):

| Field | Type | Notes |
| --- | --- | --- |
| `q` | string | **required** — your question |
| `ticker` / `cik` / `accession` | string | scope: one entity or one filing (omit all = full corpus) |
| `forms` | string | restrict to form types, e.g. `"10-Q,10-K,8-K"` |
| `max_sources` | int (1–8) | how many filings to ground on (default 4) |
| `output_schema` | object | a JSON Schema → get a **structured** answer instead of prose |

## B. `POST /v1/chat/completions` (OpenAI-compatible)

Drop-in OpenAI Chat Completions. Point any OpenAI client at
`base_url=https://api.clous.ai/v1`, `model="clous"`. The last user message is
answered, grounded in filings; citations + basis ride along under a `clous` key
on the response.

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.clous.ai/v1", api_key="clous_live_...")
resp = client.chat.completions.create(
    model="clous",
    messages=[{"role": "user", "content": "Summarize NVDA's latest quarter and risks."}],
)
print(resp.choices[0].message.content)
```

## Run

```bash
export CLOUS_API_KEY=clous_live_...

python earnings_qa.py NVDA "How did data center revenue trend last quarter?"
./earnings_qa.sh NVDA "How did data center revenue trend last quarter?"
```

The Python script shows all three: grounded `/v1/answer`, a structured
`output_schema` answer, and the OpenAI-compatible endpoint (via plain `requests`,
no extra dependency). Install `openai` only if you want the client shown above.
