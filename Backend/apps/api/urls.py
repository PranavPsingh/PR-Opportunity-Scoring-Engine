from django.urls import path

from .views import analyze_opportunity_strengthening, change_user_role, client_detail, clients, confirm_opportunity_extraction, csrf, current_user, dashboard_summary, delete_user, extract_opportunity_information, generate_opportunity_angles, health_check, latest_opportunity_extraction, login_view, logout_view, opportunity_angle_detail, opportunity_angles, opportunity_detail, opportunity_score, opportunity_score_explanation, opportunity_score_history, opportunities, opportunity_strengthening, opportunity_strengthening_detail, protected_example, register, users_list

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
    path("dashboard/summary/", dashboard_summary, name="dashboard-summary"),
    path("opportunities/", opportunities, name="opportunities"),
    path("opportunities/<int:opportunity_id>/", opportunity_detail, name="opportunity-detail"),
    path("opportunities/<int:opportunity_id>/extract/", extract_opportunity_information, name="opportunity-extract"),
    path("opportunities/<int:opportunity_id>/extraction/", latest_opportunity_extraction, name="opportunity-extraction"),
    path("opportunities/<int:opportunity_id>/extraction/confirm/", confirm_opportunity_extraction, name="opportunity-extraction-confirm"),
    path("opportunities/<int:opportunity_id>/score/", opportunity_score, name="opportunity-score"),
    path("opportunities/<int:opportunity_id>/score/explanation/", opportunity_score_explanation, name="opportunity-score-explanation"),
    path("opportunities/<int:opportunity_id>/scores/", opportunity_score_history, name="opportunity-score-history"),
    path("opportunities/<int:opportunity_id>/angles/generate/", generate_opportunity_angles, name="opportunity-angles-generate"),
    path("opportunities/<int:opportunity_id>/angles/", opportunity_angles, name="opportunity-angles"),
    path("opportunities/<int:opportunity_id>/angles/<int:angle_id>/", opportunity_angle_detail, name="opportunity-angle-detail"),
    path("opportunities/<int:opportunity_id>/strengthening/analyze/", analyze_opportunity_strengthening, name="opportunity-strengthening-analyze"),
    path("opportunities/<int:opportunity_id>/strengthening/", opportunity_strengthening, name="opportunity-strengthening"),
    path("opportunities/<int:opportunity_id>/strengthening/<int:recommendation_id>/", opportunity_strengthening_detail, name="opportunity-strengthening-detail"),
]
