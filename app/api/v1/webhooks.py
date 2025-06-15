from fastapi import APIRouter, Request, HTTPException, status, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import Optional
from datetime import datetime
from app.config import settings
from app.database import get_async_db
from app.crud.user import user_crud

# Import Svix for webhook verification if Clerk uses Svix
from svix.webhooks import Webhook, WebhookVerificationError

router = APIRouter()

# You need to get your Webhook Signing Secret from the Clerk Dashboard
# Store it in your .env and load via settings
# settings.CLERK_WEBHOOK_SECRET

@router.post("/clerk", summary="Handle Clerk Webhooks")
async def handle_clerk_webhooks(
    request: Request,
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
    db: AsyncSession = Depends(get_async_db)
):
    if not settings.CLERK_WEBHOOK_SECRET:
        print("Warning: CLERK_WEBHOOK_SECRET not configured. Skipping webhook verification.")
        # In production, you should raise an error or ensure it's configured.
    elif not all([svix_id, svix_timestamp, svix_signature]):
        raise HTTPException(status_code=400, detail="Missing Svix headers for webhook verification")

    payload_bytes = await request.body()
    
    if settings.CLERK_WEBHOOK_SECRET:
        try:
            wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
            evt = wh.verify(payload_bytes, {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature,
            })
        except WebhookVerificationError as e:
            print(f"Webhook verification failed: {e}")
            raise HTTPException(status_code=400, detail="Webhook verification failed")
    else: # If secret not set, parse without verification (NOT FOR PRODUCTION)
        evt = json.loads(payload_bytes.decode('utf-8'))


    event_type = evt.get("type")
    data = evt.get("data")

    print(f"Received Clerk webhook event: {event_type}")

    if event_type == "user.created":
        print(f"Processing user.created for Clerk ID: {data.get('id')}")
        await user_crud.create_user_from_clerk(db, clerk_data=data)
    elif event_type == "user.updated":
        print(f"Processing user.updated for Clerk ID: {data.get('id')}")
        await user_crud.update_user_from_clerk(db, clerk_user_id=data.get("id"), clerk_data=data)
    elif event_type == "user.deleted":
        print(f"Processing user.deleted for Clerk ID: {data.get('id')}")
        clerk_user_id = data.get("id")
        if clerk_user_id:
            user_to_delete = await user_crud.get_user_by_clerk_id(db, clerk_user_id=clerk_user_id)
            if user_to_delete:
                # Decide: soft delete (is_active=False) or hard delete
                user_to_delete.is_active = False 
                db.add(user_to_delete)
                await db.commit()
                # await user_crud.remove(db, id=user_to_delete.id) # For hard delete
                print(f"User {clerk_user_id} marked as inactive/deleted.")
            else:
                print(f"User {clerk_user_id} for deletion not found in local DB.")
    elif event_type == "session.created":
        # You might want to update last_login_at for the user
        user_id = data.get("user_id") # This is Clerk User ID
        user = await user_crud.get_user_by_clerk_id(db, clerk_user_id=user_id)
        if user:
            user.last_login_at = datetime.utcnow() # Or parse from event if available
            user.login_count = (user.login_count or 0) + 1
            db.add(user)
            await db.commit()
    # Handle other events like session.revoked, organization.*, etc., as needed
    else:
        print(f"Unhandled Clerk event type: {event_type}")

    return {"status": "success", "message": "Webhook received"}