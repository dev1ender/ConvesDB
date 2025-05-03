"""
Tests for the config module.
"""

import unittest
import os
import tempfile
from app.config.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.config_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")
        self.config_file.write(b"""
database:
  type: sqlite
  path: test.sqlite
  seed_on_startup: true

llm:
  provider: ollama
  ollama:
    model: llama3:3b
    temperature: 0.0
    host: http://localhost:11434
  openai:
    model: gpt-3.5-turbo
    temperature: 0.1
    max_tokens: 500
        """)
        self.config_file.close()
        
        # Set environment variable for testing
        os.environ["TEST_ENV_VAR"] = "test_value"
        
        # Create config manager
        self.config_manager = ConfigManager(self.config_file.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.unlink(self.config_file.name)
        
    def test_get(self):
        """Test getting configuration values."""
        # Test getting a value
        self.assertEqual(self.config_manager.get("database.type"), "sqlite")
        
        # Test getting a nested value
        self.assertEqual(self.config_manager.get("llm.ollama.model"), "llama3:3b")
        
        # Test getting a non-existent value
        self.assertIsNone(self.config_manager.get("non.existent.key"))
        
        # Test getting a non-existent value with default
        self.assertEqual(self.config_manager.get("non.existent.key", "default"), "default")
    
    def test_get_database_config(self):
        """Test getting database configuration."""
        db_config = self.config_manager.get_database_config()
        self.assertEqual(db_config["type"], "sqlite")
        self.assertEqual(db_config["path"], "test.sqlite")
        self.assertTrue(db_config["seed_on_startup"])
    
    def test_get_llm_provider(self):
        """Test getting LLM provider."""
        self.assertEqual(self.config_manager.get_llm_provider(), "ollama")
    
    def test_is_using_openai(self):
        """Test checking if using OpenAI."""
        self.assertFalse(self.config_manager.is_using_openai())


if __name__ == "__main__":
    unittest.main() 