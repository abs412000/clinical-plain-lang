"""
app.py
------
Streamlit web interface for clinical-plain-lang.

Run with:
    streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
from converter import ClinicalPlainLangConverter, readability_stats

# ── Page config ──
st.set_page_config(
    page_title="Clinical Plain Language Converter",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .metric-box {
        background: #f0f4f8;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-label { font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.6rem; font-weight: bold; color: #1B3A6B; }
    .metric-delta { font-size: 0.85rem; }
    .plain-output {
        background: #fafbfe;
        border: 1px solid #e0e6ee;
        border-radius: 8px;
        padding: 20px;
        line-height: 1.7;
    }
    h1 { color: #1B3A6B; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.title("🏥 Clinical Plain Language Converter")
st.markdown(
    "Convert clinical trial documents, medical reports, and research summaries into "
    "accessible plain language for patients, the public, or caregivers."
)
st.markdown("---")

# ── Sidebar: configuration ──
with st.sidebar:
    st.header("⚙️ Settings")

    api_key = st.text_input(
        "GEMINI API Key",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Your Gemini API key. Get one at console.gemini.com"
    )

    audience = st.selectbox(
        "Target Audience",
        options=["patient", "public", "caregiver"],
        format_func=lambda x: {
            "patient": "👤 Informed Patient",
            "public": "🌐 General Public",
            "caregiver": "❤️ Family Caregiver"
        }[x],
        help="Choose who will read this plain language summary"
    )

    audience_desc = {
        "patient": "Has their diagnosis; understands their disease broadly but no clinical training. Target: FK Grade 8, Flesch 60–70.",
        "public": "No medical background at all. Target: FK Grade 6, Flesch 70+.",
        "caregiver": "Lay family caregiver. Practical framing + suggested questions for their medical team."
    }
    st.info(audience_desc[audience])

    st.markdown("---")
    st.markdown("**Regulatory alignment:**")
    st.markdown("- EU CTR 536/2014 Art.37")
    st.markdown("- FDA 21 CFR 50 Subpart B")
    st.markdown("- ICH E6(R2) GCP")

    st.markdown("---")
    st.markdown(
        "Built by [Abhishek Shukla](mailto:shukla11.abhi@gmail.com)  \n"
        "[GitHub →](https://github.com/abhishekshukla-dev/clinical-plain-lang)"
    )

# ── Main area ──
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📄 Clinical Document Input")
    clinical_text = st.text_area(
        "Paste clinical text here",
        height=420,
        placeholder=(
            "Paste any clinical document here: a trial result, CSR excerpt, "
            "informed consent form, discharge summary, or oncology report...\n\n"
            "Example: 'A phase III, randomised, double-blind, placebo-controlled trial "
            "evaluated the efficacy of pembrolizumab versus placebo in patients with "
            "recurrent or metastatic head and neck squamous cell carcinoma...'"
        ),
        label_visibility="collapsed"
    )

    if clinical_text:
        src_stats = readability_stats(clinical_text)
        st.markdown("**Source document readability:**")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Flesch Ease", src_stats["flesch_reading_ease"], help="Higher = easier. Target for plain language: 60+")
        mc2.metric("FK Grade", src_stats["fk_grade"], help="US school grade level. Target: 8 or below")
        mc3.metric("SMOG Grade", src_stats["smog_grade"])
        mc4.metric("Words", src_stats["word_count"])

    convert_btn = st.button(
        f"✨ Convert to Plain Language ({audience})",
        type="primary",
        disabled=not clinical_text or not api_key
    )

with col_right:
    st.subheader("🟢 Plain Language Output")

    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    if convert_btn:
        if not api_key:
            st.error("Please enter your Gemini API key in the sidebar.")
        elif not clinical_text.strip():
            st.error("Please paste some clinical text to convert.")
        else:
            with st.spinner("Converting..."):
                try:
                    converter = ClinicalPlainLangConverter(api_key=api_key)
                    result = converter.convert(clinical_text, audience=audience)
                    st.session_state.last_result = result
                except Exception as e:
                    st.error(f"Conversion failed: {e}")

    if st.session_state.last_result:
        result = st.session_state.last_result
        out = result["output_stats"]
        src = result["source_stats"]

        # Readability improvement metrics
        m1, m2, m3, m4 = st.columns(4)
        fre_delta = round(out["flesch_reading_ease"] - src["flesch_reading_ease"], 1)
        fk_delta = round(out["fk_grade"] - src["fk_grade"], 1)
        m1.metric("Flesch Ease", out["flesch_reading_ease"], delta=f"{fre_delta:+.1f}")
        m2.metric("FK Grade", out["fk_grade"], delta=f"{fk_delta:+.1f}", delta_color="inverse")
        m3.metric("SMOG Grade", out["smog_grade"])
        m4.metric("Words", out["word_count"])

        st.markdown("---")
        st.markdown(
            f'<div class="plain-output">{result["plain_text"].replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "⬇️ Download Plain Text",
                data=result["plain_text"],
                file_name=f"plain_language_{audience}.txt",
                mime="text/plain"
            )
        with col_dl2:
            import json
            st.download_button(
                "⬇️ Download Full Report (JSON)",
                data=json.dumps(result, indent=2),
                file_name=f"conversion_report_{audience}.json",
                mime="application/json"
            )
    else:
        st.markdown(
            """
            <div style="height:420px; display:flex; align-items:center; justify-content:center;
                        color:#aaa; font-size:1.1rem; border:2px dashed #e0e6ee; border-radius:8px;">
                Your plain language summary will appear here
            </div>
            """,
            unsafe_allow_html=True
        )
