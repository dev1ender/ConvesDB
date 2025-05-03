#!/usr/bin/env python3
"""
Utility script to test and verify embedding model initialization.

This script attempts to initialize various embedding models and providers
to verify they're working correctly.
"""

import logging
import argparse
import numpy as np
from time import time

from app.llm.factory import LLMFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("test_embeddings")

def test_embedding_provider(provider, model=None):
    """
    Test an embedding provider with sample text.
    
    Args:
        provider: Provider name
        model: Optional model name
    
    Returns:
        bool: True if successful, False otherwise
    """
    factory = LLMFactory()
    
    try:
        logger.info(f"Testing embedding provider: {provider}" + (f" with model: {model}" if model else ""))
        start_time = time()
        
        # Initialize the embedding client
        client = factory.get_embedding_client(provider, model_name=model)
        init_time = time() - start_time
        logger.info(f"✅ Client initialization successful ({init_time:.2f}s)")
        
        # Test single embedding
        test_text = "This is a test sentence to verify the embedding model works correctly."
        start_time = time()
        embedding = client.embed_text(test_text)
        embed_time = time() - start_time
        
        if not embedding or len(embedding) == 0:
            logger.error("❌ Generated embedding is empty")
            return False
        
        logger.info(f"✅ Successfully generated embedding with {len(embedding)} dimensions ({embed_time:.2f}s)")
        logger.info(f"   Vector norm: {np.linalg.norm(embedding):.4f}")
        
        # Test batch embedding
        test_texts = [
            "This is the first test sentence.",
            "Here is another completely different sentence.",
            "A third example with some unique words and concepts."
        ]
        
        start_time = time()
        embeddings = client.embed_texts(test_texts)
        batch_time = time() - start_time
        
        if not embeddings or len(embeddings) != len(test_texts):
            logger.error(f"❌ Expected {len(test_texts)} embeddings, got {len(embeddings) if embeddings else 0}")
            return False
        
        logger.info(f"✅ Successfully generated {len(embeddings)} embeddings in batch ({batch_time:.2f}s)")
        
        # Calculate similarity between embeddings to verify they make sense
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])
        sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])
        sim_2_3 = cosine_similarity(embeddings[1], embeddings[2])
        
        logger.info(f"Similarity checks:")
        logger.info(f"   1-2: {sim_1_2:.4f}, 1-3: {sim_1_3:.4f}, 2-3: {sim_2_3:.4f}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error testing embedding provider: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test embedding model initialization and usage")
    parser.add_argument("--provider", type=str, default="local_huggingface", 
                        help="Embedding provider to test (default: local_huggingface)")
    parser.add_argument("--model", type=str, default=None,
                        help="Model name to use (default: provider's default model)")
    
    args = parser.parse_args()
    
    print("\n===== EMBEDDING MODEL TEST =====\n")
    success = test_embedding_provider(args.provider, args.model)
    
    if success:
        print("\n✅ Embedding test completed successfully\n")
    else:
        print("\n❌ Embedding test failed\n")

if __name__ == "__main__":
    main() 