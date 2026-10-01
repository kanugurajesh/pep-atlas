from pepatlas import lexicon as lx


def test_strict_identifiers_need_code_context_in_corpus():
    # "Final" as an English word must not count; as code it must.
    assert "final" not in lx.count_concepts("The Final decision was made by the council.")
    assert lx.count_concepts("Use ``Final[int]`` here.").get("final") == 1
    assert "final" in lx.count_concepts("x: Final = 3")


def test_unambiguous_identifiers_match_anywhere():
    assert "typeddict" in lx.count_concepts("A TypedDict type represents a dictionary")


def test_input_matching_reports_surface_forms():
    hits = lx.match_input("Allow T? as shorthand for Optional[T]")
    assert "optional_shorthand" in hits and "union" in hits


def test_sentence_initial_ambiguous_words_ignored_in_input():
    assert "gradual_typing" not in lx.match_input("Any developer would want this.")


def test_builtin_generics_is_case_sensitive():
    assert "builtin_generics" not in lx.count_concepts("``Dict[str, int]``")
    assert "builtin_generics" in lx.count_concepts("``dict[str, int]``")


def test_concern_classifier_returns_evidence_sentence():
    out = lx.classify_concerns(["This would break existing code. It is also confusing to read."])
    assert out["backward_compat"] == "This would break existing code."
    assert out["readability"] == "It is also confusing to read."


def test_intents():
    assert "new_syntax" in lx.detect_intents("add a new operator syntax")
    assert "runtime_change" in lx.detect_intents("enforce this at runtime")
