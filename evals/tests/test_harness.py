from katha_evals.personas import FIXTURE_LIFE_BRIEF, PERSONAS, RAJAMMA, VENKAT, storyteller_for
from katha_evals.scorecard import PASS_THRESHOLD, DimensionScore, Scorecard
from katha_evals.simulator import render_dialogue


def test_personas_are_distinct_and_complete():
    assert len(PERSONAS) == 2
    assert "rambl" in RAJAMMA.simulator_prompt.lower()
    assert "one-word" in VENKAT.simulator_prompt.lower()
    assert all(p.judge_notes for p in PERSONAS)


def test_fixture_brief_plants_memory_probe():
    # Judges score memory usage against these planted facts.
    assert "Ravi" in FIXTURE_LIFE_BRIEF and "Bombay" in FIXTURE_LIFE_BRIEF
    st = storyteller_for(RAJAMMA)
    assert st.life_brief == FIXTURE_LIFE_BRIEF
    assert st.language == "te-IN"  # column defaults don't apply off-session
    assert storyteller_for(VENKAT).life_brief == ""  # cold-start persona


def test_scorecard_gate():
    card = Scorecard(persona_key="x")
    assert not card.passed  # empty card never passes

    card.scores = {
        "warmth": DimensionScore(4.5),
        "memory_usage": DimensionScore(PASS_THRESHOLD),
    }
    assert card.passed

    card.scores["memory_usage"] = DimensionScore(1.0, "fabricated a memory")
    assert not card.passed
    weakest = card.weakest
    assert weakest is not None and weakest[0] == "memory_usage"
    assert "FAIL" in card.render() and "fabricated" in card.render()


def test_render_dialogue_roles():
    text = render_dialogue([
        {"role": "assistant", "content": "Namaskaram Rajamma garu."},
        {"role": "user", "content": "Namaskaram amma."},
    ])
    assert text.splitlines()[0].startswith("BIOGRAPHER:")
    assert text.splitlines()[1].startswith("STORYTELLER:")
