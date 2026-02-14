"""Tests for TrustService."""

import pytest
from uuid import uuid4

from app.models.user import User
from app.services.trust import TrustService


@pytest.mark.asyncio
async def test_get_trust_level_default(test_db):
    """Test that new users start at trust level 1."""
    # Create test user
    user = User(email="test@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    level = await service.get_trust_level(str(user.id), "email", "read")
    assert level == 1


@pytest.mark.asyncio
async def test_requires_approval_level1(test_db):
    """Test that level 1 requires approval for all actions."""
    user = User(email="test2@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    user_id = str(user.id)
    assert await service.requires_approval(user_id, "email", "read") is True
    assert await service.requires_approval(user_id, "email", "send") is True


@pytest.mark.asyncio
async def test_record_action_increments(test_db):
    """Test that recording actions increments counters."""
    user = User(email="test3@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    user_id = str(user.id)
    await service.record_action(user_id, "email", "read", success=True)
    score = await service.get_or_create_score(user_id, "email", "read")
    assert score.successful_actions == 1
    assert score.total_actions == 1


@pytest.mark.asyncio
async def test_auto_escalation_level1_to_level2(test_db):
    """Test that 10 successful actions escalate from level 1 to level 2."""
    user = User(email="test4@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    user_id = str(user.id)
    for _ in range(10):
        await service.record_action(user_id, "email", "read", success=True)
    score = await service.get_or_create_score(user_id, "email", "read")
    assert score.trust_level == 2


@pytest.mark.asyncio
async def test_no_auto_escalation_to_level3(test_db):
    """Test that level 3 requires manual escalation (no auto-escalation)."""
    user = User(email="test5@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    user_id = str(user.id)
    for _ in range(50):
        await service.record_action(user_id, "email", "read", success=True)
    score = await service.get_or_create_score(user_id, "email", "read")
    assert score.trust_level == 2


@pytest.mark.asyncio
async def test_manual_set_level3(test_db):
    """Test that trust level 3 can be set manually."""
    user = User(email="test6@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    user_id = str(user.id)
    await service.set_trust_level(user_id, "email", "send", 3)
    level = await service.get_trust_level(user_id, "email", "send")
    assert level == 3


@pytest.mark.asyncio
async def test_downgrade_on_rejection(test_db):
    """Test that violations downgrade level 3 to level 2."""
    user = User(email="test7@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    user_id = str(user.id)
    await service.set_trust_level(user_id, "email", "send", 3)
    await service.record_violation(user_id, "email", "send")
    level = await service.get_trust_level(user_id, "email", "send")
    assert level == 2


@pytest.mark.asyncio
async def test_level2_read_auto_write_approval(test_db):
    """Test that level 2 allows read actions but requires approval for write actions."""
    user = User(email="test8@example.com", password_hash="hash", display_name="Test")
    test_db.add(user)
    await test_db.flush()

    service = TrustService(test_db)
    user_id = str(user.id)
    await service.set_trust_level(user_id, "email", "read", 2)
    await service.set_trust_level(user_id, "email", "send", 2)
    assert await service.requires_approval(user_id, "email", "read") is False
    assert await service.requires_approval(user_id, "email", "send") is True
