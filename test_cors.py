#!/usr/bin/env python3
"""
CORS Configuration Test Script
===============================
Tests the Unk Agent FastAPI CORS middleware implementation.

Who Visions LLC - AI with Dav3
"""

import sys
import asyncio
from typing import Optional

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


class CORSTest:
    """Test CORS configuration."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self.results = []
        
    async def test_preflight(self, origin: str, expected_allowed: bool = True):
        """Test CORS preflight request."""
        print(f"\n🧪 Testing preflight for: {origin}")
        
        try:
            response = await self.client.options(
                f"{self.base_url}/chat",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type, Authorization"
                }
            )
            
            cors_allowed = "access-control-allow-origin" in response.headers
            
            if expected_allowed:
                if cors_allowed:
                    print(f"✅ PASS - Origin allowed")
                    print(f"   Allow-Origin: {response.headers.get('access-control-allow-origin')}")
                    print(f"   Allow-Methods: {response.headers.get('access-control-allow-methods')}")
                    print(f"   Allow-Headers: {response.headers.get('access-control-allow-headers')}")
                    self.results.append(("PASS", origin, "Preflight allowed"))
                else:
                    print(f"❌ FAIL - Origin should be allowed but was rejected")
                    self.results.append(("FAIL", origin, "Preflight rejected unexpectedly"))
            else:
                if cors_allowed:
                    print(f"⚠️  WARNING - Origin allowed but should be rejected (dev mode?)")
                    self.results.append(("WARNING", origin, "Preflight allowed in dev mode"))
                else:
                    print(f"✅ PASS - Origin correctly rejected")
                    self.results.append(("PASS", origin, "Preflight correctly blocked"))
                    
        except Exception as e:
            print(f"❌ ERROR - {e}")
            self.results.append(("ERROR", origin, str(e)))
    
    async def test_actual_request(self, origin: str, expected_allowed: bool = True):
        """Test actual CORS request."""
        print(f"\n🧪 Testing actual request for: {origin}")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat",
                headers={
                    "Origin": origin,
                    "Content-Type": "application/json",
                    "Authorization": "Bearer dev_token"
                },
                json={
                    "message": "Test message",
                    "mode": "default"
                }
            )
            
            cors_allowed = "access-control-allow-origin" in response.headers
            
            if expected_allowed:
                if cors_allowed:
                    print(f"✅ PASS - Request allowed")
                    print(f"   Status: {response.status_code}")
                    print(f"   Allow-Origin: {response.headers.get('access-control-allow-origin')}")
                    print(f"   Allow-Credentials: {response.headers.get('access-control-allow-credentials')}")
                    self.results.append(("PASS", origin, f"Request allowed ({response.status_code})"))
                else:
                    print(f"❌ FAIL - No CORS headers in response")
                    self.results.append(("FAIL", origin, "Missing CORS headers"))
            else:
                if cors_allowed:
                    print(f"⚠️  WARNING - Request allowed but should be rejected (dev mode?)")
                    self.results.append(("WARNING", origin, "Request allowed in dev mode"))
                else:
                    print(f"✅ PASS - Request correctly rejected")
                    self.results.append(("PASS", origin, "Request correctly blocked"))
                    
        except Exception as e:
            print(f"❌ ERROR - {e}")
            self.results.append(("ERROR", origin, str(e)))
    
    async def test_health_endpoint(self):
        """Test health endpoint without CORS."""
        print(f"\n🧪 Testing health endpoint")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed")
                print(f"   Status: {data.get('status')}")
                print(f"   Environment: {data.get('environment')}")
                print(f"   Version: {data.get('version')}")
                self.results.append(("PASS", "Health", "Endpoint responding"))
            else:
                print(f"❌ Health check failed - {response.status_code}")
                self.results.append(("FAIL", "Health", f"Status {response.status_code}"))
                
        except Exception as e:
            print(f"❌ ERROR - {e}")
            self.results.append(("ERROR", "Health", str(e)))
    
    async def test_a2a_identity(self):
        """Test A2A identity card endpoint."""
        print(f"\n🧪 Testing A2A identity card")
        
        try:
            response = await self.client.get(f"{self.base_url}/.well-known/agent.json")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ A2A identity card available")
                print(f"   Name: {data.get('name')}")
                print(f"   Version: {data.get('version')}")
                print(f"   Capabilities: {len(data.get('capabilities', []))}")
                self.results.append(("PASS", "A2A", "Identity card available"))
            else:
                print(f"❌ A2A identity failed - {response.status_code}")
                self.results.append(("FAIL", "A2A", f"Status {response.status_code}"))
                
        except Exception as e:
            print(f"❌ ERROR - {e}")
            self.results.append(("ERROR", "A2A", str(e)))
    
    async def run_all_tests(self):
        """Run all CORS tests."""
        print("=" * 80)
        print("🚀 CORS Configuration Test Suite")
        print("=" * 80)
        
        # Test server is running
        await self.test_health_endpoint()
        await self.test_a2a_identity()
        
        # Test allowed origins
        print("\n" + "=" * 80)
        print("📋 Testing Allowed Origins")
        print("=" * 80)
        
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://aiwithdav3.com",
            "https://www.aiwithdav3.com",
            "https://whovisions.com",
            "https://www.whovisions.com",
        ]
        
        for origin in allowed_origins:
            await self.test_preflight(origin, expected_allowed=True)
            await self.test_actual_request(origin, expected_allowed=True)
        
        # Test disallowed origins (production mode only)
        print("\n" + "=" * 80)
        print("🚫 Testing Disallowed Origins (if in production)")
        print("=" * 80)
        
        disallowed_origins = [
            "https://evil-site.com",
            "http://malicious.com",
        ]
        
        for origin in disallowed_origins:
            # Note: In development mode with CORS="*", these will pass
            await self.test_preflight(origin, expected_allowed=False)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)
        
        pass_count = sum(1 for r in self.results if r[0] == "PASS")
        fail_count = sum(1 for r in self.results if r[0] == "FAIL")
        error_count = sum(1 for r in self.results if r[0] == "ERROR")
        warning_count = sum(1 for r in self.results if r[0] == "WARNING")
        
        print(f"\n✅ Passed: {pass_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"⚠️  Warnings: {warning_count}")
        print(f"💥 Errors: {error_count}")
        print(f"📝 Total: {len(self.results)}")
        
        if fail_count == 0 and error_count == 0:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed or had errors")
            print("\nFailed/Error tests:")
            for result in self.results:
                if result[0] in ["FAIL", "ERROR"]:
                    print(f"  {result[0]}: {result[1]} - {result[2]}")
        
        await self.client.aclose()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Unk Agent CORS configuration")
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Base URL of the Unk Agent server (default: http://localhost:8080)"
    )
    
    args = parser.parse_args()
    
    tester = CORSTest(base_url=args.url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
