"""Render the operator question journey in Streamlit."""

import streamlit as st

from support_desk.domain import AnswerDraft
from support_desk.ui.client import (
    ApiQuestionFailure,
    InvalidApiResponse,
    QuestionApi,
    QuestionApiUnavailable,
)


def render_app(client: QuestionApi, operator_email: str | None = None) -> None:
    """Render the question form and latest unreviewed draft.

    Args:
        client:
            Typed question API client.
        operator_email:
            Authenticated operator email shown for session awareness.
    """

    st.set_page_config(page_title="Support Desk", page_icon="💬")
    st.title("Support Desk")
    st.caption("Draft Boardlight product guidance from authored evidence.")
    if operator_email is not None:
        st.sidebar.caption(f"Signed in as {operator_email}")
        if st.sidebar.button("Sign out"):
            st.logout()

    with st.form("question-form"):
        question = st.text_area(
            "Product question",
            max_chars=2048,
            placeholder="How many boards can a Free workspace have?",
        )
        submitted = st.form_submit_button("Generate draft", type="primary")

    if not submitted:
        return
    if not question.strip():
        st.warning("Enter a product question before generating a draft.")
        return

    try:
        with st.spinner("Generating an evidence-based draft…"):
            draft = client.ask(question.strip())
    except ApiQuestionFailure as exc:
        st.error(exc.message)
        return
    except QuestionApiUnavailable:
        st.error("The Support Desk API is unavailable. Check it and try again.")
        return
    except InvalidApiResponse:
        st.error("The Support Desk API returned an unexpected response.")
        return

    _render_draft(draft)


def _render_draft(draft: AnswerDraft) -> None:
    """Display an answer draft and its source identities.

    Args:
        draft:
            Valid unreviewed answer draft.
    """

    st.warning("Unreviewed draft — verify the guidance before using it.")
    st.subheader("Draft")
    if draft.status == "insufficient_evidence":
        st.info(draft.answer)
    else:
        st.write(draft.answer)

    st.subheader("Evidence")
    if not draft.evidence:
        st.caption("No supporting source was identified.")
        return

    for evidence in draft.evidence:
        st.markdown(f"- `{evidence.source_id.value}` · version `{evidence.version}`")
