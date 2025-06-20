# LLM Hallucination Detection System

A comprehensive Python toolkit for detecting and alerting on potential hallucinations in Large Language Model (LLM) outputs. This system provides real-time monitoring, confidence analysis, and automated alerting capabilities.

## 🚀 Features

- **Real-time Detection**: Monitor LLM outputs as they're generated
- **Multi-layered Analysis**: Confidence patterns, factual consistency, source verification
- **Streaming Support**: Works with streaming API responses
- **Flexible Alerting**: Email, Slack, logs, and custom notification channels
- **API Integration**: Easy integration with OpenAI, Anthropic, and other LLM providers
- **Customizable Thresholds**: Adjust sensitivity based on your use case
- **Comprehensive Logging**: Track patterns and false positives over time

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-hallucination-detector.git
cd llm-hallucination-detector

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```txt
requests>=2.28.0
openai>=1.0.0
websockets>=11.0.0
python-dateutil>=2.8.0
```

## 🏃 Quick Start

### Basic Usage

```python
from hallucination_detector import HallucinationDetector

# Initialize detector
detector = HallucinationDetector(confidence_threshold=0.7)

# Analyze text
text = "I think Paris might have around 10 million people, but I'm not sure."
is_suspicious = detector.alert_if_suspicious(text, "User query")

if is_suspicious:
    print("🚨 Potential hallucination detected!")
```

### Real-time Monitoring

```python
from realtime_monitor import OpenAIMonitor
import asyncio

async def monitor_example():
    monitor = OpenAIMonitor("your-openai-api-key")
    
    async for chunk in monitor.monitored_chat_completion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Tell me about quantum physics"}]
    ):
        if chunk.get('alert'):
            print("🚨 ALERT: Potential hallucination detected!")
        else:
            print(chunk['text'], end='', flush=True)

asyncio.run(monitor_example())
```

## 🔧 Configuration

### HallucinationDetector Parameters

```python
detector = HallucinationDetector(
    confidence_threshold=0.7,      # Confidence score threshold (0-1)
    fact_check_api_key="your-key"  # Optional: External fact-checking API
)
```

### Detection Categories

The system analyzes four main categories:

1. **Confidence Analysis** - Detects uncertain language patterns
2. **Factual Consistency** - Identifies contradictions and impossible claims  
3. **Source Verification** - Flags unsupported statistical claims
4. **External Validation** - Integrates with fact-checking APIs

## 📊 Detection Methods

### Confidence Patterns
Detects low-confidence language:
- Uncertainty words: "I think", "maybe", "perhaps", "possibly"
- Hedge words: "allegedly", "supposedly", "reportedly"
- Approximations: "around", "roughly", "approximately"

### Consistency Checks
Identifies contradictions and impossible facts:
- Internal contradictions: "always" vs "never"
- Impossible dates: Future years beyond reasonable projection
- Unrealistic numbers: Suspiciously large figures

### Source Analysis
Flags unsupported claims:
- Unattributed statistics: "Studies show that X% of people..."
- Vague authorities: "Scientists have discovered..."
- Specific but unverifiable claims

## 🔔 Alerting & Notifications

### Built-in Alert Methods

```python
# Console logging (default)
detector.alert_if_suspicious(text, context)

# Custom notification function
def custom_alert(message):
    # Send to Slack
    webhook_url = "YOUR_SLACK_WEBHOOK"
    requests.post(webhook_url, json={"text": message})
    
    # Send email
    send_email("admin@company.com", "Hallucination Alert", message)

# Override notification method
detector.send_notification = custom_alert
```

### Log Files

The system automatically logs to:
- `hallucination_alerts.log` - Alert notifications
- `llm_interactions.jsonl` - All API interactions (JSON Lines format)

## 🔌 API Integrations

### OpenAI Integration

```python
from realtime_monitor import OpenAIMonitor

monitor = OpenAIMonitor("your-api-key")

# Wrap existing OpenAI calls
@monitor.monitor_api_calls
def my_openai_function():
    return openai.ChatCompletion.create(...)
```

### WebSocket Monitoring

```python
import asyncio
from realtime_monitor import RealTimeLLMMonitor

async def websocket_example():
    monitor = RealTimeLLMMonitor()
    await monitor.websocket_monitor("ws://your-llm-service/stream")

asyncio.run(websocket_example())
```

## 🎯 Use Cases

### Production API Monitoring
Monitor all LLM API responses in production:

```python
# Add to your API middleware
def llm_middleware(request, response):
    detector = HallucinationDetector()
    detector.alert_if_suspicious(
        response.content, 
        f"API endpoint: {request.path}"
    )
    return response
```

### Chatbot Quality Assurance
Real-time monitoring for chatbots:

```python
# In your chatbot response handler
def process_bot_response(user_message, bot_response):
    detector = HallucinationDetector(confidence_threshold=0.8)
    
    if detector.alert_if_suspicious(bot_response, f"User: {user_message}"):
        # Log for review, request human intervention, etc.
        escalate_to_human(user_message, bot_response)
    
    return bot_response
```

### Content Generation Pipeline
Monitor generated content before publication:

```python
# Content review pipeline
def review_generated_content(content):
    detector = HallucinationDetector(confidence_threshold=0.6)
    analysis = detector.analyze_text(content)
    
    if analysis['overall_suspicious']:
        return "NEEDS_REVIEW"
    elif analysis['suspicion_score'] > 0.3:
        return "MODERATE_RISK"
    else:
        return "APPROVED"
```

## ⚙️ Advanced Configuration

### Custom Detection Patterns

```python
# Add domain-specific patterns
class CustomDetector(HallucinationDetector):
    def check_domain_specific(self, text):
        medical_flags = []
        
        # Medical misinformation patterns
        dangerous_patterns = [
            r'cure for (cancer|aids|diabetes)',
            r'miracle drug',
            r'doctors hate this'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                medical_flags.append(f"Dangerous medical claim: {pattern}")
        
        return {'medical_flags': medical_flags}
```

### Threshold Tuning

Adjust thresholds based on your requirements:

```python
# Conservative (fewer false positives)
detector = HallucinationDetector(confidence_threshold=0.8)

# Sensitive (catches more potential issues)
detector = HallucinationDetector(confidence_threshold=0.5)

# Domain-specific thresholds
if content_type == "medical":
    threshold = 0.9  # Very strict
elif content_type == "creative":
    threshold = 0.4  # More lenient
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

Test with sample texts:

```python
# Run built-in tests
python hallucination_detector.py

# Custom test
detector = HallucinationDetector()
test_cases = [
    "The Eiffel Tower is 324 meters tall.",  # Factual
    "I think the Eiffel Tower might be around 500 meters.",  # Uncertain
    "The Eiffel Tower was built in 2025.",  # Impossible
]

for text in test_cases:
    result = detector.analyze_text(text)
    print(f"Suspicion score: {result['suspicion_score']:.2f}")
```

## 📈 Performance Considerations

- **Latency**: Analysis adds ~10-50ms per response depending on text length
- **Memory**: Minimal memory footprint, scales with text length
- **Rate Limits**: Respects external API rate limits for fact-checking
- **Concurrency**: Thread-safe for multiple simultaneous analyses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linting
flake8 hallucination_detector.py
black hallucination_detector.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by research in AI safety and hallucination detection
- Built with love for the AI community
- Special thanks to contributors and beta testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/llm-hallucination-detector/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/llm-hallucination-detector/discussions)
- **Email**: support@yourproject.com

## 🔮 Roadmap

- [ ] Machine learning-based detection models
- [ ] Integration with more fact-checking APIs
- [ ] Dashboard for monitoring and analytics  
- [ ] Multi-language support
- [ ] Fine-tuning capabilities for domain-specific detection
- [ ] Integration with popular MLOps platforms

---

**⚠️ Disclaimer**: This tool provides detection capabilities but cannot guarantee 100% accuracy. Always combine automated detection with human review for critical applications.