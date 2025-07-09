#!/usr/bin/env python3
"""
Script to update a user's role to ADMIN
Usage: python update_user_role.py <clerk_user_id>
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.crud.user import user_crud
from app.models.user import UserRole

async def update_user_to_admin(clerk_user_id: str):
    """Update a user's role to ADMIN by their Clerk user ID"""
    async for db in get_async_db():
        try:
            # Find the user by Clerk ID
            user = await user_crud.get_user_by_clerk_id(db, clerk_user_id=clerk_user_id)
            
            if not user:
                print(f"❌ User with Clerk ID '{clerk_user_id}' not found in database")
                return False
            
            print(f"✅ Found user: {user.email} (ID: {user.id})")
            print(f"   Current role: {user.role}")
            
            # Update the role to ADMIN
            user.role = UserRole.ADMIN.value
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            print(f"✅ Successfully updated user role to: {user.role}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user: {e}")
            await db.rollback()
            return False
        finally:
            await db.close()

async def main():
    if len(sys.argv) != 2:
        print("Usage: python update_user_role.py <clerk_user_id>")
        print("Example: python update_user_role.py user_2yEuhn2z7dSQsW8ZvY1uzZ09Dd1")
        sys.exit(1)
    
    clerk_user_id = sys.argv[1]
    print(f"🔄 Updating user with Clerk ID: {clerk_user_id}")
    
    success = await update_user_to_admin(clerk_user_id)
    
    if success:
        print("🎉 User role updated successfully!")
        print("You can now access admin endpoints with your JWT token.")
    else:
        print("💥 Failed to update user role.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 