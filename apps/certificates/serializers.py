from rest_framework import serializers
# from apps.courses.serializers import CoursesListSerializer

from .models import *

class CertificateSerializer(serializers.ModelSerializer):
    # course = CoursesListSerializer()
    class Meta:
        model = Certificate
        fields=[
            'id',
            'instructor',
            'instructor_first_name',
            'instructor_last_name',
            'user',
            'course',
            'date',
        ]


