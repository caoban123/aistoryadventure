import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
        
    for i in range(1, 9):
        step_id = f"rpgStep{i}"
        match = re.search(r'id=["\']' + step_id + r'["\']', html)
        if match:
            print(f"✅ {step_id} exists in index.html")
        else:
            print(f"❌ {step_id} is missing from index.html!")
            
    # Also check Next/Back buttons for each step
    buttons = [
        "rpgStep1Next",
        "rpgStep2Next", "rpgStep2Back",
        "rpgStep3Next", "rpgStep3Back",
        "rpgStep4Next", "rpgStep4Back",
        "rpgStep5Next", "rpgStep5Back",
        "rpgStep6Next", "rpgStep6Back",
        "rpgStep7Next", "rpgStep7Back",
        "rpgStep8Back", "rpgStartAdventureBtn"
    ]
    print("\nChecking buttons:")
    for btn in buttons:
        match = re.search(r'id=["\']' + btn + r'["\']', html)
        if match:
            print(f"✅ {btn} exists")
        else:
            print(f"❌ {btn} is missing!")

if __name__ == '__main__':
    main()
