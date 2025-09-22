#!/usr/bin/env python3
"""
Microsoft Copilot UI Stress Test Script

Automatiserer sending av meldinger til Microsoft Copilot for Windows-appen
for å teste ytelse og stabilitet gjennom en flerspråklig samtalesimulering.

Krav:
- Installer pywinauto: pip install pywinauto
- Sørg for at Microsoft Copilot er åpen før du kjører skriptet
"""

import time
import random
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.findbestmatch import MatchErrorimport time
import random
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.findbestmatch import MatchError

# =============================================================================
# KONFIGURASJON
# =============================================================================

NUMBER_OF_MESSAGES = 50
WAIT_TIME_SECONDS = 3

SAMPLE_MESSAGES = [
    "Hello! How are you today? 😊",
    "Can you help me with a coding problem? 🤔💻",
    "What's the weather like? ☀️🌤️⛅",
    "I'm working on a Python project 🐍✨",
    "This is a stress test message 🧪⚡",
    "Thank you for your assistance! 🙏😊",
    "Can you explain machine learning? 🤖📚",
    "I love programming! 💖👨‍💻",
    "Have a great day! 🌟💫",
    "Testing the UI automation 🔧⚙️",
    "Hei! Hvordan har du det i dag? 😊🇳🇴",
    "Kan du hjelpe meg med et kodeproblem? 🤔💻",
    "Hvordan er været? ☀️❄️",
    "Jeg jobber med et Python-prosjekt 🐍✨",
    "Dette er en stresstest-melding 🧪⚡",
    "Tusen takk for hjelpen! 🙏😊",
    "Kan du forklare maskinlæring? 🤖📚",
    "Jeg elsker å programmere! 💖👨‍💻",
    "Ha en flott dag! 🌟💫",
    "Tester UI-automatisering 🔧⚙️",
    "Jeg bor i Norge 🇳🇴🏔️",
    "Kaffe og kode er bra 😊☕💻",
    "Rødt, gult og grønt 🔴🟡🟢",
    "Ærlighet, øl og åpenhet 🍺💭",
    "Bjørn går på lørdagstur 🐻🚶‍♂️",
    "Hello! Jeg snakker både engelsk og norsk 🌍🗣️",
    "Machine learning og kunstig intelligens 🤖🧠",
    "Python programming med æ, ø, å karakterer 🐍📝"
]

# =============================================================================
# VERIFISERTE UI-IDENTIFIKATORER
# =============================================================================

WINDOW_TITLE_REGEX = r"^Copilot.*"  # Matcher alle vinduer som starter med "Copilot"
TEXT_BOX_AUTO_ID = "InputTextBox"
SEND_BUTTON_AUTO_ID = "OldComposerMicButton"

ALT_TEXT_BOX_CONTROL_TYPE = "Edit"
ALT_SEND_BUTTON_NAME = "Snakk med Copilot"

# =============================================================================
# HOVEDFUNKSJON
# =============================================================================

def main():
    print("🚀 Starter Microsoft Copilot UI Stress Test")
    print(f"📊 Konfigurasjon: {NUMBER_OF_MESSAGES} meldinger, {WAIT_TIME_SECONDS}s mellomrom")
    print("="*60)

    try:
        print("🔗 Kobler til Copilot-vindu (regex-match)...")
        app = Application(backend="uia").connect(title_re=WINDOW_TITLE_REGEX)
        window = app.window(title_re=WINDOW_TITLE_REGEX)
        print("✅ Tilkobling til Copilot-vinduet vellykket")

        print("🔄 Starter meldingssløyfe...")

        for i in range(1, NUMBER_OF_MESSAGES + 1):
            try:
                print(f"📝 Sender melding {i} av {NUMBER_OF_MESSAGES}")
                message = random.choice(SAMPLE_MESSAGES)
                print(f"💬 Valgt melding: {message[:50]}{'...' if len(message) > 50 else ''}")

                # Finn tekstfelt
                try:
                    text_box = window.child_window(auto_id=TEXT_BOX_AUTO_ID)
                except ElementNotFoundError:
                    print("⚠️  Primær tekstfelt-identifikator feilet, prøver fallback...")
                    text_box = window.child_window(control_type=ALT_TEXT_BOX_CONTROL_TYPE)

                text_box.click_input()
                text_box.type_keys("^a{BACKSPACE}")
                text_box.type_keys(message, with_spaces=True)
                print("✏️  Melding skrevet inn")

                # Finn sendeknapp
                try:
                    send_button = window.child_window(auto_id=SEND_BUTTON_AUTO_ID)
                except ElementNotFoundError:
                    print("⚠️  Primær sendeknapp feilet, prøver fallback...")
                    send_button = window.child_window(title=ALT_SEND_BUTTON_NAME)

                send_button.click()
                print("🚀 Sendeknapp klikket")

                if i < NUMBER_OF_MESSAGES:
                    print(f"⏳ Venter {WAIT_TIME_SECONDS} sekunder før neste melding...")
                    time.sleep(WAIT_TIME_SECONDS)

            except ElementNotFoundError as e:
                print(f"❌ UI-element ikke funnet for melding {i}: {e}")
                continue

            except Exception as e:
                print(f"❌ Uventet feil ved melding {i}: {e}")
                continue

        print("="*60)
        print("🎉 Stresstest fullført!")
        print(f"📊 Totalt sendt: {NUMBER_OF_MESSAGES} meldinger")

    except MatchError:
        print("❌ Kunne ikke finne Copilot-vinduet via regex")
        print(f"💡 Sjekk at Copilot kjører og at tittelen starter med 'Copilot'")
        return

    except Exception as e:
        print(f"❌ Uventet feil: {e}")
        return

if __name__ == "__main__":
    main()