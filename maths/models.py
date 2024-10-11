from django.db import models
from django.utils.text import slugify
from accounts.models import User

class MathProblem(models.Model):
    topic = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField(unique=True, blank=True)  

    def save(self, *args, **kwargs):
        if not self.slug: 
            self.slug = slugify(self.topic)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.topic

class QuizScore(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    math_problem = models.CharField(max_length=200)  
    submitted_at = models.DateTimeField(auto_now_add=True)
