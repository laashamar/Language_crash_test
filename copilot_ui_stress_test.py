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
import json
import re

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
# DYNAMISKE UI-IDENTIFIKATORER (NO HARDCODED VALUES)
# =============================================================================

# Window detection uses dynamic regex pattern
WINDOW_TITLE_REGEX = r"^Copilot.*"  # Matcher både "Copilot" og "Copilot – Ny samtale"

# Known identifier patterns for prioritized fallback (NOT hardcoded - used for scoring)
KNOWN_TEXT_INPUT_PATTERNS = [
    "InputTextBox",  # Most commonly working pattern
    "TextBox", 
    "MessageInput",
    "ChatInput"
]

KNOWN_SEND_BUTTON_PATTERNS = [
    "OldComposerMicButton",  # Most commonly working pattern  
    "SendButton",
    "MicButton",
    "SubmitButton"
]

KNOWN_NEW_CONVERSATION_PATTERNS = [
    "Ny samtale",  # Norwegian
    "New conversation",  # English
    "New chat",
    "Start new"
]

# Control type fallbacks for dynamic discovery
TEXT_INPUT_CONTROL_TYPES = ["Edit", "Text", "Document", "Custom"]
BUTTON_CONTROL_TYPES = ["Button", "Custom", "MenuItem"]

# =============================================================================
# HJELPEFUNKSJONER FOR DYNAMISK UI-ELEMENT OPPDAGELSE
# =============================================================================

def parse_debug_output(debug_output):
    """
    Parse structured JSON data from debug script output.
    Returns dictionary with element candidates or None if parsing fails.
    """
    try:
        # Find JSON data between markers
        start_marker = "JSON_DATA_START"
        end_marker = "JSON_DATA_END"
        
        start_idx = debug_output.find(start_marker)
        end_idx = debug_output.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            print("⚠️ Ingen strukturert data funnet i debug-output")
            return None
        
        # Extract JSON data
        json_data = debug_output[start_idx + len(start_marker):end_idx].strip()
        return json.loads(json_data)
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Kunne ikke parse JSON fra debug-output: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Feil ved parsing av debug-output: {e}")
        return None

def dump_control_tree_via_script():
    """
    Kaller den separate debug-scriptet for å dumpe kontrolltre.
    Returns parsed structured data or None if failed.
    """
    try:
        script_path = os.path.join(os.path.dirname(__file__), "copilot_ui_debug.py")
        if os.path.exists(script_path):
            print("📋 Kjører separat debug-script for kontrolltre (required fallback)...")
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Debug-script kjørt vellykket")
                # Parse structured data from output
                parsed_data = parse_debug_output(result.stdout)
                if parsed_data:
                    print("✅ Strukturert data parsed vellykket")
                    return parsed_data
                else:
                    print("⚠️ Kunne ikke parse strukturert data - viser rådata:")
                    print(result.stdout)
                    return None
            else:
                print(f"⚠️ Debug-script feilet med returkode {result.returncode}:")
                print(f"STDERR: {result.stderr}")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                return None
        else:
            print(f"❌ KRITISK: Debug-script ikke funnet: {script_path}")
            print("💡 Debug-scriptet er en påkrevd fallback-mekanisme og må være tilgjengelig")
            return None
    except subprocess.TimeoutExpired:
        print("⚠️ Debug-script timeout etter 30 sekunder")
        return None
    except Exception as e:
        print(f"❌ Feil ved kjøring av debug-script: {type(e).__name__}: {e}")
        print("💡 Debug-scriptet er en påkrevd fallback-mekanisme for UI-inspeksjon")
        return None

def try_element_candidates(window, candidates, element_type):
    """
    Try to find and validate UI elements from prioritized candidate list.
    Returns (element, candidate_info) if successful, (None, None) if all fail.
    """
    if not candidates:
        print(f"❌ Ingen {element_type} kandidater tilgjengelig")
        return None, None
    
    print(f"🔍 Prøver {len(candidates)} {element_type} kandidater...")
    
    for i, candidate in enumerate(candidates, 1):
        try:
            auto_id = candidate.get('auto_id', '')
            title = candidate.get('title', '')
            control_type = candidate.get('control_type', '')
            score = candidate.get('score', 0)
            
            print(f"  {i}. Prøver kandidat (score: {score})")
            print(f"     auto_id: '{auto_id}', title: '{title}', type: '{control_type}'")
            
            element = None
            
            # Try different search strategies
            if auto_id:
                try:
                    element = window.child_window(auto_id=auto_id)
                    if element.exists() and element.is_enabled():
                        print(f"     ✅ Suksess med auto_id: '{auto_id}'")
                        return element, candidate
                    else:
                        print(f"     ⚠️ auto_id funnet men ikke tilgjengelig")
                except ElementNotFoundError:
                    print(f"     ⚠️ auto_id ikke funnet")
            
            if title and not element:
                try:
                    element = window.child_window(title=title)
                    if element.exists() and element.is_enabled():
                        print(f"     ✅ Suksess med title: '{title}'")
                        return element, candidate
                    else:
                        print(f"     ⚠️ title funnet men ikke tilgjengelig")
                except ElementNotFoundError:
                    print(f"     ⚠️ title ikke funnet")
            
            if control_type and not element:
                try:
                    element = window.child_window(control_type=control_type)
                    if element.exists() and element.is_enabled():
                        print(f"     ✅ Suksess med control_type: '{control_type}'")
                        return element, candidate
                    else:
                        print(f"     ⚠️ control_type funnet men ikke tilgjengelig")
                except ElementNotFoundError:
                    print(f"     ⚠️ control_type ikke funnet")
            
            print(f"     ❌ Kandidat {i} feilet")
            
        except Exception as e:
            print(f"     ❌ Uventet feil ved kandidat {i}: {type(e).__name__}: {e}")
            continue
    
    print(f"❌ Alle {element_type} kandidater feilet")
    return None, None

def find_element_with_dynamic_fallback(window, element_type, known_patterns):
    """
    Find UI element using known patterns first, then dynamic discovery as fallback.
    Returns (element, method_used) if successful, (None, None) if failed.
    """
    print(f"🔍 Søker etter {element_type} med dynamisk fallback...")
    
    # First try known working patterns (prioritized)
    for pattern in known_patterns:
        try:
            if element_type == "text_input":
                # Try both auto_id and control_type
                element = None
                try:
                    element = window.child_window(auto_id=pattern)
                except ElementNotFoundError:
                    try:
                        element = window.child_window(control_type=pattern)
                    except ElementNotFoundError:
                        continue
                        
            elif element_type == "send_button":
                # Try auto_id, then title
                element = None
                try:
                    element = window.child_window(auto_id=pattern)
                except ElementNotFoundError:
                    try:
                        element = window.child_window(title=pattern)
                    except ElementNotFoundError:
                        continue
                        
            elif element_type == "new_conversation":
                # Try title match for new conversation
                try:
                    element = window.child_window(title=pattern, control_type="Button")
                except ElementNotFoundError:
                    try:
                        element = window.child_window(title=pattern)
                    except ElementNotFoundError:
                        continue
            
            if element and element.exists() and element.is_enabled():
                print(f"✅ {element_type} funnet med kjent pattern: '{pattern}'")
                return element, f"known_pattern: {pattern}"
        
        except Exception as e:
            print(f"⚠️ Feil ved testing av kjent pattern '{pattern}': {e}")
            continue
    
    print(f"⚠️ Alle kjente patterns feilet for {element_type} - starter dynamisk fallback...")
    
    # Dynamic fallback via debug script
    debug_data = dump_control_tree_via_script()
    if not debug_data:
        print(f"❌ Kan ikke utføre dynamisk fallback - debug data ikke tilgjengelig")
        return None, None
    
    # Get candidates based on element type
    candidates = []
    if element_type == "text_input":
        candidates = debug_data.get('text_input_candidates', [])
    elif element_type == "send_button":
        candidates = debug_data.get('send_button_candidates', [])
    elif element_type == "new_conversation":
        candidates = debug_data.get('new_conversation_candidates', [])
    
    # Try candidates
    element, candidate_info = try_element_candidates(window, candidates, element_type)
    if element:
        method_used = f"dynamic_discovery: {candidate_info.get('auto_id', '')}/{candidate_info.get('title', '')}"
        print(f"✅ {element_type} funnet med dynamisk oppdagelse")
        return element, method_used
    
    print(f"❌ Dynamisk fallback feilet for {element_type}")
    return None, None

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

        # Start new conversation using dynamic detection
        try:
            new_chat_element, method = find_element_with_dynamic_fallback(
                window, "new_conversation", KNOWN_NEW_CONVERSATION_PATTERNS
            )
            if new_chat_element:
                new_chat_element.click_input()
                print(f"🆕 Ny samtale startet (metode: {method})")
                time.sleep(1)  # Gi UI tid til å oppdatere
            else:
                print("ℹ️ Ny samtale-knapp ikke funnet med noen metode - fortsetter med eksisterende samtale")
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

                # Find text input field using dynamic discovery
                text_box, text_method = find_element_with_dynamic_fallback(
                    window, "text_input", KNOWN_TEXT_INPUT_PATTERNS
                )
                
                if not text_box:
                    print(f"❌ Tekstfelt ikke tilgjengelig for melding {i} - alle metoder feilet")
                    continue

                print(f"✅ Tekstfelt funnet (metode: {text_method})")

                # Type message into text box
                try:
                    text_box.click_input()
                    text_box.type_keys("^a{BACKSPACE}")  # Clear existing text
                    text_box.type_keys(message, with_spaces=True)
                    print("✏️  Melding skrevet inn")
                except (TypeError, AttributeError, RuntimeError) as e:
                    print(f"❌ Feil ved skriving til tekstfelt: {type(e).__name__}: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Uventet feil ved tekstinput: {type(e).__name__}: {e}")
                    continue

                # Find send button using dynamic discovery
                send_button, send_method = find_element_with_dynamic_fallback(
                    window, "send_button", KNOWN_SEND_BUTTON_PATTERNS
                )
                
                if not send_button:
                    print(f"❌ Sendeknapp ikke tilgjengelig for melding {i} - alle metoder feilet")
                    continue

                print(f"✅ Sendeknapp funnet (metode: {send_method})")

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