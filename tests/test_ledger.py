from provenance_gate.ledger import AppendOnlyLedger


def test_ledger_append_and_chain():
    ledger = AppendOnlyLedger()
    entry1 = ledger.append("n1", "actorA", "SPEC", {"x": 1})
    entry2 = ledger.append("n2", "actorA", "PLAN", {"y": 2})

    assert entry1.hash != entry2.hash
    assert ledger.last_hash() == entry2.hash
