# GPT-5.5 Availability Check Log

## 2026-09-12
- Status: NOT FOUND (as image generation model) — inferred via web search (direct abacus.ai access blocked, 13th consecutive day)
- Models seen (image generation, via web search — abacus.ai domain EGRESS_BLOCKED): GPT Image 1.5, GPT Image 2, **GPT Image 2.5** (NEW — released Sept 8 2026), GPT Image 1.5 [Edit], GPT Image 2 [Edit], Nano Banana 2, Nano Banana Pro, Seedream 4.5, Midjourney, Grok Imagine Image, FLUX.2 [Pro], Flux Ultra, Flux Kontext, Hunyuan Image 3.0, Wan 2.7, Imagen 4, Recraft SVG, Ideogram 3.0, Magnific Upscaler, DALL-E, Qwen Image Edit
- Notes: abacus.ai domain remains blocked by the remote execution environment's network egress proxy (WebFetch: EGRESS_BLOCKED, 13th consecutive day). GPT-5.5 is confirmed as a language/LLM model only — NOT an image generation model. Strings '5.5', 'gpt-5.5', 'GPT-5.5', 'gpt55', 'GPT5.5', 'gpt_55' do NOT appear in the image generation lineup. NOTABLE: GPT Image 2.5 is a NEW image generation model released by OpenAI on September 8, 2026 (sharper details, 50% faster than GPT Image 2), and is now available on Abacus.AI. This is separate from GPT-5.5 (the LLM). Action recommended: update SUPPORTED_MODELS in abacus_image_gen.py to add 'GPT Image 2.5'. Sources: openai.com/index/introducing-chatgpt-images-2-5/, eesel.ai/blog/abacus-ai-pricing, aidisruption.ai/p/gpt-image-25-released.

## 2026-09-11
- Status: NOT FOUND (as image generation model) — inferred via web search (direct abacus.ai access blocked, 12th consecutive day)
- Models seen (image generation, via web search — abacus.ai domain EGRESS_BLOCKED): GPT Image 1.5, GPT Image 2, GPT Image 1.5 [Edit], GPT Image 2 [Edit], Nano Banana 2, Nano Banana Pro, Seedream 4.5, Midjourney, Grok Imagine Image, FLUX.2 [Pro], Hunyuan Image 3.0, Wan 2.7, Imagen 4, Recraft SVG, Ideogram 3.0, Magnific Upscaler, Flux Ultra
- Notes: abacus.ai domain remains blocked by the remote execution environment's network egress proxy (WebFetch: EGRESS_BLOCKED, 12th consecutive day). Web search confirmed: GPT-5.5 is listed on Abacus.AI as a language/LLM (text generation) model alongside Claude Opus 4.8 and Gemini 3.1 Pro — NOT as an image generation model. Strings '5.5', 'gpt-5.5', 'GPT-5.5', 'gpt55', 'GPT5.5', 'gpt_55' do NOT appear in the image generation model lineup. GPT Image 1.5 and GPT Image 2 remain the latest GPT-family image generation models. Sources: eesel.ai/blog/abacus-ai-pricing, kdnuggets.com/2026/08/abacus/honest-abacus-ai-review, studio.abacus.ai.

## 2026-09-10
- Status: NOT FOUND (as image generation model) — inferred via web search (direct abacus.ai access blocked, 11th consecutive day)
- Models seen (image generation, via web search — abacus.ai domain EGRESS_BLOCKED): GPT Image 1.5, GPT Image 2, GPT Image 1.5 [Edit], GPT Image 2 [Edit], Nano Banana 2, Nano Banana Pro, Seedream 4.5, Midjourney, Grok Imagine Image, FLUX.2 [Pro], Hunyuan Image 3.0, Wan 2.7, Imagen 4, Recraft SVG, Ideogram 3.0, Magnific Upscaler, Qwen Image Edit, Flux Ultra
- Notes: abacus.ai domain remains blocked by the remote execution environment's network egress proxy (WebFetch: EGRESS_BLOCKED, 11th consecutive day). Web search confirmed: GPT-5.5 IS available on Abacus.AI but only as a language/LLM (text generation) model — NOT an image generation model. Strings '5.5', 'gpt-5.5', 'GPT-5.5', 'gpt55', 'GPT5.5', 'gpt_55' do NOT appear in the image generation model lineup on Abacus.AI. GPT Image 1.5 and GPT Image 2 remain the latest GPT-family image generation models. Sources: eesel.ai/blog/abacus-ai-pricing, studio.abacus.ai/faq, kdnuggets.com/2026/08/abacus/honest-abacus-ai-review.

## 2026-09-09
- Status: NOT FOUND (as image generation model)
- Models seen (image generation, via web search — direct abacus.ai access blocked, 10th consecutive day): GPT Image 1.5, GPT Image 2, GPT Image 1.5 [Edit], GPT Image 2 [Edit], Nano Banana 2, Nano Banana Pro, Seedream 4.5, Midjourney, Grok Imagine Image, FLUX.2 [Pro], Hunyuan Image 3.0, Wan 2.7, Imagen 4, Recraft SVG, Ideogram 3.0, Magnific Upscaler, Qwen Image Edit
- Notes: abacus.ai domain remains blocked by the remote execution environment's network egress proxy (WebFetch: EGRESS_BLOCKED, 10th consecutive day). Web search via WebSearch confirmed: GPT-5.5 ("Spud") was released by OpenAI on April 23, 2026, but it is a language/LLM model — NOT an image generation model. Its codename is "Spud". Alongside it, OpenAI released GPT Image 2 (the image generation successor). Abacus.AI's current image generation lineup does NOT include "GPT-5.5" — GPT Image 1.5 and GPT Image 2 remain the latest GPT-family image models. Sources: openai.com/index/introducing-gpt-5-5/, studio.abacus.ai/faq. No GPT-5.5 image model is imminent or announced.

## 2026-08-31
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Both curl (403 from proxy) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Cannot fetch https://abacus.ai/help/developer-platform/route-llm/image-analysis or https://abacus.ai/foundation_models from this environment. GPT-5.5 presence UNKNOWN. Manual check required, or run this task from a local machine with unrestricted network access.

## 2026-09-01
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Same as 2026-08-31. Both curl (CONNECT tunnel 403) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Attempted URLs: https://abacus.ai/help/developer-platform/route-llm/image-analysis and https://abacus.ai/foundation_models. GPT-5.5 presence UNKNOWN. This check cannot run from the cloud remote environment — manual check required, or configure the scheduled task to run from a local machine with unrestricted network access.

## 2026-09-02
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Same as prior days. Both curl (CONNECT tunnel 403) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Attempted URLs: https://abacus.ai/help/developer-platform/route-llm/image-analysis and https://abacus.ai/foundation_models. GPT-5.5 presence UNKNOWN. This recurring check cannot be performed from the cloud remote execution environment. Please run manually from a local machine with unrestricted network access, or reconfigure this scheduled task to run locally via cron.

## 2026-09-03
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Same as prior days. Both curl (CONNECT tunnel 403) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Attempted URLs: https://abacus.ai/help/developer-platform/route-llm/image-analysis and https://abacus.ai/foundation_models. GPT-5.5 presence UNKNOWN. This is the 4th consecutive day the check has been blocked. This scheduled task cannot be performed from the cloud remote execution environment. Please run manually from a local machine with unrestricted network access, or reconfigure this scheduled task to run locally via cron.

## 2026-09-04
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Same as prior days. Both curl (CONNECT tunnel 403) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Attempted URLs: https://abacus.ai/help/developer-platform/route-llm/image-analysis and https://abacus.ai/foundation_models. GPT-5.5 presence UNKNOWN. This is the 5th consecutive day the check has been blocked. This scheduled task cannot be performed from the cloud remote execution environment. Please run manually from a local machine with unrestricted network access, or reconfigure this scheduled task to run locally via cron.

## 2026-09-05
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Same as prior days. Both curl (CONNECT tunnel 403) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Attempted URLs: https://abacus.ai/help/developer-platform/route-llm/image-analysis and https://abacus.ai/foundation_models. GPT-5.5 presence UNKNOWN. This is the 6th consecutive day the check has been blocked. This scheduled task cannot be performed from the cloud remote execution environment. Please run manually from a local machine with unrestricted network access, or reconfigure this scheduled task to run locally via cron.

## 2026-09-06
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Same as prior days. Both curl (CONNECT tunnel 403) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Attempted URLs: https://abacus.ai/help/developer-platform/route-llm/image-analysis and https://abacus.ai/foundation_models. GPT-5.5 presence UNKNOWN. This is the 7th consecutive day the check has been blocked. This scheduled task cannot be performed from the cloud remote execution environment. Please run manually from a local machine with unrestricted network access, or reconfigure this scheduled task to run locally via cron.

## 2026-09-07
- Status: CHECK BLOCKED
- Models seen: N/A — abacus.ai is blocked by the remote execution environment's network egress proxy
- Notes: Same as prior days. Both curl (CONNECT tunnel 403) and WebFetch (EGRESS_BLOCKED) failed for abacus.ai. Attempted URLs: https://abacus.ai/help/developer-platform/route-llm/image-analysis and https://abacus.ai/foundation_models. GPT-5.5 presence UNKNOWN. This is the 8th consecutive day the check has been blocked. This scheduled task cannot be performed from the cloud remote execution environment. Please run manually from a local machine with unrestricted network access, or reconfigure this scheduled task to run locally via cron.

## 2026-09-08
- Status: NOT FOUND (as image generation model) — inferred via web search (direct abacus.ai access blocked, 9th consecutive day)
- Models seen (image generation, via web search of Abacus.AI Studio/ChatLLM sources): GPT Image 1.5, GPT Image 2, GPT Image 1.5 [Edit], GPT Image 2 [Edit], Nano Banana 2, Nano Banana Pro, Seedream 4.5, Midjourney, Grok Imagine Image, FLUX.2 [Pro], Hunyuan Image 3.0, Wan 2.7, Imagen 4, Recraft SVG, Ideogram 3.0, Magnific Upscaler, Qwen Image Edit
- Notes: abacus.ai domain remains blocked by the remote execution environment's network egress proxy (curl: CONNECT tunnel 403, WebFetch: EGRESS_BLOCKED). Web search (WebSearch tool) returned indirect results from eesel.ai, studio.abacus.ai/faq, kdnuggets.com, and wikipedia.org for GPT Image. No mention of 'GPT-5.5', 'gpt-5.5', 'GPT5.5', 'gpt55', or '5.5' in any image generation context. GPT-5.5 is confirmed as a language/LLM model (text generation), not an image generation model. The current image generation lineup on Abacus.AI does not include GPT-5.5. Manual verification on abacus.ai still recommended when direct access is available.
