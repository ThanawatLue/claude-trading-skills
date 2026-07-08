"""Gemini Adapter — migrated to google-genai SDK (google.generativeai is deprecated).

Usage:
    - call_gemini(prompt, ...)           → simple text/JSON call
    - run_gemini_agent(prompt, ...)      → agentic loop with file tools
    - extract_json_from_text(text)       → parse JSON from LLM output
"""
import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger("gemini_adapter")


def _get_client():
    """Return a configured google.genai client, or None if API key missing."""
    try:
        from google import genai
    except ImportError:
        logger.error("google-genai package not installed. Run: pip install google-genai")
        return None, None

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error(
            "Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
        )
        return None, None

    client = genai.Client(api_key=api_key)
    return client, genai


def _call_generate_content_with_retry(
    client,
    model: str,
    contents,
    config,
    max_retries: int = 5,
    initial_delay: float = 5.0,
):
    """Call generate_content with retry logic on transient errors."""
    import time
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            err_msg = str(e)
            is_transient = (
                "503" in err_msg
                or "UNAVAILABLE" in err_msg
                or "429" in err_msg
                or "RESOURCE_EXHAUSTED" in err_msg
            )
            if is_transient and attempt < max_retries - 1:
                sleep_time = delay
                is_429 = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                if is_429:
                    match = re.search(r"Please retry in (\d+(?:\.\d+)?)s", err_msg, re.IGNORECASE)
                    if match:
                        sleep_time = float(match.group(1)) + 2.0  # 2s safety buffer
                    else:
                        match_delay = re.search(r"retryDelay':\s*'(\d+)s'", err_msg)
                        if match_delay:
                            sleep_time = float(match_delay.group(1)) + 2.0
                        else:
                            sleep_time = 62.0  # safe default for 429
                
                logger.warning(
                    "Gemini API returned transient error (attempt %d/%d): %s. Retrying in %.1f seconds...",
                    attempt + 1,
                    max_retries,
                    err_msg,
                    sleep_time,
                )
                time.sleep(sleep_time)
                delay *= 2.0
            else:
                raise e


def call_gemini(
    prompt: str,
    model_name: str = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    temperature: float = 0.2,
    max_output_tokens: int = 8192,
    response_mime_type: str = "text/plain",
) -> str | None:
    """Call Gemini CLI (or fall back to Gemini API via SDK) and return the text response."""
    import subprocess
    import shutil

    gemini_path = shutil.which("gemini")
    if gemini_path:
        import uuid
        import os
        session_id = str(uuid.uuid4())
        js_path = os.path.join(os.path.dirname(gemini_path), "node_modules", "@google", "gemini-cli", "bundle", "gemini.js")
        if os.path.exists(js_path):
            cmd = ["node", js_path, "-o", "json", "--skip-trust", "--session-id", session_id]
            use_shell = False
        else:
            cmd = [gemini_path, "-o", "json", "--skip-trust", "--session-id", session_id]
            use_shell = True if os.name == "nt" else False
            
        if model_name:
            cmd.extend(["-m", model_name])
            
        try:
            import time
            # Respect Free Tier RPM (15 RPM = 4 seconds per request)
            logger.info("Sleeping 4.5 seconds to respect Free Tier API rate limits...")
            time.sleep(4.5)
            
            logger.info("Calling gemini CLI for prompt...")
            env = os.environ.copy()
            for k in list(env.keys()):
                if k.startswith("ANTIGRAVITY_"):
                    env.pop(k)
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                shell=use_shell,
                env=env
            )
            if result.returncode == 0:
                output_text = result.stdout
                pos = output_text.find("{")
                if pos != -1:
                    json_text = output_text[pos:]
                    try:
                        data = json.loads(json_text)
                        response = data.get("response")
                        if response:
                            return response
                    except json.JSONDecodeError:
                        pass
                if output_text.strip():
                    return output_text.strip()
            else:
                logger.warning("Gemini CLI returned non-zero code (%d): %s. Falling back to SDK...", result.returncode, result.stderr)
        except Exception as e:
            logger.warning("Failed to call gemini CLI: %s. Falling back to SDK...", e)

    # 2. Fallback to google-genai SDK
    client, genai = _get_client()
    if client is None:
        return None

    try:
        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "safety_settings": [
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai.types.SafetySetting(
                    category=genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                ),
            ],
        }
        if response_mime_type == "application/json":
            config_kwargs["response_mime_type"] = "application/json"

        response = _call_generate_content_with_retry(
            client=client,
            model=model_name,
            contents=prompt,
            config=genai.types.GenerateContentConfig(**config_kwargs),
        )

        if not response or not response.text:
            logger.error("Gemini returned an empty response.")
            return None

        return response.text

    except Exception as e:
        logger.error("Error calling Gemini API: %s", e)
        return None



# ── File Tool Implementations ─────────────────────────────────────────────────


def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {path}: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file (creates parent directories if needed)."""
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file {path}: {e}"


def list_files(path: str) -> str:
    """List files in a directory."""
    try:
        items = os.listdir(path)
        return "\n".join(items) if items else "(empty directory)"
    except Exception as e:
        return f"Error listing directory {path}: {e}"


def grep_search(pattern: str, path: str) -> str:
    """Search for a regex pattern in all files under a path."""
    results: list[str] = []
    try:
        for root, _, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                results.append(f"{full_path}:{i}: {line.strip()}")
                except (OSError, UnicodeDecodeError):
                    continue
        return "\n".join(results[:100]) or "No matches found."
    except Exception as e:
        return f"Error searching in {path}: {e}"


# ── Agentic Loop ──────────────────────────────────────────────────────────────

_TOOL_MAP = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "grep_search": grep_search,
}


def run_gemini_agent(
    prompt: str,
    model_name: str = "gemini-2.0-flash",
    max_turns: int = 10,
) -> bool:
    """Run a Gemini agentic loop via the gemini CLI (or fall back to Python SDK)."""
    import subprocess
    import shutil

    gemini_path = shutil.which("gemini")
    if gemini_path:
        import uuid
        import os
        session_id = str(uuid.uuid4())
        js_path = os.path.join(os.path.dirname(gemini_path), "node_modules", "@google", "gemini-cli", "bundle", "gemini.js")
        if os.path.exists(js_path):
            cmd = ["node", js_path, "--approval-mode", "yolo", "-o", "json", "--skip-trust", "--session-id", session_id]
            use_shell = False
        else:
            cmd = [gemini_path, "--approval-mode", "yolo", "-o", "json", "--skip-trust", "--session-id", session_id]
            use_shell = True if os.name == "nt" else False
            
        if model_name:
            cmd.extend(["-m", model_name])
            
        try:
            import time
            # Respect Free Tier RPM (15 RPM = 4 seconds per request)
            logger.info("Sleeping 4.5 seconds to respect Free Tier API rate limits in agent mode...")
            time.sleep(4.5)
            
            logger.info("Spawning gemini CLI in YOLO mode...")
            env = os.environ.copy()
            for k in list(env.keys()):
                if k.startswith("ANTIGRAVITY_"):
                    env.pop(k)
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                shell=use_shell,
                env=env
            )
            if result.returncode == 0:
                logger.info("Gemini CLI agent completed successfully.")
                return True
            else:
                logger.warning("Gemini CLI agent returned non-zero code (%d): %s. Falling back to SDK...", result.returncode, result.stderr)
        except Exception as e:
            logger.warning("Failed to call gemini CLI agent: %s. Falling back to SDK...", e)

    # 2. Fallback to google-genai SDK
    client, genai = _get_client()
    if client is None:
        return False

    # Declare tools to Gemini
    tools = [
        genai.types.Tool(
            function_declarations=[
                genai.types.FunctionDeclaration(
                    name="read_file",
                    description="Read a file from the local filesystem.",
                    parameters=genai.types.Schema(
                        type="OBJECT",
                        properties={"path": genai.types.Schema(type="STRING")},
                        required=["path"],
                    ),
                ),
                genai.types.FunctionDeclaration(
                    name="write_file",
                    description="Write content to a file on the local filesystem.",
                    parameters=genai.types.Schema(
                        type="OBJECT",
                        properties={
                            "path": genai.types.Schema(type="STRING"),
                            "content": genai.types.Schema(type="STRING"),
                        },
                        required=["path", "content"],
                    ),
                ),
                genai.types.FunctionDeclaration(
                    name="list_files",
                    description="List files in a directory.",
                    parameters=genai.types.Schema(
                        type="OBJECT",
                        properties={"path": genai.types.Schema(type="STRING")},
                        required=["path"],
                    ),
                ),
                genai.types.FunctionDeclaration(
                    name="grep_search",
                    description="Search for a regex pattern in files under a path.",
                    parameters=genai.types.Schema(
                        type="OBJECT",
                        properties={
                            "pattern": genai.types.Schema(type="STRING"),
                            "path": genai.types.Schema(type="STRING"),
                        },
                        required=["pattern", "path"],
                    ),
                ),
            ]
        )
    ]

    contents = [{"role": "user", "parts": [{"text": prompt}]}]

    try:
        import time
        for turn in range(max_turns):
            if turn > 0:
                logger.info("Rate limit safety: sleeping 6.5 seconds before turn %d...", turn + 1)
                time.sleep(6.5)

            response = _call_generate_content_with_retry(
                client=client,
                model=model_name,
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    tools=tools,
                    temperature=0.2,
                    max_output_tokens=8192,
                    safety_settings=[
                        genai.types.SafetySetting(
                            category=genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        genai.types.SafetySetting(
                            category=genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        genai.types.SafetySetting(
                            category=genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        genai.types.SafetySetting(
                            category=genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                    ],
                ),
            )

            candidate = response.candidates[0] if response.candidates else None
            if candidate is None:
                logger.error("Gemini agent: no candidate in response.")
                return False

            if not candidate.content or not hasattr(candidate.content, "parts"):
                logger.error("Gemini agent: candidate content is None or has no parts.")
                return False

            # Check if we have tool calls
            tool_calls = [
                part.function_call
                for part in candidate.content.parts
                if hasattr(part, "function_call") and part.function_call
            ]

            if not tool_calls:
                # Final text response — done
                logger.info("Gemini agent completed in %d turn(s).", turn + 1)
                return True

            # Execute each tool call and feed results back
            tool_results = []
            logger.info("Gemini agent requested tool calls: %s", [(fc.name, dict(fc.args)) for fc in tool_calls])
            for fc in tool_calls:
                fn = _TOOL_MAP.get(fc.name)
                if fn:
                    result = fn(**dict(fc.args))
                else:
                    result = f"Unknown tool: {fc.name}"
                logger.info("Tool %s completed. Output length: %s chars", fc.name, len(str(result)))
                tool_results.append(
                    {
                        "function_response": {
                            "name": fc.name,
                            "response": {"output": str(result)},
                        }
                    }
                )

            # Append model response and tool results to conversation
            contents.append({"role": "model", "parts": candidate.content.parts})
            contents.append({"role": "user", "parts": tool_results})

        logger.warning("Gemini agent reached max_turns (%d) without finishing.", max_turns)
        return False

    except Exception as e:
        logger.error("Gemini agent error: %s", e)
        return False


# ── JSON Helper ───────────────────────────────────────────────────────────────


def extract_json_from_text(text: str) -> dict | None:
    """Extract and parse JSON from an LLM response string."""
    if not text:
        return None

    text = text.strip()

    # 1. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Try to strip markdown code fences
    stripped = re.sub(r"^```(?:json)?\s*", "", text)
    stripped = re.sub(r"\s*```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3. Scan for JSON object using raw_decode
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        pos = text.find("{", idx)
        if pos == -1:
            break
        try:
            obj, _ = decoder.raw_decode(text, pos)
            if isinstance(obj, dict):
                return obj
            idx = pos + 1
        except json.JSONDecodeError:
            idx = pos + 1

    return None


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    test_prompt = "Reply with only a JSON object: {\"status\": \"ok\", \"model\": \"gemini-3-flash\"}"
    result = call_gemini(test_prompt, response_mime_type="application/json")
    print("Response:", result)
    parsed = extract_json_from_text(result or "")
    print("Parsed JSON:", parsed)
    sys.exit(0 if parsed else 1)
