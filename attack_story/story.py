"""Phase 14 - Story builder."""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from attack_story.narrator import narrate
from attack_story.timeline import build_timeline
from database.repository import Repository

logger = logging.getLogger(__name__)


async def build_story(session: AsyncSession, story_db_id: int):
    repo = Repository(session)
    story = await repo.attack_stories.get(story_db_id)
    if story is None:
        raise ValueError(f"Story {story_db_id} not found")

    from digital_twin.graph import twin_graph
    all_asset_db_ids = list(twin_graph._asset_db_ids.values())

    timeline = await build_timeline(session, story, all_asset_db_ids)
    target_code = story.title.split("->")[-1].strip() if "->" in story.title else story.title
    narrative = narrate(story.title, target_code, timeline)

    for e in timeline:
        await repo.attack_story_events.add(
            story_db_id=story_db_id, evidence_kind=e.evidence_kind,
            title=e.title, occurred_at=e.occurred_at,
            evidence_id=e.evidence_id, asset_db_id=e.asset_db_id,
            severity=e.severity, details=e.details, tactic=e.tactic,
        )

    for t in narrative["tactics"]:
        await repo.attack_story_tactics.upsert(
            story_db_id=story_db_id, tactic=t["tactic"],
            confidence=t["confidence"], evidence_count=t["evidence_count"],
        )

    story.narrative = narrative["summary"] + "\n\n" + "\n\n".join(narrative["paragraphs"])
    if not story.ended_at:
        story.ended_at = datetime.now(timezone.utc)
    if story.status == "running":
        story.status = "analyzed"
    await session.commit()

    return {"story_id": story.id, "attack_id": story.attack_id,
            "title": story.title, "status": story.status,
            "summary": narrative["summary"],
            "paragraphs": narrative["paragraphs"],
            "attribution": narrative["attribution"],
            "tactics": narrative["tactics"], "event_count": len(timeline)}
