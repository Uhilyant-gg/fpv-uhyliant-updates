@security @P0 @state-machine @fail-closed @level2
Feature: Orchestrator v2 deterministic security boundary

  @stale-execution @concurrency
  Scenario: stale execution cannot mutate a newer PR head
    Given an active Story is bound to a baseline, PR and expected HEAD SHA
    When the current PR HEAD no longer equals the expected HEAD SHA
    Then the execution is stale
    And autonomous privileged mutation is blocked

  @ci-integrity @stale-execution
  Scenario: baseline evidence changed
    Given an execution is bound to an exact baseline SHA
    When factual GitHub evidence reports another base SHA
    Then the execution binding is not current
    And autonomous privileged mutation is blocked

  @repair-loop @provider-failure
  Scenario: repair budget is exhausted
    Given CI failed for the active Story and PR
    And repair attempts equal max_repair_attempts
    When another repair is requested
    Then the state is BLOCKED_AUTOMATION

  @merge-gate @ci-integrity
  Scenario: reviewed SHA differs from current HEAD
    Given required CI and security checks are green
    And review approved an older SHA
    When merge eligibility is evaluated for the current HEAD
    Then merge is denied

  @protected-files @workflow-integrity
  Scenario: control-plane files change
    Given a PR changes workflow or Orchestrator control-plane files
    When autonomous merge eligibility is evaluated
    Then SECURITY_REVIEW_REQUIRED is required
    And the change cannot silently auto-merge

  @generated @supply-chain
  Scenario: generated agentic workflow drifts
    Given an agentic workflow markdown source is canonical
    When recompilation does not reproduce its lock YAML
    Then CI fails closed

  @hardware @physical-boundary
  Scenario: software evidence cannot establish hardware verification
    Given CI, mocks and simulation passed
    And AI claims hardware success
    When no physical evidence exists
    Then HARDWARE_VERIFIED is false

  @recovery @adversarial
  Scenario: reconciliation evidence is ambiguous
    Given persisted state and GitHub evidence do not identify one safe lifecycle state
    When deterministic reconciliation runs without AI
    Then the state is STATE_INCONSISTENT
