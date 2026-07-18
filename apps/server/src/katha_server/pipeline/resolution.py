"""Entity resolution: merge newly extracted entities into the life graph.

v0 is deterministic and conservative: case-insensitive match on canonical name
or any alias, within the same entity kind. Unmatched entities are created.
Ambiguity (two Ravis) is deferred to the storyteller herself — the session
planner can queue a clarifying follow-up rather than guessing.
"""

from katha_core.models import Entity, EntityKind

from .extraction import ExtractedEntity


def _norm(name: str) -> str:
    return " ".join(name.lower().split())


def _names(entity: Entity) -> set[str]:
    return {_norm(entity.canonical_name), *(_norm(a) for a in entity.aliases or [])}


def resolve(
    storyteller_id: str,
    extracted: list[ExtractedEntity],
    existing: list[Entity],
) -> tuple[list[Entity], dict[str, Entity]]:
    """Returns (new_entities_to_persist, name -> Entity mapping for fact linking)."""
    by_name: dict[str, Entity] = {}
    new: list[Entity] = []

    for ext in extracted:
        kind = EntityKind(ext.kind)
        match = next(
            (e for e in existing if e.kind == kind and _norm(ext.name) in _names(e)),
            None,
        )
        if match is not None:
            merged = set(match.aliases or [])
            merged.update(a for a in ext.aliases if _norm(a) not in _names(match))
            match.aliases = sorted(merged)
            if not match.summary and ext.summary:
                match.summary = ext.summary
            entity = match
        else:
            entity = Entity(
                storyteller_id=storyteller_id,
                kind=kind,
                canonical_name=ext.name,
                aliases=ext.aliases,
                summary=ext.summary,
            )
            new.append(entity)
            existing = [*existing, entity]

        by_name[_norm(ext.name)] = entity
        for alias in ext.aliases:
            by_name.setdefault(_norm(alias), entity)

    return new, by_name
