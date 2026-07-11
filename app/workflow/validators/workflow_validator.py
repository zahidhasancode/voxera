"""Workflow definition and input validation."""

from app.workflow.schemas import ValidateWorkflowRequest, WorkflowRuleDefinition


class WorkflowValidator:
    def validate_definition(self, request: ValidateWorkflowRequest) -> list[str]:
        violations: list[str] = []
        definition = request.definition

        if not definition.get("slug") and not definition.get("name"):
            violations.append("missing_slug_or_name")

        steps = definition.get("steps", [])
        if not isinstance(steps, list):
            violations.append("steps_must_be_list")

        rules = definition.get("rules", [])
        for idx, rule in enumerate(rules):
            try:
                WorkflowRuleDefinition.model_validate(rule)
            except Exception as exc:
                violations.append(f"invalid_rule_{idx}:{exc}")

        approval_chain = definition.get("approval_chain", [])
        if approval_chain and not isinstance(approval_chain, list):
            violations.append("approval_chain_must_be_list")

        return violations
