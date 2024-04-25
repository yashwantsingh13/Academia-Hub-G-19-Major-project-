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
import razorpay
client = razorpay.Client(auth=(KEY_ID,KYE_SECRET))

# ------------------------------------------------
    
def BASE(request):
    return render(request, 'base.html')

def PAGE_NOT_FOUND(request):
    category = Categories.objects.all().order_by('id')[0:5]
    context = {
        'category': category,
    }
    return render(request, 'error/404.html', context)

def HOME(request):
    category = Categories.objects.all().order_by('id')[0:5]
    course = Course.objects.filter(status = 'PUBLISH').order_by('-id')
    
    context = {
        'category': category,
        'course': course,
    }
    return render(request, 'Main/home.html', context)

def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    course = Course.objects.all()
    FreeCourse_count = Course.objects.filter(price = 0).count()
    PaidCourse_count = Course.objects.filter(price__gte = 1).count()

    context = {
        'category': category,
        'level': level,
        'course': course,
        'FreeCourse_count':FreeCourse_count,
        'PaidCourse_count':PaidCourse_count,
    }
    return render(request, 'Main/single_course.html', context)

def filter_data(request):
    categories = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')
    
    if price == ['PriceAll']:
        course = Course.objects.all()
    elif price == ['PriceFree']:
        course = Course.objects.filter(price=0)
    elif price == ['PricePaid']:
        course = Course.objects.filter(price__gte=1)
    elif categories:
        course = Course.objects.filter(category__id__in = categories).order_by('-id')
    elif level:
        course = Course.objects.filter(level__id__in=level).order_by('-id')
    else:
        course = Course.objects.all().order_by('-id')

    context = {
        'course':course
    }
    t = render_to_string('ajax/course.html', context)
    return JsonResponse({'data': t})


def SEARCH_COURSE(request):
    category = Categories.objects.all().order_by('id')[0:5]
    query = request.GET['query']
    course = Course.objects.filter(title__icontains=query)
    # print('------------------')
    # print(query)
    # print(course)
    # print('------------------')
    context = {
        'course': course,
        'category': category,
    }
    return render(request, 'search/search.html', context)

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
        category = Categories.objects.all().order_by('id')[0:5]
        
        # Ensure the course exists and get the first instance
        course = Course.objects.filter(slug=slug).first()
        if not course:
            return redirect('404')  # Assuming '404' is your 404 error view
        
        time_duration = Video.objects.filter(course__slug=slug).aggregate(sum=Sum('time_duration'))
        
        # Get the course_id explicitly from the course object
        course_id = course.id
        
        # Attempt to get the UserCourse object, handling the case where it might not exist
        try:
            check_enroll = UserCourse.objects.get(user=request.user, course_id=course_id)
        except UserCourse.DoesNotExist:
            check_enroll = None
        
        context = {
            'category': category,
            'course': course,
            'time_duration': time_duration,
            'check_enroll': check_enroll,
        }
        return render(request, 'course/course_details.html', context)
    
    else:
        # User is not authenticated, but still render the page
        category = Categories.objects.all().order_by('id')[0:5]
        
        # Ensure the course exists and get the first instance
        course = Course.objects.filter(slug=slug).first()
        if not course:
            return redirect('404')  # Assuming '404' is your 404 error view
        
        time_duration = Video.objects.filter(course__slug=slug).aggregate(sum=Sum('time_duration'))
        
        context = {
            'category': category,
            'course': course,
            'time_duration': time_duration,
            'check_enroll': None,  # User is not authenticated, so no enrollment check needed
        }
        return render(request, 'course/course_details.html', context)


def WATCH_COURSE(request, slug):
    course = Course.objects.filter(slug=slug)
    lecture = request.GET.get('lecture')
    course_id = Course.objects.get(slug=slug)

    try:
        # check_enroll = UserCourse.objects.get(user=request.user, course=course_id)
        video = Video.objects.get(id=lecture)
        if course.exists():
            course = course.first()
        else:
            return redirect('404')
    except UserCourse.DoesNotExist:
        return redirect('404')

    context = {
        'course': course,
        'video': video,
        'lecture': lecture,
    }
    return render(request, 'course/watch_course.html', context)
    



def CONTACT_US(request):
    category = Categories.objects.all().order_by('id')[0:5]
    context = {
        'category': category,
    }
    return render(request, 'Main/contact_us.html', context)

def ABOUT_US(request):
    category = Categories.objects.all().order_by('id')[0:5]
    context = {
        'category': category,
    }
    return render(request, 'Main/about_us.html', context)

def CHECKOUT(request, slug):
    category = Categories.objects.all().order_by('id')[0:5]
    course = Course.objects.get(slug = slug)
    action = request.GET.get('action')
    order = None
    
    if request.user.is_authenticated:
        if course.discount == 100:
            course = UserCourse(
                user = request.user,
                course = course,
            )
            course.save()
            messages.success(request, 'Course Enrolled Successfully!!')
            return redirect('my_course')
        elif action == 'create_payment' :
            if request.method == 'POST':
                first_name = request.POST.get('billing_first_name')
                last_name = request.POST.get('billing_last_name')
                country = request.POST.get('billing_country')
                address_1 = request.POST.get('billing_address_1')
                address_2 = request.POST.get('billing_address_2')
                city = request.POST.get('billing_city')
                state = request.POST.get('billing_state')
                postcode = request.POST.get('billing_postcode')
                phone = request.POST.get('billing_phone')
                email = request.POST.get('billing_email')
                order_comments = request.POST.get('order_comments')

                # amount = course.price * 100
                amount = discount_calculation(course.price, course.discount) * 100
                currency = "INR"
                notes = {
                    "name": f'{first_name} {last_name}',
                    "country": country,
                    "address":f'{address_1} {address_2}',
                    "city":city,
                    "state":state,
                    "postcode":postcode,
                    "phone":phone,
                    "email":email,
                    "order_comments":order_comments,
                }
                receipt = f'Skola-{int(time())}'
                order = client.order.create(
                    {
                        'receipt': receipt,
                        'notes': notes,
                        'amount': amount,
                        'currency': currency,
                        
                    }
                )
                
                payment = Payment(
                    course = course,
                    user = request.user,
                    order_id = order.get('id')
                )
                payment.save()
        context = {
            'course': course,
            'order': order,
            'category': category,
        }
        return render(request, 'checkout/checkout.html', context)
    else:
        messages.warning(request, 'You need to login first')
        return redirect('login')

@csrf_exempt
def VERIFY_PAYMENT(request):
    category = Categories.objects.all().order_by('id')[0:5]
    if request.method == 'POST':
        data = request.POST 
        try:
            client.utility.verify_payment_signature(data)
            razorpay_order_id = data['razorpay_order_id']
            razorpay_payment_id = data['razorpay_payment_id']
            
            payment = Payment.objects.get(order_id = razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True
            
            usercourse = UserCourse(
                user = payment.user,
                course = payment.course,
            )
            usercourse.save()
            payment.user_course = usercourse
            payment.save()
            
            context = {
                'data': data,
                'payment': payment,
                'category': category,
            }
            return render(request, 'verify_payment/success.html', context)
        except:
            context = {
                'category': category,
            }
            return render(request, 'verify_payment/fail.html', context)


def MY_COURSE(request):
    category = Categories.objects.all().order_by('id')[0:5]
    course = UserCourse.objects.filter(user = request.user)
    # time_duration = Video.objects.filter(course__slug = slug).aggregate(sum=Sum('time_duration'))
    
    context = {
        'course': course,
        # 'time_duration': time_duration,
        'category': category,
    }
    return render(request, 'course/my_course.html', context)
