from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone


# Create your models here.
class Categories(models.Model):
    icon = models.CharField(max_length=200, null=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    def get_all_category(self):
        return Categories.objects.all().order_by("id")


class Author(models.Model):
    author_profile = models.ImageField(upload_to="Media/author")
    name = models.CharField(max_length=100, null=True)
    author_title = models.CharField(max_length=100, null=True)
    about_author = models.TextField(null=True)

    def __str__(self):
        return self.name


class Level(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Language(models.Model):
    language = models.CharField(max_length=100)

    def __str__(self):
        return self.language


class Course(models.Model):
    STATUS = (
        ("PUBLISH", "PUBLISH"),
        ("DRAFT", "DRAFT"),
    )

    featured_image = models.ImageField(upload_to="Media/featured_image", null=True)
    featured_video = models.CharField(max_length=300, null=True)
    title = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, null=True)
    deadline = models.CharField(max_length=100, null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    price = models.IntegerField(null=True, default=0)
    discount = models.IntegerField(null=True)
    slug = models.SlugField(default="", max_length=255, null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=100, null=True)
    certificate = models.CharField(null=True, default=False, max_length=100)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course_details", kwargs={"slug": self.slug})


def create_slug(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug
    qs = Course.objects.filter(slug=slug).order_by("-id")
    exists = qs.exists()
    if exists:
        new_slug = "%s-%s" % (slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug


def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)


pre_save.connect(pre_save_post_receiver, Course)


class What_you_learn(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    points = models.CharField(max_length=500)

    def __str__(self):
        return self.points


class Requirements(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    points = models.CharField(max_length=500)

    def __str__(self):
        return self.points


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name + " - " + self.course.title


# Quiz model
class Quiz(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


# QuizQuestion model
class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question = models.CharField(max_length=500)
    option_1 = models.CharField(max_length=200)
    option_2 = models.CharField(max_length=200)
    option_3 = models.CharField(max_length=200)
    option_4 = models.CharField(max_length=200)
    correct_answer = (
        models.IntegerField()
    )  # Index of the correct option (1, 2, 3, or 4)

    def __str__(self):
        return self.question


class Video(models.Model):
    serial_number = models.IntegerField(null=True)
    thumbnail = models.ImageField(upload_to="Media/Yt_Thumbnail", null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    # youtube_id = models.CharField(max_length=200)
    video_file = models.FileField(upload_to="Media/Videos", null=True, blank=True)
    time_duration = models.IntegerField(null=True)
    preview = models.BooleanField(default=False)
    quiz = models.ForeignKey(
        Quiz, on_delete=models.SET_NULL, null=True, blank=True, related_name="videos"
    )

    def __str__(self):
        return self.title


class UserCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    paid = models.BooleanField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " - " + self.course.title


class Payment(models.Model):
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    user_course = models.ForeignKey(UserCourse, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.user.first_name + "--" + self.course.title


STATUS_CHOICES = (
    ("not_started", "Not Started"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
)


class UserVideoWatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)
    watch_status = models.CharField(
        choices=STATUS_CHOICES, max_length=20, default="not_started"
    )
    progress = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.first_name} - {self.video.title} ({self.watch_status})"


class UserQuizScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    percentage = models.FloatField()
    last_attempted = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'quiz')  # Ensures a unique record for each user-quiz pair

