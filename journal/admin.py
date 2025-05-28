from django.contrib import admin
from .models import Question, UserProblem, Tag

class CustomQuestionInterface(admin.ModelAdmin):
    list_display=('id','question_no','title','link','problem_statement_html','leetcode_difficulty')

class CustomUserProblemInterface(admin.ModelAdmin):
    list_display=('id','user','question','user_difficulty','my_solution','optimized_solution','note','note_image','last_solved','created_at','updated_at')

class CustomTagInterface(admin.ModelAdmin):
    list_display=('id','name')

admin.site.register(Question,CustomQuestionInterface)
admin.site.register(UserProblem,CustomUserProblemInterface)
admin.site.register(Tag,CustomTagInterface)

# Register your models here.
