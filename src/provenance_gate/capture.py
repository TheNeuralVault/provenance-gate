from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from provenance_gate.tiers import Tier

if TYPE_CHECKING:
    from provenance_gate.evidence import EvidenceArtifact


# ---------------------------------------------------------------------------
# Process-local secret for HMAC signing
# ---------------------------------------------------------------------------

_PROCESS_SECRET = secrets.token_bytes(32)


def _sign(content: str) -> str:
    """
    Sign content with a process-local HMAC key.

    This is NOT a cryptographic isolation boundary — any in-process
    attacker can read the key. It is a discipline mechanism to ensure
    that only actually captured output is treated as T1.
    """
    return hmac.new(_PROCESS_SECRET, content.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(content: str, signature: str) -> bool:
    """
    Verify that the signature matches the content under the current process key.
    """
    expected = _sign(content)
    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# SignedEvidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignedEvidence:
    """
    SignedEvidence represents captured terminal output with an HMAC signature.

    Fields:
        content: full captured text (stdout + stderr + command + exit code)
        signature: HMAC-SHA256 over content
        command: tuple of command arguments
        exit_code: process exit code

    This is the canonical T1 evidence type for VERIFY.
    """

    content: str
    signature: str
    command: tuple[str, ...]
    exit_code: int

    def is_valid(self) -> bool:
        return verify_signature(self.content, self.signature)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "SignedEvidence",
            "command": list(self.command),
            "exit_code": self.exit_code,
            "content": self.content,
            "signature": self.signature,
            "valid": self.is_valid(),
        }

    def to_t1_artifact(self, source: str = "runtime_capture") -> EvidenceArtifact:
        from provenance_gate.evidence import EvidenceArtifact

        if not self.is_valid():
            raise ValueError("SignedEvidence signature invalid")
        return EvidenceArtifact(
            tier=Tier.T1,
            source=source,
            content={
                "command": list(self.command),
                "exit_code": self.exit_code,
                "content": self.content,
            },
        )


# ---------------------------------------------------------------------------
# TerminalCapture
# ---------------------------------------------------------------------------

class TerminalCapture:
    """
    Capture subprocess output as signed evidence.

    This is the primary mechanism for generating T1 evidence from
    actual executed commands (tests, builds, scripts).
    """

    @staticmethod
    def run(
        cmd: list[str],
        *,
        cwd: str | None = None,
        timeout: int = 300,
        env: dict[str, str] | None = None,
    ) -> SignedEvidence:
        """
        Run a command, capture stdout/stderr, and return SignedEvidence.

        The content format is:

            $ <command...>
            <stdout>
            <stderr>
            [exit <code>]

        This is then HMAC-signed with the process-local key.
        """
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            env=env,
        )

        header = f"$ {' '.join(cmd)}\n"
        body = f"{result.stdout}{result.stderr}"
        footer = f"\n[exit {result.returncode}]"
        content = header + body + footer

        sig = _sign(content)

        return SignedEvidence(
            content=content,
            signature=sig,
            command=tuple(cmd),
            exit_code=result.returncode,
        )

    @staticmethod
    def grep_output(evidence: SignedEvidence, pattern: str) -> list[str]:
        """
        Convenience helper: grep lines in the captured content.

        This does NOT affect the signature; it is purely a view.
        """
        lines = evidence.content.splitlines()
        regex = re.compile(pattern)
        return [line for line in lines if regex.search(line)]
