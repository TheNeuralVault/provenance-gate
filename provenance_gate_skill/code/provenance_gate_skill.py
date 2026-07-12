from provenance_gate.governance import governed_step
from provenance_gate.session import SessionScope
from provenance_gate.pipeline import PipelineState

def init_skill():
    return {
        "governed_step": governed_step,
        "SessionScope": SessionScope,
        "PipelineState": PipelineState,
    }
