LIGHT THEME UPDATE

1. Stop the dashboard in VS Code with Ctrl+C.
2. Extract this ZIP completely.
3. Double-click APPLY_LIGHT_THEME.cmd inside the extracted folder.
4. Wait for LIGHT THEME INSTALLED.
5. In the VS Code terminal for Temporal_GNN_Streamlit, run:

   .\START_LIGHT.cmd

Open http://localhost:8502 if the browser does not open automatically.
Keep the terminal open while using the app.

This updates only intelligence/theme.py and adds START_LIGHT.cmd.
The previous theme file is backed up as intelligence/theme.before_light.py.bak.
Your existing model, predictions and training artifacts are unchanged.
No package installation or training is required.

The light shortcut supplies Streamlit's complete light palette, overriding the
existing dark colours in .streamlit/config.toml. The updated custom CSS and
Plotly charts follow the theme.base startup setting.

To return to dark mode, stop the running app and use your previous VS Code command:

   .\.venv\Scripts\python.exe -m streamlit run app_intelligence.py --server.port 8502 --theme.base dark

Use these startup commands rather than the browser Settings theme switch;
custom chart styling follows the server's startup theme setting.
