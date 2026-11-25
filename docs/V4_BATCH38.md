# Batch 38 — Edge workflow integration

Extends Batch 37 on its existing feature branch (PR #1). No actual external voice service requests made in development. The existing local-only automatic engine list remains unchanged.

- `project-edge-plan --project-id ID --max-new 1` audits the approved current script and cast, existing receipts and remaining Edge turns. Reports turn IDs, speakers, preset IDs and character counts without dialogue content or network calls.
- `edge-voice-inventory --language hi --allow-network --acknowledgment I_AUTHORIZE_ONLINE_EDGE_VOICE_INVENTORY_REQUEST` is separate from speech consent; sends no project/dialogue. Optional language filter, normalized locale matching, deterministic sorting/deduplication, conflicting metadata rejection, 5000 input row and 1000 displayed row limits, 30-second fetch timeout. Provider service/voice availability is not guaranteed. Unsupported voice shapes are skipped.
- Optional guided package installation: `dependency-plan --group edge` then `dependency-install --group edge --acknowledgment I_AUTHORIZE_INSTALLING_FREE_OPTIONAL_PYTHON_PACKAGES`.
- Dashboard: preview, inventory and bounded online generation are distinct controls; inventory and generation require separate per-action network consent plus existing authoring consent. Generation displays verified per-turn progress and permits task-ID scoped stop between turns (not force cancellation of active request).
- Continuity-enabled projects are blocked from online Edge generation/preview to preserve the existing local-only continuity policy. Use authorized imported audio/local TTS instead.
- 63 new authored tests: 36 inventory filter/order cases, 6 malformed inventory cases, 4 inventory consent cases, 2 inventory mock/bounds cases, 4 invalid plan counts, 8 browser consent cases, and 3 integration/markup/dispatch cases = 63 cases. No full repository test execution confirmed. Physical Windows/browser and real service acceptance remain pending.
