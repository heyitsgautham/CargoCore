"""Executes the SQL tool calls Gemini makes and summarises their results."""

import uuid

from google.genai import types
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.user import User
from app.schemas.ai import (
    ChatResponse,
)
from app.services.ai_chat.conversations import _persist_message
from app.services.ai_chat.intents import _safe_message_text
from app.services.ai_chat.sql_scope import (
    _format_results_fallback,
    _make_json_serializable,
    _scope_sql_for_user,
)
from app.services.sql_validator import SQLValidationError, validate_sql
from app.utils.gemini import (
    EXECUTE_SQL_TOOL,
    generate_with_fallback,
)

# ── Function Call Handler ─────────────────────────────────────────────────────


async def _handle_function_call(
    db: AsyncSession,
    ro_db: AsyncSession,
    user: User,
    session_id: uuid.UUID,
    user_message: str,
    linked_order_meta: dict[str, str] | None,
    linked_order: Order | None,
    client,
    contents: list,
    response,
    function_call,
    system_instruction: str,
) -> ChatResponse:
    """
    Handle a Gemini function call (execute_sql_query).

    Validates the SQL, executes on read-only session, feeds results back to Gemini.
    Uses the new google-genai SDK pattern for multi-turn function calling.
    """
    fn_name = function_call.name
    fn_args = dict(function_call.args) if function_call.args else {}

    logger.info(f"Gemini function call: {fn_name}({fn_args})")

    if fn_name != "execute_sql_query":
        logger.warning(f"Unknown function call: {fn_name}")
        error_msg = "I tried to use an unknown tool. Let me try answering directly."
        await _persist_message(
            db,
            session_id,
            user.id,
            "user",
            user_message,
            "error",
            linked_order_meta=linked_order_meta,
        )
        await _persist_message(
            db,
            session_id,
            user.id,
            "assistant",
            error_msg,
            "error",
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=error_msg,
            intent="error",
            sql_generated=None,
            requires_human=False,
            human_handoff_reason=None,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    raw_sql = fn_args.get("sql_query", "")

    # ── Validate SQL ──────────────────────────────────────────────────────
    try:
        validated_sql = validate_sql(raw_sql)
    except SQLValidationError as e:
        logger.warning(f"SQL validation failed: {e} | SQL: {raw_sql}")
        # Build the function response with error and send back to Gemini
        error_result = {"error": f"Query rejected: {str(e)}"}
        try:
            # Append the model's function call + our error response, then re-call
            follow_up_contents = contents + [
                response.candidates[0].content,
                types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name="execute_sql_query",
                            response=error_result,
                        )
                    ],
                ),
            ]
            follow_up = await generate_with_fallback(
                contents=follow_up_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[EXECUTE_SQL_TOOL],
                ),
            )
            assistant_message = _safe_message_text(
                follow_up.text,
                "I could not format the validation error response. Please rephrase your request.",
            )
        except Exception:
            assistant_message = (
                f"I tried to query the database but the query was rejected: {str(e)}. "
                "Could you rephrase your question?"
            )

        await _persist_message(
            db, session_id, user.id, "user", user_message, "error",
            sql_generated=raw_sql,
            linked_order_meta=linked_order_meta,
        )
        await _persist_message(
            db, session_id, user.id, "assistant", assistant_message, "error",
            sql_generated=raw_sql,
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="error",
            sql_generated=raw_sql,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    # ── Execute SQL on read-only session ──────────────────────────────────
    role_scoped_sql = validated_sql
    try:
        role_scoped_sql = _scope_sql_for_user(validated_sql, user)
    except SQLValidationError as e:
        logger.warning(f"Role scope validation failed: {e} | SQL: {validated_sql}")
        assistant_message = (
            "I can only access data for your own account in this assistant. "
            "Please ask using your own orders, shipments, or payments."
        )
        await _persist_message(
            db, session_id, user.id, "user", user_message, "error",
            sql_generated=validated_sql,
            linked_order_meta=linked_order_meta,
        )
        await _persist_message(
            db, session_id, user.id, "assistant", assistant_message, "error",
            sql_generated=validated_sql,
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="error",
            sql_generated=validated_sql,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    try:
        result = await ro_db.execute(text(role_scoped_sql))
        rows = result.fetchall()
        columns = list(result.keys())

        # Serialize results to JSON-friendly format
        query_result = [dict(zip(columns, row, strict=True)) for row in rows]

        # Convert non-serializable types (UUID, datetime, etc.)
        query_result = _make_json_serializable(query_result)

        logger.info(f"SQL executed successfully: {len(query_result)} rows returned")

    except Exception as e:
        logger.error(f"SQL execution error: {e} | SQL: {validated_sql}")
        error_result = {"error": f"Query execution failed: {str(e)}"}
        try:
            follow_up_contents = contents + [
                response.candidates[0].content,
                types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name="execute_sql_query",
                            response=error_result,
                        )
                    ],
                ),
            ]
            follow_up = await generate_with_fallback(
                contents=follow_up_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[EXECUTE_SQL_TOOL],
                ),
            )
            assistant_message = _safe_message_text(
                follow_up.text,
                "I could not run that data query due to a database mismatch, but I can still help. "
                "Try: 'Where is my latest order?', 'Show my dashboard summary', or 'What is my wallet balance?'."
            )
        except Exception:
            assistant_message = (
                "I tried to query the database but encountered an execution error. "
                "Could you rephrase your question?"
            )

        await _persist_message(
            db, session_id, user.id, "user", user_message, "error",
            sql_generated=role_scoped_sql,
            linked_order_meta=linked_order_meta,
        )
        await _persist_message(
            db, session_id, user.id, "assistant", assistant_message, "error",
            sql_generated=role_scoped_sql,
            linked_order_meta=linked_order_meta,
        )
        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            intent="error",
            sql_generated=role_scoped_sql,
            linked_order_id=linked_order.id if linked_order else None,
            linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
        )

    # ── Feed results back to Gemini ───────────────────────────────────────
    function_response_data = {
        "columns": columns,
        "row_count": len(query_result),
        "data": query_result,
    }

    try:
        # Build multi-turn: original contents + model's function call + our result
        follow_up_contents = contents + [
            response.candidates[0].content,
            types.Content(
                role="tool",
                parts=[
                    types.Part.from_function_response(
                        name="execute_sql_query",
                        response=function_response_data,
                    )
                ],
            ),
        ]
        follow_up = await generate_with_fallback(
            contents=follow_up_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[EXECUTE_SQL_TOOL],
            ),
        )
        assistant_message = _safe_message_text(
            follow_up.text,
            _format_results_fallback(query_result, columns),
        )
    except Exception as e:
        logger.error(f"Gemini response error after function call: {e}")
        # Fallback: format results directly
        assistant_message = _format_results_fallback(query_result, columns)

    # ── Persist messages ──────────────────────────────────────────────────
    await _persist_message(
        db, session_id, user.id, "user", user_message, "db_query",
        sql_generated=role_scoped_sql, query_result=query_result,
        linked_order_meta=linked_order_meta,
    )
    await _persist_message(
        db, session_id, user.id, "assistant", assistant_message, "db_query",
        sql_generated=role_scoped_sql,
        linked_order_meta=linked_order_meta,
    )

    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        intent="db_query",
        sql_generated=role_scoped_sql,
        linked_order_id=linked_order.id if linked_order else None,
        linked_order_tracking_code=linked_order.tracking_code if linked_order else None,
    )
