from django.shortcuts import get_object_or_404
from rest_framework_api.views import BaseAPIView, StandardAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from .models import Certificate
from .serializers import CertificateSerializer
from apps.courses.models import Course
import jwt
import requests
from django.conf import settings
secret_key = settings.SECRET_KEY

auth_ms_url=settings.AUTH_MS_URL

def get_course_instructor(courseId):
    course = Course.objects.get(id=courseId)
    user_response = requests.get(f'{auth_ms_url}/api/users/get/' + str(course.author) + '/').json()
    profile_response = requests.get(f'{auth_ms_url}/api/users/get/profile/' + str(course.author) + '/').json()
    user = user_response.get('results')
    profile = profile_response.get('results')
    return user,profile


def validate_token(request):
    token = request.META.get('HTTP_AUTHORIZATION').split()[1]

    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return Response({"error": "Token has expired."}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.DecodeError:
        return Response({"error": "Token is invalid."}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        return Response({"error": "An error occurred while decoding the token."}, status=status.HTTP_401_UNAUTHORIZED)

    return payload

# Create your views here.
class GetCertificateView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self,request, course_uuid,*args, **kwargs):
        payload = validate_token(request)
        user = payload['user_id']
        course=Course.objects.get(id=course_uuid)

        try:
            certificate = Certificate.objects.get(course=course,user=user)
            serializer = CertificateSerializer(certificate)
            return self.send_response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response({'error':'Not found'},status=status.HTTP_404_NOT_FOUND)


class CreateCertificateView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def post(self, request, format=None):
        payload = validate_token(request)
        user = payload['user_id']
        data= self.request.data

        author,profile = get_course_instructor(data['courseUUID'])

        course=Course.objects.get(id=data['courseUUID'])

        certificate = Certificate.objects.create(
            instructor=author.get('username'),
            instructor_first_name=author.get('first_name'),
            instructor_last_name=author.get('last_name'),
            user=user,
            course=course,
        )
        
        serializer = CertificateSerializer(certificate).data

        return self.send_response(serializer, status=status.HTTP_200_OK)