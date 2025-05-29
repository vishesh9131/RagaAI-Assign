import streamlit as st
import os
from language_agent import LanguageAgent

# Set the API key
os.environ.setdefault("MISTRAL_API_KEY", "NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")

agent = LanguageAgent(model_name="open-mistral-nemo", api_key="NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")

st.set_page_config(page_title="Language Agent", layout="centered")

st.title("📝 Language Agent")

analysis_type = st.selectbox("Choose action", ["Summarize", "Explain"], index=0)

input_text = st.text_area("Input Text", height=250)

if analysis_type == "Summarize":
    max_words = st.slider("Maximum words in summary", min_value=50, max_value=300, value=150)
    if st.button("Generate Summary") and input_text.strip():
        with st.spinner("Generating summary..."):
            summary = agent.summarize(input_text, max_words=max_words)
        st.subheader("Summary")
        st.success(summary)
elif analysis_type == "Explain":
    audience = st.text_input("Audience (e.g., non-expert, student)", value="non-expert")
    if st.button("Generate Explanation") and input_text.strip():
        with st.spinner("Generating explanation..."):
            explanation = agent.explain(input_text, target_audience=audience)
        st.subheader("Explanation")
        st.info(explanation) 