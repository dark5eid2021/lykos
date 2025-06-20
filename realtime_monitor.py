import asyncio
import websockets
import json
import time
from typing import AsyncGenerator, Dict, Any
import threading
from queue import Queue
import openai
from hallucination_detector import HallucinationDetector

class RealTimeLLMMonitor:
    def __init__(self, api_key: str = None):
        self.detector = HallucinationDetector()
        self.api_key = api_key
        self.monitoring = False
        self.response_queue = Queue()
        
    async def monitor_streaming_response(self, response_stream: AsyncGenerator):
        """Monitor streaming LLM responses in real-time"""
        accumulated_text = ""
        chunk_buffer = ""
        
        async for chunk in response_stream:
            chunk_text = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
            
            if chunk_text:
                chunk_buffer += chunk_text
                accumulated_text += chunk_text
                
                # Check every sentence or every 50 characters
                if len(chunk_buffer) > 50 or chunk_text.endswith(('.', '!', '?')):
                    # Quick check on the chunk
                    if self.detector.alert_if_suspicious(chunk_buffer, "Streaming chunk"):
                        yield {"alert": True, "text": chunk_buffer, "full_context": accumulated_text}
                    
                    chunk_buffer = ""
                
                yield {"alert": False, "text": chunk_text, "accumulated": accumulated_text}
        
        # Final check on complete response
        if accumulated_text:
            final_suspicious = self.detector.alert_if_suspicious(accumulated_text, "Complete response")
            if final_suspicious:
                yield {"alert": True, "text": accumulated_text, "final_check": True}

    def monitor_api_calls(self, wrapper_function):
        """Decorator to monitor LLM API calls"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                response = wrapper_function(*args, **kwargs)
                
                # Extract text from response
                response_text = ""
                if hasattr(response, 'choices') and response.choices:
                    response_text = response.choices[0].message.content
                elif isinstance(response, str):
                    response_text = response
                
                # Check for hallucinations
                is_suspicious = self.detector.alert_if_suspicious(
                    response_text, 
                    f"API call to {wrapper_function.__name__}"
                )
                
                # Log the interaction
                self.log_interaction({
                    'function': wrapper_function.__name__,
                    'duration': time.time() - start_time,
                    'response_length': len(response_text),
                    'suspicious': is_suspicious,
                    'timestamp': time.time()
                })
                
                return response
                
            except Exception as e:
                print(f"Error monitoring API call: {e}")
                return wrapper_function(*args, **kwargs)
        
        return wrapper
    
    def log_interaction(self, interaction_data: Dict[str, Any]):
        """Log interaction data for analysis"""
        with open('llm_interactions.jsonl', 'a') as f:
            f.write(json.dumps(interaction_data) + '\n')
    
    async def websocket_monitor(self, websocket_url: str):
        """Monitor LLM outputs via WebSocket"""
        async with websockets.connect(websocket_url) as websocket:
            print("Connected to WebSocket for monitoring...")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Extract text content based on your WebSocket format
                    text_content = data.get('content', data.get('text', ''))
                    
                    if text_content:
                        is_suspicious = self.detector.alert_if_suspicious(
                            text_content,
                            "WebSocket stream"
                        )
                        
                        if is_suspicious:
                            # Send alert back through WebSocket
                            alert_message = {
                                "type": "hallucination_alert",
                                "original_message": data,
                                "timestamp": time.time()
                            }
                            await websocket.send(json.dumps(alert_message))
                
                except json.JSONDecodeError:
                    print(f"Failed to parse WebSocket message: {message}")
                except Exception as e:
                    print(f"Error processing WebSocket message: {e}")

# Integration examples for popular LLM libraries

class OpenAIMonitor(RealTimeLLMMonitor):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = openai.OpenAI(api_key=api_key)
    
    async def monitored_chat_completion(self, **kwargs):
        """Monitored version of OpenAI chat completion"""
        kwargs['stream'] = True  # Enable streaming
        
        response = self.client.chat.completions.create(**kwargs)
        
        async for chunk_data in self.monitor_streaming_response(response):
            if chunk_data.get('alert'):
                print(f"🚨 ALERT: Potential hallucination detected!")
                print(f"Text: {chunk_data['text'][:100]}...")
            
            yield chunk_data

class AnthropicMonitor(RealTimeLLMMonitor):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        # Import Anthropic client here if using
    
    def monitored_completion(self, prompt: str, **kwargs):
        """Monitored version of Anthropic completion"""
        # Implementation would depend on Anthropic's streaming API
        pass

# Example usage and testing
async def main():
    # Example 1: Monitor OpenAI streaming
    if False:  # Set to True to test with actual API key
        monitor = OpenAIMonitor("your-openai-api-key")
        
        async for chunk in monitor.monitored_chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Tell me about the history of Paris"}]
        ):
            if not chunk.get('alert'):
                print(chunk['text'], end='', flush=True)
    
    # Example 2: Monitor via WebSocket (mock)
    print("Starting WebSocket monitor simulation...")
    
    # Simulate WebSocket messages
    test_messages = [
        '{"content": "Paris is the capital of France, established in 1889."}',  # Wrong date
        '{"content": "I think Paris might have around 10 million people, but I\'m not sure."}',  # Uncertain
        '{"content": "Paris has approximately 2.2 million residents in the city proper."}',  # Accurate
    ]
    
    monitor = RealTimeLLMMonitor()
    
    for message in test_messages:
        data = json.loads(message)
        text_content = data.get('content', '')
        
        print(f"\nProcessing: {text_content}")
        is_suspicious = monitor.detector.alert_if_suspicious(text_content, "Simulated WebSocket")
        
        if is_suspicious:
            print("🚨 ALERT TRIGGERED!")
        else:
            print("✅ No issues detected")

if __name__ == "__main__":
    asyncio.run(main())