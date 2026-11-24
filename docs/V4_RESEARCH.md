# V4 source-grounded research increment

Choose research_mode=web in the request JSON. Create a project, optionally attach the primary input source, then explicitly capture 2–4 distinct user-selected public HTTPS pages before outline generation. No automatic search discovery, search API fees, redirects, local-network access or paid grounding. The existing ingestion limits and TLS/DNS restrictions apply; combined extracted research text must not exceed 12,000 characters. Use concise, trustworthy public sources and review them yourself.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-research-capture --project-id PROJECT_ID --url https://example.org/article --url https://example.net/article --allow-web-fetch
.venv\Scripts\python.exe -m podcast_gpt project-research-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-plan --project-id PROJECT_ID --offline-only
.venv\Scripts\python.exe -m podcast_gpt project-script-generate --project-id PROJECT_ID --offline-only --max-new 1
```

The private pack is immutable, timestamped and hash-bound to the request, outline and script checkpoints. The script includes source IDs and exact 12–200-character excerpts. Every research unit needs at least one exact citation; each turn can have 0–3. Invented source IDs or text excerpts absent from their captured source are refused. Quote matching is not semantic entailment, fact-checking, source credibility assessment, claim completeness or proof of current accuracy. Human review is required; no publication approval. Knowledge-mode legacy outlines/scripts remain compatible.

Cloud text consent still applies separately and transmits primary input text, research excerpts and prior dialogue to eligible providers. Small local context windows may not fit combined sources; shorten the sources or use an explicitly consented free cloud provider. Automatic discovery/search, source ranking, cross-source claim comparison, comprehensive citation coverage and human review remain pending. No real website or model calls are made by synthetic CI fixtures.

Research-backed scripts can now be manually revised and reviewed. Exact source quote matching is retained for every edit; human review is separate from independent claim verification. See V4_SCRIPT_REVIEW.md.

Explicit English Wikipedia candidate discovery and optional source-bound human factual review now available through V4_LANGUAGE_RESEARCH.md. Candidate search is not broad web research or independent verification.
