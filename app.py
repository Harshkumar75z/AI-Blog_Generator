import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

from graph import blog_graph
from state import BlogState

load_dotenv()

# Page Configuration

st.set_page_config(
    page_title="AI Blog Generator",
    page_icon="✍️",
    layout="wide"
)

# Custom CSS

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #777;
    font-size: 17px;
    margin-bottom: 35px;
}

.footer {
    text-align: center;
    color: #888;
    margin-top: 40px;
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)

# Header

st.markdown(
    '<div class="main-title">✍️ AI Blog Generator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Research → Human Review → Write → Human Review → Edit</div>',
    unsafe_allow_html=True
)

# Session State

if "graph" not in st.session_state:
    st.session_state.graph = blog_graph()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "blog_session_1"

if "started" not in st.session_state:
    st.session_state.started = False

if "current_stage" not in st.session_state:
    st.session_state.current_stage = None

if "result" not in st.session_state:
    st.session_state.result = None


# Sidebar

with st.sidebar:

    st.header("Blog Settings")

    st.divider()

    topic = st.text_input(
        "Blog Topic",
        placeholder="Example: Future of Artificial Intelligence"
    )

    audience = st.text_input(
        "Target Audience",
        placeholder="Example: College students"
    )

    temperature = st.slider(
        "Creativity",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1
    )

    st.divider()

    generate_blog = st.button(
        "Generate Blog",
        type="primary",
        use_container_width=True
    )

# Config

config = {
    "configurable": {
        "thread_id": st.session_state.thread_id
    }
}

# Start Blog Generation

if generate_blog:

    if not topic.strip():

        st.warning("Please enter a blog topic.")
        st.stop()

    if not audience.strip():

        st.warning("Please enter the target audience.")
        st.stop()

    # Reset old session
    st.session_state.thread_id = f"blog_{id(topic)}"

    config = {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }

    initial_state = BlogState(
        topic=topic,
        audience=audience,
        research="",
        research_feedback="",
        draft="",
        draft_feedback="",
        final_blog="",
        revision_count=0
    )

    try:

        result = st.session_state.graph.invoke(
            initial_state,
            config=config
        )

        st.session_state.result = result

        # Check if graph stopped at human review
        state = st.session_state.graph.get_state(config)

        if state.next:

            st.session_state.current_stage = state.next[0]

        else:

            st.session_state.current_stage = None

        st.session_state.started = True

        st.rerun()

    except Exception as e:

        st.error(f"Error: {e}")


# HUMAN REVIEW - RESEARCH

if st.session_state.started:

    state_snapshot = st.session_state.graph.get_state(config)

    if state_snapshot.next:

        current_node = state_snapshot.next[0]
        # Research Review

        if current_node == "review_research":

            st.divider()

            st.subheader("🧑 Human Review - Research")

            research = state_snapshot.values.get(
                "research",
                ""
            )

            st.markdown("### Research Outline")

            st.markdown(research)

            st.divider()

            st.markdown(
                "**Review the research before the Writer Agent continues.**"
            )

            research_action = st.radio(
                "What would you like to do?",
                [
                    "Approve Research",
                    "Request Changes"
                ],
                key="research_action"
            )

            if research_action == "Request Changes":

                research_feedback = st.text_area(
                    "What should be changed?",
                    placeholder="Example: Add more points about AI in education.",
                    key="research_feedback"
                )

            else:

                research_feedback = ""

            if st.button(
                "Continue",
                type="primary",
                key="research_continue"
            ):

                if research_action == "Approve Research":

                    human_response = {
                        "action": "approve",
                        "feedback": ""
                    }

                else:

                    if not research_feedback.strip():

                        st.warning(
                            "Please enter feedback before requesting changes."
                        )

                        st.stop()

                    human_response = {
                        "action": "revise",
                        "feedback": research_feedback
                    }

                try:

                    result = st.session_state.graph.invoke(
                        Command(resume=human_response),
                        config=config
                    )

                    st.session_state.result = result

                    state = st.session_state.graph.get_state(
                        config
                    )

                    if state.next:

                        st.session_state.current_stage = state.next[0]

                    else:

                        st.session_state.current_stage = None

                    st.rerun()

                except Exception as e:

                    st.error(f"Error: {e}")

        # Draft Review

        elif current_node == "review_draft":

            st.divider()

            st.subheader(" Human Review - Draft")

            draft = state_snapshot.values.get(
                "draft",
                ""
            )

            st.markdown("### Initial Blog Draft")

            st.markdown(draft)

            st.divider()

            st.markdown(
                "**Review the draft before the Editor Agent publishes it.**"
            )

            draft_action = st.radio(
                "What would you like to do?",
                [
                    "Approve Draft",
                    "Request Changes"
                ],
                key="draft_action"
            )

            if draft_action == "Request Changes":

                draft_feedback = st.text_area(
                    "What should be changed?",
                    placeholder="Example: Make the introduction shorter and add a practical example.",
                    key="draft_feedback"
                )

            else:

                draft_feedback = ""

            if st.button(
                "Continue",
                type="primary",
                key="draft_continue"
            ):

                if draft_action == "Approve Draft":

                    human_response = {
                        "action": "approve",
                        "feedback": ""
                    }

                else:

                    if not draft_feedback.strip():

                        st.warning(
                            "Please enter feedback before requesting changes."
                        )

                        st.stop()

                    human_response = {
                        "action": "revise",
                        "feedback": draft_feedback
                    }

                try:

                    result = st.session_state.graph.invoke(
                        Command(resume=human_response),
                        config=config
                    )

                    st.session_state.result = result

                    state = st.session_state.graph.get_state(
                        config
                    )

                    if state.next:

                        st.session_state.current_stage = state.next[0]

                    else:

                        st.session_state.current_stage = None

                    st.rerun()

                except Exception as e:

                    st.error(f"Error: {e}")

# FINAL BLOG

if st.session_state.started:

    state_snapshot = st.session_state.graph.get_state(config)

    final_blog = state_snapshot.values.get(
        "final_blog",
        ""
    )

    if final_blog:

        st.divider()

        st.subheader("Generated Blog")

        tab1, tab2, tab3 = st.tabs([
            "Research",
            "Draft",
            "Final Blog"
        ])

        # Research

        with tab1:

            st.markdown("### Research Outline")

            st.markdown(
                state_snapshot.values.get(
                    "research",
                    ""
                )
            )

        # Draft

        with tab2:

            st.markdown("### Initial Draft")

            st.markdown(
                state_snapshot.values.get(
                    "draft",
                    ""
                )
            )

        # Final

        with tab3:

            st.markdown("### Final Published Blog")

            st.markdown(final_blog)

            st.divider()

            st.download_button(
                label="Download Blog",
                data=final_blog,
                file_name="generated_blog.md",
                mime="text/markdown",
                use_container_width=True
            )


# Footer

st.markdown(
    '<div class="footer">Built with Streamlit + LangChain + Gemini AI</div>',
    unsafe_allow_html=True
)
