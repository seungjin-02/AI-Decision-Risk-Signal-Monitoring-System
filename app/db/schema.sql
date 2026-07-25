CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY,
    trace_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    level TEXT NOT NULL
        CHECK (level in ('INFO', 'WARN', 'CRITICAL')),
    risk_score INTEGER NOT NULL
        CHECK (risk_score >= 0),
    uncertainty_score INTEGER NOT NULL
        CHECK (uncertainty_score >= 0),
    human_required INTEGER NOT NULL
        CHECK (human_required in (0, 1)),
    reason_summary TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}'
        CHECK (json_valid(metadata) and json_type(metadata) = 'object'),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_signals (
    signal_id INTEGER PRIMARY KEY,
    alert_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,
    category TEXT NOT NULL
        CHECK (category in ('risk', 'uncertainty', 'failure', 'stability')),
    score INTEGER NOT NULL
        CHECK (score >= 0),
    reason TEXT NOT NULL,
    evidence TEXT NOT NULL DEFAULT '{}'
        CHECK (json_valid(evidence) and json_type(evidence) = 'object'),
    is_critical_override INTEGER NOT NULL
        CHECK (is_critical_override in (0, 1)),
    metadata TEXT NOT NULL DEFAULT '{}'
        CHECK (json_valid(metadata) and json_type(metadata) = 'object'),

    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id) ON DELETE CASCADE,
    UNIQUE (alert_id, rule_id)
);

CREATE TABLE IF NOT EXISTS alert_actions (
    action_id INTEGER PRIMARY KEY,
    alert_id INTEGER NOT NULL,
    action_word TEXT NOT NULL,
    action_order INTEGER NOT NULL
        CHECK (action_order >= 0),

    FOREIGN KEY (alert_id) REFERENCES alerts(alert_id) ON DELETE CASCADE,
    UNIQUE (alert_id, action_word),
    UNIQUE (alert_id, action_order)
);

CREATE INDEX IF NOT EXISTS idx_alerts_trace_id
    ON alerts(trace_id);

CREATE INDEX IF NOT EXISTS idx_alerts_event_id
    ON alerts(event_id);

CREATE INDEX IF NOT EXISTS idx_alerts_created_at
    ON alerts(created_at DESC);