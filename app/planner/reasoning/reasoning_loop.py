"""Multi-step reasoning loop."""

from app.core.config import settings
from app.core.enums import PlannerAction, PlannerDecisionStatus, PlannerIntent, SessionState
from app.planner.planning.planning_engine import PlanningEngine
from app.planner.reasoning.intent_engine import IntentEngine
from app.planner.schemas import OptimizedPlannerContext, PlannerInput, PlannerPlan, ToolCallPlan


class ReasoningLoop:
    """Evaluates context through configurable reasoning steps."""

    def __init__(
        self,
        *,
        intent_engine: IntentEngine | None = None,
        planning_engine: PlanningEngine | None = None,
        max_steps: int | None = None,
    ) -> None:
        self._intent = intent_engine or IntentEngine()
        self._planning = planning_engine or PlanningEngine()
        self._max_steps = max_steps or settings.PLANNER_MAX_REASONING_STEPS

    def evaluate(
        self,
        context: OptimizedPlannerContext,
        planner_input: PlannerInput,
        *,
        intent: PlannerIntent,
        confidence: float,
    ) -> PlannerPlan:
        reasoning: list[str] = []
        message = context.current_user_message or ""

        reasoning.append(f"Classified intent as {intent.value} with confidence {confidence:.2f}")

        if intent == PlannerIntent.EMERGENCY:
            return self._build(
                intent=intent,
                confidence=confidence,
                action=PlannerAction.TRANSFER_HUMAN,
                next_action="transfer_human",
                reasoning=reasoning + ["Emergency detected — immediate human transfer"],
                context=context,
                planner_input=planner_input,
                tool_call=ToolCallPlan(tool_slug="human_transfer", arguments={"reason": "emergency", "department": "emergency"}),
                response="I'm connecting you to a specialist immediately. Please stay on the line.",
                status=PlannerDecisionStatus.ESCALATED,
            )

        if confidence < settings.PLANNER_ESCALATION_CONFIDENCE_THRESHOLD:
            reasoning.append("Confidence too low — asking clarification")
            return self._build(
                intent=intent,
                confidence=confidence,
                action=PlannerAction.ASK_CLARIFICATION,
                next_action="clarify_intent",
                reasoning=reasoning,
                context=context,
                planner_input=planner_input,
                response=self._clarification_response(planner_input.language),
                status=PlannerDecisionStatus.NEEDS_CLARIFICATION,
            )

        if intent == PlannerIntent.GREETING:
            reasoning.append("Greeting detected — respond and probe intent")
            return self._build(
                intent=intent,
                confidence=confidence,
                action=PlannerAction.RESPOND,
                next_action="identify_intent",
                reasoning=reasoning,
                context=context,
                planner_input=planner_input,
                response=self._greeting_response(planner_input.language),
            )

        needs_knowledge = (
            intent in (PlannerIntent.GENERAL_QUESTION, PlannerIntent.TECHNICAL_ISSUE)
            and not context.retrieved_knowledge
            and context.current_state != SessionState.RETRIEVAL_RUNNING
        )
        if needs_knowledge:
            reasoning.append("Knowledge required — plan retrieval")
            return self._build(
                intent=intent,
                confidence=confidence,
                action=PlannerAction.RETRIEVE,
                next_action="retrieve_knowledge",
                reasoning=reasoning,
                context=context,
                planner_input=planner_input,
                response=None,
                status=PlannerDecisionStatus.NEEDS_RETRIEVAL,
                retrieval_query=message,
            )

        tool_action = self._resolve_tool_action(intent, context, planner_input)
        if tool_action:
            action, tool_slug, tool_args, next_action, response, reasoning_extra = tool_action
            reasoning.extend(reasoning_extra)
            return self._build(
                intent=intent,
                confidence=confidence,
                action=action,
                next_action=next_action,
                reasoning=reasoning,
                context=context,
                planner_input=planner_input,
                tool_call=ToolCallPlan(tool_slug=tool_slug, arguments=tool_args) if tool_slug else None,
                response=response,
                status=PlannerDecisionStatus.NEEDS_TOOL if action == PlannerAction.CALL_TOOL else PlannerDecisionStatus.COMPLETED,
                expected_tool=tool_slug,
            )

        if intent == PlannerIntent.COMPLAINT:
            reasoning.append("Complaint detected — escalate with empathy")
            return self._build(
                intent=intent,
                confidence=confidence,
                action=PlannerAction.ESCALATE,
                next_action="create_ticket",
                reasoning=reasoning,
                context=context,
                planner_input=planner_input,
                tool_call=ToolCallPlan(
                    tool_slug="ticket_creation",
                    arguments={"subject": "Customer complaint", "description": message, "priority": "high"},
                ),
                response="I understand your frustration. I'm creating a priority ticket for our team.",
                status=PlannerDecisionStatus.NEEDS_TOOL,
                expected_tool="ticket_creation",
            )

        reasoning.append("Default respond path")
        return self._build(
            intent=intent,
            confidence=confidence,
            action=PlannerAction.RESPOND,
            next_action="respond",
            reasoning=reasoning,
            context=context,
            planner_input=planner_input,
            response="How can I assist you further?",
        )

    def _resolve_tool_action(
        self,
        intent: PlannerIntent,
        context: OptimizedPlannerContext,
        planner_input: PlannerInput,
    ) -> tuple | None:
        available = {t.slug for t in planner_input.available_tools if t.enabled}
        wm = context.working_memory

        if intent == PlannerIntent.APPOINTMENT and "appointment" in available:
            if "email" not in wm and "phone" not in wm:
                return (
                    PlannerAction.RESPOND,
                    None,
                    {},
                    "verify_identity",
                    "Certainly. May I have your registered email or phone number?",
                    ["Appointment intent — identity verification required first"],
                )
            return (
                PlannerAction.CALL_TOOL,
                "appointment",
                {"action": "book", "customer_email": wm.get("email"), "customer_phone": wm.get("phone")},
                "book_appointment",
                "I'm checking available appointment slots for you.",
                ["Identity present — plan appointment booking tool"],
            )

        if intent == PlannerIntent.ORDER_STATUS and "order_lookup" in available:
            order_num = wm.get("order_number")
            if not order_num:
                return (
                    PlannerAction.ASK_CLARIFICATION,
                    None,
                    {},
                    "collect_order_number",
                    "Could you please provide your order number?",
                    ["Order lookup requires order number"],
                )
            return (
                PlannerAction.CALL_TOOL,
                "order_lookup",
                {"order_number": order_num},
                "lookup_order",
                "Let me check your order status.",
                ["Order number available — plan order lookup"],
            )

        if intent == PlannerIntent.IDENTITY_VERIFICATION and "identity_verification" in available:
            return (
                PlannerAction.CALL_TOOL,
                "identity_verification",
                {"method": "otp_email", "identifier": wm.get("email", "")},
                "verify_identity",
                "I'll send a verification code to your registered email.",
                ["Identity verification flow initiated"],
            )

        return None

    def _build(
        self,
        *,
        intent: PlannerIntent,
        confidence: float,
        action: PlannerAction,
        next_action: str,
        reasoning: list[str],
        context: OptimizedPlannerContext,
        planner_input: PlannerInput,
        tool_call: ToolCallPlan | None = None,
        response: str | None = None,
        status: PlannerDecisionStatus = PlannerDecisionStatus.COMPLETED,
        retrieval_query: str | None = None,
        expected_tool: str | None = None,
    ) -> PlannerPlan:
        plan = self._planning.build_plan(
            intent, context, planner_input, action=action, expected_tool=expected_tool or (tool_call.tool_slug if tool_call else None)
        )
        return PlannerPlan(
            intent=intent,
            confidence=confidence,
            reasoning=reasoning[: self._max_steps],
            next_action=next_action,
            action=action,
            tool_call=tool_call,
            response=response,
            plan=plan,
            status=status,
            language=planner_input.language,
            retrieval_query=retrieval_query,
        )

    def _greeting_response(self, language: str) -> str:
        responses = {
            "en": "Hello! How can I help you today?",
            "es": "¡Hola! ¿En qué puedo ayudarle hoy?",
            "fr": "Bonjour! Comment puis-je vous aider?",
            "de": "Hallo! Wie kann ich Ihnen heute helfen?",
            "ar": "مرحباً! كيف يمكنني مساعدتك اليوم؟",
            "bn": "হ্যালো! আজ আমি কীভাবে সাহায্য করতে পারি?",
        }
        return responses.get(language, responses["en"])

    def _clarification_response(self, language: str) -> str:
        responses = {
            "en": "Could you please tell me more about what you need help with?",
            "es": "¿Podría decirme más sobre en qué necesita ayuda?",
            "fr": "Pourriez-vous m'en dire plus sur ce dont vous avez besoin?",
            "de": "Könnten Sie mir bitte mehr darüber sagen, wobei Sie Hilfe benötigen?",
            "ar": "هل يمكنك إخباري بالمزيد عما تحتاج المساعدة فيه؟",
            "bn": "আপনি কী নিয়ে সাহায্য চান, একটু বিস্তারিত বলবেন?",
        }
        return responses.get(language, responses["en"])
