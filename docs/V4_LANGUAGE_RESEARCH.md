# V4 Kokoro language expansion, discovery and factual review

The local V4 Kokoro adapter now permits Hindi, Spanish, French, Italian and Brazilian Portuguese using explicit matching presets and language-specific Misaki EspeakG2P. See upstream [voice catalog](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) and [Misaki](https://github.com/hexgrad/misaki). The catalog is a candidate list, not installed voice verification. Existing Hindi receipts remain unchanged. New languages record their language code in separate provenance; a real run checks selected preset presence in the installed pack. Distinct presets remain required, so French currently supports one Kokoro speaker, Italian two, Spanish and Brazilian Portuguese three. Additional speakers may use authorized imports or configured eSpeak. English, Japanese, Mandarin and Edge TTS remain pending; generic Portuguese without Brazil is not mapped automatically. No automatic downloads, cloud text or paid APIs. Real voice quality, runtime and language accuracy need physical listening tests.

```cmd
.venv\Scripts\python.exe -m podcast_gpt kokoro-language-catalog
.venv\Scripts\python.exe -m podcast_gpt project-tts-kokoro --project-id PROJECT_ID --use-config --run-local --acknowledgment I_HAVE_RIGHTS_TO_USE_LOCAL_MODEL_AND_VOICES
```

## Research discovery
Explicit opt-in sends only the chosen search query (default project topic, maximum 200 characters) to the fixed English Wikipedia REST search endpoint. See [MediaWiki reference](https://www.mediawiki.org/wiki/API:REST_API/Reference). Pinned public DNS/TLS, no redirects, bounded JSON and 1–10 links. No key or paid fallback. This is encyclopedia-only discovery, not broad search or independent-source corroboration. Review candidate links manually, select 2–4 distinct suitable source URLs and capture using the existing explicit workflow. Full pages may exceed the existing capture budget; choose shorter sources manually. No automatic capture, no snippets treated as evidence. Network service availability is not guaranteed.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-research-discover --project-id PROJECT_ID --query "public topic" --allow-web-search
```

## Human factual review
For a current web-research script, generate the private review template. Each turn contains original text, matched citations and source URLs. Review the full saved research snapshot and source context manually, then select SUPPORTED (requires a saved citation), NO_FACTUAL_CLAIM or NEEDS_CORRECTION and write a substantive note. Record explicit acknowledgment. Immutable receipts bind current script and research hashes; a new script revision starts unreviewed.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-fact-review-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-fact-review-record --project-id PROJECT_ID --acknowledgment I_CHECKED_EACH_TURN_AND_ITS_CITED_SOURCE_CONTEXT
.venv\Scripts\python.exe -m podcast_gpt project-fact-review-status --project-id PROJECT_ID
```

This is optional human self-attestation, not independent claim verification or a mandatory media gate. Correct flagged claims using existing script revisions. Neither exact quotation nor a PASS proves truth, source independence or publication rights. Actual Wikipedia calls, natural model inference and real Windows acceptance remain untested; tests are offline fixtures.

English US/UK frontend and optional dependency group are now implemented; see V4_STUDIO_ENGLISH.md. CJK remains pending.

Mandarin v1.0 frontend and eight candidate presets now implemented with optional dependency group; Japanese still pending. See V4_BATCH29.md.

Batch 31 adds 17 allowlisted Wikipedia discovery editions, exact citation coverage and browser portrait brief/coverage controls. New CI pending; broad web search, semantic verification and independent corroboration remain pending. See V4_BATCH31.md.
