@security @P0 @state-machine @fail-closed @level2
Feature: Orchestrator v2 deterministic security boundary
  @stale-execution @concurrency
  Scenario: stale execution cannot mutate a newer PR head
    Given an active Story is bound to a baseline, PR and expected HEAD SHA
    When the current PR HEAD no longer equals the expected HEAD SHA
    Then autonomous privileged mutation is blocked
  @repair-loop @provider-failure
  Scenario: repair budget is exhausted
    Given CI failed for the active Story and PR
    And repair attempts equal max_repair_attempts
    When another repair is requested
    Then the state is BLOCKED_AUTOMATION
  @merge-gate @ci-integrity @audit
  Scenario: GitHub evidence authorizes merge only for exact HEAD
    Given factual PR checks security and review evidence were acquired from GitHub
    When required CI security review tested SHA and reviewed SHA match current HEAD
    Then the deterministic gate may report READY_TO_MERGE
  @merge-gate @stale-execution
  Scenario: old workflow run observes a new PR head
    Given an expected HEAD SHA was bound to the execution
    When newly acquired GitHub PR evidence has another HEAD SHA
    Then merge authority is denied as stale execution
  @protected-files @workflow-integrity
  Scenario: control-plane files change
    Given a PR changes workflow or Orchestrator control-plane files
    Then SECURITY_REVIEW_REQUIRED is required
  @generated @supply-chain
  Scenario: generated agentic workflow drifts
    Given an agentic workflow markdown source is canonical
    When recompilation does not reproduce its lock YAML
    Then CI fails closed
  @input-validation @adversarial
  Scenario: GitHub evidence is incomplete or ambiguous
    Given duplicate missing stale or malformed required GitHub evidence
    When the collector normalizes evidence
    Then privileged action fails closed
  @hardware @physical-boundary
  Scenario: software evidence cannot establish hardware verification
    Given CI mocks simulation and AI claim success
    When no physical evidence exists
    Then HARDWARE_VERIFIED is false
  @recovery @level2
  Scenario: recovery remains deterministic
    Given persisted binding and factual GitHub evidence
    When the AI engine is unavailable
    Then reconciliation remains available
