import sys

sys.stdout.reconfigure(encoding='utf-8')

def read_last_lines(filepath, num_lines=50):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return lines[-num_lines:]
    except Exception as e:
        return [f"Error reading {filepath}: {e}\n"]

def main():
    print("=== FRONTEND LOGS ===")
    frontend_log = r"C:\Users\Admin\.gemini\antigravity\brain\ad58124c-a7df-432e-bd9c-d8434358287d\.system_generated\tasks\task-4789.log"
    for line in read_last_lines(frontend_log):
        print(line, end="")
        
    print("\n=== BACKEND LOGS ===")
    backend_log = r"C:\Users\Admin\.gemini\antigravity\brain\ad58124c-a7df-432e-bd9c-d8434358287d\.system_generated\tasks\task-4798.log"
    for line in read_last_lines(backend_log):
        print(line, end="")

if __name__ == '__main__':
    main()
