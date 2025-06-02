# JSON Response Format Support in OpenAI Models

## Overview
Not all OpenAI models support the `response_format` parameter with `json_object` type. Using this parameter with unsupported models will result in a 400 Bad Request error.

## Models Supporting JSON Response Format

### ✅ Supported Models
- **gpt-4o** - Recommended for complex operations requiring structured output
- **gpt-4o-mini** - Good for simpler operations with JSON output
- **gpt-4-turbo-preview** - Alternative option with JSON support
- **gpt-3.5-turbo** (versions 1106 and later) - Budget option with JSON support

### ❌ Models WITHOUT JSON Response Format Support
- **gpt-4** - Does NOT support response_format parameter
- **gpt-4-32k** - Does NOT support response_format parameter
- **gpt-3.5-turbo** (versions before 1106) - Older versions don't support it

## Error Example
```
Error code: 400 - {'error': {'message': "Invalid parameter: 'response_format' of type 'json_object' is not supported with this model.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': None}}
```

## Best Practices

1. **Always use a supported model** when you need JSON response format
2. **Default to gpt-4o** for operations requiring structured JSON output
3. **Implement fallback logic** to handle cases where JSON format might fail
4. **Test model compatibility** before deploying changes

## Code Example
```python
# Correct usage
response = self._call_llm(
    messages,
    model="gpt-4o",  # Supports JSON response format
    response_format="json_object"
)

# Incorrect usage (will fail)
response = self._call_llm(
    messages,
    model="gpt-4",  # Does NOT support JSON response format
    response_format="json_object"
)
```

## Fallback Strategy
If you need to support multiple models, implement a fallback:
```python
try:
    # Try with JSON response format
    response = self._call_llm(messages, model="gpt-4o", response_format="json_object")
except Exception as e:
    if "response_format" in str(e):
        # Fallback to parsing JSON from text response
        response = self._call_llm(messages, model="gpt-4o")
        # Parse JSON from response.content manually
``` 