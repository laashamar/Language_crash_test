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
import subprocess
import sys
import os

try:
    from pywinauto.application import Application
    from pywinauto import timings
    from pywinauto.findwindows import ElementNotFoundError
    from pywinauto.findbestmatch import MatchError
    WINDOWS_AVAILABLE = True
except ImportError:
    # Not on Windows or missing dependencies - define dummy classes for syntax checking
    WINDOWS_AVAILABLE = False
    class Application:
        def __init__(self, backend=None): pass
        def connect(self, title_re=None): return self
        def window(self, title_re=None): return self
    class ElementNotFoundError(Exception): pass
    class MatchError(Exception): pass
    class timings:
        class Timings:
            window_find_timeout = 5
            after_clickinput_wait = 0

# =============================================================================
# KONFIGURASJON
# =============================================================================

NUMBER_OF_MESSAGES = 50
WAIT_TIME_SECONDS = 0.5  # Raskere meldingsflyt

# Optimaliser pywinauto-timings
timings.Timings.window_find_timeout = 5
timings.after_clickinput_wait = 0

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

WINDOW_TITLE_REGEX = r"^Copilot.*"  # Matcher både "Copilot" og "Copilot – Ny samtale"
TEXT_BOX_AUTO_ID = "InputTextBox"
SEND_BUTTON_AUTO_ID = "OldComposerMicButton"

ALT_TEXT_BOX_CONTROL_TYPE = "Edit"
ALT_SEND_BUTTON_NAME = "Snakk med Copilot"

# =============================================================================
# HJELPEFUNKSJONER
# =============================================================================

def dump_control_tree_via_script():
    """
    Kaller den separate debug-scriptet for å dumpe kontrolltre
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), "copilot_ui_debug.py")
        if os.path.exists(script_path):
            print("📋 Kjører separat debug-script for kontrolltre...")
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"⚠️ Debug-script feilet: {result.stderr}")
        else:
            print(f"⚠️ Debug-script ikke funnet: {script_path}")
    except subprocess.TimeoutExpired:
        print("⚠️ Debug-script timeout")
    except Exception as e:
        print(f"⚠️ Feil ved kjøring av debug-script: {e}")

def validate_window(window):
    """
    Validerer at vinduset er tilgjengelig og brukbart
    """
    try:
        # Sjekk at vinduset eksisterer
        if not window.exists():
            print("❌ Vindu eksisterer ikke")
            return False
        
        # Sjekk at vinduset er synlig
        if not window.is_visible():
            print("❌ Vindu er ikke synlig")
            return False
        
        # Sjekk at vinduset er aktivt/tilgjengelig
        if not window.is_enabled():
            print("❌ Vindu er ikke aktivert")
            return False
        
        # Test basic window interaction
        try:
            window.set_focus()
            print("✅ Vindu validert og fokusert")
            return True
        except Exception as e:
            print(f"⚠️ Kunne ikke fokusere vindu: {e}")
            return True  # Still continue if focus fails but window is otherwise valid
            
    except Exception as e:
        print(f"❌ Feil ved vindu-validering: {e}")
        return False

# =============================================================================
# HOVEDFUNKSJON
# =============================================================================

def main():
    print("🚀 Starter Microsoft Copilot UI Stress Test")
    print(f"📊 Konfigurasjon: {NUMBER_OF_MESSAGES} meldinger, {WAIT_TIME_SECONDS}s mellomrom")
    print("="*60)
    
    # Check if we're on Windows with proper dependencies
    if not WINDOWS_AVAILABLE:
        print("❌ pywinauto ikke tilgjengelig eller ikke på Windows")
        print("💡 Installer med: pip install pywinauto")
        print("💡 Denne scriptet må kjøres på Windows")
        sys.exit(1)
    
    # Track success/failure for exit code
    success_count = 0
    failed_first_element_lookup = False

    try:
        print("🔗 Kobler til Copilot-vindu (regex-match)...")
        
        # Window detection with explicit error handling
        try:
            app = Application(backend="uia").connect(title_re=WINDOW_TITLE_REGEX)
            window = app.window(title_re=WINDOW_TITLE_REGEX)
        except MatchError as e:
            print("❌ Kunne ikke finne Copilot-vinduet via regex")
            print(f"💡 Sjekk at Copilot kjører og at tittelen starter med 'Copilot'")
            print(f"🔍 MatchError detaljer: {e}")
            sys.exit(1)
        except ElementNotFoundError as e:
            print("❌ Copilot-vindu ikke funnet")
            print(f"🔍 ElementNotFoundError detaljer: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Uventet feil ved tilkobling til vindu: {type(e).__name__}: {e}")
            sys.exit(1)
        
        print("✅ Tilkobling til Copilot-vinduet vellykket")
        
        # Validate window is usable
        if not validate_window(window):
            print("❌ Vindu-validering feilet - avslutter")
            sys.exit(1)

        # Åpne ny samtale ved å trykke på "Ny samtale"-knappen hvis den finnes
        try:
            new_chat_button = window.child_window(title="Ny samtale", control_type="Button")
            if new_chat_button.exists() and new_chat_button.is_enabled():
                new_chat_button.click_input()
                print("🆕 Ny samtale startet")
                time.sleep(1)  # Gi UI tid til å oppdatere
            else:
                print("ℹ️ Ny samtale-knapp ikke tilgjengelig - fortsetter med eksisterende samtale")
        except ElementNotFoundError:
            print("ℹ️ Ny samtale-knapp ikke funnet – fortsetter med eksisterende samtale")
        except (TypeError, AttributeError, RuntimeError) as e:
            print(f"⚠️ Feil ved ny samtale-knapp: {type(e).__name__}: {e}")
            print("ℹ️ Fortsetter med eksisterende samtale")
        except Exception as e:
            print(f"⚠️ Uventet feil ved ny samtale: {type(e).__name__}: {e}")
            print("ℹ️ Fortsetter med eksisterende samtale")

        print("🔄 Starter meldingssløyfe...")

        for i in range(1, NUMBER_OF_MESSAGES + 1):
            try:
                print(f"📝 Sender melding {i} av {NUMBER_OF_MESSAGES}")
                message = random.choice(SAMPLE_MESSAGES)
                print(f"💬 Valgt melding: {message[:50]}{'...' if len(message) > 50 else ''}")

                # Finn tekstfelt med forbedret validering
                text_box = None
                try:
                    text_box = window.child_window(auto_id=TEXT_BOX_AUTO_ID)
                    if not text_box.exists():
                        raise ElementNotFoundError("Primary text box not found")
                    if not text_box.is_enabled():
                        print(f"❌ Primær tekstfelt finnes men er deaktivert for melding {i}")
                        raise ElementNotFoundError("Primary text box disabled")
                except ElementNotFoundError:
                    print("⚠️  Primær tekstfelt feilet, prøver fallback...")
                    try:
                        text_box = window.child_window(control_type=ALT_TEXT_BOX_CONTROL_TYPE)
                        if not text_box.exists():
                            raise ElementNotFoundError("Fallback text box not found")
                        if not text_box.is_enabled():
                            print(f"❌ Fallback tekstfelt finnes men er deaktivert for melding {i}")
                            raise ElementNotFoundError("Fallback text box disabled")
                    except ElementNotFoundError:
                        print(f"❌ Tekstfelt ikke tilgjengelig for melding {i}")
                        if i == 1 and not failed_first_element_lookup:
                            failed_first_element_lookup = True
                            print("📋 Første element-feil - dumper kontrolltre for feilsøking:")
                            try:
                                window.print_control_identifiers()
                            except Exception as tree_error:
                                print(f"⚠️ Kunne ikke dumpe kontrolltre: {tree_error}")
                                dump_control_tree_via_script()
                        continue

                # Type message into text box
                try:
                    text_box.click_input()
                    text_box.type_keys("^a{BACKSPACE}")
                    text_box.type_keys(message, with_spaces=True)
                    print("✏️  Melding skrevet inn")
                except (TypeError, AttributeError, RuntimeError) as e:
                    print(f"❌ Feil ved skriving til tekstfelt: {type(e).__name__}: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Uventet feil ved tekstinput: {type(e).__name__}: {e}")
                    continue

                # Finn sendeknapp med forbedret validering
                send_button = None
                try:
                    send_button = window.child_window(auto_id=SEND_BUTTON_AUTO_ID)
                    if not send_button.exists():
                        raise ElementNotFoundError("Primary send button not found")
                    if not send_button.is_enabled():
                        print(f"❌ Primær sendeknapp finnes men er deaktivert for melding {i}")
                        raise ElementNotFoundError("Primary send button disabled")
                except ElementNotFoundError:
                    print("⚠️  Primær sendeknapp feilet, prøver fallback...")
                    try:
                        send_button = window.child_window(title=ALT_SEND_BUTTON_NAME)
                        if not send_button.exists():
                            raise ElementNotFoundError("Fallback send button not found")
                        if not send_button.is_enabled():
                            print(f"❌ Fallback sendeknapp finnes men er deaktivert for melding {i}")
                            raise ElementNotFoundError("Fallback send button disabled")
                    except ElementNotFoundError:
                        print(f"❌ Sendeknapp ikke tilgjengelig for melding {i}")
                        if i == 1 and not failed_first_element_lookup:
                            failed_first_element_lookup = True
                            print("📋 Første element-feil - dumper kontrolltre for feilsøking:")
                            try:
                                window.print_control_identifiers()
                            except Exception as tree_error:
                                print(f"⚠️ Kunne ikke dumpe kontrolltre: {tree_error}")
                                dump_control_tree_via_script()
                        continue

                # Click send button
                try:
                    send_button.click_input()
                    print("🚀 Sendeknapp klikket")
                    success_count += 1
                except (TypeError, AttributeError, RuntimeError) as e:
                    print(f"❌ Feil ved klikking av sendeknapp: {type(e).__name__}: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Uventet feil ved sendeklikk: {type(e).__name__}: {e}")
                    continue

                # Wait between messages (except for last message)
                if i < NUMBER_OF_MESSAGES:
                    time.sleep(WAIT_TIME_SECONDS)

            except ElementNotFoundError as e:
                print(f"❌ Element ikke funnet ved melding {i}: {e}")
                continue
            except (TypeError, AttributeError, RuntimeError) as e:
                print(f"❌ Type/attribute/runtime feil ved melding {i}: {type(e).__name__}: {e}")
                continue
            except Exception as e:
                print(f"❌ Uventet feil ved melding {i}: {type(e).__name__}: {e}")
                continue

        print("="*60)
        print("🎉 Stresstest fullført!")
        print(f"📊 Totalt sendt: {success_count} av {NUMBER_OF_MESSAGES} meldinger")
        
        # Exit with appropriate code
        if success_count == 0:
            print("❌ Ingen meldinger ble sendt - avslutter med feilkode")
            sys.exit(1)
        elif success_count < NUMBER_OF_MESSAGES:
            print(f"⚠️ {NUMBER_OF_MESSAGES - success_count} meldinger feilet - delvis suksess")
            sys.exit(0)  # Still considered success if some messages sent
        else:
            print("✅ Alle meldinger sendt vellykket")
            sys.exit(0)

    except MatchError as e:
        print("❌ Kunne ikke finne Copilot-vinduet via regex")
        print(f"💡 Sjekk at Copilot kjører og at tittelen starter med 'Copilot'")
        print(f"🔍 MatchError detaljer: {e}")
        sys.exit(1)
    except ElementNotFoundError as e:
        print(f"❌ Element ikke funnet: {e}")
        sys.exit(1)
    except (TypeError, AttributeError, RuntimeError) as e:
        print(f"❌ {type(e).__name__} feil: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Stoppet av bruker")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Uventet feil: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()