# Severity Policy

## Component

release_pipeline

## Symptoms

- Incident reports use inconsistent severity labels.
- Teams disagree on escalation urgency for customer-impacting bugs.
- Issues with deployment or update failures lack clear triage priority.
- Support requests are missing impact, scope, or workaround information.

## Common Root Causes

- Severity is assigned from technical component ownership instead of customer impact.
- Issue reports omit affected version, rollout percentage, or user segment.
- Regression and incident labels are applied inconsistently across teams.
- On-call escalation criteria are not included in issue templates.

## Recommended Next Steps

- Assign severity based on user impact, blast radius, and availability of workaround.
- Use `sev1` for broad production outage, security exposure, or data loss risk.
- Use `sev2` for major feature failure, failed production rollout, or high-volume customer impact.
- Use `sev3` for limited-impact regressions, isolated customer reports, or known workaround cases.
- Include affected versions, rollout cohort, environment, owner team, and mitigation status.

## Related Keywords

severity, triage, incident, escalation, sev1, sev2, sev3, regression, customer impact, rollout
