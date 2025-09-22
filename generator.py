import random

EMOJIS = ["🤖", "🌍", "✨", "🧠", "🚀", "💬", "📝", "🎯", "🔍", "📚", "😅", "🙃", "🧩", "⚙️", "📡"]
SPECIALS = ["—", "…", "✓", "→", "©", "™", "§", "¤"]

PERSONALITIES = ["filosofisk", "teknisk", "humoristisk", "pedagogisk", "refleksiv"]

def random_intro(lang, tone):
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
            "pedagogisk": "Let’s take a closer look at how",
            "refleksiv": "I’ve often thought about how"
        }[tone]

def random_statement(lang, tone):
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
            "the agent’s response depends on context and intent",
            "error handling should be as elegant as the main flow",
            "translation requires more than words—it demands understanding",
            "a deterministic setup gives confidence to all participants"
        ])

def random_closure(lang, tone):
    if lang == "norsk":
        return random.choice([
            "og det er nettopp derfor vi må tenke helhetlig.",
            "slik at systemet kan tilpasses virkelige behov.",
            "og det gjør hele forskjellen i praksis.",
            "som gir rom for både kontroll og fleksibilitet.",
            "og det er her intelligens møter design."
        ])
    else:
        return random.choice([
            "and that’s exactly why holistic thinking matters.",
            "so the system can adapt to real-world needs.",
            "and that makes all the difference in practice.",
            "which allows for both control and flexibility.",
            "and that’s where intelligence meets design."
        ])

def generate_message():
    lang = random.choice(["norsk", "english"])
    tone = random.choice(PERSONALITIES)
    emoji = random.choice(EMOJIS)
    special = random.choice(SPECIALS)

    intro = random_intro(lang, tone)
    statement = random_statement(lang, tone)
    closure = random_closure(lang, tone)

    return f"{emoji} {intro} {statement} {closure} {special}"

def generate_messages(n=50):
    return [generate_message() for _ in range(n)]

if __name__ == "__main__":
    for i, msg in enumerate(generate_messages(), start=1):
        print(f"{i:02d}: {msg}")