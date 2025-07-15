#!/usr/bin/env python3
"""
Test script for Multi-Agent Content Developer
Tests the basic multi-agent setup following the Azure AI Foundry pattern
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add references
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ConnectedAgentTool, MessageRole, ListSortOrder
from azure.identity import DefaultAzureCredential

def test_multi_agent_setup():
    """Test basic multi-agent setup"""
    
    # Clear the console
    os.system('cls' if os.name=='nt' else 'clear')
    
    # Get configuration
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
    
    if not project_endpoint or not model_deployment:
        print("❌ Missing required environment variables:")
        print("   PROJECT_ENDPOINT:", project_endpoint or "NOT SET")
        print("   MODEL_DEPLOYMENT_NAME:", model_deployment or "NOT SET")
        print("\nPlease set these in your .env file.")
        return False
    
    print("🔧 Testing Multi-Agent Setup")
    print(f"   Endpoint: {project_endpoint}")
    print(f"   Model: {model_deployment}")
    print()
    
    try:
        # Initialize client
        print("📡 Connecting to Azure AI Foundry...")
        agents_client = AgentsClient(
            endpoint=project_endpoint,
            credential=DefaultAzureCredential(
                exclude_environment_credential=True,
                exclude_managed_identity_credential=True
            ),
        )
        
        with agents_client:
            # Create a simple test agent
            print("🤖 Creating test agent...")
            test_agent = agents_client.create_agent(
                model=model_deployment,
                name="test_agent",
                instructions="You are a test agent. Simply respond with 'Test successful!'"
            )
            print("✅ Test agent created successfully")
            
            # Create thread
            print("🧵 Creating thread...")
            thread = agents_client.threads.create()
            print("✅ Thread created successfully")
            
            # Send test message
            print("💬 Sending test message...")
            message = agents_client.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content="Hello, test agent!"
            )
            
            # Process
            print("⚙️  Processing...")
            run = agents_client.runs.create_and_process(
                thread_id=thread.id, 
                agent_id=test_agent.id
            )
            
            # Get response
            messages = agents_client.messages.list(
                thread_id=thread.id, 
                order=ListSortOrder.ASCENDING
            )
            
            # Display response
            print("\n📨 Response:")
            for msg in messages:
                if msg.text_messages:
                    print(f"   {msg.role}: {msg.text_messages[-1].text.value}")
            
            # Clean up
            print("\n🧹 Cleaning up...")
            agents_client.delete_agent(test_agent.id)
            print("✅ Test agent deleted")
            
            print("\n✨ Multi-agent setup test completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify your Azure AI Foundry project is active")
        print("2. Check that your model deployment is ready")
        print("3. Ensure you have proper authentication")
        print("   - Run 'az login' for Azure CLI auth")
        print("   - Or configure service principal in .env")
        return False


def test_content_developer_import():
    """Test that the multi-agent content developer can be imported"""
    print("\n📦 Testing Multi-Agent Content Developer import...")
    
    try:
        from multi_agent_content_developer import MultiAgentContentDeveloper
        print("✅ MultiAgentContentDeveloper imported successfully")
        
        # Test that all required prompts are available
        from content_developer.prompts import (
            MATERIAL_SUMMARY_SYSTEM,
            DIRECTORY_SELECTION_SYSTEM,
            UNIFIED_CONTENT_STRATEGY_SYSTEM,
            CREATE_CONTENT_SYSTEM,
            SEO_REMEDIATION_SYSTEM,
            SECURITY_REMEDIATION_SYSTEM,
            ACCURACY_VALIDATION_SYSTEM,
            TOC_UPDATE_SYSTEM,
            get_content_quality_system
        )
        print("✅ All required prompts are available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("\nMake sure you have:")
        print("1. Created multi_agent_content_developer.py")
        print("2. Installed all requirements: pip install -r requirements-multi-agent.txt")
        return False


if __name__ == "__main__":
    print("🚀 Multi-Agent Content Developer Test Suite")
    print("=" * 50)
    
    # Test imports first
    if not test_content_developer_import():
        sys.exit(1)
    
    # Test Azure AI setup
    if not test_multi_agent_setup():
        sys.exit(1)
    
    print("\n🎉 All tests passed! Your multi-agent system is ready to use.")
    print("\nTry running:")
    print("  python main.py <repo> <goal> <service> <materials> --multi-agent")
    print("\nFor more details, see docs/MULTI_AGENT_SETUP.md") 