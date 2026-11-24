# V4 bounded source ingestion

Create a V4 request with input_kind set to document, pdf, custom_script, url, or topic. Keep research_mode=knowledge for now. Use project-create first, then attach one source to a non-topic project.

Install optional local PDF parser in the app virtual environment:
```cmd
.venv\Scripts\python.exe -m pip install -e ".[documents]"
```

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-import-source --project-id PROJECT_ID --file "D:\Sources\article.pdf"
.venv\Scripts\python.exe -m podcast_gpt project-import-source --project-id PROJECT_ID --url "https://example.org/article" --allow-web-fetch
.venv\Scripts\python.exe -m podcast_gpt project-show --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-plan --project-id PROJECT_ID --offline-only
```

- PDF: text-based, unencrypted, up to 30 pages. No OCR or scanned image transcription. Only trusted documents; parsing isn't a malware sandbox.
- Document: DOCX main-body paragraphs (including table paragraphs), UTF-8 TXT/Markdown. No legacy DOC, embedded media, external links, macros or layout reconstruction.
- Custom script: UTF-8 TXT/Markdown; retains extracted text for planning, not yet a timed dialogue importer.
- URL: direct public HTTPS HTML/plain text only, no query, fragments, credentials, redirects, cookies, JS, proxy or browser; DNS checked and pinned to a public address, TLS certificate verified. Separate fetch consent. Some sites will be unsupported; use an authorized saved text excerpt instead. URL fetch is not independently verified live research.
- Local files at most 8 MB, web response at most 1 MB, extracted text at most 12,000 characters. Larger sources rejected, not silently truncated. Chunking and multi-source research remain future work.
- One immutable private evidence JSON per project binds request, extracted text hash and raw-byte hash; original file remains with the user. A saved outline binds the evidence. Hashes detect accidental changes, not malicious replacement of data plus hashes. No original files copied to Git.
- Source text is treated as untrusted reference data in the AI prompt. Prompt injection defenses are limited; outputs still need human review. Cloud planning requires --allow-cloud-text and transmits the imported text to the selected provider. No cloud key or text upload during local import; URL retrieval contacts the public site only. Do not import sensitive documents into cloud requests.

Full script generation, live multi-source research, citations and general video rendering are not yet implemented.

Separate multi-source research capture is now available for web-mode projects. See V4_RESEARCH.md for limits, explicit network consent and citation checks.
