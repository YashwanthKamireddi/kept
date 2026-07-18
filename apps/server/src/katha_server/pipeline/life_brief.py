"""Life Brief compilation.

The Life Brief is the interviewer's memory: a compact markdown artifact,
deterministically compiled from the life graph. Deterministic on purpose —
it is derived state (always rebuildable), testable offline, and it keeps the
prompt-cache prefix stable between calls except when the graph actually grew.
"""

from katha_core.models import Entity, EntityKind, Fact, FollowUp, FollowUpStatus, Storyteller

_KIND_HEADINGS = [
    (EntityKind.PERSON, "People"),
    (EntityKind.PLACE, "Places"),
    (EntityKind.ERA, "Eras"),
    (EntityKind.EVENT, "Events"),
    (EntityKind.OBJECT, "Objects & keepsakes"),
]

MAX_FACTS_PER_ENTITY = 6
MAX_UNLINKED_FACTS = 30
MAX_OPEN_THREADS = 12


def compile_life_brief(
    storyteller: Storyteller,
    entities: list[Entity],
    facts: list[Fact],
    follow_ups: list[FollowUp],
) -> str:
    facts_by_entity: dict[str | None, list[Fact]] = {}
    for f in facts:
        facts_by_entity.setdefault(f.entity_id, []).append(f)

    lines: list[str] = [f"# Life Brief — {storyteller.name}", ""]

    for kind, heading in _KIND_HEADINGS:
        of_kind = [e for e in entities if e.kind == kind]
        if not of_kind:
            continue
        lines.append(f"## {heading}")
        for e in sorted(of_kind, key=lambda x: x.canonical_name):
            alias_str = f" ({', '.join(e.aliases)})" if e.aliases else ""
            summary = f" — {e.summary}" if e.summary else ""
            lines.append(f"- **{e.canonical_name}**{alias_str}{summary}")
            for f in facts_by_entity.get(e.id, [])[:MAX_FACTS_PER_ENTITY]:
                lines.append(f"  - {f.statement}")
        lines.append("")

    unlinked = facts_by_entity.get(None, [])
    if unlinked:
        lines.append("## Other things she has shared")
        lines.extend(f"- {f.statement}" for f in unlinked[:MAX_UNLINKED_FACTS])
        lines.append("")

    pending = [fu for fu in follow_ups if fu.status == FollowUpStatus.PENDING]
    if pending:
        lines.append("## Open threads (worth asking about)")
        for fu in sorted(pending, key=lambda x: -x.priority)[:MAX_OPEN_THREADS]:
            lines.append(f"- {fu.question}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
