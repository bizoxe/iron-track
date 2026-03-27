from typing import TYPE_CHECKING

import pytest
from fastapi import status

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("data", "result", "status_code"),
    [
        ({"name": "abdominals"}, None, status.HTTP_409_CONFLICT),
        ({"name": None}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ({"name": "  Upper Chest  "}, "upper chest", status.HTTP_201_CREATED),
        ({"name": "Lower-BacK"}, "lower-back", status.HTTP_201_CREATED),
        ({"name": "ab"}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ({"name": "a" * 101}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_create_muscle_group(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    data: dict[str, str | None],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("muscles:create"),
        json=data,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_201_CREATED:
        response_data = response.json()
        assert response_data["name"] == result
        assert "id" in response_data


async def test_get_list_muscle_groups_base(
    app: "FastAPI",
    user_client: "AsyncClient",
) -> None:
    response = await user_client.get(app.url_path_for("muscles:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 17  # noqa: PLR2004


@pytest.mark.parametrize(
    ("params", "expected_name"),
    [
        ({"searchString": "quadriceps"}, "quadriceps"),
        ({"searchString": "  string  "}, "hamstrings"),
        ({"orderBy": "name", "sortOrder": "desc"}, "triceps"),
        ({"orderBy": "id", "sortOrder": "desc"}, "abductors"),
        ({"searchString": "ba", "sortOrder": "desc"}, "middle back"),
    ],
)
async def test_get_list_muscle_groups_params(
    app: "FastAPI",
    user_client: "AsyncClient",
    params: dict[str, str],
    expected_name: str,
) -> None:
    response = await user_client.get(
        app.url_path_for("muscles:list"),
        params=params,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data[0]["name"] == expected_name


@pytest.mark.parametrize(
    ("muscle_id", "status_code"),
    [
        (1, status.HTTP_200_OK),
        (99, status.HTTP_404_NOT_FOUND),
    ],
)
async def test_get_muscle_group_by_id(
    app: "FastAPI",
    user_client: "AsyncClient",
    muscle_id: int,
    status_code: int,
) -> None:
    response = await user_client.get(app.url_path_for("muscles:get", muscle_id=muscle_id))
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == 1
        assert response_data["name"] == "abdominals"


@pytest.mark.parametrize(
    ("muscle_id", "data", "result", "status_code"),
    [
        (2, {"name": "  Hamstrings New  "}, "hamstrings new", status.HTTP_200_OK),
        (2, {"name": "abdominals"}, None, status.HTTP_409_CONFLICT),
        (99, {"name": "not found"}, None, status.HTTP_404_NOT_FOUND),
        (2, {"name": "a"}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_update_muscle_group(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    muscle_id: int,
    data: dict[str, str],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("muscles:update", muscle_id=muscle_id),
        json=data,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == muscle_id
        assert response_data["name"] == result


@pytest.mark.parametrize(
    ("muscle_id", "status_code", "verify_missing"),
    [
        (3, status.HTTP_204_NO_CONTENT, True),
        (99, status.HTTP_404_NOT_FOUND, False),
    ],
)
async def test_delete_muscle_group(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    muscle_id: int,
    status_code: int,
    verify_missing: bool,
) -> None:
    response = await superuser_client.delete(app.url_path_for("muscles:delete", muscle_id=muscle_id))
    assert response.status_code == status_code

    if verify_missing:
        response = await superuser_client.get(app.url_path_for("muscles:get", muscle_id=muscle_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    ("url_path", "muscle_id", "method"),
    [
        ("muscles:create", None, "post"),
        ("muscles:update", 1, "patch"),
        ("muscles:delete", 1, "delete"),
    ],
)
async def test_regular_user_modification_forbidden(
    user_client: "AsyncClient",
    app: "FastAPI",
    url_path: str,
    muscle_id: int | None,
    method: str,
) -> None:
    path_params = {"muscle_id": muscle_id} if muscle_id is not None else {}
    url = app.url_path_for(url_path, **path_params)
    http_method = getattr(user_client, method)

    response = await http_method(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
