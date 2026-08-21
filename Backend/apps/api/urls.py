from django.urls import path

from .views import change_user_role, client_detail, clients, csrf, current_user, delete_user, health_check, login_view, logout_view, opportunity_detail, opportunities, protected_example, register, users_list

app_name = "api"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("auth/csrf/", csrf, name="csrf"),
    path("auth/register/", register, name="register"),
    path("auth/login/", login_view, name="login"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/me/", current_user, name="current-user"),
    path("auth/protected/", protected_example, name="protected-example"),
    path("auth/users/", users_list, name="users-list"),
    path("auth/users/<int:user_id>/role/", change_user_role, name="change-user-role"),
    path("auth/users/<int:user_id>/delete/", delete_user, name="delete-user"),
    path("clients/", clients, name="clients"),
    path("clients/<int:client_id>/", client_detail, name="client-detail"),
    path("opportunities/", opportunities, name="opportunities"),
    path("opportunities/<int:opportunity_id>/", opportunity_detail, name="opportunity-detail"),
]
