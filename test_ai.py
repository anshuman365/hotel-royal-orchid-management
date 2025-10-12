# test_ai_service.py
import requests
import json
from datetime import datetime

def test_openrouter_connection():
    """Test the OpenRouter API connection directly"""
    
    # Test configuration
    api_key = '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'
    base_url = 'https://openrouter.ai/api/v1/chat/completions'
    model = 'anthropic/claude-3-sonnet'
    
    print("=== Testing OpenRouter API Connection ===")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    
    # Test payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test message from Hotel Royal Orchid. Please respond with 'AI service is working' if you receive this."
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hotelroyalorchid.com",
        "X-Title": "Hotel Royal Orchid AI"
    }
    
    try:
        print(f"\nSending request to: {base_url}")
        print(f"Headers: { {k: v for k, v in headers.items() if k != 'Authorization'} }")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(base_url, headers=headers, json=payload, timeout=30)
        
        print(f"\n=== Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! AI Response: {result}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.reason}")
            return False
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def test_alternative_models():
    """Test with alternative models in case the primary one is unavailable"""
    
    models_to_test = [
        'google/palm-2-chat-bison',
        'meta-llama/llama-2-13b-chat',
        'openai/gpt-3.5-turbo',
        'microsoft/wizardlm-2-8x22b'
    ]
    
    api_key = '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'
    base_url = 'https://openrouter.ai/api/v1/chat/completions'
    
    for model in models_to_test:
        print(f"\n=== Testing model: {model} ===")
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say 'Hello from Hotel Royal Orchid'"}],
            "max_tokens": 50
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hotelroyalorchid.com"
        }
        
        try:
            response = requests.post(base_url, headers=headers, json=payload, timeout=15)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"Success: {content}")
                return model  # Return the first working model
            else:
                print(f"Error: {response.text[:100]}...")
        except Exception as e:
            print(f"Exception: {str(e)}")
    
    return None

if __name__ == "__main__":
    print("Starting AI Service Tests...")
    
    # Test primary connection
    success = test_openrouter_connection()
    
    if not success:
        print("\nPrimary model failed, testing alternatives...")
        working_model = test_alternative_models()
        if working_model:
            print(f"\n✅ Found working model: {working_model}")
            print(f"Update your config.py with: OPENROUTER_MODEL = '{working_model}'")
        else:
            print("\n❌ No models are working. Please check your API key and network connection.")