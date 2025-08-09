from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import SignUpForm, CourseForm, EnrollStudentForm, ProgressForm
from .models import InstructorProfile, StudentProfile, StudentProgress, Course


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Create the user
            user: User = form.save()
            role = form.cleaned_data.get("role")
            # Auto-create the appropriate profile based on selected role
            if role == "student":
                StudentProfile.objects.create(user=user)
            else:
                InstructorProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Account created!")
            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard(request):
    # Simple role-aware dashboard
    student_profile = getattr(request.user, "student_profile", None)
    instructor_profile = getattr(request.user, "instructor_profile", None)

    progress_items = []
    if student_profile is not None:
        progress_items = StudentProgress.objects.filter(student=student_profile).order_by("-updated_at")

    instructor_courses = []
    if instructor_profile is not None:
        instructor_courses = Course.objects.filter(instructor=instructor_profile).order_by("-created_at")

    published_courses = Course.objects.filter(is_published=True).order_by("-created_at")[:10]

    context = {
        "student_profile": student_profile,
        "instructor_profile": instructor_profile,
        "progress_items": progress_items,
        "instructor_courses": instructor_courses,
        "published_courses": published_courses,
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def create_course(request):
    if not hasattr(request.user, "instructor_profile"):
        messages.error(request, "Only instructors can add courses.")
        return redirect("dashboard")
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user.instructor_profile
            course.save()
            messages.success(request, "Course created.")
            return redirect("my_courses")
    else:
        form = CourseForm()
    return render(request, "accounts/course_form.html", {"form": form})


def courses(request):
    qs = Course.objects.filter(is_published=True).select_related("instructor__user").order_by("-created_at")
    return render(request, "accounts/course_list.html", {"courses": qs, "mine": False})


@login_required
def my_courses(request):
    if not hasattr(request.user, "instructor_profile"):
        messages.error(request, "Only instructors can view this page.")
        return redirect("dashboard")
    qs = Course.objects.filter(instructor=request.user.instructor_profile).order_by("-created_at")
    return render(request, "accounts/course_list.html", {"courses": qs, "mine": True})


def course_detail(request, course_id: int):
    try:
        course = Course.objects.select_related("instructor__user").get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect("courses")

    student_profile = getattr(request.user, "student_profile", None) if request.user.is_authenticated else None
    enrolled_progress = None
    if student_profile:
        enrolled_progress = StudentProgress.objects.filter(student=student_profile, course=course).first()

    if request.method == "POST" and student_profile is not None:
        # Student self-enroll
        obj, created = StudentProgress.objects.get_or_create(
            student=student_profile,
            course=course,
            defaults={"course_name": course.title, "progress_percent": 0},
        )
        if created:
            messages.success(request, "You are enrolled in this course.")
        else:
            messages.info(request, "You are already enrolled.")
        return redirect("course_detail", course_id=course.id)

    return render(
        request,
        "accounts/course_detail.html",
        {"course": course, "enrolled_progress": enrolled_progress},
    )


@login_required
def manage_course_progress(request, course_id: int):
    # Ensure the user owns this course
    try:
        course = Course.objects.select_related("instructor__user").get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect("my_courses")
    if not hasattr(request.user, "instructor_profile") or course.instructor != request.user.instructor_profile:
        messages.error(request, "You do not have access to manage this course.")
        return redirect("dashboard")

    enroll_form = EnrollStudentForm()
    if request.method == "POST" and "enroll" in request.POST:
        enroll_form = EnrollStudentForm(request.POST)
        if enroll_form.is_valid():
            username = enroll_form.cleaned_data["username"]
            try:
                user = User.objects.get(username=username)
                student = getattr(user, "student_profile", None)
                if student is None:
                    messages.error(request, "That user is not a student.")
                else:
                    obj, created = StudentProgress.objects.get_or_create(
                        student=student, course=course,
                        defaults={"course_name": course.title, "progress_percent": 0},
                    )
                    if created:
                        messages.success(request, f"Enrolled {username}.")
                    else:
                        messages.info(request, f"{username} is already enrolled.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        return redirect("manage_course_progress", course_id=course.id)

    progress_list = (
        StudentProgress.objects.filter(course=course)
        .select_related("student__user")
        .order_by("student__user__username")
    )
    return render(
        request,
        "accounts/course_progress.html",
        {"course": course, "progress_list": progress_list, "enroll_form": enroll_form},
    )


@login_required
def update_progress(request, pk: int):
    try:
        prog = StudentProgress.objects.select_related("course__instructor__user", "student__user").get(pk=pk)
    except StudentProgress.DoesNotExist:
        messages.error(request, "Progress entry not found.")
        return redirect("my_courses")
    if not hasattr(request.user, "instructor_profile") or prog.course.instructor != request.user.instructor_profile:
        messages.error(request, "You do not have access to edit this entry.")
        return redirect("dashboard")
    if request.method == "POST":
        form = ProgressForm(request.POST, instance=prog)
        if form.is_valid():
            form.save()
            messages.success(request, "Progress updated.")
            return redirect("manage_course_progress", course_id=prog.course.id)
    else:
        form = ProgressForm(instance=prog)
    return render(request, "accounts/progress_form.html", {"form": form, "prog": prog})


@login_required
def delete_progress(request, pk: int):
    try:
        prog = StudentProgress.objects.select_related("course__instructor__user").get(pk=pk)
    except StudentProgress.DoesNotExist:
        messages.error(request, "Progress entry not found.")
        return redirect("my_courses")
    if not hasattr(request.user, "instructor_profile") or prog.course.instructor != request.user.instructor_profile:
        messages.error(request, "You do not have access to delete this entry.")
        return redirect("dashboard")
    if request.method == "POST":
        cid = prog.course.id
        prog.delete()
        messages.success(request, "Progress removed.")
        return redirect("manage_course_progress", course_id=cid)
    return render(request, "accounts/confirm_delete.html", {"object": prog, "type": "progress entry"})
