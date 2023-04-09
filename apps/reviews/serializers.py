from rest_framework import serializers
from .models import *
from apps.courses.serializers import CoursesListSerializer

class CourseReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'user',
            'rating',
            'comment',
            'date_created',
        ]