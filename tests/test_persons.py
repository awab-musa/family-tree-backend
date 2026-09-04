import pytest


@pytest.mark.asyncio
async def test_list_persons_requires_auth(client):
    import uuid

    response = await client.get("/api/v1/persons", params={"tree_id": str(uuid.uuid4())})
    assert response.status_code == 401
