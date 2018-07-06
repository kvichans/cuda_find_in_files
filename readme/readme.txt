Plugin "Find in Files" for CudaText. Gives dialog to search/replace in multiple files.

- Supports usual search and regex. Regex are from Python, groups are \0...\9.
- Can save current options to "presets".
- Lots of options (much more than in SynWrite).
- Results are shown in editor tab (bottom pane of CudaText not used).
- Can navigate to found lines from result-tab: 
    - using double-click
    - using commands in Plugins menu
    - using "Go to definition" CudaText command

Notes:

- Replace-fields are hidden by default, press the "=" button to show.
- Some opts must be set in user.json, see info after pressing the Help button.
- Files are handled line by line, so can't find/replace multiline matches, with line-end chars.

Author: A.Kvichanskiy (kvichans at forum/github)
