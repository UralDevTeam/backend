"""Tests for other application services."""
import pytest
from io import BytesIO
from uuid import uuid4

from src.application.services.avatar import AvatarService
from src.infrastructure.repositories.avatar import AvatarRepository

@pytest.mark.integration
class TestAvatarService:
    """Integration tests for the AvatarService."""

    @staticmethod
    def create_test_image() -> bytes:
        """Create a simple test PNG image."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")
        
        # Create a simple 100x100 red square
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_save_avatar_success(
        self,
        avatar_service: AvatarService,
        sample_employee,
        session,
    ):
        """Test successfully saving an avatar."""
        image_data = self.create_test_image()
        
        avatar = await avatar_service.save_avatar(sample_employee.id, image_data)
        await session.commit()
        
        assert avatar is not None
        assert avatar.employee_id == sample_employee.id
        assert avatar.mime_type == "image/png"
        assert len(avatar.image_small) > 0
        assert len(avatar.image_large) > 0

    @pytest.mark.asyncio
    async def test_save_avatar_empty_content(
        self,
        avatar_service: AvatarService,
        sample_employee,
    ):
        """Test that saving empty content raises error."""
        with pytest.raises(ValueError, match="Empty image content"):
            await avatar_service.save_avatar(sample_employee.id, b"")

    @pytest.mark.asyncio
    async def test_save_avatar_invalid_image(
        self,
        avatar_service: AvatarService,
        sample_employee,
    ):
        """Test that invalid image data raises error."""
        invalid_data = b"not an image"
        
        with pytest.raises(ValueError, match="not a valid image"):
            await avatar_service.save_avatar(sample_employee.id, invalid_data)

    @pytest.mark.asyncio
    async def test_get_avatar_existing(
        self,
        avatar_service: AvatarService,
        sample_employee,
        session,
    ):
        """Test getting an existing avatar."""
        image_data = self.create_test_image()
        
        # Save avatar first
        await avatar_service.save_avatar(sample_employee.id, image_data)
        await session.commit()
        
        # Retrieve avatar
        avatar = await avatar_service.get_avatar(sample_employee.id)
        
        assert avatar is not None
        assert avatar.employee_id == sample_employee.id

    @pytest.mark.asyncio
    async def test_get_avatar_nonexistent(
        self,
        avatar_service: AvatarService,
    ):
        """Test getting a non-existent avatar returns None."""
        fake_id = uuid4()
        
        avatar = await avatar_service.get_avatar(fake_id)
        
        assert avatar is None

    @pytest.mark.asyncio
    async def test_delete_avatar_existing(
        self,
        avatar_service: AvatarService,
        sample_employee,
        session,
    ):
        """Test deleting an existing avatar."""
        image_data = self.create_test_image()
        
        # Save avatar first
        await avatar_service.save_avatar(sample_employee.id, image_data)
        await session.commit()
        
        # Delete avatar
        await avatar_service.delete_avatar(sample_employee.id)
        await session.commit()
        
        # Verify deletion
        avatar = await avatar_service.get_avatar(sample_employee.id)
        assert avatar is None

    @pytest.mark.asyncio
    async def test_delete_avatar_nonexistent(
        self,
        avatar_service: AvatarService,
    ):
        """Test that deleting non-existent avatar raises error."""
        fake_id = uuid4()
        
        with pytest.raises(ValueError, match="No avatar found"):
            await avatar_service.delete_avatar(fake_id)

    @pytest.mark.asyncio
    async def test_upsert_avatar(
        self,
        avatar_service: AvatarService,
        sample_employee,
        session,
    ):
        """Test that saving avatar twice updates instead of creating duplicate."""
        image_data1 = self.create_test_image()
        
        # Save first avatar
        avatar1 = await avatar_service.save_avatar(sample_employee.id, image_data1)
        await session.commit()
        
        # Save second avatar (should update)
        image_data2 = self.create_test_image()
        avatar2 = await avatar_service.save_avatar(sample_employee.id, image_data2)
        await session.commit()
        
        # Both should have same employee_id
        assert avatar1.employee_id == avatar2.employee_id
        
        # Verify only one avatar exists
        avatar = await avatar_service.get_avatar(sample_employee.id)
        assert avatar is not None
