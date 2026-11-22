@security @P0 @state-machine @fail-closed @level2
Feature: Orchestrator v2 deterministic security boundary
  @stale-execution @concurrency
  Scenario: stale execution cannot mutate a newer PR head
    Given an active Story is bound to a baseline, PR and expected HEAD SHA
    When the current PR HEAD no longer equals the expected HEAD SHA
    Then autonomous privileged mutation is blocked
  @ci-integrity @stale-execution
  Scenario: baseline evidence changed
    Given an execution is bound to an exact baseline SHA
    When factual GitHub evidence reports another base SHA
    Then autonomous privileged mutation is blocked
  @repair-loop @provider-failure
  Scenario: repair budget is exhausted
    Given CI failed for the active Story and PR
    And repair attempts equal max_repair_attempts
    When another repair is requested
    Then the state is BLOCKED_AUTOMATION
  @repair-loop @stale-execution
  Scenario: repair is scoped to exact execution
    Given CI failed for the active Story and PR
    When Story baseline PR or HEAD differs from the persisted binding
    Then AI repair is not invoked
  @merge-gate @ci-integrity
  Scenario: reviewed or tested SHA differs from current HEAD
    Given required CI and security checks are green
    When review or required checks refer to another HEAD
    Then merge is denied
  @protected-files @workflow-integrity
  Scenario: control-plane files change
    Given a PR changes workflow or Orchestrator control-plane files
    Then SECURITY_REVIEW_REQUIRED is required
  @generated @supply-chain
  Scenario: generated agentic workflow drifts
    Given an agentic workflow markdown source is canonical
    When recompilation does not reproduce its lock YAML
    Then CI fails closed
  @recovery @audit
  Scenario: persisted state is recovered without AI
    Given versioned state and exact factual GitHub evidence
    When deterministic reconciliation runs without an AI engine
    Then lifecycle state is recovered from evidence
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
