client<llm> Gemma3 {
  provider ollama
  options {
    base_url "http://localhost:11434/v1"
    model "gemma3:12b"
  }
}

client<llm> GeminiPro2_5 {
  provider google-ai
  retry_policy Exponential
  options {
    model "gemini-2.5-pro-preview-03-25"
    api_key env.GEMINI_API_KEY
  }
}

client<llm> GeminiFlash2 {
  provider google-ai
  retry_policy Exponential
  options {
    generationConfig {
      temperature 0.7
    }
    model "gemini-2.0-flash"
    api_key env.GEMINI_API_KEY
  }
}

client<llm> GeminiFlash2_5 {
  provider google-ai
  options {
    model "gemini-2.5-flash-preview-04-17"
    api_key env.GEMINI_API_KEY
  }
}

client<llm> GeminiFlashLLite2 {
  provider google-ai
  options {
    model "gemini-2.0-flash-lite"
    api_key env.GEMINI_API_KEY
  }
}

client<llm> GeminiFlash1_5 {
  provider google-ai
  options {
    model "gemini-1.5-flash"
    api_key env.GEMINI_API_KEY
  }
}

retry_policy Constant {
  max_retries 3
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  strategy {
    type exponential_backoff
    delay_ms 300
    mutliplier 1.5
    max_delay_ms 10000
  }
}