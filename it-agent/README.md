# 🤖 IT Support AI Agent

An AI agent that takes natural-language IT support requests and carries them out using browser automation on a mock IT admin panel — no DOM shortcuts, no API calls, just the agent navigating like a human.

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Natural Language  │────▶│   Groq LLM (Llama 4) │────▶│  Playwright Browser │
│   IT Request        │     │   Vision + Reasoning  │     │  (Computer Use)     │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
                                        │                           │
                                        ▼                           ▼
                              ┌──────────────────┐      ┌──────────────────────┐
                              │  Action Decision  │      │  Mock IT Admin Panel │
                              │ (click/fill/nav)  │      │  (Flask App)         │
                              └──────────────────┘      └──────────────────────┘
```

**How it works:**
1. User gives a natural language IT request
2. Agent navigates to the admin panel in a real browser
3. Takes a screenshot and sends it to Groq (Llama 4 Vision)
4. LLM decides what action to take (navigate, click, fill, submit)
5. Agent executes the action in the browser
6. Repeat until task is complete

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set your Groq API key
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Or export it directly:
```bash
export GROQ_API_KEY=your_key_here
```

### 3. Start the IT Admin Panel
```bash
cd admin_panel
python app.py
```
Panel runs at http://localhost:5050

### 4. Run the Agent

**Single task:**
```bash
cd agent
python agent.py "reset password for john@company.com"
python agent.py "create user Sarah Connor sarah@company.com as Manager with Pro license"
python agent.py "deactivate bob@company.com"
```

**Interactive chat mode:**
```bash
cd agent
python chat.py
```

## Supported IT Tasks

| Task | Example |
|------|---------|
| Reset password | "reset password for john@company.com to Temp@1234" |
| Create user | "create a new user named Sarah Connor with email sarah@company.com as Manager" |
| Deactivate user | "deactivate user bob@company.com" |
| Activate user | "activate bob@company.com" |
| Assign license | "assign Pro license to john@company.com" |
| Delete user | "delete user bob@company.com" |

## Bonus: Multi-step with conditional logic
```bash
python agent.py "check if sarah@company.com exists, if not create her as a Manager with Pro license"
```

## Key Design Decisions

- **Groq + Llama 4 Scout**: Free, fast, supports vision — perfect for screenshot-based browser control
- **Playwright**: Real browser automation, no DOM selector cheating — agent sees what a human sees
- **Flask admin panel**: Lightweight, functional, realistic IT workflows
- **Screenshot loop**: Agent takes screenshot → LLM decides → executes → repeat (like Anthropic Computer Use)
- **No API shortcuts**: The agent fills forms and clicks buttons just like a human would

## Project Structure
```
it-agent/
├── admin_panel/
│   ├── app.py              # Flask IT admin panel
│   └── templates/          # HTML pages
│       ├── base.html
│       ├── index.html
│       ├── reset_password.html
│       ├── create_user.html
│       └── manage_users.html
├── agent/
│   ├── agent.py            # Core AI agent
│   └── chat.py             # Interactive CLI
├── requirements.txt
├── .env
└── README.md
```