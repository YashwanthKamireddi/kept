"""Dev seed: attach a demo storyteller with a verified chapter to YOUR family.

Usage (after signing up in the app or via /auth/signup):
    uv run python -m katha_server.devseed --email you@example.com

Everything seeded is honestly marked: the demo session has no synced audio, so
tapping a gold sentence shows the real "recording hasn't synced" state.
"""

import argparse
import asyncio

from katha_core.db import create_all, session as db_session
from katha_core.models import (
    CallSession,
    Chapter,
    ChapterStatus,
    ConsentStatus,
    FollowUp,
    Keeper,
    SessionStatus,
    Speaker,
    Storyteller,
    TranscriptSegment,
)
from sqlalchemy import select

SEGMENTS = [
    (Speaker.BIOGRAPHER, "Tell me about the house you grew up in."),
    (
        Speaker.STORYTELLER,
        "It was a small house behind my father's bakery. The whole street smelled "
        "of bread before sunrise.",
    ),
    (Speaker.BIOGRAPHER, "Who woke up first?"),
    (
        Speaker.STORYTELLER,
        "My mother, always. She would sing very quietly so as not to wake us, "
        "but I used to lie awake just to hear it.",
    ),
]

CHAPTER_TITLE = "The Street That Smelled of Bread"


async def seed(email: str, create: bool = False) -> None:
    await create_all()
    async with db_session() as s:
        keeper = await s.scalar(select(Keeper).where(Keeper.email == email))
        if keeper is None and create:
            from katha_core.models import Family  # noqa: PLC0415

            family = Family(name="Demo Family")
            s.add(family)
            await s.flush()
            keeper = Keeper(family_id=family.id, email=email, name="Demo Keeper")
            s.add(keeper)
            await s.flush()
        if keeper is None:
            raise SystemExit(f"no keeper with email {email} — sign up first, or pass --create")

        st = Storyteller(
            family_id=keeper.family_id,
            name="Grandma Rose",
            address_as="Grandma Rose",
            phone_e164="+15550000000",
            language="en",
            consent=ConsentStatus.GRANTED,
            life_brief_version=1,
        )
        s.add(st)
        await s.flush()

        call = CallSession(storyteller_id=st.id, status=SessionStatus.COMPLETED)
        s.add(call)
        await s.flush()

        seg_rows = []
        for idx, (speaker, text) in enumerate(SEGMENTS):
            seg = TranscriptSegment(
                session_id=call.id, idx=idx, speaker=speaker,
                t_start_ms=idx * 8000, t_end_ms=(idx + 1) * 8000,
                text=text, language="en",
            )
            s.add(seg)
            seg_rows.append(seg)
        await s.flush()

        s.add(
            Chapter(
                storyteller_id=st.id, ordinal=1, title=CHAPTER_TITLE,
                status=ChapterStatus.VERIFIED,
                body=[
                    [
                        {
                            "text": "Our house stood behind my father's bakery, and the "
                            "whole street smelled of bread before sunrise.",
                            "segment_ids": [seg_rows[1].id],
                            "bridge": False,
                        },
                        {
                            "text": "Mornings there began before the light did.",
                            "segment_ids": [],
                            "bridge": True,
                        },
                        {
                            "text": "My mother woke first and sang quietly so as not to "
                            "wake us — I used to lie awake just to hear her.",
                            "segment_ids": [seg_rows[3].id],
                            "bridge": False,
                        },
                    ]
                ],
            )
        )
        s.add(
            FollowUp(
                storyteller_id=st.id,
                question="What songs did her mother sing in the mornings?",
                rationale="Mentioned the singing but never what the songs were.",
                priority=8,
                source_session_id=call.id,
            )
        )
        await s.commit()
        print(f"seeded: storyteller 'Grandma Rose' + 1 verified chapter for {email}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--create", action="store_true",
                        help="create the account too, if it doesn't exist")
    args = parser.parse_args()
    asyncio.run(seed(args.email, create=args.create))


if __name__ == "__main__":
    main()
