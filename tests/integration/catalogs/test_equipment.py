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
        ({"name": "body only"}, None, status.HTTP_409_CONFLICT),
        ({"name": None}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ({"name": "T-Bar"}, "t-bar", status.HTTP_201_CREATED),
        ({"name": "  Weighted   Vest  "}, "weighted vest", status.HTTP_201_CREATED),
        ({"name": "ab"}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ({"name": "a" * 101}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_create_equipment(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    data: dict[str, str | None],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("equipment:create"),
        json=data,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_201_CREATED:
        response_data = response.json()
        assert response_data["name"] == result
        assert "id" in response_data


async def test_get_list_equipment_base(
    app: "FastAPI",
    user_client: "AsyncClient",
) -> None:
    response = await user_client.get(app.url_path_for("equipment:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 12  # noqa: PLR2004


@pytest.mark.parametrize(
    ("params", "expected_name"),
    [
        ({"searchString": "barbell"}, "barbell"),
        ({"searchString": "  e-z  "}, "e-z curl bar"),
        ({"orderBy": "name", "sortOrder": "desc"}, "other"),
        ({"orderBy": "id", "sortOrder": "desc"}, "e-z curl bar"),
        ({"searchString": "ba", "sortOrder": "desc"}, "medicine ball"),
    ],
)
async def test_get_list_equipment_params(
    app: "FastAPI",
    user_client: "AsyncClient",
    params: dict[str, str],
    expected_name: str,
) -> None:
    response = await user_client.get(
        app.url_path_for("equipment:list"),
        params=params,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data[0]["name"] == expected_name


@pytest.mark.parametrize(
    ("equipment_id", "status_code"),
    [
        (1, status.HTTP_200_OK),
        (99, status.HTTP_404_NOT_FOUND),
    ],
)
async def test_get_equipment_by_id(
    app: "FastAPI",
    user_client: "AsyncClient",
    equipment_id: int,
    status_code: int,
) -> None:
    response = await user_client.get(app.url_path_for("equipment:get", equipment_id=equipment_id))
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == equipment_id
        assert response_data["name"] == "body only"


@pytest.mark.parametrize(
    ("equipment_id", "data", "result", "status_code"),
    [
        (2, {"name": "  Dumbbell Updated  "}, "dumbbell updated", status.HTTP_200_OK),
        (2, {"name": "barbell"}, None, status.HTTP_409_CONFLICT),
        (99, {"name": "not found"}, None, status.HTTP_404_NOT_FOUND),
        (2, {"name": "a"}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (2, {"name": "a" * 101}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_update_equipment(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    equipment_id: int,
    data: dict[str, str],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("equipment:update", equipment_id=equipment_id),
        json=data,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == equipment_id
        assert response_data["name"] == result


@pytest.mark.parametrize(
    ("equipment_id", "status_code", "verify_missing"),
    [
        (3, status.HTTP_204_NO_CONTENT, True),
        (99, status.HTTP_404_NOT_FOUND, False),
    ],
)
async def test_delete_equipment(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    equipment_id: int,
    status_code: int,
    verify_missing: bool,
) -> None:
    response = await superuser_client.delete(
        app.url_path_for("equipment:delete", equipment_id=equipment_id),
    )
    assert response.status_code == status_code

    if verify_missing:
        response = await superuser_client.get(
            app.url_path_for("equipment:get", equipment_id=equipment_id),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    ("url_path", "equipment_id", "method"),
    [
        ("equipment:create", None, "post"),
        ("equipment:update", 1, "patch"),
        ("equipment:delete", 1, "delete"),
    ],
)
async def test_regular_user_modification_forbidden(
    user_client: "AsyncClient",
    app: "FastAPI",
    url_path: str,
    equipment_id: int | None,
    method: str,
) -> None:
    path_params = {"equipment_id": equipment_id} if equipment_id is not None else {}
    url = app.url_path_for(url_path, **path_params)
    http_method = getattr(user_client, method)

    response = await http_method(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
