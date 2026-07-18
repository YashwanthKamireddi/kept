from katha_core.models import FollowUp, FollowUpStatus, Storyteller
from katha_server.pipeline.planner import LIFE_ARC, plan_session


def _st() -> Storyteller:
    return Storyteller(id="st", family_id="f", name="Rajamma", address_as="Rajamma garu",
                       phone_e164="+91")


def test_first_session_is_introduction_and_consent():
    themes, plan = plan_session(_st(), completed_sessions=0, follow_ups=[])
    assert themes[0] == "introduction"
    assert "consent" in plan.lower()
    assert "first conversation" in plan.lower()


def test_later_sessions_follow_arc_and_pull_threads():
    fus = [
        FollowUp(id="f1", storyteller_id="st", question="What happened to Ravi in Bombay?",
                 priority=8, status=FollowUpStatus.PENDING),
        FollowUp(id="f2", storyteller_id="st", question="The wedding sari story",
                 priority=3, status=FollowUpStatus.PENDING),
        FollowUp(id="f3", storyteller_id="st", question="Already asked",
                 priority=9, status=FollowUpStatus.ASKED),
    ]
    themes, plan = plan_session(_st(), completed_sessions=2, follow_ups=fus)
    assert themes[0] == LIFE_ARC[1]
    assert "What happened to Ravi in Bombay?" in plan
    assert "Already asked" not in plan  # non-pending excluded
    assert plan.index("Ravi") < plan.index("sari")  # priority ordering


def test_arc_clamps_at_final_theme():
    themes, _ = plan_session(_st(), completed_sessions=50, follow_ups=[])
    assert themes[0] == LIFE_ARC[-1]
