#!/usr/bin/env python3
"""
Simple test for Multi-Agent Content Developer
Tests basic functionality without full workflow
"""
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Configure logging to see cleanup messages
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

from content_developer.models import Config
from multi_agent_content_developer import MultiAgentContentDeveloper

def test_multi_agent_basic():
    """Test basic multi-agent functionality"""
    
    print("🧪 Testing Multi-Agent Content Developer - Basic Test")
    print("=" * 50)
    
    try:
        # Test 1: Create configuration
        config = Config(
            repo_url="https://github.com/MicrosoftDocs/azure-aks-docs",
            content_goal="Create a test guide",
            service_area="Azure Kubernetes Service",
            work_dir=Path("./test_output"),
            support_materials=["test.md"],
            audience="developers",
            audience_level="intermediate",
            auto_confirm=True,
            multi_agent=True
        )
        print("✅ Configuration created")
        
        # Test 2: Initialize developer
        developer = MultiAgentContentDeveloper(config)
        print("✅ MultiAgentContentDeveloper initialized")
        
        # Test 3: Process a simple request
        print("\n📋 Testing documentation request processing...")
        try:
            result = developer.process_documentation_request()
            if result.success:
                print(f"✅ Documentation process completed: {result.message}")
            else:
                print(f"❌ Documentation process failed: {result.message}")
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_multi_agent_basic() 