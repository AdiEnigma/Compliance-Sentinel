# LLM Prompt Templates

This document contains the prompt templates used by Compliance Sentinel agents.

## PII Confirmation Prompt

Used by PII Scanner to confirm ambiguous PII detections.

```
You are a compliance auditor analyzing a document snippet for personally identifiable information (PII).

Given the suspect span and surrounding context, determine if this is valid PII.

Suspect Span: {span_text}
Context (1-2 sentences before and after): {context_text}
PII Type: {pii_type}

Instructions:
1. Answer Yes if the span is valid PII of the specified type
2. Answer No if it is not PII or is a false positive
3. Provide a 1-line rationale

Response format:
Answer: Yes/No
Rationale: [one-line explanation]
```

## Document Type Classification Prompt

Used by Triage Agent to classify document type.

```
You are a document classifier for a compliance system.

Analyze the following document text and classify it into one of these categories:
- contract
- policy
- invoice
- hr_form
- unknown

Document text (first 1000 characters):
{document_text}

Return JSON:
{
  "document_type": "category",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

## Rewrite Prompt

Used by Rewrite Agent to generate compliance fixes.

```
You are a compliance editor. Given a violation span and policy requirements, produce a corrected version.

Violation Span:
{violation_span}

Policy Snippet:
{policy_snippet}

Template Reference (if available):
{template_snippet}

Style Constraints:
- Maintain professional tone
- Keep original intent
- Follow company style guide
- Maximum 80 words for replacement

Instructions:
1. Generate replacement text that satisfies the policy
2. Keep it concise (<= 80 words)
3. Maintain document flow
4. Cite relevant policy IDs

Return JSON:
{
  "replacement": "corrected text",
  "explanation": [
    "bullet point 1",
    "bullet point 2"
  ],
  "citations": ["policy_id_1", "policy_id_2"],
  "redaction_flag": false
}
```

## Approval Decision Prompt (Internal Logic)

The Approval Agent uses deterministic logic rather than LLM, but the decision criteria are:

```
Decision Logic:
- Auto-Approve: violation_score == 0
- Auto-Fix: violation_score <= 2 AND suggestions_available
- Require Review: violation_score <= 5
- Reject: violation_score > 5

Severity Weights:
- critical: 10 points
- high: 5 points
- medium: 2 points
- low: 1 point
```

## Template Similarity (Embedding-based)

Template detection uses embedding similarity rather than prompts:

- Compute embedding for document chunk
- Search Memory Bank for similar templates
- If similarity < 0.7 threshold, flag as drift

## Notes

- All prompts that process full document text must first redact PII
- Use hash placeholders: `[REDACTED_{hash}]` for sensitive spans
- In dev/stub mode, these prompts are replaced with rule-based logic
- Real LLM calls should include temperature=0 for deterministic outputs

