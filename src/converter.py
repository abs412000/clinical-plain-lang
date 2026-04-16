"""
converter.py
------------
Core logic for converting clinical trial / medical documents into
plain language summaries using the Google Gemini API.

Supports three audience levels:
  - patient     : informed patient with disease knowledge, no clinical training
  - public      : general adult public, no medical background
  - caregiver   : lay family caregiver, needs practical + emotional framing

Regulatory alignment:
  EU CTR 536/2014 Art.37 (plain language summaries)
  FDA 21 CFR 50 Subpart B (informed consent readability)
  ICH E6(R2) GCP plain language principles
"""

import os
import re
import json
from google import genai
from google.genai import types

# ── Audience-specific system prompts ──────────────────────────────────────────

SYSTEM_PROMPTS = {
    "patient": """You are a plain language medical writer helping an informed patient understand
clinical research documents. The patient has their own diagnosis and understands their disease
broadly but has no formal medical training.

Your output must:
- Use plain English (target Flesch reading ease 60–70, Flesch-Kincaid Grade 8 or below)
- Define every medical term the first time it is used (e.g., "metastasis (spread of cancer)")
- Use active voice wherever possible
- Replace jargon with everyday equivalents where meaning is preserved
- Organise with clear headings: What was studied | What happened | What this means for you
- Be factually accurate — do not simplify away clinical meaning
- Avoid false reassurance or alarmist language
- Length: comprehensive but concise (300–500 words for a typical trial summary)""",

    "public": """You are a plain language medical writer producing a general public summary of
clinical research. Your reader has no medical background and may have encountered this document
through a hospital website, news article, or patient advocacy group.

Your output must:
- Use very plain English (target Flesch reading ease 70+, Flesch-Kincaid Grade 6 or below)
- Avoid ALL medical jargon — if a technical term is unavoidable, explain it in brackets
- Use short sentences (aim for average 15 words per sentence)
- Use analogies or everyday comparisons to explain complex concepts
- Organise with clear headings: What was this research about | What did researchers find | Why does this matter
- Do not include statistics unless they can be expressed in natural frequencies (e.g., "3 in 10 people")
- Length: brief and accessible (200–350 words)""",

    "caregiver": """You are a plain language medical writer helping a family caregiver understand
clinical research about a condition affecting their loved one. The caregiver is not medically
trained but is deeply invested and will use this to have conversations with doctors.

Your output must:
- Use warm, supportive but factual language
- Explain what the research means practically for day-to-day care decisions
- Highlight what questions the caregiver should ask their medical team
- Define medical terms simply on first use
- Organise with clear headings: What this research looked at | What it found | What to ask the doctor
- Flag any findings about side effects, quality of life, or patient burden clearly
- Length: practical and actionable (250–400 words)"""
}

# ── Main converter class ──────────────────────────────────────────────────────

class ClinicalPlainLangConverter:
    """
    Converts dense clinical/medical text into plain language summaries.

    Usage:
        converter = ClinicalPlainLangConverter()
        result = converter.convert(text, audience="patient")
        print(result["plain_text"])
        print(result["readability"])
    """

    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")

        # New SDK: instantiate a client (replaces genai.configure())
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.temperature = 0.3        # Lower = more consistent & factual
        self.max_output_tokens = 2048

    def convert(self, clinical_text: str, audience: str = "patient") -> dict:
        """
        Convert clinical text to plain language for a given audience.

        Args:
            clinical_text: The source clinical / medical document text
            audience: One of "patient", "public", "caregiver"

        Returns:
            dict with keys:
              plain_text      - the plain language output
              audience        - audience level used
              source_stats    - readability of input
              output_stats    - readability of output
              improvement     - FK grade reduction
        """
        if audience not in SYSTEM_PROMPTS:
            raise ValueError(f"audience must be one of: {list(SYSTEM_PROMPTS.keys())}")

        system = SYSTEM_PROMPTS[audience]

        # Combine system + user prompt
        user_prompt = f"""Please convert the following clinical document into a plain language summary 
for a {audience} audience. Follow all the guidelines in your instructions exactly.

--- CLINICAL DOCUMENT START ---
{clinical_text}
--- CLINICAL DOCUMENT END ---

Produce the plain language summary now. Use clear headings as instructed."""

        # API call using new google.genai SDK
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            ),
        )

        plain_text = response.text

        # Readability scoring (unchanged)
        source_stats = readability_stats(clinical_text)
        output_stats = readability_stats(plain_text)
        improvement = round(source_stats["fk_grade"] - output_stats["fk_grade"], 1)

        return {
            "plain_text": plain_text,
            "audience": audience,
            "source_stats": source_stats,
            "output_stats": output_stats,
            "improvement": improvement,
            "model": self.model,
            "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else None,
            "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else None,
        }
    def convert_all_audiences(self, clinical_text: str) -> dict:
        """
        Run conversion for all three audience levels in one call.
        Returns a dict keyed by audience name.
        """
        results = {}
        for audience in SYSTEM_PROMPTS:
            results[audience] = self.convert(clinical_text, audience=audience)
        return results


# ── Readability scoring ───────────────────────────────────────────────────────

def count_syllables(word: str) -> int:
    """Approximate syllable count for a single word."""
    word = word.lower().strip(".,;:!?\"'()-")
    if not word:
        return 0
    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    # Adjust for silent e
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def readability_stats(text: str) -> dict:
    """
    Compute Flesch Reading Ease and Flesch-Kincaid Grade Level.

    Flesch Reading Ease:
      206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
      90-100 = very easy, 60-70 = standard, 30-50 = difficult, <30 = very difficult

    FK Grade Level:
      0.39*(words/sentences) + 11.8*(syllables/words) - 15.59
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    num_sentences = max(len(sentences), 1)

    words = re.findall(r'\b[a-zA-Z]+\b', text)
    num_words = max(len(words), 1)

    num_syllables = sum(count_syllables(w) for w in words)

    asl = num_words / num_sentences          # Average sentence length
    asw = num_syllables / num_words          # Average syllables per word

    fre = round(206.835 - (1.015 * asl) - (84.6 * asw), 1)
    fk_grade = round(0.39 * asl + 11.8 * asw - 15.59, 1)

    # SMOG estimate (requires 30+ sentences; best effort otherwise)
    if num_sentences >= 30:
        poly_words = sum(1 for w in words if count_syllables(w) >= 3)
        smog = round(1.0430 * (poly_words * (30 / num_sentences)) ** 0.5 + 3.1291, 1)
    else:
        poly_words = sum(1 for w in words if count_syllables(w) >= 3)
        smog = round(3.0 + (poly_words ** 0.5), 1)  # simplified

    return {
        "word_count": num_words,
        "sentence_count": num_sentences,
        "flesch_reading_ease": fre,
        "fk_grade": fk_grade,
        "smog_grade": smog,
        "avg_sentence_length": round(asl, 1),
        "avg_syllables_per_word": round(asw, 2),
    }


def format_report(result: dict) -> str:
    """Format a conversion result as a human-readable report."""
    src = result["source_stats"]
    out = result["output_stats"]

    lines = [
        f"\n{'='*60}",
        f"  PLAIN LANGUAGE CONVERSION REPORT",
        f"  Audience: {result['audience'].upper()}",
        f"{'='*60}",
        f"\n── Readability Comparison ──────────────────────────────",
        f"  {'Metric':<30} {'Source':>8}  {'Output':>8}",
        f"  {'-'*46}",
        f"  {'Flesch Reading Ease':<30} {src['flesch_reading_ease']:>8}  {out['flesch_reading_ease']:>8}",
        f"  {'FK Grade Level':<30} {src['fk_grade']:>8}  {out['fk_grade']:>8}",
        f"  {'SMOG Grade':<30} {src['smog_grade']:>8}  {out['smog_grade']:>8}",
        f"  {'Word Count':<30} {src['word_count']:>8}  {out['word_count']:>8}",
        f"  {'Avg Sentence Length':<30} {src['avg_sentence_length']:>8}  {out['avg_sentence_length']:>8}",
        f"\n  FK Grade Improvement: {result['improvement']:+.1f} grade levels",
        f"\n── Plain Language Output ───────────────────────────────\n",
        result["plain_text"],
        f"\n{'='*60}\n"
    ]
    return "\n".join(lines)