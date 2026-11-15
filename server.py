"""Local MCP server for a running SketchUp AI Bridge extension."""
import argparse
import json
import math
import os
from pathlib import Path
import time
import uuid

from mcp.server.fastmcp import FastMCP

bridge = Path.home() / ".sketchup-ai-bridge"
mcp = FastMCP("SketchUp AI Bridge", host="127.0.0.1", port=8765)


def request(command, arguments=None, timeout=20):
    for folder in (bridge, bridge / "requests", bridge / "responses"):
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    identifier = uuid.uuid4().hex
    pending = bridge / "requests" / (identifier + ".json")
    response = bridge / "responses" / (identifier + ".json")
    temp = bridge / "requests" / (identifier + ".tmp")
    payload = {"command": command, "arguments": arguments or {}, "expires_at": time.time() + timeout}
    try:
        with temp.open("x", encoding="utf-8") as f:
            json.dump(payload, f, allow_nan=False)
        os.replace(temp, pending)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if response.exists():
                result = json.loads(response.read_text(encoding="utf-8"))
                if not result.get("ok"):
                    raise RuntimeError(result.get("error", "SketchUp command failed"))
                return result["result"]
            time.sleep(0.1)
        raise TimeoutError("SketchUp did not respond in time. The operation may have completed; inspect the model before retrying.")
    finally:
        temp.unlink(missing_ok=True)
        pending.unlink(missing_ok=True)
        response.unlink(missing_ok=True)


@mcp.tool()
def model_info() -> dict:
    """Get the active SketchUp model name, path, and entity counts."""
    return request("model_info")


@mcp.tool()
def list_groups() -> dict:
    """List up to 500 top-level groups and their bounding box dimensions in mm."""
    return request("list_groups")


@mcp.tool()
def create_box(width_mm: float, depth_mm: float, height_mm: float,
               x_mm: float = 0, y_mm: float = 0, z_mm: float = 0,
               name: str = "AI box") -> dict:
    """Create one undoable rectangular solid group. Dimensions and origin are millimetres.

    Width runs along X, depth along Y, height along Z. Changes the active model.
    """
    numbers = (width_mm, depth_mm, height_mm, x_mm, y_mm, z_mm)
    if not all(math.isfinite(v) and abs(v) <= 1_000_000 for v in numbers):
        raise ValueError("All dimensions and coordinates must be finite and within 1,000,000 mm.")
    if min(width_mm, depth_mm, height_mm) <= 0:
        raise ValueError("Box dimensions must be positive.")
    if len(name) > 100:
        raise ValueError("Name must be at most 100 characters.")
    return request("create_box", dict(width_mm=width_mm, depth_mm=depth_mm,
                   height_mm=height_mm, x_mm=x_mm, y_mm=y_mm, z_mm=z_mm, name=name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Serve on localhost:8765 for a secure tunnel")
    args = parser.parse_args()
    mcp.run(transport="streamable-http" if args.http else "stdio")
