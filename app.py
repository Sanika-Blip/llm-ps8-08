import json
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()
MODEL = "gemini-2.5-flash"

PROMPT = """You are an expert e-commerce copywriter.
Write a listing for this product.

Product name: {name}
Features: {features}
Target audience: {audience}
Tone: {tone}

Return ONLY valid JSON (no markdown fences) with exactly these keys:
"title": a catchy listing title (max 12 words),
"benefits": a list of exactly 3 short benefit bullets (benefits for the buyer, not just features),
"description": a description of EXACTLY 60 words.
Use only the features given; do not invent specifications."""


def generate(name, features, audience, tone, retry=True):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = PROMPT.format(name=name, features=features, audience=audience, tone=tone)
    resp = client.models.generate_content(model=MODEL, contents=prompt)
    text = resp.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if retry:
            return generate(name, features, audience, tone, retry=False)
        raise


st.set_page_config(page_title="Product Description Writer", page_icon="🛍️")
st.title("🛍️ Product Description Writer")
st.caption("Generate a title, 3 benefit bullets and a 60-word description.")

with st.form("product_form"):
    name = st.text_input("Product name", placeholder="e.g. AquaPure Steel Water Bottle")
    features = st.text_area(
        "Key features (one per line or comma separated)",
        placeholder="1L capacity, keeps cold 24h, leak-proof lid, BPA free",
    )
    audience = st.text_input("Target audience", placeholder="e.g. college students, gym-goers")
    tone = st.selectbox("Tone", ["Friendly", "Professional", "Luxury", "Playful"])
    submitted = st.form_submit_button("Generate")

if submitted:
    if not (name.strip() and features.strip() and audience.strip()):
        st.warning("Please fill in the product name, features and audience.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("GEMINI_API_KEY not found. Add it to your .env file.")
    else:
        with st.spinner("Writing your listing..."):
            try:
                out = generate(name, features, audience, tone)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()
        st.subheader(out["title"])
        for b in out["benefits"]:
            st.markdown(f"- ✅ {b}")
        st.write(out["description"])
        st.caption(f"Description length: {len(out['description'].split())} words")
        full = (
            f"{out['title']}\n\n"
            + "\n".join(f"- {b}" for b in out["benefits"])
            + f"\n\n{out['description']}"
        )
        st.download_button("Download as .txt", full, file_name="product_listing.txt")
