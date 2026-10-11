from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt
from typing import Literal

from state import BlogState
from agent import get_llm, researcher_agent, writer_agent, editor_agent

MAX_REVISION = 3


def researcher_node(state: BlogState):
    llm = get_llm()

    research_data = researcher_agent(
        llm=llm,
        topic=state.topic,
        audience=state.audience,
        feedback=state.research_feedback
    )

    return {
        "research": research_data,
        "research_feedback": ""
    }


def human_review_research_node(state: BlogState):
    decision = interrupt({
        "stage": "researcher_review",
        "research": state.research,
        "instructions": "Approve the research or provide feedback."
    })

    if isinstance(decision, dict):
        action = decision.get("action", "approve")
        feedback = decision.get("feedback", "")
    else:
        text = str(decision).strip()
        action = "approve" if text.lower() in [
            "approve", "approved", "ok", "yes", "process"
        ] else "revise"
        feedback = "" if action == "approve" else text

    return {
        "research_feedback": feedback if action == "revise" else ""
    }


def writer_node(state: BlogState):
    llm = get_llm()

    draft_data = writer_agent(
        llm=llm,
        topic=state.topic,
        audience=state.audience,
        research=state.research,
        feedback=state.draft_feedback
    )

    if not draft_data or not str(draft_data).strip():
        raise ValueError("Writer Agent returned an empty draft.")

    return {
        "draft": draft_data,
        "draft_feedback": "",
        "revision_count": state.revision_count + 1
    }


def human_review_draft_node(state: BlogState):
    decision = interrupt({
        "stage": "draft_review",
        "draft": state.draft,
        "instructions": "Approve the draft or provide feedback for revision."
    })

    if isinstance(decision, dict):
        action = decision.get("action", "approve")
        feedback = decision.get("feedback", "")
    else:
        text = str(decision).strip()
        action = "approve" if text.lower() in [
            "approve", "approved", "ok", "yes", "process"
        ] else "revise"
        feedback = "" if action == "approve" else text

    return {
        "draft_feedback": feedback if action == "revise" else ""
    }


def editor_node(state: BlogState):
    llm = get_llm()

    final = editor_agent(
        llm=llm,
        topic=state.topic,
        draft=state.draft
    )

    if not final or not str(final).strip():
        raise ValueError("Editor Agent returned an empty final blog.")

    return {"final_blog": final}


def route_after_research_review(
    state: BlogState
) -> Literal["research", "writer"]:
    if state.research_feedback:
        return "research"
    return "writer"


def route_after_draft_review(
    state: BlogState
) -> Literal["edit", "writer"]:
    if state.draft_feedback and state.revision_count < MAX_REVISION:
        return "writer"
    return "edit"


def blog_graph():
    builder = StateGraph(BlogState)

    builder.add_node("research", researcher_node)
    builder.add_node("review_research", human_review_research_node)
    builder.add_node("writer", writer_node)
    builder.add_node("review_draft", human_review_draft_node)
    builder.add_node("edit", editor_node)

    builder.add_edge(START, "research")

    builder.add_edge("research", "review_research")

    builder.add_conditional_edges(
        "review_research",
        route_after_research_review,
        {
            "research": "research",
            "writer": "writer"
        }
    )

    builder.add_edge("writer", "review_draft")

    builder.add_conditional_edges(
        "review_draft",
        route_after_draft_review,
        {
            "writer": "writer",
            "edit": "edit"
        }
    )

    builder.add_edge("edit", END)

    return builder.compile(checkpointer=InMemorySaver())
