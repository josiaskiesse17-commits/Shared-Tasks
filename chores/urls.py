from django.urls import path

from . import views

app_name = "chores"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("household/", views.household, name="household"),
    path("household/join/", views.join_household, name="join_household"),
    path("household/members/add/", views.add_member, name="add_member"),
    path("household/invite/regenerate/", views.regenerate_invite, name="regenerate_invite"),
    path("chores/", views.chore_list, name="chore_list"),
    path("chores/new/", views.chore_create, name="chore_create"),
    path("chores/<int:pk>/edit/", views.chore_edit, name="chore_edit"),
    path("chores/<int:pk>/delete/", views.chore_delete, name="chore_delete"),
    path("chores/<int:pk>/claim/", views.claim_chore, name="claim_chore"),
    path("chores/<int:pk>/complete/", views.complete_chore, name="complete_chore"),
]
