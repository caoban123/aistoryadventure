import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    with open('frontend/rpg_app.js', 'r', encoding='utf-8') as f:
        content = f.read()
        
    funcs = [
        "initRpgSetupWizard",
        "initRpgComposer",
        "initShopController",
        "initPartyController",
        "initCombatOverlayController",
        "initRpgImagesController",
        "initRpgSettingsDrawer",
        "initRpgQuestController",
        "initRpgMapController",
        "initRpgDungeonController",
        "initRpgHelpController",
        "initRpgDebugConsoleController",
        "initRpgKeyboardShortcuts"
    ]
    
    for func in funcs:
        match = re.search(r'function\s+' + func + r'\b', content)
        if match:
            print(f"✅ {func} is defined.")
        else:
            print(f"❌ {func} is NOT defined!")

if __name__ == '__main__':
    main()
