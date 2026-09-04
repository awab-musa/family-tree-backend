import pytest


@pytest.mark.asyncio
async def test_tree_ancestors_requires_auth(client):
    import uuid

    response = await client.get(
        f"/api/v1/tree/{uuid.uuid4()}/ancestors", params={"tree_id": str(uuid.uuid4())}
    )
    assert response.status_code == 401
