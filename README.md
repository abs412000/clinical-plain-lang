# clinical-plain-lang

**AI-powered plain language conversion for clinical and medical documents.**

Convert dense clinical trial results, discharge summaries, informed consent forms, and oncology reports into accessible plain language for patients, the general public, or family caregivers — with built-in readability scoring.

Built using the [Anthropic Claude API](https://www.anthropic.com/api), with regulatory alignment to:
- EU CTR 536/2014 Article 37 (plain language summaries for clinical trials)
- FDA 21 CFR 50 Subpart B (informed consent readability)
- ICH E6(R2) GCP plain language principles

---

## Motivation

This project was built to solve a problem I experienced personally.

Over a 12-month period, three members of my family were simultaneously diagnosed with advanced cancers: metastatic triple-negative breast cancer, metastatic prostate adenocarcinoma (low-PSA phenotype), and recurrent head and neck squamous cell carcinoma. I became the person responsible for understanding the clinical documents — PET/MRI reports, oncology notes, biomarker results, treatment trial data — and translating them into decisions the family could act on.

The gap between what doctors write and what patients and caregivers can understand is enormous. Clinical documents are written for clinicians. Even an educated, motivated layperson will struggle with hazard ratios, ECOG scores, and immunohistochemistry findings. That struggle has real consequences: patients make decisions without understanding their options, caregivers miss critical side effect signals, and families cannot effectively advocate at the bedside.

This tool addresses one part of that problem: making clinical documents readable.

---

## Features

- **Three audience levels** with distinct prompt strategies:
  - `patient` — informed patient with disease knowledge, no clinical training (FK Grade ≤8)
  - `public` — general adult public, no medical background (FK Grade ≤6)
  - `caregiver` — family caregiver needing practical framing + doctor questions

- **Readability scoring** before and after conversion:
  - Flesch Reading Ease
  - Flesch-Kincaid Grade Level
  - SMOG Grade
  - Average sentence length / syllables per word

- **Three interfaces**:
  - Python API (import and use in your own code)
  - CLI (command line, supports stdin/file/JSON output)
  - Streamlit web app (browser-based, shareable)

---

## Quickstart

### Install

```bash
git clone https://github.com/abhishekshukla-dev/clinical-plain-lang.git
cd clinical-plain-lang
pip install -r requirements.txt
```

### Set your API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Python API

```python
from src.converter import ClinicalPlainLangConverter

converter = ClinicalPlainLangConverter()

result = converter.convert(
    clinical_text="A phase III, randomised, double-blind trial...",
    audience="patient"   # or "public" or "caregiver"
)

print(result["plain_text"])
print(f"FK Grade: {result['source_stats']['fk_grade']} → {result['output_stats']['fk_grade']}")
print(f"Improvement: {result['improvement']:+.1f} grade levels")
```

### CLI

```bash
# Convert a file
python cli.py --file report.txt --audience patient

# Convert for all audiences
python cli.py --file report.txt --all-audiences

# Save JSON output
python cli.py --file report.txt --audience public --output results.json

# Pipe from stdin
cat report.txt | python cli.py --stdin --audience caregiver
```

### Streamlit web app

```bash
streamlit run app.py
```

---

## Example output

**Input (FK Grade 18.4, Flesch 14.2):**
> The randomised, double-blind, placebo-controlled multicentre trial demonstrated statistically significant improvement in progression-free survival (PFS) with pembrolizumab plus chemotherapy versus chemotherapy alone (HR 0.65; 95% CI, 0.48–0.88; p=0.003), with concomitant pathological complete response rates of 64.8% versus 51.2%.

**Output — patient audience (FK Grade 7.1, Flesch 67.8):**
> **What was studied**  
> Researchers tested whether adding a drug called pembrolizumab (an immunotherapy — a medicine that helps your immune system fight cancer) to standard chemotherapy worked better than chemotherapy alone.
>
> **What happened**  
> Patients who received pembrolizumab plus chemotherapy were 35% less likely to see their cancer grow or spread compared with those who had chemotherapy alone. In practical terms: before surgery, 65 in 100 patients who received pembrolizumab had no detectable cancer remaining, compared with 51 in 100 who received chemotherapy alone.
>
> **What this means for you**  
> Adding pembrolizumab to chemotherapy may give your cancer less chance to grow before surgery. Talk to your oncologist about whether this combination is suitable for your cancer type and stage.

---

## Project structure

```
clinical-plain-lang/
├── src/
│   └── converter.py       # Core converter class + readability scoring
├── examples/
│   └── examples.py        # Sample clinical texts for testing
├── tests/
│   └── test_readability.py  # Unit tests (no API key required)
├── cli.py                 # Command-line interface
├── app.py                 # Streamlit web app
├── requirements.txt
└── README.md
```

---

## Requirements

```
anthropic>=0.25.0
streamlit>=1.32.0
```

---

## Limitations and responsible use

- This tool is for **informational purposes only**. Plain language summaries produced by this tool do not constitute medical advice.
- Always review AI-generated plain language output before sharing with patients or caregivers. Human expert review is required for regulatory submissions.
- The tool does not store or log clinical input. Your data is sent directly to the Anthropic API under their [privacy policy](https://www.anthropic.com/privacy).
- For regulatory plain language submissions (EU CTR, FDA), output must be reviewed by a qualified plain language specialist.

---

## Roadmap

- [ ] PDF input support (clinical PDFs → text → plain language)
- [ ] Batch processing for multiple documents
- [ ] Section-level conversion (convert specific sections, e.g., safety only)
- [ ] Glossary generation (extract and define all medical terms used)
- [ ] Side-by-side diff view in Streamlit app
- [ ] Multi-language output support

---

## Author

**Abhishek Shukla** — shukla11.abhi@gmail.com  
Operations & Technology Leader transitioning into AI-enabled clinical communications.

This project grew directly from personal experience navigating complex oncology documentation for three family members simultaneously. It represents the intersection of systems thinking, backend engineering, and hard-won clinical domain understanding.

---

## License

MIT
