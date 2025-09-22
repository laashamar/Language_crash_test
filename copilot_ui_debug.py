#!/usr/bin/env python3
"""
Microsoft Copilot UI Debug Script

Kobler til Microsoft Copilot for Windows-appen og dumper UI-kontrollstruktur
for feilsøking og identifisering av UI-elementer.

Krav:
- Installer pywinauto: pip install pywinauto
- Sørg for at Microsoft Copilot er åpen før du kjører skriptet
"""

import sys

try:
    from pywinauto.application import Application
    from pywinauto.findwindows import ElementNotFoundError
    from pywinauto.findbestmatch import MatchError
    WINDOWS_AVAILABLE = True
except ImportError:
    # Not on Windows or missing dependencies
    WINDOWS_AVAILABLE = False
    class Application:
        def __init__(self, backend=None): pass
        def connect(self, title_re=None, title=None): return self
        def window(self, title_re=None, class_name=None): return self
    class ElementNotFoundError(Exception): pass
    class MatchError(Exception): pass

# Use same window detection logic as main script
WINDOW_TITLE_REGEX = r"^Copilot.*"

def main():
    # Check if we're on Windows with proper dependencies
    if not WINDOWS_AVAILABLE:
        print("❌ pywinauto ikke tilgjengelig eller ikke på Windows")
        print("💡 Installer med: pip install pywinauto")
        print("💡 Denne scriptet må kjøres på Windows")
        sys.exit(1)
        
    try:
        print("🔗 Kobler til Copilot-vindu for debug...")
        
        # Try regex matching first (consistent with main script)
        try:
            app = Application(backend="uia").connect(title_re=WINDOW_TITLE_REGEX)
            window = app.window(title_re=WINDOW_TITLE_REGEX)
            print("✅ Koblet til Copilot-vinduet via regex match")
        except (MatchError, ElementNotFoundError):
            # Fallback to exact title match
            print("⚠️ Regex match feilet, prøver eksakt tittel-match...")
            app = Application(backend="uia").connect(title="Copilot")
            window = app.window(class_name="WinUIDesktopWin32WindowClass")
            print("✅ Koblet til Copilot-vinduet via eksakt match")
        
        print("📋 Skriver ut kontrollstruktur...\n")
        window.print_control_identifiers()
        
        print("\n✅ Debug-utskrift fullført")
        sys.exit(0)
        
    except ElementNotFoundError as e:
        print(f"❌ Klarte ikke å koble til Copilot-vinduet: {e}")
        print("💡 Sjekk at Microsoft Copilot er åpen og synlig")
        sys.exit(1)
    except MatchError as e:
        print(f"❌ Kunne ikke finne Copilot-vindu: {e}")
        print("💡 Sjekk at Microsoft Copilot er åpen og synlig")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Uventet feil: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()