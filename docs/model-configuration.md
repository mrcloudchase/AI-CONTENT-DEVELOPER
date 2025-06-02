# Model Configuration Guide

## Overview
AI Content Developer allows you to configure which OpenAI models to use for different operations through environment variables. This provides flexibility to use different models based on your needs, budget, and performance requirements.

## Configuration File
Copy `env.example` to `.env` and update with your settings:

```bash
cp env.example .env
```

## Environment Variables

### Required Configuration
- **OPENAI_API_KEY**: Your OpenAI API key (required)

### Model Configuration

#### Primary Models
These are the main models used throughout the application:

- **OPENAI_COMPLETION_MODEL**: Advanced model for complex operations (default: `gpt-4o`)
  - Used for content generation, TOC management, and other complex tasks
  - Must support JSON response format
  
- **OPENAI_SIMPLE_MODEL**: Simple model for basic operations (default: `gpt-4o-mini`)
  - Used for simpler tasks like material summarization
  - Should support JSON response format
  
- **OPENAI_EMBEDDING_MODEL**: Model for generating embeddings (default: `text-embedding-3-small`)
  - Used for semantic similarity searches in the strategy phase

#### Operation-Specific Overrides
You can optionally override models for specific operations:

- **OPENAI_TOC_MODEL**: Model for TOC management (defaults to OPENAI_COMPLETION_MODEL)
- **OPENAI_STRATEGY_MODEL**: Model for strategy generation (defaults to OPENAI_COMPLETION_MODEL)
- **OPENAI_CONTENT_MODEL**: Model for content generation (defaults to OPENAI_COMPLETION_MODEL)

### Temperature Settings
- **OPENAI_TEMPERATURE**: Temperature for most operations (default: `0.3`)
- **OPENAI_CREATIVE_TEMPERATURE**: Temperature for creative content (default: `0.7`)

## Example Configurations

### Budget-Conscious Configuration
```env
OPENAI_API_KEY=your-key-here
OPENAI_COMPLETION_MODEL=gpt-3.5-turbo
OPENAI_SIMPLE_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Performance-Optimized Configuration
```env
OPENAI_API_KEY=your-key-here
OPENAI_COMPLETION_MODEL=gpt-4o
OPENAI_SIMPLE_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

### Mixed Configuration
```env
OPENAI_API_KEY=your-key-here
OPENAI_COMPLETION_MODEL=gpt-4o
OPENAI_SIMPLE_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TOC_MODEL=gpt-4o-mini  # Use cheaper model for TOC
```

## Model Compatibility

### JSON Response Format Support
The following operations require models that support JSON response format:
- Material processing
- Directory selection
- Strategy generation
- Content generation (CREATE and UPDATE)
- TOC management

Compatible models:
- ✅ gpt-4o
- ✅ gpt-4o-mini
- ✅ gpt-4-turbo-preview
- ✅ gpt-3.5-turbo (1106 and later)
- ❌ gpt-4 (does NOT support JSON response format)

### Embedding Models
Available embedding models:
- text-embedding-3-small (recommended for cost/performance balance)
- text-embedding-3-large (better quality, higher cost)
- text-embedding-ada-002 (legacy, not recommended)

## Troubleshooting

### Model Not Found
If you get a "model not found" error:
1. Check that the model name is spelled correctly
2. Verify you have access to the model with your API key
3. Ensure the model supports the required features (e.g., JSON response format)

### JSON Response Format Error
If you get "response_format not supported":
1. Check that your configured model supports JSON response format
2. See the [JSON Response Format Models](./json-response-format-models.md) guide
3. Use a compatible model like `gpt-4o` or `gpt-4o-mini`

### Performance Issues
If generation is slow:
1. Consider using `gpt-4o-mini` for simpler operations
2. Use operation-specific overrides to use faster models where appropriate
3. Check your OpenAI rate limits

## Best Practices

1. **Start with defaults**: The default configuration is optimized for quality
2. **Test before changing**: Always test with new models before production use
3. **Monitor costs**: Different models have different pricing
4. **Use overrides sparingly**: Only override specific operations if needed
5. **Keep models consistent**: Use models from the same family for consistency 