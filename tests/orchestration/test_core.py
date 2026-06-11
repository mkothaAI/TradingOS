"""Orchestration pipeline tests (Phase 9)"""
import pytest
from backend.engines.orchestration.calc import run_pipeline
from backend.engines.orchestration.assembler import compute_pipeline, build_pipeline_response
from backend.schemas.shared import ErrorItem


def test_pipeline_happy_path(request_meta, ticker_list, universe_response, fundamental_response, event_response, risk_response, decision_response):
    payloads = {
        "universe": universe_response,
        "fundamental": fundamental_response,
        "event": event_response,
        "risk": risk_response,
        "decision": decision_response,
    }
    res = run_pipeline(request_meta, ticker_list, payloads, {})
    assert res["status"] == "OK"
    assert res["decisions"] is not None


def test_pipeline_idempotent(request_meta, ticker_list, universe_response, risk_response, decision_response):
    payloads = {"universe": universe_response, "risk": risk_response, "decision": decision_response}
    r1 = run_pipeline(request_meta, ticker_list, payloads, {})
    r2 = run_pipeline(request_meta, ticker_list, payloads, {})
    assert r1["run_id"] == r2["run_id"]
    assert r1["audit"] == r2["audit"]


# Missing required upstream
def test_missing_universe_fails_closed(request_meta, ticker_list, risk_response, decision_response):
    payloads = {"risk": risk_response, "decision": decision_response}
    res = run_pipeline(request_meta, ticker_list, payloads, {"fail_on_missing_upstream": True})
    assert res["status"] == "ERROR"
    codes = [e.code for e in res["errors"]]
    assert "UNIVERSE_MISSING" in codes


def test_missing_decision_fails_closed(request_meta, ticker_list, universe_response, risk_response):
    payloads = {"universe": universe_response, "risk": risk_response}
    res = run_pipeline(request_meta, ticker_list, payloads, {"fail_on_missing_upstream": True})
    assert res["status"] == "ERROR"
    codes = [e.code for e in res["errors"]]
    assert "DECISION_MISSING" in codes


def test_missing_risk_fails_closed(request_meta, ticker_list, universe_response, decision_response):
    payloads = {"universe": universe_response, "decision": decision_response}
    res = run_pipeline(request_meta, ticker_list, payloads, {"fail_on_missing_upstream": True})
    assert res["status"] == "ERROR"
    codes = [e.code for e in res["errors"]]
    assert "RISK_MISSING" in codes


# Partial per-ticker errors
def test_partial_engine_error_ticker_level(request_meta, ticker_list, universe_response, risk_response, decision_response):
    # simulate engine returning per-ticker ErrorItems in universe_response.errors
    universe_response.errors.append(ErrorItem(code="U_ERR", message="per-ticker error"))
    payloads = {"universe": universe_response, "risk": risk_response, "decision": decision_response}
    res = run_pipeline(request_meta, ticker_list, payloads, {})
    assert res["status"] == "ERROR"
    codes = [e.code for e in res["errors"]]
    assert "U_ERR" in codes


def test_engine_exception_propagates(request_meta, ticker_list):
    # simulate assembler raising by passing a non-model in payloads
    payloads = {"universe": None, "risk": None, "decision": None}
    with pytest.raises(Exception):
        run_pipeline(request_meta, ticker_list, payloads, {"fail_on_missing_upstream": False})


def test_audit_step_ordering(request_meta, ticker_list, universe_response, risk_response, decision_response):
    payloads = {"universe": universe_response, "risk": risk_response, "decision": decision_response}
    res = run_pipeline(request_meta, ticker_list, payloads, {})
    order = [a.step_name for a in res["audit"]]
    assert order == ["Universe", "Fundamental", "Event", "Risk", "Decision"]


def test_ticker_list_authoritative_order(request_meta, ticker_list, universe_response, risk_response, decision_response):
    payloads = {"universe": universe_response, "risk": risk_response, "decision": decision_response}
    res = run_pipeline(request_meta, ticker_list, payloads, {})
    # decisions forwarded; ensure keys appear in provided ticker_list order
    if res["decisions"] is not None:
        keys = list(res["decisions"].keys())
        assert keys == ticker_list


def test_invalid_pipeline_config_raises(request_meta, ticker_list, universe_response, risk_response, decision_response):
    payloads = {"universe": universe_response, "risk": risk_response, "decision": decision_response}
    with pytest.raises(ValueError):
        run_pipeline(request_meta, ticker_list, payloads, {"unknown_key": True})