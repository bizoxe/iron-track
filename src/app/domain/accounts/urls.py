# ruff: noqa: S105

USER_CREATE = "/accounts"
USER_LIST = "/accounts"
USER_DETAIL = "/accounts/{user_id}"
USER_UPDATE = "/accounts/{user_id}"

USER_EXERCISE_LIST = "/accounts/{user_id}/exercises"
USER_EXERCISE_DETAIL = "/accounts/{user_id}/exercises/{exercise_id}"

ACCESS_REGISTER = "/accounts/auth/signup"
ACCESS_LOGIN = "/accounts/auth/signin"
ACCESS_PROFILE = "/accounts/me"
ACCESS_REFRESH_TOKEN = "/accounts/auth/refresh-jwt"
ACCESS_UPDATE_PWD = "/accounts/update-password"
ACCESS_LOGOUT = "/accounts/auth/logout"
ACCESS_DELETE_ACCOUNT = "/accounts/delete-account"

USER_ROLE_ASSIGN = "/accounts/{user_id}/roles/assign"
USER_ROLE_REVOKE = "/accounts/{user_id}/roles/revoke"
