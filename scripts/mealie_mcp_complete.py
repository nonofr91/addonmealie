#!/usr/bin/env python3
"""
Mealie MCP Server - Bridge vers mealie-mcp-server/

Ce fichier sert de point d'entrée compatible pour Windsurf,
délégant au serveur MCP canonique dans mealie-mcp-server/.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Délègue au serveur MCP canonique mealie-mcp-server"""
    repo_root = Path(__file__).resolve().parent
    mcp_server_path = repo_root / "mealie-mcp-server"
    
    if not mcp_server_path.exists():
        print(f"Erreur: mealie-mcp-server introuvable à {mcp_server_path}", file=sys.stderr)
        sys.exit(1)
    
    # Utiliser uv pour exécuter le serveur MCP
    cmd = [
        "uv",
        "--directory",
        str(mcp_server_path),
        "run",
        "src/server.py"
    ]
    
    try:
        process = subprocess.Popen(cmd, cwd=repo_root)
        process.wait()
    except KeyboardInterrupt:
        print("\nArrêt du serveur MCP...")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur lors du démarrage du serveur MCP: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
