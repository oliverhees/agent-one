"""GraphitiClient wrapper for ALICE's temporal knowledge graph memory.

Provides graceful degradation when FalkorDB is unavailable — the chat
continues to work without memory features.  All graphiti-core imports
are performed inside methods so the module loads even when the library
is not installed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 13 predefined ADHS behavioral patterns (German descriptions)
# ---------------------------------------------------------------------------

ADHD_SEED_PATTERNS: list[dict[str, str]] = [
    {
        "name": "Procrastination",
        "description": (
            "Aufschieben von Aufgaben trotz Wissen um negative Konsequenzen. "
            "Typisch bei ADHS durch Schwierigkeiten mit der Handlungsinitiierung "
            "und dem Belohnungssystem."
        ),
    },
    {
        "name": "Hyperfocus",
        "description": (
            "Intensives, stundenlanges Eintauchen in eine interessante Taetigkeit "
            "bei gleichzeitigem Ausblenden aller anderen Reize und Pflichten. "
            "Kann produktiv sein, fuehrt aber oft zu vernachlaessigten Aufgaben."
        ),
    },
    {
        "name": "Task-Switching",
        "description": (
            "Haeufiges Wechseln zwischen Aufgaben ohne eine abzuschliessen. "
            "Entsteht durch hohe Ablenkbarkeit und Schwierigkeiten bei der "
            "Aufrechterhaltung der Aufmerksamkeit."
        ),
    },
    {
        "name": "Paralysis by Analysis",
        "description": (
            "Handlungsunfaehigkeit durch Ueberanalyse von Optionen. "
            "Das ADHS-Gehirn wird von zu vielen Entscheidungsmoeglichkeiten "
            "ueberwaeltigt und blockiert."
        ),
    },
    {
        "name": "Time Blindness",
        "description": (
            "Eingeschraenktes Zeitgefuehl — Schwierigkeiten, Zeitspannen "
            "einzuschaetzen, Deadlines wahrzunehmen und puenktlich zu sein. "
            "Eines der Kernsymptome bei ADHS."
        ),
    },
    {
        "name": "Emotional Dysregulation",
        "description": (
            "Starke, schnelle emotionale Reaktionen die schwer zu kontrollieren "
            "sind. Uebermaessige Frustration, Ungeduld oder ploetzliche "
            "Stimmungswechsel."
        ),
    },
    {
        "name": "Rejection Sensitivity",
        "description": (
            "Uebermaessige emotionale Empfindlichkeit gegenueber wahrgenommener "
            "Ablehnung oder Kritik (Rejection Sensitive Dysphoria). "
            "Kann zu Vermeidungsverhalten fuehren."
        ),
    },
    {
        "name": "Dopamine Seeking",
        "description": (
            "Staendige Suche nach neuen Reizen und sofortiger Belohnung. "
            "Aeussert sich in impulsivem Verhalten, uebermässigem Social-Media-"
            "Konsum oder staendigem Wechsel von Hobbys."
        ),
    },
    {
        "name": "Working Memory Overload",
        "description": (
            "Eingeschraenkte Kapazitaet des Arbeitsgedaechtnisses. "
            "Informationen gehen schnell verloren, Anweisungen werden vergessen, "
            "Gespraechsfaeden gehen verloren."
        ),
    },
    {
        "name": "Sleep Disruption",
        "description": (
            "Stoerungen des Schlaf-Wach-Rhythmus — Einschlafprobleme durch "
            "kreisende Gedanken, verzoegerte Schlafphase, Schwierigkeiten "
            "beim Aufstehen."
        ),
    },
    {
        "name": "Transition Difficulty",
        "description": (
            "Schwierigkeiten beim Wechsel zwischen Aktivitaeten oder Kontexten. "
            "Das 'Umschalten' von einer Aufgabe zur naechsten kostet "
            "ueberproportional viel Energie."
        ),
    },
    {
        "name": "Perfectionism Paralysis",
        "description": (
            "Laehmendes Streben nach Perfektion — Aufgaben werden nicht "
            "begonnen oder fertiggestellt aus Angst, sie nicht perfekt zu "
            "erledigen. Oft verbunden mit geringem Selbstwertgefuehl."
        ),
    },
    {
        "name": "Social Masking",
        "description": (
            "Verbergen von ADHS-Symptomen im sozialen Umfeld durch "
            "Anpassungsstrategien. Fuehrt zu Erschoepfung und dem Gefuehl, "
            "nicht authentisch sein zu koennen."
        ),
    },
]


# ---------------------------------------------------------------------------
# GraphitiClient
# ---------------------------------------------------------------------------


class GraphitiClient:
    """Wrapper around Graphiti for ALICE's temporal knowledge graph.

    Provides graceful degradation: when ``enabled=False`` or when
    FalkorDB is unreachable, every public method returns an
    empty / neutral value instead of raising an exception.
    """

    def __init__(
        self,
        uri: str = "falkor://localhost:6379",
        enabled: bool = True,
    ) -> None:
        self.uri = uri
        self.enabled = enabled
        self._client: Any = None  # Graphiti instance, set in initialize()
        self._initialized = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Connect to FalkorDB via Graphiti and build indices.

        On failure the client disables itself so the rest of the
        application continues to work without memory features.
        """
        if not self.enabled:
            logger.info("GraphitiClient disabled by configuration.")
            return

        try:
            from graphiti_core import Graphiti

            self._client = Graphiti(self.uri)
            await self._client.build_indices_and_constraints()
            self._initialized = True
            logger.info("GraphitiClient initialized successfully (uri=%s).", self.uri)
        except Exception as exc:
            logger.warning(
                "GraphitiClient initialization failed — disabling memory features: %s",
                exc,
            )
            self.enabled = False
            self._client = None
            self._initialized = False

    async def close(self) -> None:
        """Close the underlying Graphiti connection."""
        if self._client is not None:
            try:
                await self._client.close()
                logger.info("GraphitiClient connection closed.")
            except Exception as exc:
                logger.warning("Error closing GraphitiClient: %s", exc)
            finally:
                self._client = None
                self._initialized = False

    # ------------------------------------------------------------------
    # Seed ADHS Patterns
    # ------------------------------------------------------------------

    async def seed_adhd_patterns(self) -> None:
        """Seed the 13 ADHS behavioral patterns as episodes.

        Safe to call multiple times — Graphiti handles deduplication.
        """
        if not self.enabled or self._client is None:
            logger.debug("seed_adhd_patterns skipped (client disabled).")
            return

        try:
            from graphiti_core import RawEpisode, EpisodeType

            for pattern in ADHD_SEED_PATTERNS:
                episode = RawEpisode(
                    name=f"adhd_pattern:{pattern['name']}",
                    body=pattern["description"],
                    episode_type=EpisodeType.text,
                    source_description="ADHS seed pattern",
                    reference_time=datetime.now(timezone.utc),
                    source=EpisodeType.text,
                )
                await self._client.add_episode(episode)

            logger.info("Seeded %d ADHS patterns into knowledge graph.", len(ADHD_SEED_PATTERNS))
        except Exception as exc:
            logger.warning("Failed to seed ADHS patterns: %s", exc)

    # ------------------------------------------------------------------
    # Episodes
    # ------------------------------------------------------------------

    async def add_episode(
        self,
        name: str,
        content: str,
        user_id: str,
        reference_time: datetime | None = None,
    ) -> str | None:
        """Add a conversation episode to the knowledge graph.

        Args:
            name: Episode name / identifier.
            content: The conversation text.
            user_id: User identifier (used as group_id for data isolation).
            reference_time: Timestamp for the episode.  Defaults to now.

        Returns:
            The episode ID string, or ``None`` on failure / when disabled.
        """
        if not self.enabled or self._client is None:
            return None

        try:
            from graphiti_core import RawEpisode, EpisodeType

            ref_time = reference_time or datetime.now(timezone.utc)

            episode = RawEpisode(
                name=name,
                body=content,
                episode_type=EpisodeType.text,
                source_description=f"user:{user_id}",
                reference_time=ref_time,
                source=EpisodeType.text,
            )
            result = await self._client.add_episode(
                episode,
                group_id=user_id,
            )

            episode_id = str(result.episode_id) if hasattr(result, "episode_id") else str(result)
            logger.debug("Added episode '%s' for user %s → %s", name, user_id, episode_id)
            return episode_id
        except Exception as exc:
            logger.warning("Failed to add episode '%s' for user %s: %s", name, user_id, exc)
            return None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        user_id: str,
        num_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search the knowledge graph for relevant facts.

        Args:
            query: Natural-language search query.
            user_id: User identifier for data isolation.
            num_results: Maximum number of results.

        Returns:
            A list of fact dicts with ``uuid``, ``name``, ``fact`` and
            ``valid_at`` / ``invalid_at`` keys, or an empty list on
            failure / when disabled.
        """
        if not self.enabled or self._client is None:
            return []

        try:
            results = await self._client.search(
                query=query,
                group_ids=[user_id],
                num_results=num_results,
            )

            facts: list[dict[str, Any]] = []
            for edge in results:
                facts.append({
                    "uuid": str(edge.uuid) if hasattr(edge, "uuid") else None,
                    "name": getattr(edge, "name", None),
                    "fact": getattr(edge, "fact", str(edge)),
                    "valid_at": (
                        edge.valid_at.isoformat()
                        if hasattr(edge, "valid_at") and edge.valid_at
                        else None
                    ),
                    "invalid_at": (
                        edge.invalid_at.isoformat()
                        if hasattr(edge, "invalid_at") and edge.invalid_at
                        else None
                    ),
                })

            logger.debug(
                "Search for '%s' (user %s) returned %d facts.", query, user_id, len(facts)
            )
            return facts
        except Exception as exc:
            logger.warning("Search failed for user %s: %s", user_id, exc)
            return []

    # ------------------------------------------------------------------
    # DSGVO Art. 17 — Right to Erasure
    # ------------------------------------------------------------------

    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all knowledge-graph data for a user (DSGVO Art. 17).

        Returns:
            ``True`` if deletion succeeded or the client is disabled
            (nothing to delete).  ``False`` on error.
        """
        if not self.enabled or self._client is None:
            return True

        try:
            # Graphiti provides a group-level deletion API
            await self._client.delete_group(group_id=user_id)
            logger.info("Deleted all knowledge-graph data for user %s.", user_id)
            return True
        except Exception as exc:
            logger.error("Failed to delete user data for %s: %s", user_id, exc)
            return False

    # ------------------------------------------------------------------
    # Entity Count
    # ------------------------------------------------------------------

    async def get_entity_count(self, user_id: str) -> int:
        """Return the number of entities stored for *user_id*.

        Returns ``0`` when disabled or on error.
        """
        if not self.enabled or self._client is None:
            return 0

        try:
            results = await self._client.search(
                query="*",
                group_ids=[user_id],
                num_results=1000,
            )
            count = len(results) if results else 0
            logger.debug("Entity count for user %s: %d", user_id, count)
            return count
        except Exception as exc:
            logger.warning("Failed to get entity count for user %s: %s", user_id, exc)
            return 0


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

graphiti_client: GraphitiClient | None = None


def get_graphiti_client() -> GraphitiClient:
    """Return the module-level GraphitiClient singleton.

    If the singleton has not been initialised (e.g. FalkorDB is not
    configured), returns a *disabled* instance so callers never have
    to deal with ``None``.
    """
    global graphiti_client
    if graphiti_client is not None:
        return graphiti_client
    # Return a disabled instance — no memory, but no crash either.
    return GraphitiClient(enabled=False)
