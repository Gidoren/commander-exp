"""Logging proxy between pi and Unsloth Studio's OpenAI-compatible endpoint.

Five wrong diagnoses in this project came from reasoning about what happened
between pi and the server instead of measuring it. `--no-session` means pi
keeps no transcript, and the harness only ever saw pi's stdout, so a task that
produced `diff_bytes: 0` could not be attributed: either the server returned
nothing, or pi discarded what it got. Those are different bugs.

This sits in front of Studio, forwards every request unchanged, and records
what actually crossed the wire - including the response bodies pi throws away.

    python scripts/trace_proxy.py --port 8899 --upstream http://127.0.0.1:8888

Then point pi's `baseUrl` at the proxy. Each completion appends one JSON line
to the trace file with the fields that distinguish the failure modes:
finish_reason, completion_tokens, whether content was empty, reasoning length,
and decode tok/s.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

UPSTREAM = "http://127.0.0.1:8888"
TRACE = Path("results/traces/trace.jsonl")
LOCK = threading.Lock()
# Hop-by-hop headers must not be forwarded; Content-Length is recomputed.
DROP = {"host", "content-length", "connection", "keep-alive", "transfer-encoding"}


def record(entry: dict) -> None:
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    with LOCK:
        TRACE.parent.mkdir(parents=True, exist_ok=True)
        with TRACE.open("a") as f:
            f.write(json.dumps(entry) + "\n")


def describe_call(name: str | None, args: str) -> dict:
    """One tool call, with a stable identity for cycle detection.

    `sig` is a hash of the exact arguments: identical sig on consecutive calls
    means verbatim repetition, a short repeating sequence of sigs means a
    cycle, and all-distinct sigs means the model is varying its approach. Those
    three shapes imply different fixes, so the trace has to tell them apart.
    """
    cmd = args
    try:
        parsed = json.loads(args)
        if isinstance(parsed, dict):
            # bash uses `command`; read/edit/write use `path`
            cmd = parsed.get("command") or parsed.get("path") or args
    except Exception:
        pass
    cmd = str(cmd)
    return {
        "name": name,
        "sig": hashlib.sha1(args.encode("utf-8", "replace")).hexdigest()[:10],
        "cmd": cmd[:300],
        "args_len": len(args),
    }


def last_tool_result(messages: list) -> dict | None:
    """The most recent tool result carried in this request.

    Tool output reaches the server as a `role: "tool"` message on the *next*
    request, so pairing it with the previous response is the only way to see
    whether the loop's commands are succeeding or failing.
    """
    for m in reversed(messages or []):
        if m.get("role") != "tool":
            continue
        c = m.get("content")
        if isinstance(c, list):  # typed content blocks
            c = " ".join(str(b.get("text", "")) for b in c if isinstance(b, dict))
        c = str(c or "")
        return {"len": len(c), "head": c[:200].replace("\n", "\\n")}
    return None


def summarize_json(body: bytes) -> dict:
    """Pull the diagnostic fields out of a non-streamed completion."""
    try:
        d = json.loads(body)
    except Exception:
        return {"parse_error": True, "raw_len": len(body)}
    ch = (d.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    usage = d.get("usage") or {}
    tim = d.get("timings") or {}
    content = msg.get("content")
    return {
        "finish_reason": ch.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "content_len": len(content or ""),
        "content_empty": not content,
        "reasoning_len": len(msg.get("reasoning_content") or ""),
        "n_tool_calls": len(msg.get("tool_calls") or []),
        "tools": [(t.get("function") or {}).get("name")
                  for t in (msg.get("tool_calls") or [])],
        "calls": [describe_call((t.get("function") or {}).get("name"),
                                (t.get("function") or {}).get("arguments") or "")
                  for t in (msg.get("tool_calls") or [])],
        "tok_per_sec": round(tim.get("predicted_per_second", 0) or 0, 1),
    }


def summarize_sse(chunks: list[bytes]) -> dict:
    """Reassemble a streamed completion into the same diagnostic shape."""
    content, reasoning, finish, usage, tools = [], [], None, {}, 0
    names: list[str] = []
    # arguments stream as fragments across deltas, keyed by index
    calls: dict[int, dict] = {}
    for raw in b"".join(chunks).split(b"\n"):
        line = raw.strip()
        if not line.startswith(b"data:"):
            continue
        payload = line[5:].strip()
        if payload == b"[DONE]":
            continue
        try:
            d = json.loads(payload)
        except Exception:
            continue
        if d.get("usage"):
            usage = d["usage"]
        for ch in d.get("choices") or []:
            delta = ch.get("delta") or {}
            if delta.get("content"):
                content.append(delta["content"])
            if delta.get("reasoning_content"):
                reasoning.append(delta["reasoning_content"])
            if delta.get("tool_calls"):
                tools += len(delta["tool_calls"])
                # name arrives in the first delta of each call; later deltas
                # stream the arguments only
                for tc in delta["tool_calls"]:
                    fn = tc.get("function") or {}
                    slot = calls.setdefault(
                        tc.get("index", 0), {"name": None, "args": []}
                    )
                    if fn.get("name"):
                        slot["name"] = fn["name"]
                        names.append(fn["name"])
                    if fn.get("arguments"):
                        slot["args"].append(fn["arguments"])
            if ch.get("finish_reason"):
                finish = ch["finish_reason"]
    text = "".join(content)
    return {
        "streamed": True,
        "finish_reason": finish,
        "completion_tokens": usage.get("completion_tokens"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "content_len": len(text),
        "content_empty": not text,
        "reasoning_len": len("".join(reasoning)),
        # count distinct calls, not deltas - arguments stream across many
        # deltas, so summing them reported 17 where there were 2
        "n_tool_calls": len(calls),
        "tools": names,
        "calls": [describe_call(c["name"], "".join(c["args"]))
                  for c in calls.values()],
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # keep stderr clean; the trace file is the log
        pass

    def _proxy(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        headers = {k: v for k, v in self.headers.items() if k.lower() not in DROP}
        url = self.server.upstream + self.path

        req_info = {}
        if body:
            try:
                d = json.loads(body)
                req_info = {
                    "n_messages": len(d.get("messages") or []),
                    "max_tokens": d.get("max_tokens"),
                    "stream": bool(d.get("stream")),
                    "n_tools": len(d.get("tools") or []),
                    "temperature": d.get("temperature"),
                    "last_tool_result": last_tool_result(d.get("messages")),
                }
            except Exception:
                pass

        started = time.time()
        try:
            with httpx.stream(
                method, url, content=body, headers=headers, timeout=None
            ) as up:
                self.send_response(up.status_code)
                for k, v in up.headers.items():
                    if k.lower() not in DROP:
                        self.send_header(k, v)
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()

                chunks = []
                for chunk in up.iter_raw():
                    if not chunk:
                        continue
                    chunks.append(chunk)
                    # chunked framing, so the client can stream as it arrives
                    self.wfile.write(b"%X\r\n%s\r\n" % (len(chunk), chunk))
                    self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
                status = up.status_code
        except Exception as e:
            record({"path": self.path, "error": repr(e), "req": req_info})
            try:
                self.send_error(502, "proxy error")
            except Exception:
                pass
            return

        if "chat/completions" in self.path:
            joined = b"".join(chunks)
            summary = (
                summarize_sse(chunks)
                if joined.lstrip().startswith(b"data:")
                else summarize_json(joined)
            )
            record({
                "path": self.path,
                "status": status,
                "elapsed_s": round(time.time() - started, 2),
                "req": req_info,
                "resp": summary,
            })

    def do_POST(self):
        self._proxy("POST")

    def do_GET(self):
        self._proxy("GET")


def main() -> None:
    global TRACE
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--upstream", default=UPSTREAM)
    ap.add_argument("--trace", type=Path, default=TRACE)
    args = ap.parse_args()

    TRACE = args.trace

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    srv.upstream = args.upstream.rstrip("/")
    print(f"proxy :{args.port} -> {srv.upstream}   trace -> {TRACE}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
