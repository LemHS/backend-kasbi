import uuid
import os
import requests
from datetime import datetime, timezone

from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Query
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.schemas.common import APIResponse

from app.database import get_db

from app.config import get_settings

router = APIRouter(prefix="/v1/whatsapp", tags=["Whatsapp"])

settings = get_settings()

def send_whatsapp_message(to: str, body: str):
    """
    Calls the WhatsApp Cloud API to send a text message.
    """
    url = f"https://graph.facebook.com/{settings.VERSION}/{settings.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }

    response = requests.post(url, headers=headers, json=payload)

    return response


@router.post("/webhook", response_model=APIResponse)
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    background_tasks.add_task(process_whatsapp_message, data)

    # Return 200 OK immediately to acknowledge receipt
    return APIResponse(
        status_code=200, 
        message="Message received")

async def process_whatsapp_message(data: dict):
    # Extract message updates
    entry = data.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    if "messages" not in value:
        return

    messages = value["messages"]
    if not messages:
        return
    # Extract user message
    message = messages[0]
    from_number = message["from"]
    user_text = message["text"]["body"]
    send_whatsapp_message(to=from_number, body="halo")


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    verify_token = settings.VERIFY_TOKEN
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")