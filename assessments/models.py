from django.db import models
from django.utils import timezone
import uuid
from userAuth.models import StudentProfile, TeacherProfile
from course.models import Lesson,Course,CourseModule
from django.core.exceptions import ValidationError
from django.db import models, transaction
# Create your models here.

class Assessment(models.Model):
    """Base model for all assessments"""
    
    class AssessmentType(models.TextChoices):
        QUIZ = 'quiz', 'Quiz' # for lesson
        ASSIGNMENT = 'assignment', 'Assignment' # for module
        COURSE_EXAM = 'course_exam', 'Course Exam' # for course
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200)
    description=models.TextField(blank=True,null=True)
    assessment_type=models.CharField(max_length=20,choices=AssessmentType.choices)
    
    # relations
    teacher=models.ForeignKey(TeacherProfile,on_delete=models.CASCADE,related_name='teacher_assessments')
    lesson=models.ForeignKey(Lesson,on_delete=models.CASCADE,related_name='quizzes',blank=True,null=True)
    module=models.ForeignKey(CourseModule,on_delete=models.CASCADE,related_name='assignments',blank=True,null=True)
    course=models.ForeignKey(Course,on_delete=models.CASCADE, related_name='course_exams', blank=True, null=True)
        
    # setting
    is_published = models.BooleanField(default=False)
    is_timed = models.BooleanField(default=False)
    time_limit = models.PositiveIntegerField(default=30, help_text="Time limit in minutes",null=True,blank=True) 
    max_attempts = models.PositiveIntegerField(default=1)
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=60.00)
    
    # scheduling
    available_from=models.DateTimeField(default=timezone.now)
    available_until=models.DateTimeField(blank=True, null=True)
    
    # statistics
    total_questions = models.PositiveIntegerField(default=0)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f"{self.context_title}"
    
    def clean(self):
        
        if self.assessment_type == self.AssessmentType.QUIZ : 
            if not self.lesson :
                raise ValidationError("Quiz must be linked to a lesson")
            
            if self.course or self.module:
                raise ValidationError("Quiz can only be linked to a lesson")
            
        elif self.assessment_type == self.AssessmentType.ASSIGNMENT : 
            if not self.module : 
                raise ValidationError("Assignment must be linked to a module")
            
            if self.lesson or self.course:
                raise ValidationError("Assignment can only be linked to a module")
            
        elif self.assessment_type == self.AssessmentType.COURSE_EXAM:
            if not self.course:
                raise ValidationError("Course exam must be linked to a course")
            if self.lesson or self.module:
                raise ValidationError("Course exam can only be linked to a course")
            
        else:
            raise ValidationError("Invalid Assignment Type")
        
        if not self.is_timed and self.time_limit:
            self.time_limit = None
            
    def save(self,*args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_available(self):
        now=timezone.now()
        # any false of this , exam not avilable
        return(
            self.is_published and
            self.available_from <= now and 
            (self.available_until is None or self.available_until >= now)
        )
        
    @property
    def related_course(self):
        
        if self.course:
            return self.course
        
        elif self.module:
            return self.module.course
        
        elif self.lesson:
            return self.lesson.module,self.lesson.module.course
        
        else:
            return None

    @property
    def context_title(self):
        """ title of related exam """
        if self.lesson:
            return f"Quiz Lesson: {self.lesson.title}"
        elif self.module:
            return f"Assignment Module: {self.module.title}"
        elif self.course:
            return f"Exam Course: {self.course.title}"
        
    def update_totals(self):
        from django.db.models import Count, Sum
        totals=self.questions.aggregate(
            total_questions=Count('id'),
            total_marks=Sum('mark')
        )
        self.total_questions=totals['total_questions'] or 0
        self.total_marks=totals['total_marks']
        self.save(update_fields=['total_questions', 'total_marks'])
        
    
class Question(models.Model):
    """Question model for assessments"""
    
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE='multiple_choice','Multiple Choice'
        TRUE_FALSE='true_false', 'True/False'
        SHORT_ANSWER ='short_answer', 'Short Answer'
        ESSAY = 'essay', 'Essay'
        FILL_BLANK = 'fill_blank', 'Fill in the Blank'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    assessment=models.ForeignKey(Assessment,on_delete=models.CASCADE,related_name='questions')
    question_text=models.TextField() # what is  questition
    question_type=models.CharField(max_length=20,choices=QuestionType.choices)
    mark=models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    order=models.PositiveIntegerField(blank=True, null=True)
    explanation = models.TextField(blank=True, null=True, help_text="Explanation for the correct answer")
    image=models.ImageField(upload_to='questions/images/',blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.order} - {self.question_text[:50]}..."
    
    class Meta:
        ordering=['order']
        # unique_together=('assessment','order')
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            if is_new:
                if self.order is None:
                    last_question_order=Question.objects.filter(assessment=self.assessment).aggregate(models.Max('order'))['order__max']
                    self.order=1 if last_question_order is None else last_question_order+1
                else:
                    if Question.objects.filter(assessment=self.assessment,order=self.order).exists():
                        Question.objects.filter(assessment=self.assessment,order__gte=self.order).update(order=models.F('order')+1)

            else:
                old_order=Question.objects.get(pk=self.pk).order
                if self.order != old_order:
                    if self.order < old_order:
                        Question.objects.filter(
                            assessment=self.assessment,
                            order__gte=self.order,
                            order__lt=old_order
                        ).update(order=models.F('order') + 1)

                    else:
                        Question.objects.filter(
                            assessment=self.assessment,
                            order__lte=self.order,
                            order__gt=old_order
                        ).update(order=models.F('order') - 1)
        
        super().save(*args, **kwargs)
        self.assessment.update_totals()
        
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.assessment.update_totals()
        
class QuestionOption(models.Model):
    """Options for multiple choice questions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order=models.PositiveIntegerField(blank=True, null=True)
    
    class Meta:
        ordering = ['order']
        # unique_together = ('question', 'order')
        
    def __str__(self):
        return f"{self.order}-{self.option_text[:50]}... ({'✓' if self.is_correct else '✗'})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        with transaction.atomic():
            if is_new:
                if self.order is None:
                    last_question_option_order=QuestionOption.objects.filter(question=self.question).aggregate(models.Max('order'))['order__max']
                    self.order=1 if last_question_option_order is None else last_question_option_order+1
                else:
                    if QuestionOption.objects.filter(question=self.question,order=self.order).exists():
                        QuestionOption.objects.filter(question=self.question,order__gte=self.order).update(order=models.F('order')+1)

            else:
                old_order=QuestionOption.objects.get(pk=self.pk).order
                if self.order != old_order:
                    if self.order < old_order:
                        QuestionOption.objects.filter(
                            question=self.question,
                            order__gte=self.order,
                            order__lt=old_order
                        ).update(order=models.F('order') + 1)

                    else:
                        QuestionOption.objects.filter(
                            question=self.question,
                            order__lte=self.order,
                            order__gt=old_order
                        ).update(order=models.F('order') - 1)
        
        super().save(*args, **kwargs)

class StudentAssessmentAttempt(models.Model):
    """Student's attempt at an assessment"""
    
    class AttemptStatus(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'
        EXPIRED = 'expired', 'Expired'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='assessment_attempts')
    assessment=models.ForeignKey(Assessment,on_delete=models.CASCADE,related_name='attempts')
    
    # Attempt details
    attempt_number=models.PositiveIntegerField(default=1)
    status=models.CharField(max_length=20,choices=AttemptStatus,default=AttemptStatus.IN_PROGRESS)
    
    # Timing
    started_at=models.DateTimeField(auto_now_add=True)
    ended_at=models.DateTimeField(null=True,blank=True)
    time_taken = models.PositiveIntegerField(blank=True, null=True, help_text="Time taken in seconds")
    
    # Scoring
    score=models.DecimalField(max_digits=6,decimal_places=2,default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_passed = models.BooleanField(default=False)
    
    # Auto-grading
    auto_graded=models.BooleanField(default=False)
    graded_at=models.DateTimeField(blank=True, null=True)
    graded_by=models.ForeignKey(TeacherProfile,models.SET_NULL,related_name='graded_assessments', blank=True, null=True)
    
    # Feedback
    teacher_feedback = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering=['-started_at']
        unique_together=('student','attempt_number','assessment')
        indexes=[
           models.Index(fields=('status',)),
           models.Index(fields=('started_at',)),
        ]
    
    def __str__(self):
        return f"{self.student.user.username} {self.assessment.title} Attempt {self.attempt_number}"
    
    def save(self, *args, **kwargs):
        self.full_clean()
        
        if self.status == self.AttemptStatus.SUBMITTED and not self.ended_at : 
            self.ended_at=timezone.now()

            if self.started_at:
                self.time_taken=int((self.submitted_at-self.started_at).total_seconds())
            
        super().save(*args, **kwargs)
        
        
    def clean(self):
        now = timezone.now()
        if not self.pk:
            if self.attempt_number > self.assessment.max_attempts:
                raise ValidationError("You exceeded the maximum attempts for this assessment.")
            
            if self.assessment.available_from and now < self.assessment.available_from:
                raise ValidationError("The assessment has not started yet.")
            
            if self.assessment.available_until and now > self.assessment.available_until:
                raise ValidationError("The assessment has already ended.")
            
    @property
    def is_expired(self):
        if self.status != self.AttemptStatus.IN_PROGRESS:
            return False

        now = timezone.now()

        # if assessment ended
        if self.assessment.available_until and now > self.assessment.available_until:
            return True

        # if time limit
        if self.assessment.is_timed and self.started_at:
            time_limit_seconds = self.assessment.time_limit * 60
            elapsed = (now - self.started_at).total_seconds()
            if elapsed > time_limit_seconds:
                return True

        return False

    def expire_attempt(self):
        """Mark attempt as expired and auto-grade if possible"""
        if self.status == self.AttemptStatus.IN_PROGRESS:
            now = timezone.now()
            elapsed = (now - self.started_at).total_seconds()
            self.status = self.AttemptStatus.EXPIRED
            self.ended_at = now
            self.time_taken = int(elapsed)
            self.save()

    def all_questions_auto_gradable(self):
        """Check if all questions in the attempt can be auto-graded."""
        auto_gradable_types = [
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.TRUE_FALSE
        ]
        return all(
            answer.question.question_type in auto_gradable_types
            for answer in self.answers.all()
        )
        
    def calculate_final_score(self):
        """
        Calculate score when all answers are graded (manual or auto).
        """
        answers = self.answers.all()

        # Check if any answers are ungraded (manual or auto)
        ungraded_exists = answers.filter(
            models.Q(
                question__question_type__in=[
                    Question.QuestionType.SHORT_ANSWER,
                    Question.QuestionType.ESSAY,
                    Question.QuestionType.FILL_BLANK
                ],
                manual_graded=False
            )
            |
            models.Q(
                question__question_type__in=[
                    Question.QuestionType.MULTIPLE_CHOICE,
                    Question.QuestionType.TRUE_FALSE
                ],
                auto_graded=False
            )
        ).exists()

        if ungraded_exists:
            # Still some ungraded answers
            self.auto_graded = False
            if self.status != self.AttemptStatus.SUBMITTED:
                self.status = self.AttemptStatus.SUBMITTED
            self.save(update_fields=["auto_graded", "status"])
            return

        # All answers graded
        total_score = sum(answer.marks_awarded for answer in answers)
        self.score = total_score
        self.percentage = round(
            (total_score / self.assessment.total_marks) * 100
            if self.assessment.total_marks > 0 else 0,2)
        self.is_passed = self.percentage >= self.assessment.passing_score
        self.auto_graded = self.all_questions_auto_gradable()
        self.graded_at = timezone.now()
        self.status = self.AttemptStatus.GRADED
        self.save()
        
class StudentAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    attempt = models.ForeignKey(StudentAssessmentAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    
    # Answer content
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, related_name='answers', blank=True, null=True)
    text_answer = models.TextField(blank=True, null=True)
    
    # Grading
    marks_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) 
    is_correct = models.BooleanField(default=False)
    teacher_feedback = models.TextField(blank=True, null=True)
    auto_graded = models.BooleanField(default=False)
    manual_graded = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('attempt', 'question')
        indexes = [
            models.Index(fields=['attempt', 'question']),
        ]
        
    def __str__(self):
        if self.selected_option:
            return f"Answer: {self.selected_option.option_text[:30]}..."
        return f"Text Answer: {self.text_answer[:30] if self.text_answer else 'No answer'}..."
    
    def auto_grade(self):
        """Auto-grade multiple choice and true/false questions"""
        if self.question.question_type in [
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.TRUE_FALSE
        ]:
            if self.selected_option and self.selected_option.is_correct:
                self.marks_awarded = self.question.mark
                self.is_correct = True
            else:
                self.marks_awarded = 0
                self.is_correct = False
            self.auto_graded = True
    
    def clean(self):
        # Validate answer type matches question type
        if self.question.question_type in [Question.QuestionType.MULTIPLE_CHOICE, Question.QuestionType.TRUE_FALSE]:
            if not self.selected_option:
                
                pass
            elif self.selected_option.question != self.question:
                raise ValidationError("Selected option does not belong to this question")
            # Clear text answer for multiple choice
            self.text_answer = None
        else:
            # For text-based questions, clear selected option
            self.selected_option = None
    
    def save(self, *args, **kwargs):
        self.full_clean()
        self.auto_grade()
        super().save(*args, **kwargs)
