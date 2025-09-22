#!/usr/bin/env python3
"""
Test suite for Language Crash Test generator functionality.

Validates message generation and content quality.
"""

import unittest
import sys
import os

# Import from the new package structure
from language_crash_test.generator import generate_single_message, generate_messages


class TestGenerator(unittest.TestCase):
    """Test cases for message generator."""
    
    def test_generate_single_message(self):
        """Test generation of a single message."""
        message = generate_single_message()
        
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 10)  # Should be substantial
        
        # Check for emoji presence
        emojis = ["🤖", "🌍", "✨", "🧠", "🚀", "💬", "📝", "🎯", "🔍", "📚", "😅", "🙃", "🧩", "⚙️", "📡"]
        has_emoji = any(emoji in message for emoji in emojis)
        self.assertTrue(has_emoji, f"Message should contain emoji: {message}")
        
        # Check for special characters
        specials = ["—", "…", "✓", "→", "©", "™", "§", "¤"]
        has_special = any(special in message for special in specials)
        self.assertTrue(has_special, f"Message should contain special character: {message}")
    
    def test_generate_multiple_messages(self):
        """Test generation of multiple messages."""
        count = 10
        messages = generate_messages(count)
        
        self.assertIsInstance(messages, list)
        self.assertEqual(len(messages), count)
        
        # Check that all are strings
        for message in messages:
            self.assertIsInstance(message, str)
            self.assertGreater(len(message), 10)
        
        # Check for diversity (shouldn't be all identical)
        unique_messages = set(messages)
        self.assertGreater(len(unique_messages), 1, "Messages should be diverse")
    
    def test_bilingual_content(self):
        """Test that messages contain both Norwegian and English content."""
        messages = generate_messages(50)  # Generate enough for statistical significance
        
        norwegian_indicators = ["språklige", "agentens", "feilhåndtering", "oversettelser", "deterministiske"]
        english_indicators = ["linguistic", "agent's", "error", "translation", "deterministic"]
        
        has_norwegian = any(
            any(indicator in message for indicator in norwegian_indicators)
            for message in messages
        )
        
        has_english = any(
            any(indicator in message for indicator in english_indicators)
            for message in messages
        )
        
        self.assertTrue(has_norwegian, "Should generate Norwegian messages")
        self.assertTrue(has_english, "Should generate English messages")
    
    def test_special_characters_norwegian(self):
        """Test that Norwegian messages contain special characters æ, ø, å."""
        messages = generate_messages(100)  # Generate enough for statistical significance
        
        norwegian_chars = ['æ', 'ø', 'å']
        found_chars = set()
        
        for message in messages:
            for char in norwegian_chars:
                if char in message:
                    found_chars.add(char)
        
        # Should find at least some Norwegian special characters
        self.assertGreater(len(found_chars), 0, "Should contain Norwegian special characters")
    
    def test_message_length(self):
        """Test that messages are reasonable length."""
        messages = generate_messages(20)
        
        for message in messages:
            # Messages should be substantial but not too long
            self.assertGreaterEqual(len(message), 50, f"Message too short: {message}")
            self.assertLessEqual(len(message), 500, f"Message too long: {message}")
    
    def test_no_empty_messages(self):
        """Test that no empty messages are generated."""
        messages = generate_messages(20)
        
        for message in messages:
            self.assertNotEqual(message.strip(), "", "Should not generate empty messages")


if __name__ == '__main__':
    unittest.main()