#!/usr/bin/env python3
"""Quick Bedrock connectivity test - run this to verify bearer token works."""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

async def main():
    from app.ai.llm import BedrockProvider
    
    print("\n" + "="*60)
    print("BEDROCK CONNECTIVITY TEST")
    print("="*60)
    
    provider = BedrockProvider()
    
    print(f"\n📋 Configuration:")
    print(f"   Region: {provider.region}")
    print(f"   Model: {provider.model}")
    print(f"   Bearer token set: {'✅ Yes' if provider.bearer else '❌ No'}")
    print(f"   IAM auth available: {'✅ Yes' if provider.use_iam else '❌ No'}")
    print(f"   Is configured: {'✅ Yes' if provider.configured() else '❌ No'}")
    
    if not provider.configured():
        print("\n❌ BEDROCK NOT CONFIGURED")
        print("\n📝 To fix:")
        print("   1. Go to AWS Bedrock console → Model access")
        print("   2. Enable: anthropic.claude-3-5-sonnet-20241022-v2:0")
        print("   3. Generate AWS access key with base64 format:")
        print("      bedrock-api-key-<base64(AccessKey:SecretKey)>")
        print("   4. Set AWS_BEARER_TOKEN_BEDROCK in .env")
        return False
    
    print("\n🔄 Sending test request...")
    try:
        text = await provider.chat(
            messages=[{"role": "user", "content": "Say 'Bedrock is working' in 5 words or less"}],
            system="You are a helpful assistant.",
            max_tokens=50
        )
        print(f"\n✅ SUCCESS!\n   Response: {text}")
        return True
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        
        # Parse error type
        error_str = str(e).lower()
        if "400" in error_str or "not found" in error_str:
            print("\n💡 Likely cause: Invalid bearer token or model not enabled")
            print("   → Check AWS console for model access status")
        elif "401" in error_str or "unauthorized" in error_str:
            print("\n💡 Likely cause: Bearer token expired or invalid credentials")
            print("   → Generate new access key and recreate bearer token")
        elif "403" in error_str or "forbidden" in error_str:
            print("\n💡 Likely cause: IAM permissions missing")
            print("   → Add bedrock:InvokeModel permission to IAM role")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print("\n" + "="*60 + "\n")
    sys.exit(0 if success else 1)
