import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Get LLM

def get_llm(
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.5
):
    api_key = os.getenv("GEMINI_API_KEY")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key
    )

    return llm

# Research Agent

RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    {
        "role": "system",
        "content": """
You are a Research Agent.

Given a blog topic and target audience, produce a clear,
structured research outline.

Include:

1. 5-7 key points the blog should cover
2. Important facts, stats, or examples for each point
3. Suggested angle or hook

Be concise.
Use bullet points.
Do NOT write the full blog yet.
"""
    },
    {
        "role": "user",
        "content": """
Topic: {topic}
Audience: {audience}

{revision_hints}

Write the research outline now.
"""
    }
])


def researcher_agent(
    llm: ChatGoogleGenerativeAI,
    topic: str,
    audience: str,
    feedback: str = ""
):

    if feedback:
        revision_hints = (
            "The Human provided this feedback on your previous research. "
            f"Please address it: {feedback}"
        )
    else:
        revision_hints = "This is your first attempt."

    chain = RESEARCHER_PROMPT | llm

    result = chain.invoke({
        "topic": topic,
        "audience": audience,
        "revision_hints": revision_hints
    })

    return result.content


# Writer Agent

WRITER_PROMPT = ChatPromptTemplate.from_messages([
    {
        "role": "system",
        "content": """
You are a Blog Writer Agent.

Using the research notes provided, write a complete,
engaging blog post.

Rules:

- Length: 500-800 words
- Structure:
  - Catchy title
  - Introduction hook
  - 3-5 sections with H2 headings
  - Conclusion
- Tone: clear and friendly
- Suitable for the target audience
- Use markdown formatting
- Do NOT add a word count line at the end
"""
    },
    {
        "role": "user",
        "content": """
Topic: {topic}
Audience: {audience}

Research Notes:
{research}

{revision_hints}

Write the full blog post now.
"""
    }
])


def writer_agent(
    llm: ChatGoogleGenerativeAI,
    topic: str,
    audience: str,
    research: str = "",
    feedback: str = ""
) -> str:

    if feedback:
        revision_hints = (
            "The Human provided this feedback on your previous draft "
            f"and asked for these changes: {feedback}. "
            "Please apply these changes while writing the blog."
        )
    else:
        revision_hints = "This is your first attempt."

    chain = WRITER_PROMPT | llm

    result = chain.invoke({
        "topic": topic,
        "audience": audience,
        "research": research,
        "revision_hints": revision_hints
    })

    return result.content


# Editor Agent

EDITOR_PROMPT = ChatPromptTemplate.from_messages([
    {
        "role": "system",
        "content": """
You are an Editor Agent - the final quality gate before publishing.

Take the draft and produce the FINAL polished version.

Specifically:

- Fix grammar, spelling and awkward phrasing
- Tighten sentences
- Improve flow and transitions between sections
- Make the title and intro more compelling if needed
- Keep the same structure and markdown formatting
- Blog wording should look human, not AI-generated
- Don't use special characters unnecessarily
- Don't use complex or fancy words

Output only the final polished blog post.
No commentary.
"""
    },
    {
        "role": "user",
        "content": """
Topic: {topic}

Draft:
{draft}

Return the published blog post.
"""
    }
])


def editor_agent(
    llm: ChatGoogleGenerativeAI,
    topic: str,
    draft: str
) -> str:

    chain = EDITOR_PROMPT | llm

    result = chain.invoke({
        "topic": topic,
        "draft": draft
    })

    return result.content
