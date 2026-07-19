"""English prompt library for Shadow Seed Learning."""

DETECTION_PASS = """
You are an epistemic analyst.

Do not improve the answer. Identify small structural absences in it.

Review the answer that was just produced. Which small concepts, relationships,
or constraints are missing even though they are needed for a complete
understanding of this specific topic?

Rules:
- Return no more than 5 seeds.
- Each seed must describe exactly one gap.
- Do not combine several analytical frameworks in one seed.
- Do not put a list inside a seed.
- Make every seed concrete and testable.
- Do not explain your choices.
- Write seeds in the same language as the source answer.

Output:
1. [seed]
2. [seed]
3. [seed]
""".strip()

SEED_NORMALIZATION = """
Split the broad gap below into atomic shadow seeds.

Rules:
- Each seed must contain one missing relationship, factor, or constraint.
- A seed must not combine multiple domains.
- Write each seed as a short sentence.
- Return no more than 8 seeds.
- Preserve the language of the broad gap.

Broad gap:
"{broad_gap}"
""".strip()

JSON_EXTRACTION = """
Convert the seeds below to JSON.

Rules:
- Preserve each seed's text exactly.
- Give 3 to 5 trigger keywords per seed.
- Do not add new seeds.
- Keep each rationale brief.

Seeds:
{seeds}

JSON output:
{
  "shadow_seeds": [
    {
      "text": "...",
      "trigger_keywords": ["...", "..."],
      "rationale": "..."
    }
  ]
}
""".strip()

DIALECTICAL_PROBE = """
Consider the hypothesis that this gap is relevant:

"{seed_text}"

Try to falsify the hypothesis. Give the strongest reason why the gap is not
relevant in this context, or why the available information is already
sufficient.

Reply with exactly one label:

FALSIFIED

or

VALIDATED
""".strip()

SOCRATIC_PROBE = """
You have a promoted seed:

"{seed_text}"

Express it as one natural Socratic question.

Rules:
- Do not say that something was forgotten.
- Do not make a list.
- Do not present an error message.
- Ask exactly one question.
- Invite the user to fill the gap.
- Use the same language as the seed.
""".strip()

RETRIEVAL_PROBE = """
Create one narrow retrieval query for this seed.

Seed:
"{seed_text}"

Rules:
- Return one query.
- Use no more than 12 words.
- Avoid broad terms such as "context" or "analysis".
- Use concrete content words.
- Use the same language as the seed.

Output:
[query]
""".strip()

JUDGE_PROMPT = """
Evaluate an SSL detection.

Input text:
{input_text}

Ground-truth seeds:
{ground_truth}

Detected seed:
{detected_seed}

Scores:
- atomicity: 0 or 1
- relevance: 0 to 2
- ground_truth_match: 0 to 2
- final_score: 0, 1, or 2

Rules:
- A score of 2 requires an atomic seed.
- A broad list can receive no more than 1.
- Give a short reason.

Return JSON only.
""".strip()
