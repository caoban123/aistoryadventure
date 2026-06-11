import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    try:
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', '--', 'frontend/index.html'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        diff_lines = result.stdout.splitlines()
        print(f"Total diff lines in index.html: {len(diff_lines)}")
        
        for line in diff_lines:
            if line.startswith('@@'):
                print("\n" + "="*80)
                print(line)
                print("="*80)
            elif line.startswith('+') and not line.startswith('+++'):
                if any(x in line for x in ['rpg', 'setup', 'Step', 'Next', 'Name', 'button', 'input']):
                    print(f"+ {line[1:]}")
            elif line.startswith('-') and not line.startswith('---'):
                if any(x in line for x in ['rpg', 'setup', 'Step', 'Next', 'Name', 'button', 'input']):
                    print(f"- {line[1:]}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
