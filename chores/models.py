from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError("Users must have an email address")

		user = self.model(email=self.normalize_email(email), **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)
		extra_fields.setdefault("is_active", True)
		extra_fields.setdefault("role", User.Role.ADMIN)

		if extra_fields.get("is_staff") is not True:
			raise ValueError("Superuser must have is_staff=True")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True")

		return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
	class Role(models.TextChoices):
		ADMIN = "admin", "Admin"
		MEMBER = "member", "Member"

	username = None
	email = models.EmailField(unique=True)
	role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
	household = models.ForeignKey(
		"Household",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="members",
	)

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = []
	objects = UserManager()

	def __str__(self):
		return self.email


class Household(models.Model):
	name = models.CharField(max_length=150)
	invite_code = models.CharField(max_length=64, unique=True, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name


class Chore(models.Model):
	class Priority(models.TextChoices):
		LOW = "low", "Low"
		MEDIUM = "medium", "Medium"
		HIGH = "high", "High"

	class Category(models.TextChoices):
		CLEANING = "cleaning", "Cleaning"
		COOKING = "cooking", "Cooking"
		SHOPPING = "shopping", "Shopping"
		MAINTENANCE = "maintenance", "Maintenance"
		OTHER = "other", "Other"

	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		COMPLETED = "completed", "Completed"
		OVERDUE = "overdue", "Overdue"

	class Recurrence(models.TextChoices):
		DAILY = "daily", "Daily"
		WEEKLY = "weekly", "Weekly"
		MONTHLY = "monthly", "Monthly"

	household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="chores")
	name = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	assignee = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="assigned_chores",
	)
	due_date = models.DateField()
	priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
	category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
	status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
	recurrence = models.CharField(max_length=10, choices=Recurrence.choices, blank=True)
	is_recurring = models.BooleanField(default=False)
	rotation_enabled = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["due_date", "priority", "name"]
		indexes = [
			models.Index(fields=["household", "status"]),
			models.Index(fields=["household", "due_date"]),
		]
		constraints = [
			models.CheckConstraint(
				condition=models.Q(is_recurring=False, recurrence="")
				| models.Q(is_recurring=True, recurrence__in=["daily", "weekly", "monthly"]),
				name="recurrence_matches_flag",
			),
		]

	def __str__(self):
		return self.name


class ChoreCompletion(models.Model):
	chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name="completions")
	completed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="chore_completions")
	completed_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-completed_at"]
		indexes = [
			models.Index(fields=["chore", "completed_at"]),
			models.Index(fields=["completed_by", "completed_at"]),
		]
