# SketchUp AI Bridge

An experimental, local-first connector that lets an MCP-compatible assistant inspect the active SketchUp desktop model and create simple 3D boxes using plain language. It combines a SketchUp Ruby extension with a small Python MCP server.

**Early prototype:** an MCP client has discovered and called the server against a simulated SketchUp peer, but it has not yet been verified end to end in SketchUp or either assistant. It currently offers three tools: model information, a list of top-level groups, and an undoable rectangular solid. It does not provide general SketchUp command coverage, arbitrary Ruby execution, rendering, or SketchUp for Web support.

## Requirements

- SketchUp desktop with Ruby extensions enabled (macOS or Windows); not SketchUp for Web.
- Python 3.10 or later and internet access to install dependencies.
- Claude Desktop with local MCP support, or ChatGPT with access to a custom MCP server and Secure MCP Tunnel.
- A single SketchUp instance and a test model. Save a backup before making changes.

## 1. Install the SketchUp extension

Download this repository, including the prebuilt `sketchup-ai-bridge.rbz`. In SketchUp open **Window → Extension Manager → Install Extension**, select that RBZ, and enable it. SketchUp may warn that the extension is unsigned. Restart SketchUp and open a model. The **Extensions → SketchUp AI Bridge: Status** menu confirms the extension loaded. Alternatively, create a ZIP containing `rose_sketchup_bridge.rb` and the `rose_sketchup_bridge` folder directly at the archive root, both found inside `extension/`, and rename the ZIP to `sketchup-ai-bridge.rbz`.

Alternatively, on macOS or Linux, run `python3 build_extension.py`; on Windows run `py build_extension.py`. The resulting `sketchup-ai-bridge.rbz` is created in the project folder.

## 2. Install the MCP server

In a terminal in this repository, create a virtual environment and install the dependency:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Windows use `py -3 -m venv .venv` and `.venv\Scripts\python.exe -m pip install -r requirements.txt`. Keep the repository in a permanent location, since the assistant will use its absolute path.

## 3. Connect Claude Desktop

In Claude Desktop open **Settings → Developer → Edit Config** (or the local MCP servers configuration under Desktop app settings). Merge the following into the configuration, replacing both paths with absolute paths to the project. Do not replace existing servers.

```json
{
  "mcpServers": {
    "sketchup-ai-bridge": {
      "command": "/ABSOLUTE/PATH/TO/PROJECT/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/TO/PROJECT/server.py"]
    }
  }
}
```

On Windows use the full path to `.venv\\Scripts\\python.exe`, with backslashes escaped in JSON. Restart Claude Desktop. With SketchUp running and a model open, ask: “Get my SketchUp model information,” then “Create a 1000 mm wide, 500 mm deep, 750 mm high box at the origin.” Check the model and use SketchUp Undo if necessary. See [Claude's local MCP guidance](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

## 4. Connect ChatGPT

Run `.venv/bin/python server.py --http` (on Windows, `.venv\Scripts\python.exe server.py --http`). The MCP endpoint listens **only** on `http://127.0.0.1:8765/mcp`. Localhost is not directly reachable by ChatGPT on the web. Set up an [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) for this endpoint and add the tunnel as a custom MCP server in ChatGPT, following [OpenAI's connection instructions](https://developers.openai.com/api/docs/guides/custom-mcp-server). The tunnel requires an eligible OpenAI Platform organization, a tunnel ID, a runtime API key, the tunnel client, and appropriate workspace permissions. The tunnel flow has not been verified with this project. Keep access private; do not expose this unauthenticated local endpoint to the internet.

## Commands and units

| Tool | Effect |
| --- | --- |
| `model_info` | Reports the active model's title, path and counts. |
| `list_groups` | Lists up to 500 top-level groups, IDs and bounding-box dimensions. |
| `create_box` | Adds one named group, with dimensions and origin in millimetres, along the model's X, Y and Z axes. Undoable in SketchUp. |

All commands operate on the active model's root, including while another group is open for editing. This bridge does not save the model. A timeout does **not** prove a change failed: inspect the model before retrying. One running SketchUp instance is supported; two instances may process the same request or apply it to the wrong model. The bridge uses `~/.sketchup-ai-bridge` as local IPC storage. It is not an authentication boundary against other programs running as the same user. Only connect trusted assistants and users; model information including its local path may be shared with the assistant provider. Avoid sensitive models, especially when using remote services.

## Troubleshooting

- If the assistant times out, ensure SketchUp desktop is running, a model is open, and the extension's Status menu appears. A modal dialog can prevent timers from running.
- If Claude does not see the tools, verify the JSON and absolute paths and restart Claude. Consult its server logs.
- If an RBZ is rejected, verify its root contains the Ruby loader and matching folder, not a parent folder.
- This prototype has not been verified on Windows or with multiple accounts. Its protocol tests use a simulated bridge, not SketchUp. The real MCP SDK was tested on macOS with Python 3.12 and MCP 1.30.0.

Not affiliated with or endorsed by Trimble, SketchUp, OpenAI, or Anthropic.
