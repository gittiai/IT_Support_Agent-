
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import run_agent

def main():
    print("=" * 60)
    print("🤖 IT Support AI Agent - Chat Interface")
    print("=" * 60)
    print("Type your IT support request in natural language.")
    print("Examples:")
    print("  - reset password for john@company.com")
    print("  - create user Sarah Connor sarah@company.com Manager Pro")
    print("  - deactivate bob@company.com")
    print("  - check if user exists, if not create them")
    print("\nType 'exit' to quit.\n")
    
    while True:
        try:
            task = input("💬 Your request: ").strip()
            if not task:
                continue
            if task.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            run_agent(task)
            print()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
