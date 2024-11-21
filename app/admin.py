from django.contrib import admin
from .models import *

class What_you_learn_TabularInline(admin.TabularInline):
    model = What_you_learn

class Requirements_TabularInline(admin.TabularInline):
    model = Requirements

class Video_TabularInline(admin.TabularInline):
    model = Video

class course_admin(admin.ModelAdmin):
    inlines = (What_you_learn_TabularInline, Requirements_TabularInline, Video_TabularInline)


class QuizQuestionInline(admin.StackedInline):  # Change to StackedInline
    model = QuizQuestion
    extra = 3  # Number of extra question fields to display initially
    fields = ['question', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_answer']

class QuizAdmin(admin.ModelAdmin):
    inlines = [QuizQuestionInline]

admin.site.register(Categories)
admin.site.register(Course, course_admin)
admin.site.register(Author)
admin.site.register(Level)
admin.site.register(Video)
admin.site.register(Lesson)
admin.site.register(Language)
admin.site.register(UserCourse)
admin.site.register(UserVideoWatch)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizQuestion)
admin.site.register(Payment)
admin.site.register(UserQuizScore)