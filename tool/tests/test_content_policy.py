from copy import deepcopy

from socnhotv.core.engine import content_policy as cp


def test_default_policy_flags_violence_and_keeps_vietnamese_accents():
    r = cp.check_texts({"dialogue": "Mun tạo ra tháp rồi đánh nhau với Bi"}, cp.DEFAULT_POLICY)
    terms = [v["term"].lower() for v in r["violations"]]
    assert "đánh nhau" in terms
    assert "tạo" not in terms and not r["passed"]


def test_warn_does_not_block_unless_strict():
    pol = deepcopy(cp.DEFAULT_POLICY)
    text = {"caption": "mua ngay nhé"}
    assert cp.check_texts(text, pol)["passed"] is True
    pol["mode"] = "strict"
    assert cp.check_texts(text, pol)["passed"] is False


def test_allowlist_and_extra_terms():
    pol = deepcopy(cp.DEFAULT_POLICY)
    pol["allowlist"] = ["không đánh nhau"]
    assert cp.check_texts({"d": "Bi nói không đánh nhau"}, pol)["passed"] is True
    pol2 = cp.merge_extra_terms(cp.DEFAULT_POLICY, ["bánh quy"])
    assert cp.check_texts({"d": "ăn bánh quy"}, pol2)["blockCount"] == 1


def test_import_text_and_merge_rules():
    rules = cp.parse_policy_text("x.txt", "# Bạo lực\nđập phá\nghét: ghét bỏ, xa lánh\n- thô lỗ")
    cats = {r["category"]: r["terms"] for r in rules}
    assert cats["Bạo lực"] == ["đập phá", "thô lỗ"] and cats["ghét"] == ["ghét bỏ", "xa lánh"]
    merged = cp.merge_rules(cp.DEFAULT_POLICY, rules, "upload-x")
    assert any(r["source"] == "upload-x" for r in merged["rules"])
    assert cp.check_texts({"d": "đập phá đồ"}, merged)["blockCount"] == 1
    again = cp.merge_rules(merged, rules, "upload-x")
    assert len(again["rules"]) == len(merged["rules"])  # nhập lại thì ghi đè, không nhân đôi


def test_fetch_blocks_internal_hosts():
    import pytest

    with pytest.raises(ValueError):
        cp.fetch_policy_page("https://127.0.0.1/x")
    with pytest.raises(ValueError):
        cp.fetch_policy_page("http://example.com")
