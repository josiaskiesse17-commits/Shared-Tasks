import calendar
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChoreForm, EmailAuthenticationForm, JoinHouseholdForm, MemberForm, SignUpForm
from .decorators import admin_required
from .models import Chore, ChoreCompletion, Household, User


def _next_due_date(due_date, recurrence):
	if recurrence == Chore.Recurrence.DAILY:
		return due_date + timedelta(days=1)
	if recurrence == Chore.Recurrence.WEEKLY:
		return due_date + timedelta(weeks=1)
	month = due_date.month % 12 + 1
	year = due_date.year + (due_date.month // 12)
	day = min(due_date.day, calendar.monthrange(year, month)[1])
	return due_date.replace(year=year, month=month, day=day)


def _new_invite_code():
	while True:
		code = secrets.token_urlsafe(12)
		if not Household.objects.filter(invite_code=code).exists():
			return code


def signup(request):
	if request.user.is_authenticated:
		return redirect("chores:household")

	form = SignUpForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		with transaction.atomic():
			household = Household.objects.create(
				name=form.cleaned_data["household_name"],
				invite_code=_new_invite_code(),
			)
			user = User.objects.create_user(
				email=form.cleaned_data["email"],
				password=form.cleaned_data["password"],
				role=User.Role.ADMIN,
				household=household,
			)
		login(request, user)
		return redirect("chores:household")

	return render(request, "chores/signup.html", {"form": form})


def login_view(request):
	if request.user.is_authenticated:
		return redirect("chores:household")

	form = EmailAuthenticationForm(request, data=request.POST or None)
	if request.method == "POST" and form.is_valid():
		login(request, form.get_user())
		return redirect("chores:household")

	return render(request, "chores/login.html", {"form": form})


def logout_view(request):
	logout(request)
	return redirect("chores:login")


@login_required
def household(request):
	return render(request, "chores/household.html", {"household": request.user.household})


@login_required
def chore_list(request):
	household = request.user.household
	today = timezone.localdate()
	Chore.objects.filter(
		household=household,
		status=Chore.Status.PENDING,
		due_date__lt=today,
	).update(status=Chore.Status.OVERDUE)
	chores = Chore.objects.filter(household=household)
	filters = {
		"status": {choice.value for choice in Chore.Status},
		"priority": {choice.value for choice in Chore.Priority},
		"category": {choice.value for choice in Chore.Category},
	}
	for field, values in filters.items():
		value = request.GET.get(field)
		if value in values:
			chores = chores.filter(**{field: value})
	assignee = request.GET.get("assignee")
	if assignee and household.members.filter(pk=assignee).exists():
		chores = chores.filter(assignee_id=assignee)
	search = request.GET.get("q", "").strip()
	if search:
		chores = chores.filter(name__icontains=search)

	all_chores = Chore.objects.filter(household=household)
	total_count = all_chores.count()
	completed_count = all_chores.filter(status=Chore.Status.COMPLETED).count()
	context = {
		"chores": chores,
		"today_chores": all_chores.filter(due_date=today),
		"overdue_chores": all_chores.filter(status=Chore.Status.OVERDUE),
		"upcoming_chores": all_chores.filter(
			status=Chore.Status.PENDING,
			due_date__gt=today,
			due_date__lte=today + timedelta(days=3),
		),
		"completion_rate": round(completed_count * 100 / total_count, 1) if total_count else 0,
		"member_stats": User.objects.filter(household=household).annotate(
			completed_chore_count=Count(
				"chore_completions",
				filter=Q(chore_completions__chore__household=household),
			)
		),
		"members": household.members.all(),
	}
	return render(request, "chores/chore_list.html", context)


@admin_required
def chore_create(request):
	form = ChoreForm(request.POST or None, household=request.user.household)
	if request.method == "POST" and form.is_valid():
		chore = form.save(commit=False)
		chore.household = request.user.household
		chore.save()
		return redirect("chores:chore_list")
	return render(request, "chores/chore_form.html", {"form": form, "title": "Create chore"})


@admin_required
def chore_edit(request, pk):
	chore = get_object_or_404(Chore, pk=pk, household=request.user.household)
	form = ChoreForm(request.POST or None, instance=chore, household=request.user.household)
	if request.method == "POST" and form.is_valid():
		form.save()
		return redirect("chores:chore_list")
	return render(request, "chores/chore_form.html", {"form": form, "title": "Edit chore"})


@admin_required
@require_POST
def chore_delete(request, pk):
	chore = get_object_or_404(Chore, pk=pk, household=request.user.household)
	chore.delete()
	return redirect("chores:chore_list")


@login_required
@require_POST
def claim_chore(request, pk):
	if request.user.role != User.Role.MEMBER or not request.user.household_id:
		return HttpResponseForbidden("Only household members can claim chores.")
	chore = get_object_or_404(Chore, pk=pk, household=request.user.household, assignee__isnull=True)
	chore.assignee = request.user
	chore.save(update_fields=["assignee", "updated_at"])
	return redirect("chores:chore_list")


@login_required
@require_POST
def complete_chore(request, pk):
	if request.user.role != User.Role.MEMBER or not request.user.household_id:
		return HttpResponseForbidden("Only household members can complete chores.")

	with transaction.atomic():
		chore = get_object_or_404(
			Chore,
			pk=pk,
			household=request.user.household,
			assignee=request.user,
			status__in=[Chore.Status.PENDING, Chore.Status.OVERDUE],
		)
		chore.status = Chore.Status.COMPLETED
		chore.save(update_fields=["status", "updated_at"])
		ChoreCompletion.objects.create(chore=chore, completed_by=request.user)

		if chore.is_recurring:
			next_assignee = chore.assignee
			if chore.rotation_enabled:
				members = list(chore.household.members.order_by("pk"))
				if len(members) > 1:
					current_index = members.index(chore.assignee)
					next_assignee = members[(current_index + 1) % len(members)]
			Chore.objects.create(
				household=chore.household,
				name=chore.name,
				description=chore.description,
				assignee=next_assignee,
				due_date=_next_due_date(chore.due_date, chore.recurrence),
				priority=chore.priority,
				category=chore.category,
				recurrence=chore.recurrence,
				is_recurring=True,
				rotation_enabled=chore.rotation_enabled,
			)

	return redirect("chores:chore_list")


@login_required
def join_household(request):
	if request.user.household_id:
		return redirect("chores:household")

	form = JoinHouseholdForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		household = Household.objects.filter(
			invite_code=form.cleaned_data["invite_code"],
		).first()
		if household:
			request.user.household = household
			request.user.role = User.Role.MEMBER
			request.user.save(update_fields=["household", "role"])
			household.invite_code = None
			household.save(update_fields=["invite_code"])
			return redirect("chores:household")
		form.add_error("invite_code", "That invite code is not valid.")

	return render(request, "chores/join_household.html", {"form": form})


@admin_required
def add_member(request):
	form = MemberForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		if User.objects.filter(email=form.cleaned_data["email"]).exists():
			form.add_error("email", "That email is already registered.")
		else:
			User.objects.create_user(
				email=form.cleaned_data["email"],
				password=form.cleaned_data["password"],
				household=request.user.household,
				role=User.Role.MEMBER,
			)
			return redirect("chores:household")

	return render(request, "chores/add_member.html", {"form": form})


@admin_required
@require_POST
def regenerate_invite(request):
	request.user.household.invite_code = _new_invite_code()
	request.user.household.save(update_fields=["invite_code"])
	return redirect("chores:household")
