#!/usr/bin/env python3
"""
Debug Subscription Lookup
Check if subscription exists and debug phone number formats
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.supabase_client import SupabaseService
from app.deps import get_supabase_client

# Load environment variables
load_dotenv()

async def debug_subscription():
    """Debug subscription lookup"""
    
    print("🔍 Debugging subscription lookup...")
    
    try:
        # Get Supabase client
        supabase_client = get_supabase_client()
        supabase_service = SupabaseService(supabase_client)
        
        # Test different phone number formats
        test_numbers = [
            "+31657779475",
            "31657779475", 
            "whatsapp:+31657779475",
            "+31 6 5777 9475"
        ]
        
        for phone_number in test_numbers:
            print(f"\n📱 Testing lookup for: '{phone_number}'")
            
            try:
                subscription = await supabase_service.get_subscription_by_wa_id(phone_number)
                
                if subscription:
                    print(f"✅ FOUND subscription!")
                    print(f"   ID: {subscription.get('id')}")
                    print(f"   Status: {subscription.get('status')}")
                    print(f"   Phone: {subscription.get('phone_number')}")
                    print(f"   WA ID: {subscription.get('wa_id')}")
                else:
                    print(f"❌ No subscription found")
                    
            except Exception as e:
                print(f"❌ Error querying: {e}")
        
        # Also check all subscriptions in database
        print(f"\n📊 Checking all subscriptions in database...")
        
        # Get all subscriptions (this might need a different method)
        try:
            # Direct Supabase query to see all data
            result = supabase_client.table("subscribers").select("*").execute()
            
            if result.data:
                print(f"Found {len(result.data)} total subscriptions:")
                for sub in result.data:
                    print(f"  - ID: {sub.get('id')}")
                    print(f"    Phone: {sub.get('phone_number')}")
                    print(f"    WA ID: {sub.get('wa_id')}")
                    print(f"    Status: {sub.get('status')}")
                    print()
            else:
                print("❌ No subscriptions found in database")
                
        except Exception as e:
            print(f"❌ Error getting all subscriptions: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Subscription Debug...")
    asyncio.run(debug_subscription())