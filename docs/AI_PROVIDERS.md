# V4 free AI provider and topic planner

Current text-only provider order: OpenRouter free router, Gemini Flash-Lite free tier, Ollama local. No paid fallback or tools. No API request is sent by ai-provider-status. Cloud text generation explicitly transmits the selected request to a third party; never include confidential material or keys in the topic. Gemini free-tier content may be used to improve products. Check the provider's current terms and billing setup.

Use the installed application venv. To inspect local key presence:

```cmd
.venv\Scripts\python.exe -m podcast_gpt ai-provider-status
```

For Ollama, manually install it and choose a known small local model, e.g. ollama pull qwen3:1.7b. The app never downloads models. It checks /api/tags and /api/show metadata on 127.0.0.1:11434 and rejects missing/remote or >=3B metadata. Use a trusted local Ollama server with cloud features disabled; the app cannot authenticate its binary or model metadata. The 2B Qwen3.5 quantized model is preferred on a machine with sufficient available RAM; smaller candidates are preferred when available RAM is low.

Create a request.json outside Git (for example in your private studio):

```json
{"topic":"The future of education","language":"Hindi","duration_minutes":10,"presenters":["Aarav","Meera","Kabir"],"video_format":"landscape","workflow":"automatic","input_kind":"topic","research_mode":"knowledge"}
```

Default local-only (no cloud consent):

```cmd
.venv\Scripts\python.exe -m podcast_gpt plan-episode --request "%USERPROFILE%\PodcastGPTStudio\request.json" --offline-only
```

For cloud-first, use environment keys OPENROUTER_API_KEY and GEMINI_API_KEY, or hidden session-only entry with --prompt-keys. Never put keys in command arguments, source control or scripts. Only use --confirm-gemini-free-project after verifying billing is disabled on that Google project. It is NOT possible to verify the billing tier with a model API key alone. If uncertain, omit this flag and Gemini is skipped. Do not fund OpenRouter or enable Gemini billing if strictly free.

```cmd
.venv\Scripts\python.exe -m podcast_gpt plan-episode --request "%USERPROFILE%\PodcastGPTStudio\request.json" --allow-cloud-text --confirm-gemini-free-project --prompt-keys
```

The result is a validated outline printed as JSON; it is not an actual timed script, rendered episode or verified research. Non-topic sources and web research are explicitly blocked until implemented. Cloud consent is required every run. Errors are sanitized provider/status labels, not raw API bodies or keys.

Official references:
- https://openrouter.ai/openrouter/free
- https://ai.google.dev/gemini-api/docs/pricing
- https://ollama.com/library/qwen3
- https://ollama.com/library/qwen3.5
