from django.db import models
from django.contrib.auth.models import User


DIFFICULTY_CHOICES=[
    ('Easy','Easy'),
    ('Medium','Medium'),
    ('Hard','Hard')
]


class Tag(models.Model):
    name=models.CharField(max_length=50,unique=True)


    def __str__(self):
        return self.name


class Question(models.Model):
    question_no = models.IntegerField(unique=True)
    title = models.CharField(max_length=300)
    link = models.URLField(unique=True)
    problem_statement_html = models.TextField(blank=True,null=True)
    leetcode_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    tags = models.ManyToManyField('Tag',blank=True)

    def __str__(self):
        return f"{self.question_no}. {self.title}"





class UserProblem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    user_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    my_solution = models.TextField()
    optimized_solution = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True)
    note_image = models.ImageField(upload_to='note_images/', blank=True, null=True)
    last_solved = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mark_for_revision = models.BooleanField(default=False)


    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.username} - {self.question.title}"



# Create your models here.
