from pathlib import Path
path = Path('sam/document_management/app.py')
text = path.read_text(encoding='utf-8')
replacements = {
    'page_icon="?\x8f?"': 'page_icon="ZGR"',
    '"label": "?\x90 SAM API v2 Access"': '"label": "SAM API v2 Access"',
    '<h1 class="main-header">?\x8f? ZGR SAM Document Management System</h1>': '<h1 class="main-header">ZGR SAM Document Management System</h1>',
    '## ?\x8e? Opportunity Analysis': '## Opportunity Analysis',
    '\"?\x8d Search Opportunities\"': '"Search Opportunities"',
    '"?\x8d Search"': '"Search"',
    '## ?\x8d Analyzing': '## Analyzing',
    '### ?\x9d Agent Coordination': '### Agent Coordination',
    '### ?\x81 Upload Document': '### Upload Document',
    '## ?\x90 SAM API v2 Access': '## SAM API v2 Access',
    '"?\x8d Fetch Opportunities"': '"Fetch Opportunities"',
    '### ?\x9d? Disconnected': '### Disconnected',
    '??\x8f': '??',
    '???\x8f': '???',
    '## ?\x8f? ZGR': '## ZGR',
    'st.error("?\x9d? Disconnected")': 'st.error("Disconnected")',
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text, encoding='utf-8')
