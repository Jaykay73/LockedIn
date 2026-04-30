from app.services.id_generator import normalize_skill


def test_learn_python_normalizes_correctly():
    assert normalize_skill("Learn Python") == "python"


def test_whitespace_is_handled():
    assert normalize_skill("  learn   Guitar  ") == "guitar"


def test_non_tech_skills_normalize_correctly():
    assert normalize_skill("Learn Public Speaking") == "public-speaking"


def test_unsafe_characters_are_removed():
    assert normalize_skill("Learn Python!!! <script>") == "python-script"
