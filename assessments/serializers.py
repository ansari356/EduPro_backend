from rest_framework import serializers
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import (
    Assessment, Question, QuestionOption, 
    StudentAssessmentAttempt, StudentAnswer
)
from course.models import Lesson, CourseModule
from userAuth.models import User

# Question Option Serializers
class QuestionOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['question', 'option_text', 'is_correct', 'order']
        
    def validate(self, attrs):
        if not attrs.get('option_text') or attrs.get('option_text').strip() == "":
            raise serializers.ValidationError({"option_text": "Option text cannot be empty."})

        question = attrs.get('question')
        if not question or not Question.objects.filter(id=question.id).exists():
            raise serializers.ValidationError({"question": "You must provide a valid question."})
        
        if attrs.get("is_correct") is None:
            raise serializers.ValidationError({"is_correct": "You must specify if this option is correct."})
         
        return attrs        

class QuestionOptionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['option_text', 'is_correct', 'order']

    def validate(self, attrs):
        if 'option_text' in attrs and attrs['option_text'].strip() == "":
            raise serializers.ValidationError({"option_text": "Option text cannot be empty."})

        if 'is_correct' in attrs and attrs.get("is_correct") is None:
            raise serializers.ValidationError({"is_correct": "You must specify if this option is correct."})

        return attrs  

class QuestionOptionRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'question', 'option_text','order']
        read_only_fields = fields
        
class QuestionOptionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text','order']
        read_only_fields = fields

# Question Serializers
class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['assessment', 'question_text', 'question_type', 'mark', 'order', 'explanation', 'image']

    def validate(self, attrs):
        if not attrs.get('question_text') or attrs.get('question_text').strip() == "":
            raise serializers.ValidationError({"question_text": "Question text cannot be empty."})

        assessment = attrs.get('assessment')
        if not assessment or not Assessment.objects.filter(id=assessment.id).exists():
            raise serializers.ValidationError({"assessment": "You must provide a valid assessment."})

        if attrs.get('question_type') not in dict(Question.QuestionType.choices):
            raise serializers.ValidationError({
                "question_type": "Invalid question type.",
                "valid_types": list(Question.QuestionType.values)
            })

        if attrs.get('mark') is None or attrs['mark'] <= 0:
            raise serializers.ValidationError({"mark": "Marks must be greater than 0."})

        return attrs

class QuestionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'mark', 'order', 'explanation', 'image']

    def validate(self, attrs):
        if 'question_text' in attrs and attrs['question_text'].strip() == "":
            raise serializers.ValidationError({"question_text": "Question text cannot be empty."})

        if 'question_type' in attrs and attrs.get('question_type') not in dict(Question.QuestionType.choices):
            raise serializers.ValidationError({
                "question_type": "Invalid question type.",
                "valid_types": list(Question.QuestionType.values)
            })

        if 'mark' in attrs and attrs['mark'] <= 0:
            raise serializers.ValidationError({"mark": "Marks must be greater than 0."})

        return attrs

class QuestionRetrieveSerializer(serializers.ModelSerializer):
    options = QuestionOptionListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'mark', 'order', 'explanation', 'image', 'options']

class QuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'mark', 'order']
        read_only_fields = fields

# Assessment Serializers
class AssessmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            'title', 'description', 'assessment_type', 'lesson', 'module', 'course',
            'is_published', 'is_timed', 'time_limit', 'max_attempts', 'passing_score',
            'available_from', 'available_until'
        ]

    def validate_title(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_passing_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Passing score must be between 0 and 100.")
        return value

    def validate_max_attempts(self, value):
        if value < 1:
            raise serializers.ValidationError("Max attempts must be at least 1.")
        return value

    def validate(self, attrs):
        assessment_type = attrs.get('assessment_type')
        lesson = attrs.get('lesson')
        module = attrs.get('module')
        course = attrs.get('course')
        teacher = self.context['request'].user.teacher_profile

        if assessment_type == Assessment.AssessmentType.QUIZ:
            if not lesson:
                raise serializers.ValidationError("Quiz must be linked to a lesson.")
            if module or course:
                raise serializers.ValidationError("Quiz can only be linked to a lesson.")
            if lesson.module.course.teacher != teacher:
                raise serializers.ValidationError("You don't own this lesson.")
                
        elif assessment_type == Assessment.AssessmentType.ASSIGNMENT:
            if not module:
                raise serializers.ValidationError("Assignment must be linked to a module.")
            if lesson or course:
                raise serializers.ValidationError("Assignment can only be linked to a module.")
            if module.course.teacher != teacher:
                raise serializers.ValidationError("You don't own this module.")
                
        elif assessment_type == Assessment.AssessmentType.COURSE_EXAM:
            if not course:
                raise serializers.ValidationError("Course exam must be linked to a course.")
            if lesson or module:
                raise serializers.ValidationError("Course exam can only be linked to a course.")
            if course.teacher != teacher:
                raise serializers.ValidationError("You don't own this course.")

        if attrs.get('is_timed'):
            if not attrs.get('time_limit') or attrs.get('time_limit') <= 0:
                raise serializers.ValidationError("Timed assessments must have a time_limit greater than 0.")
            
        available_from = attrs.get('available_from')
        available_until = attrs.get('available_until')
        if available_from and available_until and available_until <= available_from:
            raise serializers.ValidationError("Available until must be after available from.")

        return attrs

    def create(self, validated_data):
        teacher = self.context['request'].user.teacher_profile
        return Assessment.objects.create(teacher=teacher, **validated_data)

class AssessmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            'title', 'description', 'is_published', 'is_timed', 'time_limit',
            'max_attempts', 'passing_score', 'available_from', 'available_until'
        ]

    def validate_title(self, value):
        if value is not None and value.strip() == "":
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip() if value else value

    def validate_passing_score(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Passing score must be between 0 and 100.")
        return value

    def validate_max_attempts(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Max attempts must be at least 1.")
        return value

    def validate(self, attrs):
        instance = self.instance
        
        is_timed = attrs.get('is_timed', instance.is_timed if instance else False)
        time_limit = attrs.get('time_limit', instance.time_limit if instance else None)
        
        if is_timed and (not time_limit or time_limit <= 0):
            raise serializers.ValidationError("Timed assessments must have a time limit greater than 0.")

        available_from = attrs.get('available_from', instance.available_from if instance else None)
        available_until = attrs.get('available_until', instance.available_until if instance else None)
        
        if available_from and available_until and available_until <= available_from:
            raise serializers.ValidationError("Available until must be after available from.")

        return attrs

class AssessmentListSerializer(serializers.ModelSerializer):
    related_to = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'assessment_type', 'related_to', 'is_published',
            'is_timed', 'time_limit', 'max_attempts', 'total_questions',
            'total_marks', 'available_from', 'available_until', 'is_available',
            'created_at'
        ]

    def get_related_to(self, obj):
        if obj.lesson:
            return f"Lesson: {obj.lesson.title}"
        elif obj.module:
            return f"Module: {obj.module.title}"
        elif obj.course:
            return f"Course: {obj.course.title}"
        return "No relation"

    def get_is_available(self, obj):
        return obj.is_available()
     
class AssessmentRetrieveSerializer(serializers.ModelSerializer):
    questions = QuestionRetrieveSerializer(many=True, read_only=True)
    related_to = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'assessment_type', 'related_to',
            'is_published', 'is_timed', 'time_limit', 'max_attempts',
            'passing_score', 'total_questions', 'total_marks',
            'available_from', 'available_until', 'is_available',
            'created_at', 'questions'
        ]

        read_only_fields=fields
        
    def get_related_to(self, obj):
        if obj.lesson:
            return {"type": "lesson", "id": str(obj.lesson.id), "title": obj.lesson.title}
        elif obj.module:
            return {"type": "module", "id": str(obj.module.id), "title": obj.module.title}
        elif obj.course:
            return {"type": "course", "id": str(obj.course.id), "title": obj.course.title}
        return None

    def get_is_available(self, obj):
        return obj.is_available()  

# Student Assessment Attempt Serializers
class StudentAssessmentAttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAssessmentAttempt
        fields = ['assessment']

    def validate_assessment(self, value):
        student = self.context['request'].user.student_profile
        now = timezone.now()

        if not value.is_published:
            raise serializers.ValidationError("This assessment is not published yet.")

        if not value.is_available(): 
            if value.available_from and now < value.available_from:
                raise serializers.ValidationError("The assessment has not started yet.")
            elif value.available_until and now > value.available_until:
                raise serializers.ValidationError("The assessment has already ended.")
            else:
                raise serializers.ValidationError("The assessment is not available.")

        previous_attempts = StudentAssessmentAttempt.objects.filter(
            student=student,
            assessment=value
        ).count()

        if previous_attempts >= value.max_attempts:
            raise serializers.ValidationError(
                f"You have reached the maximum number of attempts ({value.max_attempts})."
            )

        in_progress = StudentAssessmentAttempt.objects.filter(
            student=student,
            assessment=value,
            status=StudentAssessmentAttempt.AttemptStatus.IN_PROGRESS
        ).exists()

        if in_progress:
            raise serializers.ValidationError("You already have an attempt in progress for this assessment.")

        return value

    def create(self, validated_data):
        student = self.context['request'].user.student_profile
        assessment = validated_data['assessment']
        
        previous_attempts = StudentAssessmentAttempt.objects.filter(
            student=student,
            assessment=assessment
        ).count()

        attempt = StudentAssessmentAttempt.objects.create(
            student=student,
            assessment=assessment,
            attempt_number=previous_attempts + 1
        )

        # Create empty answers for all questions
        questions = assessment.questions.all()
        student_answers = [
            StudentAnswer(attempt=attempt, question=question)
            for question in questions
        ]
        StudentAnswer.objects.bulk_create(student_answers)

        return attempt

# Handle answer in submitting
class AnswerSubmitSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()  
    selected_option = serializers.UUIDField(required=False, allow_null=True)  
    text_answer = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        try:
            question = Question.objects.get(id=attrs["question_id"])
        except Question.DoesNotExist:
            raise serializers.ValidationError({"question_id": "Invalid question ID."})
        
        selected_option_id = attrs.get("selected_option")
        text_answer = attrs.get("text_answer")

        # Multiple choice / true-false
        if question.question_type in [Question.QuestionType.MULTIPLE_CHOICE, Question.QuestionType.TRUE_FALSE]:
            if selected_option_id:
                try:
                    option = QuestionOption.objects.get(id=selected_option_id)
                    if option.question != question:
                        raise serializers.ValidationError({"selected_option": "Selected option does not belong to this question."})
                except QuestionOption.DoesNotExist:
                    raise serializers.ValidationError({"selected_option": "Invalid option ID."})
            # Clear text answer for multiple choice
            attrs["text_answer"] = None

        # Short answer / essay / fill blank
        elif question.question_type in [Question.QuestionType.SHORT_ANSWER, Question.QuestionType.ESSAY, Question.QuestionType.FILL_BLANK]:
            # Clear selected option for text questions
            attrs["selected_option"] = None

        attrs["question"] = question
        return attrs

# Student submit assessment   
class StudentAssessmentAttemptSubmitSerializer(serializers.Serializer):
    answers = AnswerSubmitSerializer(many=True)

    def update(self, instance, validated_data):
        now = timezone.now()

        answers_data = validated_data.get("answers", [])
        answers_map = {str(ans.question_id): ans for ans in instance.answers.all()}

        for ans_data in answers_data:
            question_id = str(ans_data["question_id"])
            student_answer = answers_map.get(question_id)
            if not student_answer:
                raise serializers.ValidationError(f"Invalid question ID {question_id}.")

            student_answer.selected_option_id = ans_data.get("selected_option")
            student_answer.text_answer = ans_data.get("text_answer")

        # Bulk update
        StudentAnswer.objects.bulk_update(
            answers_map.values(), 
            ["selected_option", "text_answer"]
        )

        # Auto-grade
        for answer in answers_map.values():
            answer.auto_grade()
            answer.save()

        # Mark as submitted
        instance.status = StudentAssessmentAttempt.AttemptStatus.SUBMITTED
        instance.ended_at = now
        if instance.started_at:
            instance.time_taken = int((now - instance.started_at).total_seconds())

        instance.calculate_final_score()
        instance.save()

        return instance

# Student Answer Serializers
class StudentAnswerRetrieveSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='question.question_text', read_only=True)
    selected_option_text = serializers.CharField(source='selected_option.option_text', read_only=True)
    
    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'question', 'selected_option_text',
            'text_answer', 'marks_awarded', 'is_correct', 'teacher_feedback',
            'auto_graded'
        ]
        read_only_fields=fields

# Student Assessment Detail (for student to see their attempt details)
class StudentAssessmentAttemptDetailSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    answers = StudentAnswerRetrieveSerializer(many=True, read_only=True)
    
    class Meta:
        model = StudentAssessmentAttempt
        fields = [
            'id', 'assessment_title', 'attempt_number', 'started_at','status',
            'ended_at', 'time_taken', 'score', 'percentage', 'is_passed',
            'teacher_feedback', 'answers'
        ]

# Student Assessment List (for student to see their attempts)
class StudentAssessmentAttemptListSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source='assessment.title', read_only=True)
    assessment_type = serializers.CharField(source='assessment.assessment_type', read_only=True)
    student_name=serializers.CharField(source='student.user.username')
    related_to = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentAssessmentAttempt
        fields = [
            'id', 'assessment_title','student_name', 'assessment_type', 'related_to',
            'attempt_number', 'status', 'started_at', 'ended_at',
            'time_taken', 'score', 'percentage', 'is_passed'
        ]

    def get_related_to(self, obj):
        assessment = obj.assessment
        if assessment.lesson:
            return f"Lesson: {assessment.lesson.title}"
        elif assessment.module:
            return f"Module: {assessment.module.title}"
        elif assessment.course:
            return f"Course: {assessment.course.title}"
        return "Unknown"



# Teacher Grading Serializers
class TeacherAnswerGradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source='attempt.student.user.get_full_name', 
        read_only=True
    )
    question_text = serializers.CharField(
        source='question.question_text', 
        read_only=True
    )
    question_mark = serializers.DecimalField(
        source='question.mark', 
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    question_type = serializers.CharField(
        source='question.question_type', 
        read_only=True
    )
    attempt_id = serializers.UUIDField(
        source='attempt.id', 
        read_only=True
    )
    assessment_title = serializers.CharField(
        source='question.assessment.title', 
        read_only=True
    )

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'student_name', 'question_text', 'question_mark', 'question_type',
            'text_answer', 'marks_awarded', 'teacher_feedback', 'is_correct',
            'attempt_id', 'assessment_title'
        ]
        read_only_fields = [
            'id', 'student_name', 'question_text', 'question_mark', 'question_type',
            'text_answer', 'attempt_id', 'assessment_title'
        ]

    def validate_marks_awarded(self, value):
        if value < 0:
            raise serializers.ValidationError("Marks cannot be negative.")

        if self.instance and value > self.instance.question.mark:
            raise serializers.ValidationError(
                f"Marks cannot exceed question maximum ({self.instance.question.mark})."
            )
        return value

    def update(self, instance, validated_data):
        teacher = self.context['request'].user.teacher_profile
        
        # Verify teacher permission
        if instance.question.assessment.teacher != teacher:
            raise serializers.ValidationError("You don't have permission to grade this answer.")
        
        # Update grading fields
        instance.marks_awarded = validated_data.get('marks_awarded', instance.marks_awarded)
        instance.teacher_feedback = validated_data.get('teacher_feedback', instance.teacher_feedback)
        instance.is_correct = validated_data.get('is_correct', instance.is_correct)

        # Mark as manually graded
        instance.auto_graded = False
        instance.manual_graded = True

        instance.save()

        # Recalculate attempt score after grading
        instance.attempt.calculate_final_score()

        return instance
