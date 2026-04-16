"""
IT Support AI Agent - Fixed Version
"""
import os, base64, json, time, sys, re
from groq import Groq
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

ADMIN_URL = os.getenv("ADMIN_URL", "http://localhost:5050")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are an IT support AI agent controlling a browser.

PAGES AND EXACT FIELD IDs:
- Reset Password (/reset-password): #email, #new_password, #confirm_password, button="Reset Password"
- Create User (/create-user): #name, #email, #role, #license, button="Create User"
- Manage Users (/manage-users): buttons "Deactivate", "Activate", "Delete"

RULES:
1. ALWAYS navigate to correct page first
2. Use ONLY exact IDs: #email #new_password #confirm_password #name #role #license
3. For buttons put exact text in selector field
4. Never use :contains() syntax

JSON response only:
{
  "action": "navigate|click|fill|select|submit|done",
  "selector": "#id or button text",
  "value": "url or fill value",
  "reasoning": "brief",
  "task_complete": false
}"""



def extract_email(task):
    match = re.search(r'[\w\.-]+@[\w\.-]+', task)
    return match.group(0) if match else ""

def screenshot_to_base64(page):
    return base64.standard_b64encode(page.screenshot()).decode("utf-8")

def fill_field(page, selector, value):
    for fn in [
        lambda: page.fill(selector, value, timeout=3000),
        lambda: page.locator(selector).fill(value),
        lambda: (page.locator(selector).click(), page.keyboard.type(value)),
    ]:
        try:
            fn()
            return True
        except:
            continue
    return False

def click_by_text(page, text):
    match = re.search(r":contains\(['\"](.+?)['\"]\)", text)
    if match:
        text = match.group(1)
    for fn in [
        lambda: page.click(f"button:text-is('{text}')", timeout=3000),
        lambda: page.click(f"button:text('{text}')", timeout=3000),
        lambda: page.get_by_role("button", name=text).first.click(timeout=3000),
        lambda: page.get_by_text(text, exact=True).first.click(timeout=3000),
    ]:
        try:
            fn()
            return True
        except:
            continue
    return False


def run_reset_password(page, task):
    email = extract_email(task)
    page.goto(f"{ADMIN_URL}/reset-password", wait_until="networkidle")
    time.sleep(1)
    fill_field(page, "#email", email)
    fill_field(page, "#new_password", "TempPass@123")
    fill_field(page, "#confirm_password", "TempPass@123")
    click_by_text(page, "Reset Password")
    page.wait_for_load_state("networkidle")
    print(f"  ✅ Password reset for {email}")

def run_create_user(page, task):
    email = extract_email(task)
    parts = task.split()
    idx = next((i for i, p in enumerate(parts) if '@' in p), -1)
    name = " ".join(parts[2:idx]) if idx > 2 else "New User"
    role = parts[idx+1] if idx+1 < len(parts) else "Employee"
    license_type = parts[idx+2] if idx+2 < len(parts) else "Basic"

    page.goto(f"{ADMIN_URL}/create-user", wait_until="networkidle")
    time.sleep(1)
    fill_field(page, "#name", name)
    fill_field(page, "#email", email)
    page.select_option("#role", role)
    page.select_option("#license", license_type)
    click_by_text(page, "Create User")
    page.wait_for_load_state("networkidle")
    print(f"  ✅ Created {name} ({email})")

def run_manage_user(page, task, button_text):
    email = extract_email(task)
    page.goto(f"{ADMIN_URL}/manage-users", wait_until="networkidle")
    time.sleep(1)
    row = page.locator(f"tr:has-text('{email}')")
    row.locator(f"button:text('{button_text}')").click()
    page.wait_for_load_state("networkidle")
    print(f"  ✅ {button_text}d {email}")

def detect_task(task):
    t = task.lower()
    if "reset password" in t:   return "reset_password"
    if "create user" in t:      return "create_user"
    if "deactivate" in t:       return "deactivate"
    if "activate" in t:         return "activate"
    if "delete" in t:           return "delete"
    return "llm"


def ask_groq(task, screenshot_b64, history):
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": f"Task: {task}\nHistory: {json.dumps(history[-3:])}\nNext action?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
            ]}
        ],
        max_tokens=300, temperature=0.1,
    )
    raw = response.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    return json.loads(raw)

def execute_action(page, action_data):
    action   = action_data.get("action")
    selector = action_data.get("selector", "")
    value    = action_data.get("value", "")
    try:
        if action == "navigate":
            url = value if value.startswith("http") else f"{ADMIN_URL}{value}"
            page.goto(url, wait_until="networkidle"); time.sleep(1)
            return f"Navigated to {url}"
        elif action == "fill":
            fill_field(page, selector, value)
            return f"Filled {selector}"
        elif action in ("click", "submit"):
            if selector.startswith("#"):
                page.click(selector, timeout=3000)
            else:
                click_by_text(page, selector)
            if action == "submit":
                page.wait_for_load_state("networkidle")
            return f"{action}: {selector}"
        elif action == "select":
            page.select_option(selector, value)
            return f"Selected {value}"
        elif action == "done":
            return "DONE"
    except Exception as e:
        return f"Error: {e}"


def run_agent(task: str, max_steps: int = 15):
    print(f"\n{'='*60}\n🤖 Task: {task}\n{'='*60}\n")
    task_type = detect_task(task)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(ADMIN_URL, wait_until="networkidle")

        if task_type == "reset_password":
            run_reset_password(page, task)
        elif task_type == "create_user":
            run_create_user(page, task)
        elif task_type == "deactivate":
            run_manage_user(page, task, "Deactivate")
        elif task_type == "activate":
            run_manage_user(page, task, "Activate")
        elif task_type == "delete":
            run_manage_user(page, task, "Delete")
        else:
            history = []
            for step in range(max_steps):
                print(f"Step {step+1}/{max_steps}")
                try:
                    action_data = ask_groq(task, screenshot_to_base64(page), history)
                    print(f"  🧠 {action_data.get('reasoning','')}")
                    result = execute_action(page, action_data)
                    print(f"  ✅ {result}")
                    history.append({"step": step+1, "action": action_data.get("action"), "result": result})
                    if result == "DONE" or action_data.get("task_complete"):
                        break
                except Exception as e:
                    print(f"  ❌ {e}"); break
                time.sleep(1.5)

        print("\nClosing in 5s...")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py 'your IT request'")
        sys.exit(1)
    run_agent(" ".join(sys.argv[1:]))