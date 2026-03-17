import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.abspath('backend'))

# Mock base and models before importing
with patch('db.base.Base', MagicMock()):
    with patch('db.base.AsyncSessionLocal', MagicMock()):
        from db.models.knowledge_base import KnowledgeEntry
        from db.models.product import Product
        from kb.loader import KBLoader

async def test_loader_sync_logic():
    loader = KBLoader()
    
    # Mock product
    mock_product = MagicMock(spec=Product)
    mock_product.id = 123
    mock_product.organisation_id = 1
    mock_product.company_id = 2
    mock_product.brand_id = 3
    mock_product.name = "Test Product"
    mock_product.category = "pesticide"
    mock_product.description = "Test Description"
    mock_product.target_crops = "Rice"
    mock_product.target_problems = "Stem Borer"
    mock_product.dosage = "1ml/L"
    mock_product.usage_instructions = "Spray"
    mock_product.is_active = True
    
    # Mock embedding
    mock_embedding = [0.1] * 1536
    
    with patch('kb.loader.fetch_embedding', AsyncMock(return_value=mock_embedding)) as mock_fetch:
        with patch('kb.loader.AsyncSessionLocal') as mock_session_factory:
            mock_db = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_db
            
            # Mock existing entry not found
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            await loader.load_product_to_vector_db(mock_product)
            
            # Verify fetch_embedding called
            mock_fetch.assert_called_once()
            
            # Verify db.add called with KnowledgeEntry
            args, kwargs = mock_db.add.call_args
            entry = args[0]
            assert isinstance(entry, KnowledgeEntry)
            assert entry.metadata_['category'] == "pesticide"
            assert entry.metadata_['brand_id'] == 3
            assert entry.language == 'hi'
            
            print("Verification successful: load_product_to_vector_db correctly populates new fields.")

if __name__ == "__main__":
    asyncio.run(test_loader_sync_logic())
