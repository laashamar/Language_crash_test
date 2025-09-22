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
import json
import re

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

def extract_control_info(window):
    """
    Extracts structured control information from window for dynamic UI element discovery.
    Returns a list of dictionaries with control properties.
    """
    controls = []
    try:
        # Get all child controls recursively
        for control in window.descendants():
            try:
                control_info = {
                    'auto_id': getattr(control, 'automation_id', '') or '',
                    'title': getattr(control, 'window_text', '') or '',
                    'control_type': getattr(control, 'element_info', {}).get('control_type', '') or '',
                    'class_name': getattr(control, 'class_name', '') or '',
                    'is_enabled': getattr(control, 'is_enabled', lambda: False)(),
                    'is_visible': getattr(control, 'is_visible', lambda: False)(),
                }
                controls.append(control_info)
            except Exception:
                # Skip controls that can't be inspected
                continue
    except Exception as e:
        print(f"⚠️ Feil ved ekstrakt av kontroller: {e}")
    
    return controls

def find_likely_text_input_controls(controls):
    """
    Identify controls that are likely text input fields based on their properties.
    Returns prioritized list of candidates.
    """
    candidates = []
    
    # Known text input patterns
    text_input_patterns = [
        r'input.*text.*box',
        r'text.*input',
        r'message.*input',
        r'chat.*input',
        r'compose.*input',
        r'^text.*box$',
        r'^input.*$'
    ]
    
    text_control_types = ['Edit', 'Text', 'Document', 'Custom']
    
    for control in controls:
        if not control['is_enabled'] or not control['is_visible']:
            continue
            
        score = 0
        reasons = []
        
        # Check auto_id patterns
        auto_id = control['auto_id'].lower()
        for pattern in text_input_patterns:
            if re.search(pattern, auto_id, re.IGNORECASE):
                score += 10
                reasons.append(f"auto_id matches pattern: {pattern}")
                break
        
        # Check control type
        if control['control_type'] in text_control_types:
            score += 5
            reasons.append(f"control_type: {control['control_type']}")
        
        # Check title/window text
        title = control['title'].lower()
        if any(keyword in title for keyword in ['input', 'text', 'message', 'chat']):
            score += 3
            reasons.append(f"title contains text input keywords")
        
        # Known good patterns get extra points
        if 'inputtextbox' in auto_id:
            score += 15
            reasons.append("Known working auto_id pattern")
        
        if score > 0:
            candidates.append({
                'control': control,
                'score': score,
                'reasons': reasons
            })
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates

def find_likely_send_button_controls(controls):
    """
    Identify controls that are likely send buttons based on their properties.
    Returns prioritized list of candidates.
    """
    candidates = []
    
    # Known send button patterns
    send_button_patterns = [
        r'send.*button',
        r'submit.*button',
        r'compose.*button',
        r'mic.*button',
        r'chat.*send',
        r'^send$',
        r'^submit$'
    ]
    
    send_control_types = ['Button', 'Custom']
    
    for control in controls:
        if not control['is_enabled'] or not control['is_visible']:
            continue
            
        score = 0
        reasons = []
        
        # Check auto_id patterns
        auto_id = control['auto_id'].lower()
        for pattern in send_button_patterns:
            if re.search(pattern, auto_id, re.IGNORECASE):
                score += 10
                reasons.append(f"auto_id matches pattern: {pattern}")
                break
        
        # Check control type
        if control['control_type'] in send_control_types:
            score += 5
            reasons.append(f"control_type: {control['control_type']}")
        
        # Check title/window text for send-related terms
        title = control['title'].lower()
        send_keywords = ['send', 'submit', 'snakk', 'talk', 'mic', 'microphone']
        if any(keyword in title for keyword in send_keywords):
            score += 8
            reasons.append(f"title contains send keywords: {title}")
        
        # Known good patterns get extra points
        if 'oldcomposermicbutton' in auto_id:
            score += 15
            reasons.append("Known working auto_id pattern")
        
        if 'snakk med copilot' in title:
            score += 12
            reasons.append("Known working title pattern")
        
        if score > 0:
            candidates.append({
                'control': control,
                'score': score,
                'reasons': reasons
            })
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates

def find_likely_new_conversation_controls(controls):
    """
    Identify controls that are likely "New conversation" buttons.
    Returns prioritized list of candidates.
    """
    candidates = []
    
    new_conversation_patterns = [
        r'new.*conversation',
        r'ny.*samtale',
        r'new.*chat',
        r'start.*new',
        r'conversation.*new'
    ]
    
    for control in controls:
        if not control['is_enabled'] or not control['is_visible']:
            continue
            
        score = 0
        reasons = []
        
        # Check auto_id patterns
        auto_id = control['auto_id'].lower()
        for pattern in new_conversation_patterns:
            if re.search(pattern, auto_id, re.IGNORECASE):
                score += 10
                reasons.append(f"auto_id matches pattern: {pattern}")
                break
        
        # Must be a button or similar clickable control
        if control['control_type'] in ['Button', 'Custom', 'MenuItem']:
            score += 5
            reasons.append(f"control_type: {control['control_type']}")
        else:
            continue  # Skip non-clickable controls
        
        # Check title/window text
        title = control['title'].lower()
        if any(keyword in title for keyword in ['ny samtale', 'new conversation', 'new chat']):
            score += 12
            reasons.append(f"title matches conversation keywords: {title}")
        
        if score > 0:
            candidates.append({
                'control': control,
                'score': score,
                'reasons': reasons
            })
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates

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
        
        # First, print the traditional control tree for human reading
        try:
            window.print_control_identifiers()
        except Exception as e:
            print(f"⚠️ Kunne ikke vise tradisjonell kontrolltre: {e}")
        
        print("\n" + "="*80)
        print("🔍 DYNAMISK UI-ELEMENT ANALYSE")
        print("="*80)
        
        # Extract structured control information
        controls = extract_control_info(window)
        print(f"📊 Totalt {len(controls)} kontroller funnet\n")
        
        # Find text input candidates
        text_candidates = find_likely_text_input_controls(controls)
        print("📝 TEKSTINPUT KANDIDATER (prioritert):")
        if text_candidates:
            for i, candidate in enumerate(text_candidates[:5], 1):  # Show top 5
                control = candidate['control']
                print(f"  {i}. Score: {candidate['score']}")
                print(f"     auto_id: '{control['auto_id']}'")
                print(f"     title: '{control['title']}'")
                print(f"     control_type: '{control['control_type']}'")
                print(f"     reasons: {', '.join(candidate['reasons'])}")
                print()
        else:
            print("  ❌ Ingen tekstinput kandidater funnet")
        
        # Find send button candidates
        send_candidates = find_likely_send_button_controls(controls)
        print("🚀 SENDEKNAPP KANDIDATER (prioritert):")
        if send_candidates:
            for i, candidate in enumerate(send_candidates[:5], 1):  # Show top 5
                control = candidate['control']
                print(f"  {i}. Score: {candidate['score']}")
                print(f"     auto_id: '{control['auto_id']}'")
                print(f"     title: '{control['title']}'")
                print(f"     control_type: '{control['control_type']}'")
                print(f"     reasons: {', '.join(candidate['reasons'])}")
                print()
        else:
            print("  ❌ Ingen sendeknapp kandidater funnet")
        
        # Find new conversation button candidates
        new_conv_candidates = find_likely_new_conversation_controls(controls)
        print("🆕 NY SAMTALE KNAPP KANDIDATER (prioritert):")
        if new_conv_candidates:
            for i, candidate in enumerate(new_conv_candidates[:5], 1):  # Show top 5
                control = candidate['control']
                print(f"  {i}. Score: {candidate['score']}")
                print(f"     auto_id: '{control['auto_id']}'")
                print(f"     title: '{control['title']}'")
                print(f"     control_type: '{control['control_type']}'")
                print(f"     reasons: {', '.join(candidate['reasons'])}")
                print()
        else:
            print("  ❌ Ingen ny samtale knapp kandidater funnet")
        
        # Output structured data for script consumption (JSON format)
        print("\n" + "="*80)
        print("📋 STRUKTURERT DATA FOR SCRIPT-PARSING:")
        print("="*80)
        
        structured_data = {
            'text_input_candidates': [
                {
                    'auto_id': c['control']['auto_id'],
                    'title': c['control']['title'],
                    'control_type': c['control']['control_type'],
                    'score': c['score'],
                    'reasons': c['reasons']
                }
                for c in text_candidates[:10]  # Top 10 for script processing
            ],
            'send_button_candidates': [
                {
                    'auto_id': c['control']['auto_id'],
                    'title': c['control']['title'],
                    'control_type': c['control']['control_type'],
                    'score': c['score'],
                    'reasons': c['reasons']
                }
                for c in send_candidates[:10]
            ],
            'new_conversation_candidates': [
                {
                    'auto_id': c['control']['auto_id'],
                    'title': c['control']['title'],
                    'control_type': c['control']['control_type'],
                    'score': c['score'],
                    'reasons': c['reasons']
                }
                for c in new_conv_candidates[:10]
            ]
        }
        
        print("JSON_DATA_START")
        print(json.dumps(structured_data, indent=2, ensure_ascii=False))
        print("JSON_DATA_END")
        
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