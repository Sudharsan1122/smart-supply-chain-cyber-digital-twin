"""Extend main Repository with extra repos."""
from database.repository import Repository as BaseRepo
from database.repository_extra import (
    BlastRadiusRepo, IOCEnrichmentRepo, AttackStoryEventRepo, AttackStoryTacticRepo,
)


def extend_repository():
    original_init = BaseRepo.__init__

    def new_init(self, session):
        original_init(self, session)
        self.blast_radius = BlastRadiusRepo(session)
        self.ioc_enrichments = IOCEnrichmentRepo(session)
        self.attack_story_events = AttackStoryEventRepo(session)
        self.attack_story_tactics = AttackStoryTacticRepo(session)

    BaseRepo.__init__ = new_init
    return BaseRepo


extend_repository()
