"""Chat interface API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas import ChatRequest, ChatResponse
from app.agents import memorabot
from app.utils import generate_conversation_id

logger = logging.getLogger("memorabot.chat")
router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """Process a chat message through the agent."""

    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or generate_conversation_id()

    try:
        # Process message through agent
        result = await memorabot.process_message(
            message=request.message,
            conversation_id=conversation_id,
            user_id=request.user_id
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/history/{conversation_id}")
async def get_chat_history(conversation_id: str) -> dict:
    """Get chat history for a conversation."""
    conversation = memorabot.get_conversation_history(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )

    return {
        "conversation_id": conversation_id,
        "messages": [msg.model_dump() for msg in conversation.messages],
        "started_at": conversation.started_at.isoformat(),
        "last_activity": conversation.last_activity.isoformat()
    }


@router.delete("/clear/{conversation_id}")
async def clear_chat(conversation_id: str) -> dict:
    """Clear a specific chat session."""
    success = memorabot.clear_conversation(conversation_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )

    return {
        "status": "cleared",
        "conversation_id": conversation_id
    }