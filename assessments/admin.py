from django.contrib import admin
from assessments.models import Assessment,Question,QuestionOption,StudentAssessmentAttempt,StudentAnswer

# Register your models here.
admin.site.register(Assessment)
admin.site.register(Question)
admin.site.register(QuestionOption)
admin.site.register(StudentAssessmentAttempt)
admin.site.register(StudentAnswer)
