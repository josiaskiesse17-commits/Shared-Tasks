from datetime import date

from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase

from .models import Chore, ChoreCompletion, Household, User


class DomainModelTests(TestCase):
	def setUp(self):
		self.household = Household.objects.create(name="Maple House", invite_code="MAPLE-123")
		self.user = User.objects.create_user(
			email="member@example.com",
			password="strong-password-123",
			household=self.household,
		)

	def test_user_uses_email_and_has_member_role_by_default(self):
		self.assertEqual(self.user.role, User.Role.MEMBER)
		self.assertTrue(self.user.check_password("strong-password-123"))
		self.assertEqual(str(self.user), "member@example.com")

	def test_email_and_invite_code_are_unique(self):
		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				User.objects.create_user(email=self.user.email, password="another-password")

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				Household.objects.create(name="Second House", invite_code=self.household.invite_code)

	def test_chore_stores_planned_fields_and_relationships(self):
		chore = Chore.objects.create(
			household=self.household,
			name="Clean kitchen",
			description="Wipe counters and mop the floor.",
			assignee=self.user,
			due_date=date(2026, 9, 10),
			priority=Chore.Priority.HIGH,
			category=Chore.Category.CLEANING,
			is_recurring=True,
			recurrence=Chore.Recurrence.WEEKLY,
		)

		self.assertEqual(chore.household, self.household)
		self.assertEqual(chore.assignee, self.user)
		self.assertEqual(chore.status, Chore.Status.PENDING)

	def test_completion_records_who_completed_a_chore(self):
		chore = Chore.objects.create(
			household=self.household,
			name="Take out bins",
			due_date=date(2026, 9, 10),
		)

		completion = ChoreCompletion.objects.create(chore=chore, completed_by=self.user)

		self.assertEqual(chore.completions.get(), completion)
		self.assertEqual(self.user.chore_completions.get(), completion)


class AuthenticationFlowTests(TestCase):
	def test_signup_creates_admin_household_and_invite(self):
		response = self.client.post(
			"/signup/",
			{
				"email": "admin@example.com",
				"password": "strong-password-123",
				"household_name": "Maple House",
			},
		)

		self.assertRedirects(response, "/household/")
		user = User.objects.get(email="admin@example.com")
		self.assertEqual(user.role, User.Role.ADMIN)
		self.assertTrue(user.household.invite_code)

	def test_member_can_join_with_invite_code(self):
		household = Household.objects.create(name="Maple House", invite_code="JOIN-123")
		member = User.objects.create_user(email="member@example.com", password="password")
		self.client.force_login(member)

		response = self.client.post("/household/join/", {"invite_code": "JOIN-123"})

		self.assertRedirects(response, "/household/")
		member.refresh_from_db()
		self.assertEqual(member.household, household)
		self.assertEqual(member.role, User.Role.MEMBER)


class ChoreManagementTests(TestCase):
	def setUp(self):
		self.household = Household.objects.create(name="Maple House", invite_code="CHORES-123")
		self.admin = User.objects.create_user(
			email="admin@example.com",
			password="password",
			role=User.Role.ADMIN,
			household=self.household,
		)
		self.member = User.objects.create_user(
			email="member@example.com",
			password="password",
			household=self.household,
		)

	def test_admin_can_create_edit_and_delete_chore(self):
		self.client.force_login(self.admin)
		data = {
			"name": "Clean kitchen",
			"description": "Wipe counters",
			"due_date": "2026-09-10",
			"priority": Chore.Priority.HIGH,
			"category": Chore.Category.CLEANING,
			"status": Chore.Status.PENDING,
			"recurrence": "",
			"is_recurring": "",
		}

		response = self.client.post("/chores/new/", data)
		chore = Chore.objects.get(name="Clean kitchen")
		self.assertRedirects(response, "/chores/")
		self.assertEqual(chore.household, self.household)

		response = self.client.post(
			f"/chores/{chore.pk}/edit/",
			{**data, "name": "Clean kitchen deeply"},
		)
		self.assertRedirects(response, "/chores/")
		self.assertTrue(Chore.objects.filter(name="Clean kitchen deeply").exists())

		response = self.client.post(f"/chores/{chore.pk}/delete/")
		self.assertRedirects(response, "/chores/")
		self.assertFalse(Chore.objects.filter(pk=chore.pk).exists())

	def test_member_can_claim_unassigned_household_chore(self):
		chore = Chore.objects.create(
			household=self.household,
			name="Take out bins",
			due_date=date(2026, 9, 10),
		)
		self.client.force_login(self.member)

		response = self.client.post(f"/chores/{chore.pk}/claim/")

		self.assertRedirects(response, "/chores/")
		chore.refresh_from_db()
		self.assertEqual(chore.assignee, self.member)

	def test_assigned_member_completes_chore_and_history_is_recorded(self):
		chore = Chore.objects.create(
			household=self.household,
			name="Wash dishes",
			assignee=self.member,
			due_date=date(2026, 9, 10),
		)
		self.client.force_login(self.member)

		response = self.client.post(f"/chores/{chore.pk}/complete/")

		self.assertRedirects(response, "/chores/")
		chore.refresh_from_db()
		self.assertEqual(chore.status, Chore.Status.COMPLETED)
		self.assertEqual(chore.completions.get().completed_by, self.member)

	def test_recurring_completion_creates_next_occurrence(self):
		chore = Chore.objects.create(
			household=self.household,
			name="Monthly clean",
			assignee=self.member,
			due_date=date(2026, 1, 31),
			recurrence=Chore.Recurrence.MONTHLY,
			is_recurring=True,
		)
		self.client.force_login(self.member)

		self.client.post(f"/chores/{chore.pk}/complete/")

		next_chore = Chore.objects.exclude(pk=chore.pk).get()
		self.assertEqual(next_chore.due_date, date(2026, 2, 28))
		self.assertEqual(next_chore.assignee, self.member)
		self.assertEqual(next_chore.status, Chore.Status.PENDING)

	def test_chore_list_marks_past_pending_chores_overdue(self):
		chore = Chore.objects.create(
			household=self.household,
			name="Overdue chore",
			due_date=date(2026, 9, 1),
		)
		self.client.force_login(self.member)

		self.client.get("/chores/")

		chore.refresh_from_db()
		self.assertEqual(chore.status, Chore.Status.OVERDUE)

	def test_chore_list_filters_and_reports_dashboard_metrics(self):
		completed = Chore.objects.create(
			household=self.household,
			name="Done dishes",
			assignee=self.member,
			due_date=date(2026, 9, 10),
			status=Chore.Status.COMPLETED,
		)
		ChoreCompletion.objects.create(chore=completed, completed_by=self.member)
		Chore.objects.create(
			household=self.household,
			name="Pending bins",
			due_date=date(2026, 9, 10),
		)
		self.client.force_login(self.member)

		response = self.client.get("/chores/?status=completed&q=Done")

		self.assertEqual(response.context["chores"].count(), 1)
		self.assertEqual(response.context["completion_rate"], 50.0)
		member_stats = next(
			member for member in response.context["member_stats"] if member.email == self.member.email
		)
		self.assertEqual(member_stats.completed_chore_count, 1)

	def test_member_cannot_create_or_manage_chores(self):
		self.client.force_login(self.member)

		self.assertEqual(self.client.get("/chores/new/").status_code, 403)
		chore = Chore.objects.create(
			household=self.household,
			name="Private chore",
			due_date=date(2026, 9, 10),
		)
		self.assertEqual(self.client.post(f"/chores/{chore.pk}/delete/").status_code, 403)

	def test_admin_can_add_member(self):
		self.client.force_login(self.admin)

		response = self.client.post(
			"/household/members/add/",
			{"email": "new-member@example.com", "password": "new-member-password-123"},
		)

		self.assertRedirects(response, "/household/")
		new_member = User.objects.get(email="new-member@example.com")
		self.assertEqual(new_member.household, self.household)

	def test_member_cannot_add_members_or_regenerate_invites(self):
		self.client.force_login(self.member)

		add_response = self.client.post(
			"/household/members/add/",
			{"email": "new-member@example.com", "password": "password"},
		)
		invite_response = self.client.post("/household/invite/regenerate/")

		self.assertEqual(add_response.status_code, 403)
		self.assertEqual(invite_response.status_code, 403)
		self.assertEqual(Household.objects.get(pk=self.household.pk).invite_code, "CHORES-123")
