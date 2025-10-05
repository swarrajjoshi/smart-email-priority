import pandas as pd
import streamlit as st

from src.predict import EmailPriorityModel
from src.action_extractor import extract_actions
from src.utils import clean_text_basic

st.set_page_config(page_title="Smart Email Priority Sorter", layout="wide")
st.title("📧 Smart Email Priority Sorter")
import os, subprocess, sys, streamlit as st

MODEL_PATH = "models/email_priority.pkl"
if not os.path.exists(MODEL_PATH):
    st.warning("Model not found. Training once…")
    try:
        subprocess.check_call([sys.executable, "-m", "src.train_classifier"])
    except Exception as e:
        st.error(f"Auto-training failed: {e}")

model = EmailPriorityModel()

st.sidebar.header("Data Source")
source = st.sidebar.radio("Choose input", ["Sample CSV", "Paste Text"], index=0)

if source == "Sample CSV":
    df = pd.read_csv("data/sample_emails.csv")
else:
    st.sidebar.write("Enter a mock email:")
    subj = st.sidebar.text_input("Subject", "Submit report by EOD")
    body = st.sidebar.text_area("Body", "Please send the Q3 sales report by 5pm today.")
    df = pd.DataFrame([{"id": 1, "from_email": "demo@demo.com", "subject": subj, "body": body, "label": "unknown"}])

# Predict priorities
pred_labels, probs = model.predict_batch(df)
df["pred_priority"] = pred_labels
df["pred_confidence"] = [round(p, 3) for p in probs]
df["action"] = ""
df["deadline"] = ""

for i, row in df.iterrows():
    acts = extract_actions(clean_text_basic(f"{row.subject} {row.body}"))
    df.at[i, "action"] = acts["action"]
    df.at[i, "deadline"] = acts["deadline"]

# Show columns by priority
cols = st.columns(3)
prio_order = ["high", "medium", "low"]

for idx, prio in enumerate(prio_order):
    with cols[idx]:
        st.subheader({"high":"🔴 Urgent","medium":"🟡 Important","low":"🟢 Normal"}[prio])
        sub = df[df["pred_priority"] == prio][["from_email","subject","action","deadline","pred_confidence"]]
        for _, r in sub.iterrows():
            st.markdown(f"**{r['subject']}**")
            st.caption(r["from_email"])
            if r["action"] or r["deadline"]:
                st.write(f"- Action: `{r['action'] or '-'}`  |  Deadline: `{r['deadline'] or '-'}`")
            st.progress(min(max(r["pred_confidence"], 0.0), 1.0))
            st.divider()

st.download_button("⬇️ Export results (CSV)", data=df.to_csv(index=False), file_name="email_priorities.csv", mime="text/csv")
