from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

try:
    # Koble til prosessen via vindustittel
    app = Application(backend="uia").connect(title="Copilot")
    window = app.window(class_name="WinUIDesktopWin32WindowClass")
except ElementNotFoundError:
    print("❌ Klarte ikke å koble til Copilot-vinduet.")
    exit(1)

# Skriv ut hele trestrukturen av UI-elementer
print("✅ Koblet til Copilot-vinduet. Skriver ut kontrollstruktur...\n")
window.print_control_identifiers()