# 📦 Relevant Python Packages for Using `playai-tts` with LangChain and Groq

This document lists the minimal and relevant Python packages from your environment that support using the `playai-tts` model with `LangChain`, `Groq`, and audio/text generation functionalities.

## 🔧 Core Libraries

- `groq==0.31.0`

  > Required for interfacing with Groq’s API (including `playai-tts` model).

- `langchain==0.3.27`

  > Core LangChain library for building LLM-powered applications.

- `langchain-groq==0.3.7`

  > Groq integration for LangChain.

- `langchain-core==0.3.72`

  > Core tools and types for LangChain.

- `langchain-community==0.3.27`

  > Community maintained LangChain integrations.

- `langchain-text-splitters==0.3.9`
  > Optional: For chunking long texts before sending to TTS.

## 🔤 Text-to-Speech and Audio Tools

- `playai-tts` _(Usage via Groq model endpoint; no separate install needed if accessed through API)_

- `pydub` _(Not listed in your env)_

  > 🔁 Optional: Audio manipulation (e.g., combine, convert formats).

- `pyttsx3`, `gTTS`, `edge-tts` _(❌ Not listed — only needed if using local engines)_

## 🌐 HTTP & Networking

- `httpx==0.28.1`

  > Used by LangChain and Groq clients for async HTTP requests.

- `aiohttp==3.12.15`
  > For asynchronous HTTP tasks (used by many AI libraries).

## 🧱 Data & Audio Handling (Optional)

- `numpy==2.3.1`

  > Audio data preprocessing.

- `soundfile` / `scipy.io.wavfile` _(Not installed — optional if processing raw audio)_

- `pandas==2.3.1`
  > Optional, for tabular handling in multi-input/output use cases.

## 🧪 Dev/Tooling (Optional)

- `uvicorn==0.35.0`

  > Useful for serving LangChain+TTS apps via FastAPI.

- `fastapi==0.116.1`
  > For creating APIs or interactive web services.

## ✅ Suggested Additional Installs (If Needed)

```bash
pip install pydub soundfile
```
