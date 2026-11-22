@security @P0 @state-machine @fail-closed
Feature: Orchestrator v2 deterministic security boundary
  @stale-execution @concurrency
  Scenario: stale execution cannot mutate a newer PR head
    Given an active Story is bound to a baseline PR and expected HEAD SHA
    When current evidence has another HEAD SHA
    Then autonomous privileged mutation is blocked
  @repair-loop @provider-failure
  Scenario: repair budget is exhausted
    Given CI failed for the active Story and PR
    And repair attempts equal max_repair_attempts
    Then the state is BLOCKED_AUTOMATION
  @merge-gate @ci-integrity @audit
  Scenario: privileged merge revalidates exact GitHub evidence
    Given persisted Story baseline PR and HEAD binding
    And fresh required CI security and review evidence for that HEAD
    When the privileged actor evaluates merge immediately before mutation
    Then merge may be authorized for exactly that HEAD
  @merge-gate @stale-execution
  Scenario: HEAD changes before privileged merge
    Given merge was previously eligible
    When fresh PR HEAD differs from expected HEAD
    Then privileged merge is denied as stale execution
  @protected-files @security
  Scenario: protected change lacks exact security review
    Given a PR changes protected control-plane files
    When no approved security review is bound to current HEAD
    Then privileged merge is denied
  @generated @supply-chain
  Scenario: generated agentic workflow drifts
    Given agentic markdown source is canonical
    When its lock YAML is stale
    Then CI fails closed
  @input-validation @adversarial
  Scenario: GitHub evidence is incomplete ambiguous or cancelled
    Given required GitHub evidence is missing stale duplicated unknown or cancelled
    Then privileged action fails closed
  @hardware @physical-boundary
  Scenario: software evidence cannot establish hardware verification
    Given CI mocks simulation and AI claim success
    When no physical evidence exists
    Then HARDWARE_VERIFIED is false
  @recovery @level2
  Scenario: recovery remains deterministic without AI
    Given persisted binding and factual GitHub evidence
    When AI is unavailable
    Then reconciliation remains available
  @adversarial @state-machine
  Scenario: untrusted executor cannot advance lifecycle authority
    Given a bounded executor request is bound to current Story baseline and state
    When a valid proposal result is accepted
    Then the deterministic lifecycle state does not advance
  @adversarial @stale-execution
  Scenario: stale executor result cannot affect current execution
    Given a bounded executor request is bound to current Story baseline and state
    When persisted Story baseline or state changes before result acceptance
    Then the executor result is rejected
  @hardware @physical-boundary
  Scenario: executor physical stop remains an operator boundary
    Given an executor reports PHYSICAL_ACTION_REQUIRED
    Then deterministic state becomes BLOCKED_HARDWARE
