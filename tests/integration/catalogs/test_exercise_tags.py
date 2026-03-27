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
        ({"name": "home friendly"}, None, status.HTTP_409_CONFLICT),
        ({"name": None}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ({"name": "  New Awesome Tag  "}, "new awesome tag", status.HTTP_201_CREATED),
        ({"name": "Pro-AthleTe"}, "pro-athlete", status.HTTP_201_CREATED),
        ({"name": "ab"}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ({"name": "a" * 101}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_create_exercise_tag(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    data: dict[str, str | None],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.post(
        app.url_path_for("exercise_tags:create"),
        json=data,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_201_CREATED:
        response_data = response.json()
        assert response_data["name"] == result
        assert "id" in response_data


async def test_get_list_exercise_tags_base(
    app: "FastAPI",
    user_client: "AsyncClient",
) -> None:
    response = await user_client.get(app.url_path_for("exercise_tags:list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 25  # noqa: PLR2004


@pytest.mark.parametrize(
    ("params", "expected_name"),
    [
        ({"searchString": "unilateral"}, "unilateral"),
        ({"searchString": "  rm-up  "}, "warm-up"),
        ({"orderBy": "name", "sortOrder": "desc"}, "warm-up"),
        ({"orderBy": "id", "sortOrder": "desc"}, "balance"),
        ({"searchString": "f", "sortOrder": "desc"}, "travel friendly"),
    ],
)
async def test_get_list_exercise_tags_params(
    app: "FastAPI",
    user_client: "AsyncClient",
    params: dict[str, str],
    expected_name: str,
) -> None:
    response = await user_client.get(
        app.url_path_for("exercise_tags:list"),
        params=params,
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data[0]["name"] == expected_name


@pytest.mark.parametrize(
    ("tag_id", "status_code"),
    [
        (1, status.HTTP_200_OK),
        (99, status.HTTP_404_NOT_FOUND),
    ],
)
async def test_get_exercise_tag_by_id(
    app: "FastAPI",
    user_client: "AsyncClient",
    tag_id: int,
    status_code: int,
) -> None:
    response = await user_client.get(app.url_path_for("exercise_tags:get", tag_id=tag_id))
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == 1
        assert response_data["name"] == "home friendly"


@pytest.mark.parametrize(
    ("tag_id", "data", "result", "status_code"),
    [
        (2, {"name": "  Outdoor Updated  "}, "outdoor updated", status.HTTP_200_OK),
        (2, {"name": "home friendly"}, None, status.HTTP_409_CONFLICT),
        (99, {"name": "not found"}, None, status.HTTP_404_NOT_FOUND),
        (2, {"name": "a"}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (2, {"name": "a" * 101}, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
)
async def test_update_exercise_tag(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    tag_id: int,
    data: dict[str, str],
    result: str | None,
    status_code: int,
) -> None:
    response = await superuser_client.patch(
        app.url_path_for("exercise_tags:update", tag_id=tag_id),
        json=data,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert response_data["id"] == tag_id
        assert response_data["name"] == result


@pytest.mark.parametrize(
    ("tag_id", "status_code", "verify_missing"),
    [
        (3, status.HTTP_204_NO_CONTENT, True),
        (99, status.HTTP_404_NOT_FOUND, False),
    ],
)
async def test_delete_exercise_tag(
    app: "FastAPI",
    superuser_client: "AsyncClient",
    tag_id: int,
    status_code: int,
    verify_missing: bool,
) -> None:
    response = await superuser_client.delete(app.url_path_for("exercise_tags:delete", tag_id=tag_id))
    assert response.status_code == status_code

    if verify_missing:
        response = await superuser_client.get(app.url_path_for("exercise_tags:get", tag_id=tag_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    ("url_path", "tag_id", "method"),
    [
        ("exercise_tags:create", None, "post"),
        ("exercise_tags:update", 1, "patch"),
        ("exercise_tags:delete", 1, "delete"),
    ],
)
async def test_regular_user_modification_forbidden(
    user_client: "AsyncClient",
    app: "FastAPI",
    url_path: str,
    tag_id: int | None,
    method: str,
) -> None:
    path_params = {"tag_id": tag_id} if tag_id is not None else {}
    url = app.url_path_for(url_path, **path_params)
    http_method = getattr(user_client, method)

    response = await http_method(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
