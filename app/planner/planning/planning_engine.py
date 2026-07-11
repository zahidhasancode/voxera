"""Execution plan generation."""

from app.core.enums import PlannerAction, PlannerIntent, PlannerRiskLevel
from app.planner.schemas import ExecutionPlan, OptimizedPlannerContext, PlannerInput


class PlanningEngine:
    """Generates goal, required info, execution plan, and completion criteria."""

    def build_plan(
        self,
        intent: PlannerIntent,
        context: OptimizedPlannerContext,
        planner_input: PlannerInput,
        *,
        action: PlannerAction,
        expected_tool: str | None = None,
    ) -> ExecutionPlan:
        message = (context.current_user_message or "").lower()
        wm = context.working_memory

        if intent == PlannerIntent.APPOINTMENT:
            return ExecutionPlan(
                goal="Book or manage customer appointment",
                required_information=["customer_name", "preferred_datetime", "service_type"],
                missing_information=self._missing(wm, ["customer_name", "email", "phone"]),
                execution_plan=[
                    "Verify customer identity",
                    "Check available appointment slots",
                    "Confirm booking details",
                    "Book appointment via appointment tool",
                ],
                expected_tool=expected_tool or "appointment",
                risk_level=PlannerRiskLevel.LOW,
                completion_criteria="Appointment confirmed and reference ID provided",
            )

        if intent == PlannerIntent.ORDER_STATUS:
            return ExecutionPlan(
                goal="Provide order status to customer",
                required_information=["order_number"],
                missing_information=self._missing(wm, ["order_number", "email"]),
                execution_plan=[
                    "Collect order number if missing",
                    "Look up order via order_lookup tool",
                    "Communicate status to customer",
                ],
                expected_tool=expected_tool or "order_lookup",
                risk_level=PlannerRiskLevel.LOW,
                completion_criteria="Customer informed of order status",
            )

        if intent == PlannerIntent.EMERGENCY:
            return ExecutionPlan(
                goal="Escalate emergency immediately",
                required_information=[],
                missing_information=[],
                execution_plan=["Transfer to human agent immediately"],
                expected_tool="human_transfer",
                risk_level=PlannerRiskLevel.CRITICAL,
                completion_criteria="Human agent engaged",
            )

        if intent == PlannerIntent.GREETING:
            return ExecutionPlan(
                goal="Greet customer and identify intent",
                required_information=[],
                missing_information=[],
                execution_plan=["Respond with greeting", "Ask how to help"],
                expected_tool=None,
                risk_level=PlannerRiskLevel.LOW,
                completion_criteria="Customer intent identified",
            )

        if intent == PlannerIntent.GENERAL_QUESTION and not context.retrieved_knowledge:
            return ExecutionPlan(
                goal="Answer customer question from knowledge base",
                required_information=["question"],
                missing_information=[],
                execution_plan=["Retrieve relevant knowledge", "Formulate response"],
                expected_tool=None,
                risk_level=PlannerRiskLevel.LOW,
                completion_criteria="Question answered with retrieved knowledge",
            )

        if intent == PlannerIntent.COMPLAINT:
            return ExecutionPlan(
                goal="Resolve customer complaint",
                required_information=["complaint_details"],
                missing_information=[],
                execution_plan=[
                    "Acknowledge complaint",
                    "Create support ticket",
                    "Offer escalation if needed",
                ],
                expected_tool="ticket_creation",
                risk_level=PlannerRiskLevel.MEDIUM,
                completion_criteria="Ticket created and customer acknowledged",
            )

        return ExecutionPlan(
            goal=f"Handle {intent.value} request",
            required_information=["clarification"],
            missing_information=["intent_details"] if intent == PlannerIntent.UNKNOWN else [],
            execution_plan=["Clarify customer intent", "Gather required information", "Execute appropriate action"],
            expected_tool=expected_tool,
            risk_level=PlannerRiskLevel.MEDIUM if intent == PlannerIntent.UNKNOWN else PlannerRiskLevel.LOW,
            completion_criteria="Customer request resolved or escalated",
        )

    def _missing(self, working_memory: dict[str, str], keys: list[str]) -> list[str]:
        return [k for k in keys if k not in working_memory or not working_memory[k]]
