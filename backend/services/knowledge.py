import abc
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KnowledgeSnippet(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    confidence: float = 1.0


class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    preferred_language: Optional[str] = "en"  # "en", "hi", "hinglish"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeResult(BaseModel):
    query: str
    snippets: List[KnowledgeSnippet] = Field(default_factory=list)
    user_profile: Optional[UserProfile] = None

    def has_content(self) -> bool:
        return bool(self.snippets or self.user_profile)

    def format_for_system_instruction(self) -> str:
        """Format retrieved context for injection into Live session instructions or turn prompts."""
        parts = []
        if self.user_profile:
            parts.append(f"User Profile: Name={self.user_profile.name or 'Unknown'}, Language Preference={self.user_profile.preferred_language}")
        if self.snippets:
            parts.append("Retrieved Knowledge Documents / FAQs:")
            for s in self.snippets:
                src_info = f" ({s.source})" if s.source else ""
                parts.append(f"- [{s.title}]{src_info}: {s.content}")
        return "\n".join(parts)


class KnowledgeProvider(abc.ABC):
    """Abstract interface for website FAQs, document retrieval, and user profiles."""

    @abc.abstractmethod
    async def retrieve_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeResult:
        """Retrieve relevant context for a query and user."""
        pass

    @abc.abstractmethod
    async def add_document(self, title: str, content: str, source: Optional[str] = None) -> None:
        """Add a new document or FAQ to the knowledge store dynamically."""
        pass


class DefaultKnowledgeProvider(KnowledgeProvider):
    """
    Default clean extension-point implementation.
    Initially contains seed knowledge for Gemini Voice Agent and website capabilities,
    and allows runtime addition of FAQ entries or documents without architecture changes.
    """

    def __init__(self):
        self._documents: List[KnowledgeSnippet] = [
            KnowledgeSnippet(
                title="About Gemini Voice Agent",
                content=(
                    "This AI voice agent is powered by Gemini Live API, supporting continuous low-latency "
                    "bidirectional voice and text streaming, real-time audio playback, and multilingual conversation in English, Hindi, and Hinglish."
                ),
                source="system://default-docs"
            ),
            KnowledgeSnippet(
                title="Multilingual Support",
                content="The agent natively responds in English, Hindi, or Hinglish depending on what the user speaks or types.",
                source="system://default-docs"
            )
        ]
        self._profiles: Dict[str, UserProfile] = {}

    async def retrieve_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeResult:
        matched: List[KnowledgeSnippet] = []
        query_lower = query.lower() if query else ""

        # Simple semantic/keyword match for initial store; easily replaced with vector DB / RAG
        for doc in self._documents:
            words = [w for w in doc.title.lower().split() if len(w) > 3]
            if any(w in query_lower for w in words):
                matched.append(doc)

        profile = self._profiles.get(user_id) if user_id else None
        return KnowledgeResult(
            query=query,
            snippets=matched,
            user_profile=profile
        )

    async def add_document(self, title: str, content: str, source: Optional[str] = None) -> None:
        self._documents.append(KnowledgeSnippet(title=title, content=content, source=source))

    def set_user_profile(self, profile: UserProfile) -> None:
        self._profiles[profile.user_id] = profile


# Global singleton instance
knowledge_provider = DefaultKnowledgeProvider()


def get_knowledge_provider() -> KnowledgeProvider:
    return knowledge_provider
