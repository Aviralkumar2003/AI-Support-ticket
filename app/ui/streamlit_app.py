import uuid

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Support Ticket Resolution", layout="centered")
st.title("AI Support Ticket Resolution")

# session_id is tracked internally so multi-turn context is preserved, but it is
# never surfaced to the user — session lifecycle is entirely backend-managed.
if "session_id" not in st.session_state:
    st.session_state.session_id = None

with st.form("ticket_form"):
    message = st.text_area("Support message")
    submitted = st.form_submit_button("Submit ticket")

if submitted:
    ticket_id = f"TICKET-{uuid.uuid4().hex[:8]}"

    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/v1/support/tickets/process",
            json={"session_id": st.session_state.session_id, "ticket_id": ticket_id, "message": message},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.RequestException as e:
        st.error(f"Failed to reach the API: {e}")
        result = None

    if result:
        st.session_state.session_id = result["session_id"]

        st.subheader("Response")
        st.write(result["response"])
        st.caption(f"Category: {result['category']} · Urgency: {result['urgency']} · Sentiment: {result['sentiment']}")

        st.subheader("Evaluation")
        col1, col2, col3 = st.columns(3)
        col1.metric("Judge score", result["judge_score"])
        col2.metric("Judge decision", result["judge_decision"])
        col3.metric("Retry count", result["retry_count"])
        st.write(f"**Judge reason:** {result['judge_feedback'] or 'No reason provided'}")
        st.write(f"Selected FAQ IDs: {result['selected_faq_ids'] or 'None'}")

        st.subheader("Escalation status")
        if result["human_review_required"]:
            st.error(f"ESCALATED — status: {result['status']}. This ticket requires human review.")
            st.write(f"**Escalation reason:** {result['escalation_reason'] or 'Not specified'}")
        else:
            st.info(f"Status: {result['status']}")

if st.session_state.session_id:
    with st.expander("Conversation history"):
        try:
            history_resp = requests.get(
                f"{API_BASE_URL}/api/v1/support/sessions/{st.session_state.session_id}", timeout=30
            )
            if history_resp.status_code == 404:
                st.write("No conversation history yet.")
            else:
                history_resp.raise_for_status()
                messages = history_resp.json().get("messages", [])
                for msg in messages:
                    st.markdown(f"**{msg['role'].capitalize()}:** {msg['content']}")
        except requests.RequestException as e:
            st.error(f"Failed to fetch conversation history: {e}")
