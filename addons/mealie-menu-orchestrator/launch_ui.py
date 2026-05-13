#!/usr/bin/env python3
import sys
import streamlit.web.cli as stcli

sys.argv = ["streamlit", "run", "src/mealie_menu_orchestrator/ui.py", "--server.headless=true", "--browser.gatherUsageStats=false", "--server.fileWatcherType=none"]
sys.exit(stcli.main())
