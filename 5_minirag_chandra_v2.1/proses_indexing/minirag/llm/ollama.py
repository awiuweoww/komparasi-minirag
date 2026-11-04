"""
Ollama LLM Interface Module
==========================

This module provides interfaces for interacting with Ollama's language models,
including text generation and embedding capabilities.

Author: Lightrag team
Created: 2024-01-24
License: MIT License

Copyright (c) 2024 Lightrag

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

Version: 1.0.0

Change Log:
- 1.0.0 (2024-01-24): Initial release
    * Added async chat completion support
    * Added embedding generation
    * Added stream response capability

Dependencies:
    - ollama
    - numpy
    - pipmaster
    - Python >= 3.10

Usage:
    from llm_interfaces.ollama_interface import ollama_model_complete, ollama_embed
"""

__version__ = "1.0.0"
__author__ = "lightrag Team"
__status__ = "Production"

import sys

if sys.version_info < (3, 9):
    from typing import AsyncIterator
else:
    from collections.abc import AsyncIterator
import pipmaster as pm  # Pipmaster for dynamic library install

# install specific modules
if not pm.is_installed("ollama"):
    pm.install("ollama")
if not pm.is_installed("tenacity"):
    pm.install("tenacity")

import ollama
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from minirag.exceptions import (
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
)
import numpy as np
from typing import Union


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (RateLimitError, APIConnectionError, APITimeoutError)
    ),
)
async def ollama_model_if_cache(
    model,
    prompt,
    system_prompt=None,
    history_messages=[],
    **kwargs,
) -> Union[str, AsyncIterator[str]]:
    stream = True if kwargs.get("stream") else False
    kwargs.pop("max_tokens", None)
    # kwargs.pop("response_format", None) # allow json
    host = kwargs.pop("host", None)
    timeout = kwargs.pop("timeout", None)
    kwargs.pop("hashing_kv", None)
    api_key = kwargs.pop("api_key", None)
    headers = (
        {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        if api_key
        else {"Content-Type": "application/json"}
    )
    ollama_client = ollama.AsyncClient(host=host, timeout=timeout, headers=headers)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    
    # Force instruction into the user prompt ONLY for QA tasks (heuristic based on system prompt).
    # This must key off a phrase from OUR OWN prompt templates (rag_response / naive_rag_response
    # both say "responding to questions about ..."), not loose words like "asisten"/"Konteks"/"Peran" --
    # those can appear by chance inside retrieved entity descriptions (confirmed: "Peran" alone showed
    # up in 48 entity descriptions in the Perikanan indexes), making the old heuristic fire randomly
    # per-question depending on what got retrieved, instead of consistently for every QA-answering call.
    is_qa_task = system_prompt and "responding to questions about" in system_prompt
    
    if is_qa_task:
        forced_instruction = """

[INSTRUKSI WAJIB:
Anda adalah asisten hukum yang memberikan jawaban singkat dan langsung pada inti pertanyaan. Jawab dengan Bahasa Indonesia.
- Jika pertanyaan dimulai dengan "Siapa", jawab dengan SUBJEK/aktor (perorangan/organisasi) yang dimaksud.
- Jika pertanyaan dimulai dengan "Apa", jawab dengan OBJEK yang ditanyakan.
- Jika pertanyaan dimulai dengan "Kapan", jawab dengan waktu/tanggal/periode.
- Jika pertanyaan dimulai dengan "Dimana", jawab dengan lokasi/tempat.
- Jika pertanyaan dimulai dengan "Mengapa", jawab dengan alasan singkat.
- Jika pertanyaan dimulai dengan "Bagaimana", jawab dengan cara/tahapan ringkas.
- Jika pertanyaan dimulai dengan "Berapa", jawab dengan angka/jumlah yang ditanyakan.
JANGAN mengulang pertanyaan ke dalam jawaban"""
        messages.append({"role": "user", "content": prompt + forced_instruction})
    else:
        messages.append({"role": "user", "content": prompt})

    # Force num_predict to limit output length if not set
    if "options" not in kwargs:
        kwargs["options"] = {}
    # if "num_predict" not in kwargs["options"]:
    #     print("DEBUG: Setting num_predict=100")
    #     kwargs["options"]["num_predict"] = 100  # Limit to ~100 tokens for short answers
    # else:
    #     print(f"DEBUG: num_predict already set to {kwargs['options']['num_predict']}")

    # Add stop tokens to prevent verbosity
    # stop_tokens = ["Berikut penjelasannya:", "Berikut adalah:", "Penjelasan:", "Detail:", "\n\n**1.", "Tabel:", "Kesimpulan:", "Berikut rinciannya:", "Rincian:", "Daftar:", "Berikut penjabaran"]
    # if "stop" not in kwargs["options"]:
    #     kwargs["options"]["stop"] = stop_tokens

    print(f"DEBUG: Calling ollama.chat with options: {kwargs['options']}")
    response = await ollama_client.chat(model=model, messages=messages, **kwargs)
    
    if not stream:
        content = response['message']['content']
        print(f"DEBUG: Original response length: {len(content)}")
        
        # Post-processing truncation (Fallback) - DISABLED to test natural prompt adherence
        # 1. Truncate at any stop token if it appears in the text
        # for token in stop_tokens:
        #     if token in content:
        #         print(f"DEBUG: Truncating at stop token: '{token}'")
        #         content = content.split(token)[0]
                
        # 2. Truncate at the first double newline (keep only the first paragraph)
        # if "\n\n" in content:
        #      print("DEBUG: Truncating at first paragraph")
        #      content = content.split("\n\n")[0]

        # 3. Limit to 3 sentences (simple heuristic)
        # Split by '. ' but be careful about abbreviations. 
        # For now, simple split is better than 3000 chars.
        # sentences = content.split('. ')
        # if len(sentences) > 3:
        #     print("DEBUG: Truncating to 3 sentences")
        #     content = '. '.join(sentences[:3])
        #     if not content.endswith('.'):
        #         content += '.'
            
        # response['message']['content'] = content.strip()
        print(f"DEBUG: Final response length: {len(response['message']['content'])}")

    if stream:
        """cannot cache stream response"""

        async def inner():
            async for chunk in response:
                yield chunk["message"]["content"]

        return inner()
    else:
        return response["message"]["content"]


async def ollama_model_complete(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> Union[str, AsyncIterator[str]]:
    keyword_extraction = kwargs.pop("keyword_extraction", None)
    if keyword_extraction:
        kwargs["format"] = "json"
    model_name = kwargs["hashing_kv"].global_config["llm_model_name"]
    return await ollama_model_if_cache(
        model_name,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        **kwargs,
    )


async def ollama_embedding(texts: list[str], embed_model, **kwargs) -> np.ndarray:
    """
    Deprecated in favor of `embed`.
    """
    embed_text = []
    ollama_client = ollama.Client(**kwargs)
    for text in texts:
        data = ollama_client.embeddings(model=embed_model, prompt=text)
        embed_text.append(data["embedding"])

    return embed_text


async def ollama_embed(texts: list[str], embed_model, **kwargs) -> np.ndarray:
    api_key = kwargs.pop("api_key", None)
    headers = (
        {"Content-Type": "application/json", "Authorization": api_key}
        if api_key
        else {"Content-Type": "application/json"}
    )
    kwargs["headers"] = headers
    ollama_client = ollama.Client(**kwargs)
    data = ollama_client.embed(model=embed_model, input=texts)
    return data["embeddings"]
