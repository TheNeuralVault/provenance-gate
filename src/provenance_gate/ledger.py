from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class LedgerEntry:
    """
    Single append-only ledger entry.

    Fields:
        nonce: unique identifier for this entry
        actor_id: actor responsible
        step: pipeline step (SPEC, PLAN, TEST, BUILD, VERIFY, COMMIT, etc.)
        payload: arbitrary structured data
        timestamp: epoch seconds
        prev_hash: hash of previous entry (or GENESIS_HASH)
        hash: hash of this entry (computed automatically)
    """

    nonce: str
    actor_id: str
    step: str
    payload: dict[str, Any]
    timestamp: float
    prev_hash: str
    hash: str

    @staticmethod
    def compute_hash(
        nonce: str,
        actor_id: str,
        step: str,
        payload: dict[str, Any],
        timestamp: float,
        prev_hash: str,
    ) -> str:
        data = json.dumps(
            {
                "nonce": nonce,
                "actor_id": actor_id,
                "step": step,
                "payload": payload,
                "timestamp": timestamp,
                "prev_hash": prev_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def create(
        cls,
        nonce: str,
        actor_id: str,
        step: str,
        payload: dict[str, Any],
        prev_hash: str,
    ) -> LedgerEntry:
        ts = time.time()
        h = cls.compute_hash(
            nonce=nonce,
            actor_id=actor_id,
            step=step,
            payload=payload,
            timestamp=ts,
            prev_hash=prev_hash,
        )
        return cls(
            nonce=nonce,
            actor_id=actor_id,
            step=step,
            payload=payload,
            timestamp=ts,
            prev_hash=prev_hash,
            hash=h,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerEntry:
        return cls(
            nonce=data["nonce"],
            actor_id=data["actor_id"],
            step=data["step"],
            payload=data["payload"],
            timestamp=float(data["timestamp"]),
            prev_hash=data["prev_hash"],
            hash=data["hash"],
        )


class LedgerIntegrityError(RuntimeError):
    pass


class AppendOnlyLedger:
    """
    Append-only ledger with hash chaining and nonce replay protection.

    This is NOT a blockchain; it is a simple, auditable log that detects:
        - tampering between runs (hash chain verification)
        - nonce reuse (replay protection)
    """

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._entries: list[LedgerEntry] = []
        self._seen_nonces: set[str] = set()
        self._lock = threading.RLock()
        self._persist_path: Path | None = (
            Path(persist_path) if persist_path is not None else None
        )

        if self._persist_path is not None and self._persist_path.exists():
            self._load_and_verify()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_and_verify(self) -> None:
        assert self._persist_path is not None
        raw = self._persist_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        prev_hash = GENESIS_HASH
        for item in data:
            entry = LedgerEntry.from_dict(item)
            # verify hash chain
            expected_hash = LedgerEntry.compute_hash(
                nonce=entry.nonce,
                actor_id=entry.actor_id,
                step=entry.step,
                payload=entry.payload,
                timestamp=entry.timestamp,
                prev_hash=entry.prev_hash,
            )
            if expected_hash != entry.hash:
                raise LedgerIntegrityError("Ledger hash mismatch on load")
            if entry.prev_hash != prev_hash:
                raise LedgerIntegrityError("Ledger prev_hash chain broken on load")
            if entry.nonce in self._seen_nonces:
                raise LedgerIntegrityError("Ledger nonce replay detected on load")

            self._entries.append(entry)
            self._seen_nonces.add(entry.nonce)
            prev_hash = entry.hash

    def _persist(self) -> None:
        if self._persist_path is None:
            return
        data = [e.to_dict() for e in self._entries]
        tmp = self._persist_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, sort_keys=True, indent=2), encoding="utf-8")
        tmp.replace(self._persist_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(
        self,
        nonce: str,
        actor_id: str,
        step: str,
        payload: dict[str, Any],
    ) -> LedgerEntry:
        """
        Append a new entry to the ledger.

        Raises LedgerIntegrityError if nonce is reused.
        """
        with self._lock:
            if nonce in self._seen_nonces:
                raise LedgerIntegrityError(f"Nonce replay detected: {nonce}")

            prev_hash = self._entries[-1].hash if self._entries else GENESIS_HASH
            entry = LedgerEntry.create(
                nonce=nonce,
                actor_id=actor_id,
                step=step,
                payload=payload,
                prev_hash=prev_hash,
            )
            self._entries.append(entry)
            self._seen_nonces.add(nonce)
            self._persist()
            return entry

    def entries(self) -> list[LedgerEntry]:
        with self._lock:
            return list(self._entries)

    def last_hash(self) -> str:
        with self._lock:
            if not self._entries:
                return GENESIS_HASH
            return self._entries[-1].hash
