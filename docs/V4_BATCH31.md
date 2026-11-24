# Batch 31 — local portrait generation and research improvements

## Local CPU portrait candidate
Use a trusted local Diffusers-format StableDiffusionPipeline directory outside Git, with safetensors weights and an enabled local safety checker. Prepare CPU torch, diffusers, transformers, safetensors and accelerate independently in a trusted environment. No installer or automatic weight download is included. Upstream pipeline loading reference: https://huggingface.co/docs/diffusers/api/pipelines/overview . Use an offline environment; flags are not a network sandbox.

```cmd
.venv\Scripts\python.exe -m podcast_gpt character-portrait-preflight --character-id CHARACTER_ID --model "D:\Models\SD15"
.venv\Scripts\python.exe -m podcast_gpt character-portrait-generate --character-id CHARACTER_ID --model "D:\Models\SD15" --seed 42 --steps 20 --acknowledgment I_TRUST_THIS_LOCAL_IMAGE_MODEL_AND_HAVE_USAGE_RIGHTS_AND_AUTHORIZE_CPU_INFERENCE
```

Preflight checks local model directory, safetensors inventory hashes, installed package metadata and conservative 8 GiB available RAM/2 GiB scratch gates. These gates are not model memory guarantees. One 512×512 CPU candidate, 10–30 steps and explicit seed, with offline loading flags, no pickle model files, no automatic cast assignment. Runtime must return a non-blocked safety result. Private UUID candidate stores PNG and provenance receipt; failed/interrupted attempts may leave private scratch. The current character and project cast are preserved. Inspect visually and use existing authorized portrait attachment only if suitable. The model and dependency set remain third-party trusted code, not sandboxed. CPU rendering can be slow, real inference and user hardware remain unverified. No browser execution yet. 12 mocked/validation cases authored, new CI pending.

## CI reconciliation
Batch 29 CI 45494573255 passed 6/6. Batch 30 CI 45495706179, 45495798832, 45495891248 all completed successfully, latest combined run 6/6. Actual model and physical acceptance remain pending.
