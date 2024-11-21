from django.shortcuts import redirect, render
from app.models import Categories, Course, Level, Video, UserCourse, Payment
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib import messages
from app.templatetags.course_tags import discount_calculation
from django.contrib.auth.models import User

from django.views.decorators.csrf import csrf_exempt
from .settings import KEY_ID, KYE_SECRET
from time import time
from app.models import *
import json

from django.shortcuts import render, get_object_or_404, redirect
from app.models import Quiz, QuizQuestion, Video
from django.contrib.auth.decorators import login_required

import razorpay

client = razorpay.Client(auth=(KEY_ID, KYE_SECRET))


# ------------------------------------------------


def BASE(request):
    return render(request, "base.html")


def PAGE_NOT_FOUND(request):
    category = Categories.objects.all().order_by("id")[0:5]
    context = {
        "category": category,
    }
    return render(request, "error/404.html", context)


def HOME(request):
    category = Categories.objects.all().order_by("id")[0:5]
    course = Course.objects.filter(status="PUBLISH").order_by("-id")

    context = {
        "category": category,
        "course": course,
    }
    return render(request, "Main/home.html", context)


def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    course = Course.objects.all()
    FreeCourse_count = Course.objects.filter(price=0).count()
    PaidCourse_count = Course.objects.filter(price__gte=1).count()

    context = {
        "category": category,
        "level": level,
        "course": course,
        "FreeCourse_count": FreeCourse_count,
        "PaidCourse_count": PaidCourse_count,
    }
    return render(request, "Main/single_course.html", context)


def filter_data(request):
    categories = request.GET.getlist("category[]")
    level = request.GET.getlist("level[]")
    price = request.GET.getlist("price[]")

    if price == ["PriceAll"]:
        course = Course.objects.all()
    elif price == ["PriceFree"]:
        course = Course.objects.filter(price=0)
    elif price == ["PricePaid"]:
        course = Course.objects.filter(price__gte=1)
    elif categories:
        course = Course.objects.filter(category__id__in=categories).order_by("-id")
    elif level:
        course = Course.objects.filter(level__id__in=level).order_by("-id")
    else:
        course = Course.objects.all().order_by("-id")

    context = {"course": course}
    t = render_to_string("ajax/course.html", context)
    return JsonResponse({"data": t})


def SEARCH_COURSE(request):
    category = Categories.objects.all().order_by("id")[0:5]
    query = request.GET["query"]
    course = Course.objects.filter(title__icontains=query)
    # print('------------------')
    # print(query)
    # print(course)
    # print('------------------')
    context = {
        "course": course,
        "category": category,
    }
    return render(request, "search/search.html", context)


# def COURSE_DETAILS(request, slug):
#     category = Categories.objects.all().order_by('id')[0:5]
#     time_duration = Video.objects.filter(course__slug = slug).aggregate(sum=Sum('time_duration'))
#     course = Course.objects.filter(slug=slug)
#     course_id = Course.objects.get(slug=slug)

#     try:
#         check_enroll = UserCourse.objects.get(user= request.user, course = course_id)
#     except UserCourse.DoesNotExist:
#         check_enroll = None
#     if course.exists():
#         course = course.first
#     else:
#         return redirect('404')

#     context = {
#         'category': category,
#         'course': course,
#         'time_duration': time_duration,
#         'check_enroll': check_enroll,
#     }
#     return render(request, 'course/course_details.html', context)


def COURSE_DETAILS(request, slug):
    # Ensure the user is authenticated
    if request.user.is_authenticated:
        category = Categories.objects.all().order_by("id")[0:5]

        # Ensure the course exists and get the first instance
        course = Course.objects.filter(slug=slug).first()
        if not course:
            return redirect("404")  # Assuming '404' is your 404 error view

        time_duration = Video.objects.filter(course__slug=slug).aggregate(
            sum=Sum("time_duration")
        )

        # Get the course_id explicitly from the course object
        course_id = course.id

        # Attempt to get the UserCourse object, handling the case where it might not exist
        try:
            check_enroll = UserCourse.objects.get(
                user=request.user, course_id=course_id
            )
        except UserCourse.DoesNotExist:
            check_enroll = None

        context = {
            "category": category,
            "course": course,
            "time_duration": time_duration,
            "check_enroll": check_enroll,
        }
        return render(request, "course/course_details.html", context)

    else:
        # User is not authenticated, but still render the page
        category = Categories.objects.all().order_by("id")[0:5]

        # Ensure the course exists and get the first instance
        course = Course.objects.filter(slug=slug).first()
        if not course:
            return redirect("404")  # Assuming '404' is your 404 error view

        time_duration = Video.objects.filter(course__slug=slug).aggregate(
            sum=Sum("time_duration")
        )

        context = {
            "category": category,
            "course": course,
            "time_duration": time_duration,
            "check_enroll": None,  # User is not authenticated, so no enrollment check needed
        }
        return render(request, "course/course_details.html", context)

from django.http import Http404

def WATCH_COURSE(request, slug):
    # Get course by slug
    course = get_object_or_404(Course, slug=slug)

    # Check if user is enrolled in the course
    try:
        enrollment = UserCourse.objects.get(user=request.user, course=course)
    except UserCourse.DoesNotExist:
        raise Http404("You are not enrolled in this course.")

    # Get the lecture ID from query parameters
    lecture_id = request.GET.get("lecture")

    # If lecture is provided, fetch the video, otherwise default to the first video in the course
    if lecture_id:
        video = get_object_or_404(Video, id=lecture_id, course=course)
    else:
        # Get the first video in the course by default
        video = Video.objects.filter(course=course).order_by("serial_number").first()
    
    if not video:
        raise Http404("No videos are available in this course.")

    # Fetch quiz and user's quiz score if the video has an associated quiz
    quiz = video.quiz
    user_quiz_score = UserQuizScore.objects.filter(user=request.user, quiz=quiz).first() if quiz else None

    context = {
        "course": course,
        "video": video,
        "lecture": lecture_id,
        "quiz": quiz,
        "user_quiz_score": user_quiz_score,
    }
    return render(request, "course/watch_course.html", context)



def CONTACT_US(request):
    category = Categories.objects.all().order_by("id")[0:5]
    context = {
        "category": category,
    }
    return render(request, "Main/contact_us.html", context)


def ABOUT_US(request):
    category = Categories.objects.all().order_by("id")[0:5]
    context = {
        "category": category,
    }
    return render(request, "Main/about_us.html", context)


def CHECKOUT(request, slug):
    category = Categories.objects.all().order_by("id")[0:5]
    course = Course.objects.get(slug=slug)
    action = request.GET.get("action")
    order = None

    if request.user.is_authenticated:
        if course.discount == 100:
            course = UserCourse(
                user=request.user,
                course=course,
            )
            course.save()
            messages.success(request, "Course Enrolled Successfully!!")
            return redirect("my_course")
        elif action == "create_payment":
            if request.method == "POST":
                first_name = request.POST.get("billing_first_name")
                last_name = request.POST.get("billing_last_name")
                country = request.POST.get("billing_country")
                address_1 = request.POST.get("billing_address_1")
                address_2 = request.POST.get("billing_address_2")
                city = request.POST.get("billing_city")
                state = request.POST.get("billing_state")
                postcode = request.POST.get("billing_postcode")
                phone = request.POST.get("billing_phone")
                email = request.POST.get("billing_email")
                order_comments = request.POST.get("order_comments")

                # amount = course.price * 100
                amount = discount_calculation(course.price, course.discount) * 100
                currency = "INR"
                notes = {
                    "name": f"{first_name} {last_name}",
                    "country": country,
                    "address": f"{address_1} {address_2}",
                    "city": city,
                    "state": state,
                    "postcode": postcode,
                    "phone": phone,
                    "email": email,
                    "order_comments": order_comments,
                }
                receipt = f"Skola-{int(time())}"
                order = client.order.create(
                    {
                        "receipt": receipt,
                        "notes": notes,
                        "amount": amount,
                        "currency": currency,
                    }
                )

                payment = Payment(
                    course=course, user=request.user, order_id=order.get("id")
                )
                payment.save()
        context = {
            "course": course,
            "order": order,
            "category": category,
        }
        return render(request, "checkout/checkout.html", context)
    else:
        messages.warning(request, "You need to login first")
        return redirect("login")


@csrf_exempt
def VERIFY_PAYMENT(request):
    category = Categories.objects.all().order_by("id")[0:5]
    if request.method == "POST":
        data = request.POST
        try:
            client.utility.verify_payment_signature(data)
            razorpay_order_id = data["razorpay_order_id"]
            razorpay_payment_id = data["razorpay_payment_id"]

            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True

            usercourse = UserCourse(
                user=payment.user,
                course=payment.course,
            )
            usercourse.save()
            payment.user_course = usercourse
            payment.save()

            context = {
                "data": data,
                "payment": payment,
                "category": category,
            }
            return render(request, "verify_payment/success.html", context)
        except:
            context = {
                "category": category,
            }
            return render(request, "verify_payment/fail.html", context)


def MY_COURSE(request):
    category = Categories.objects.all().order_by("id")[0:5]
    course = UserCourse.objects.filter(user=request.user)
    # time_duration = Video.objects.filter(course__slug = slug).aggregate(sum=Sum('time_duration'))

    context = {
        "course": course,
        # 'time_duration': time_duration,
        "category": category,
    }
    return render(request, "course/my_course.html", context)


@csrf_exempt  # Only for testing; remove in production if possible.
def update_video_watch_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            video_id = data.get("video_id")
            user_id = data.get("user_id")

            # Fetch the user and video objects
            try:
                user = User.objects.get(id=user_id)
                video = Video.objects.get(id=video_id)
            except (User.DoesNotExist, Video.DoesNotExist):
                return JsonResponse(
                    {"status": "error", "message": "User or video not found"},
                    status=404,
                )

            # Update or create a UserVideoWatch entry
            user_video_watch, created = UserVideoWatch.objects.get_or_create(
                user=user,
                video=video,
                defaults={"watch_status": "completed", "progress": video.time_duration},
            )

            # If the entry exists and is not already completed, update it
            if not created and user_video_watch.watch_status != "completed":
                user_video_watch.watch_status = "completed"
                user_video_watch.progress = video.time_duration
                user_video_watch.save()

            return JsonResponse(
                {"status": "success", "message": "Watch status updated"}
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=405
    )


@csrf_exempt  # Only for testing; remove in production if possible.
def check_video_watch_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            video_id = data.get("video_id")
            user_id = data.get("user_id")

            # Fetch the user and video objects
            try:
                user = User.objects.get(id=user_id)
                video = Video.objects.get(id=video_id)
            except (User.DoesNotExist, Video.DoesNotExist):
                return JsonResponse(
                    {"status": "error", "message": "User or video not found"},
                    status=404,
                )

            # Check if the video has an associated quiz
            if not video.quiz:
                return JsonResponse(
                    {"status": "no_quiz", "message": "No quiz available for this video"}
                )

            # Check if the user has already watched this video
            user_video_watch = UserVideoWatch.objects.filter(
                user=user, video=video
            ).first()

            # Check if the user has already attempted the quiz
            user_quiz_attempt = UserQuizAttempt.objects.filter(
                user=user, quiz=video.quiz
            ).first()

            if (
                user_quiz_attempt and user_quiz_attempt.score is not None
            ):  # User has attempted and scored
                return JsonResponse(
                    {
                        "status": "quiz_attempted",
                        "message": "You have already attempted the quiz and have a score.",
                    }
                )
            elif user_video_watch and user_video_watch.watch_status == "completed":
                return JsonResponse(
                    {
                        "status": "watched",
                        "message": "You have already watched this video",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "status": "not_watched",
                        "message": "You have not watched this video yet",
                    }
                )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=405
    )


@login_required
def quiz_detail(request, video_id):
    # Fetch the quiz associated with the video
    video = get_object_or_404(Video, id=video_id)
    quiz = video.quiz

    # If there is no quiz, redirect back or show a message
    if not quiz:
        return render(request, "quiz/no_quiz.html")

    questions = quiz.questions.all()

    context = {
        "quiz": quiz,
        "questions": questions,
        "video": video,
    }
    return render(request, "quiz/index.html", context)


@login_required
def submit_quiz(request, quiz_id):
    if request.method == "POST":
        quiz = get_object_or_404(Quiz, id=quiz_id)
        questions = quiz.questions.all()
        score = 0
        total = questions.count()

        # Calculate the score based on the user's answers
        for question in questions:
            selected_answer = request.POST.get(f"question_{question.id}")
            if (
                selected_answer is not None
                and int(selected_answer) == question.correct_answer
            ):
                score += 1

        # Calculate the percentage
        percentage = (score / total) * 100 if total > 0 else 0

        # Update the existing score or create a new entry if it doesn't exist
        user_quiz_score, created = UserQuizScore.objects.update_or_create(
            user=request.user,
            quiz=quiz,
            defaults={"score": score, "total": total, "percentage": percentage},
        )

        # Retrieve a video associated with this quiz
        video = Video.objects.filter(
            quiz=quiz
        ).first()  # Fetches the first video with this quiz

        if video:
            return redirect(
                reverse("watch_course", args=[video.course.slug])
                + f"?lecture={video.id}"
            )
        else:
            return redirect(
                "course_list"
            )  # Redirect to a generic course page if no video found

    # Redirect to the quiz detail page if the request method is not POST
    return redirect("quiz_detail", quiz_id=quiz_id)
