import subprocess
import sys

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def main():
    try:
        # Run git diff command
        result = subprocess.run(
            ['git', 'diff', 'HEAD~1', '--', 'frontend/rpg_app.js'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        diff_lines = result.stdout.splitlines()
        
        print(f"Total diff lines: {len(diff_lines)}")
        
        # Only print added/removed lines that are relevant to controllers, functions, or listeners.
        # We can look for hunks around initRPGApp, initRpgMapController, etc.
        for line in diff_lines:
            if line.startswith('@@'):
                print("\n" + "="*80)
                print(line)
                print("="*80)
            elif line.startswith('+') and not line.startswith('+++'):
                # print added lines
                if any(x in line for x in ['function', 'addEventListener', 'rpgStep1Next', 'toggleRpgMapMode', 'initRpgMapController', 'E', 'rpgMapModeBadge']):
                    print(f"+ {line[1:]}")
            elif line.startswith('-') and not line.startswith('---'):
                # print removed lines
                if any(x in line for x in ['function', 'addEventListener', 'rpgStep1Next', 'toggleRpgMapMode', 'initRpgMapController', 'E', 'rpgMapModeBadge']):
                    print(f"- {line[1:]}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
