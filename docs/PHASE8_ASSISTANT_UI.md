# Assistant V2 and speech input

Dedicated `/assistant-v2` authenticated screen: shows deterministic daily briefing, real stored task/goal context via safe backend, structured model draft with explicit human confirmation and actual saved CRUD response. Local message history is UI-only and does not imply durable conversation persistence.

Speech input uses the browser's SpeechRecognition/webkitSpeechRecognition API when available. Language selector: en-IN, te-IN, ta-IN, kn-IN, hi-IN. Browser/microphone/local permission/support may vary. This is **speech-to-text**, not a trained multimodal model or guaranteed offline regional STT. Text input always remains available.

Groq key goes only in backend environment. No API key in frontend. Provider failures produce a clearly labeled fallback.

Live user test must verify prompts, model output validation, explicit save once, reload persistence, 401 behavior, unavailable Groq fallback, and microphone permissions.

Legacy `/assistant` stays accessible until migration.
