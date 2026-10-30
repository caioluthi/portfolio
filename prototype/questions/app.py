"""Local demo page for the question layer, used for the recorded walkthrough.

  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import tools
from ask import DEFAULT_MODEL, ask, load_env

EXAMPLES = [
    "Which contracts are almost due, expiring in the next 30 days, while still performing below target?",
    "Which region has the most money at risk?",
    "Where do watches sell best?",
    "Should we move the unsold items on CT-02063 to a live auction?",
    "How are we doing?",
]
BADGES = {"answer": ("Answered", "green"), "decline": ("Declined", "orange"),
          "clarify": ("Needs clarifying", "blue"), "error": ("Error", "red")}

load_env()
st.set_page_config(page_title="Second Avenue · Ask the contract book", layout="centered")
st.title("Ask the contract book")
st.caption(f"Second Avenue Risk contracts · governed metrics as of {tools.today()}")

with st.sidebar:
    model = st.selectbox("Model", [DEFAULT_MODEL, "claude-haiku-5-5"])
    st.markdown("Answers come only from six governed tools over the Contracts data product. "
                "Questions outside those metrics are declined.")

if "history" not in st.session_state:
    st.session_state.history = []

st.write("Try one:")
for example in EXAMPLES:
    if st.button(example, use_container_width=True):
        st.session_state.pending = example

question = st.chat_input("Ask about contracts, exposure or channels")
question = question or st.session_state.pop("pending", None)
if question:
    with st.spinner("Checking the governed metrics"):
        st.session_state.history.insert(0, (question, ask(question, model)))

for asked, result in st.session_state.history:
    with st.chat_message("user"):
        st.write(asked)
    with st.chat_message("assistant"):
        label, color = BADGES.get(result["behavior"], ("?", "gray"))
        st.markdown(f":{color}-badge[{label}]")
        st.markdown(result["text"])
        with st.expander("How this was answered"):
            if not result["tools_used"]:
                st.write("No data tool was called.")
            for call in result["tools_used"]:
                filters = ", ".join(f"{k}={v}" for k, v in call["input"].items()) or "no filters"
                st.markdown(f"- `{call['tool']}` ({filters}) → {call['rows']} rows")
            st.caption(f"{result['model']} · {result['usage']['input_tokens']:,} tokens in, "
                       f"{result['usage']['output_tokens']:,} out")
