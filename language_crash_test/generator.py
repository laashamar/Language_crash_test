#!/usr/bin/env python3
"""
Bilingual Message Generator for Language Crash Test

Generates a mix of English and Norwegian test messages with special characters
(æ, ø, å) and emojis for comprehensive UI stress testing.

Features:
- Bilingual content (English/Norwegian)
- Norwegian special characters (æ, ø, å)
- Emojis and special symbols
- Varied message length and complexity
- Different conversational tones
"""

import random

EMOJIS = ["🤖", "🌍", "✨", "🧠", "🚀", "💬", "📝", "🎯", "🔍", "📚", "😅", "🙃", "🧩", "⚙️", "📡"]
SPECIALS = ["—", "…", "✓", "→", "©", "™", "§", "¤"]

PERSONALITIES = ["filosofisk", "teknisk", "humoristisk", "pedagogisk", "refleksiv"]

def random_intro(lang, tone):
    """Generate random introduction based on language and tone."""
    if lang == "norsk":
        return {
            "filosofisk": "Noen ganger undrer jeg meg over",
            "teknisk": "Systemet viser tydelig at",
            "humoristisk": "Ærlig talt, det er nesten komisk hvordan",
            "pedagogisk": "La oss se nærmere på hvordan",
            "refleksiv": "Jeg har ofte tenkt på hvordan"
        }[tone]
    else:
        return {
            "filosofisk": "Sometimes I wonder about",
            "teknisk": "The system clearly demonstrates that",
            "humoristisk": "Honestly, it's almost funny how",
            "pedagogisk": "Let's take a closer look at how",
            "refleksiv": "I've often thought about how"
        }[tone]

def random_statement(lang, tone):
    """Generate random statement based on language and tone."""
    if lang == "norsk":
        return random.choice([
            "språklige nyanser kan endre hele meningen med en interaksjon",
            "agentens respons avhenger av kontekst og intensjon",
            "feilhåndtering bør være like elegant som hovedflyten",
            "oversettelser krever mer enn bare ord—de krever forståelse",
            "det deterministiske oppsettet gir trygghet for alle parter"
        ])
    else:
        return random.choice([
            "linguistic nuance can shift the entire meaning of an interaction",
            "the agent's response depends on context and intent",
            "error handling should be as elegant as the main flow",
            "translation requires more than words—it demands understanding",
            "a deterministic setup gives confidence to all participants"
        ])

def random_closure(lang, tone):
    """Generate random closure based on language and tone."""
    if lang == "norsk":
        return random.choice([
            "og det er nettopp derfor vi må tenke helhetlig.",
            "slik at systemet kan tilpasses virkelige behov.",
            "og det gjør hele forskjellen i praksis.",
            "som gir rom for både kontroll og fleksibilitet.",
            "og da får vi en mye bedre brukeropplevelse."
        ])
    else:
        return random.choice([
            "and that's exactly why we need to think holistically.",
            "so the system can adapt to real-world needs.",
            "and that makes all the difference in practice.",
            "which allows for both control and flexibility.",
            "and then we get a much better user experience."
        ])

def simple_message(lang):
    """Generate a simple message in the specified language."""
    if lang == "norsk":
        return random.choice([
            "Hei! Hvordan har du det i dag? Jeg håper alt er bra med deg og dine",
            "Takk for hjelpen! Det setter jeg pris på og det hjelper meg mye",
            "Kan du hjelpe meg med å forstå dette bedre? Jeg trenger mer informasjon",
            "Det høres interessant ut! Fortell mer om dette emnet og dine tanker",
            "Jeg ønsker å lære noe nytt om dette emnet som interesserer meg veldig",
            "Tusen takk for svaret! Det var veldig nyttig og informativt for meg",
            "Hva synes du om denne tilnærmingen? Jeg er nysgjerrig på ditt perspektiv",
            "Kan du forklare dette på en enklere måte? Jeg sliter med å forstå det",
            "Dette er akkurat det jeg trengte å vite! Takk for den gode forklaringen",
            "Har du noen tips om hvordan jeg kan forbedre dette? Jeg vil gjerne lære mer"
        ])
    else:
        return random.choice([
            "Hi! How are you doing today? I hope everything is going well for you",
            "Thanks for the help! I really appreciate it and it makes a big difference",
            "Can you help me understand this better? I need more detailed information",
            "That sounds interesting! Tell me more about this topic and your thoughts",
            "I'd like to learn something new about this topic that really interests me",
            "Thank you so much for the answer! That was very helpful and informative",
            "What do you think about this approach? I'm curious about your perspective",
            "Can you explain this in a simpler way? I'm having trouble understanding it",
            "This is exactly what I needed to know! Thanks for the great explanation",
            "Do you have any tips on how I can improve this? I'd love to learn more"
        ])

def complex_message(lang, tone):
    """Generate a complex message with multiple parts."""
    intro = random_intro(lang, tone)
    statement = random_statement(lang, tone)
    closure = random_closure(lang, tone)
    
    emoji = random.choice(EMOJIS)
    special = random.choice(SPECIALS)
    
    return f"{intro} {statement}, {closure} {emoji}{special}"

def generate_single_message(language_choice: str = "both"):
    """
    Generate a single test message based on the language choice.
    
    Args:
        language_choice: 'english', 'norwegian', or 'both'
    """
    # Bestem språket for denne spesifikke meldingen
    if language_choice == "english":
        lang = "english"
    elif language_choice == "norwegian":
        lang = "norsk"
    else:  # 'both'
        lang = random.choice(["norsk", "english"])

    # 60% chance for simple message, 40% for complex
    if random.random() < 0.6:
        message = simple_message(lang)
        # Always add an emoji and special character for consistency
        emoji = random.choice(EMOJIS)
        special = random.choice(SPECIALS)
        return f"{message} {emoji}{special}"
    else:
        tone = random.choice(PERSONALITIES)
        return complex_message(lang, tone)

def generate_messages(count: int, language_choice: str = "both") -> list[str]:
    """
    Generate a list of test messages based on the specified language choice.
    
    Args:
        count: Number of messages to generate
        language_choice: The desired language ('english', 'norwegian', 'both')
        
    Returns:
        List of generated messages
    """
    if count <= 0:
        return []
    
    messages = []
    for _ in range(count):
        message = generate_single_message(language_choice)
        messages.append(message)
    
    return messages

def validate_message_content(messages):
    """
    Validate that the generated messages meet requirements.
    
    Args:
        messages: List of messages to validate
        
    Returns:
        Dict with validation results
    """
    results = {
        'total_messages': len(messages),
        'norwegian_chars': 0,
        'english_messages': 0,
        'norwegian_messages': 0,
        'emoji_messages': 0,
        'empty_messages': 0,
        'special_char_messages': 0
    }
    
    norwegian_chars = {'æ', 'ø', 'å', 'Æ', 'Ø', 'Å'}
    
    for message in messages:
        if not message.strip():
            results['empty_messages'] += 1
            continue
            
        # Check for Norwegian characters
        if any(char in message for char in norwegian_chars):
            results['norwegian_chars'] += 1
            results['norwegian_messages'] += 1
        else:
            results['english_messages'] += 1
            
        # Check for emojis
        if any(emoji in message for emoji in EMOJIS):
            results['emoji_messages'] += 1
            
        # Check for special characters
        if any(char in message for char in SPECIALS):
            results['special_char_messages'] += 1
    
    return results

if __name__ == "__main__":
    # Demo the message generator
    print("🧪 Testing Bilingual Message Generator")
    print("=" * 50)
    
    # Generate test messages
    test_count = 10
    messages = generate_messages(test_count, "both")
    
    print(f"Generated {len(messages)} messages:")
    print("-" * 30)
    
    for i, message in enumerate(messages, 1):
        print(f"{i:2}. {message}")
    
    print("\n📊 Validation Results:")
    print("-" * 30)
    
    validation = validate_message_content(messages)
    for key, value in validation.items():
        print(f"{key}: {value}")
    
    # Test specific requirements
    print("\n✅ Requirements Check:")
    print("-" * 30)
    
    has_norwegian = validation['norwegian_messages'] > 0
    has_english = validation['english_messages'] > 0
    has_norwegian_chars = validation['norwegian_chars'] > 0
    has_emojis = validation['emoji_messages'] > 0
    no_empty = validation['empty_messages'] == 0
    
    print(f"Norwegian messages: {'✅' if has_norwegian else '❌'}")
    print(f"English messages: {'✅' if has_english else '❌'}")
    print(f"Norwegian chars (æ,ø,å): {'✅' if has_norwegian_chars else '❌'}")
    print(f"Emojis present: {'✅' if has_emojis else '❌'}")
    print(f"No empty messages: {'✅' if no_empty else '❌'}")
    
    if all([has_norwegian, has_english, has_norwegian_chars, has_emojis, no_empty]):
        print("\n🎉 All requirements met!")
    else:
        print("\n⚠️ Some requirements not met - try generating more messages")

