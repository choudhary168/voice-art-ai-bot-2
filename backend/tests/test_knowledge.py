import pytest
from backend.services.knowledge import DefaultKnowledgeProvider, UserProfile


@pytest.mark.asyncio
async def test_knowledge_provider():
    provider = DefaultKnowledgeProvider()

    # Query initial knowledge
    res = await provider.retrieve_context("What is Gemini Voice Agent?")
    assert res.has_content()
    assert any("Gemini" in s.title for s in res.snippets)

    # Add dynamic document
    await provider.add_document(
        title="Campus Admission Process",
        content="Admissions for B.Tech CSE require JEE score and 12th standard aggregate above 75%.",
        source="admissions-portal"
    )

    res2 = await provider.retrieve_context("Tell me about admission requirements")
    assert res2.has_content()
    assert any(s.title == "Campus Admission Process" for s in res2.snippets)


@pytest.mark.asyncio
async def test_user_profile():
    provider = DefaultKnowledgeProvider()
    profile = UserProfile(user_id="user-42", name="Rohan", preferred_language="hinglish")
    provider.set_user_profile(profile)

    res = await provider.retrieve_context("Hello", user_id="user-42")
    assert res.user_profile is not None
    assert res.user_profile.name == "Rohan"
    formatted = res.format_for_system_instruction()
    assert "Rohan" in formatted
    assert "hinglish" in formatted
