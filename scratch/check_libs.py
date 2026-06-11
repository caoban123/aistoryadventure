import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    try:
        import playwright
        print("Playwright is installed!")
    except ImportError:
        print("Playwright is not installed.")
        
    try:
        import selenium
        print("Selenium is installed!")
    except ImportError:
        print("Selenium is not installed.")

if __name__ == '__main__':
    main()
