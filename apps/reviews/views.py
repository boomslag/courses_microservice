# from ..product.models import Product
from apps.reviews.pagination import LargeSetPagination
from rest_framework.views import APIView
from rest_framework_api.views import StandardAPIView
from rest_framework.response import Response
from rest_framework import permissions
from uuid import UUID
from rest_framework import  status
from apps.courses.models import Course, Rate
from apps.reviews.serializers import CourseReviewSerializer

from django.core.exceptions import ObjectDoesNotExist
# from apps.classroom.models import CourseClassRoom, Rate as ClassRoomRate
from .models import Review
from django.shortcuts import get_object_or_404
import json
import jwt
from django.conf import settings
secret_key = settings.SECRET_KEY


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


def is_valid_uuid(uuid):
    try:
        UUID(uuid, version=4)
        return True
    except ValueError:
        return False


def get_course_by_identifier(identifier):
    if is_valid_uuid(identifier):
        return Course.objects.get(id=identifier)
    elif identifier.startswith("0x"):
        return Course.objects.get(nft_address=identifier)
    else:
        return Course.objects.get(slug=identifier)
    

class GetCourseReviewsView(StandardAPIView):
    def get(self, request, identifier, *args, **kwargs):
        # Get the course using the identifier (UUID, slug, or nft_address)
        course = get_course_by_identifier(identifier)
        rating_filter = request.GET.get('rating', None)
        
        if rating_filter is not None and rating_filter != "undefined":
            reviews = Review.objects.filter(course=course, rating=rating_filter)
        else:
            reviews = Review.objects.filter(course=course)

        review_counts = []
        total_rating = 0
        for rating in range(1, 6):
            count = reviews.filter(rating=rating).count()
            total_rating += rating * count
            review_counts.append({"rating": rating, "count": count})

        review_average = float(total_rating) / float(reviews.count()) if reviews.count() > 0 else 0
        
        review_data = {
            "totalCount": reviews.count(),
            "counts": review_counts,
            "average": review_average
        }

        return self.paginate_response_with_extra(request, CourseReviewSerializer(reviews, many=True).data, review_data )


class GetTeacherCourseReviewsView(APIView):
    def get(self, request, format=None):

        data = self.request.data
        user = self.request.user
        
        try:
            courses = Course.objects.filter(author=user).order_by('-created')

            results = []

            for course in courses:
                if Review.objects.filter(course=course).exists():
                    reviews = Review.objects.order_by(
                        '-date_created'
                    ).filter(course=course)

                    for review in reviews:
                        item = {}

                        item['id'] = review.id
                        item['rating'] = review.rating
                        item['comment'] = review.comment
                        item['date_created'] = review.date_created
                        item['user'] = review.user.username
                        item['verified'] = review.user.verified
                        item['thumbnail'] = review.user.picture.url

                        results.append(item)

            paginator = LargeSetPagination()
            review_results = paginator.paginate_queryset(results, request)

            return paginator.get_paginated_response({'reviews':review_results})
        except:
            return Response(
                {'error': 'Something went wrong when retrieving reviews'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetReviewView(StandardAPIView):
    def get(self, request, id, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        course = Course.objects.get(id=id)
        try:
            review = Review.objects.get(user=user_id, course=course)
            return self.send_response(CourseReviewSerializer(review).data)
        except ObjectDoesNotExist:
            return self.send_response(False)
        

class CreateReviewView(StandardAPIView):
    permission_classes=(permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        data = self.request.data

        course_uuid = data['courseUUID']

        try:
            rating = float(data['rating'])
        except:
            return Response(
                {'error': 'Rating must be a decimal value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            comment = str(data['content'])
        except:
            return Response(
                {'error': 'Must pass a comment when creating review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not Course.objects.filter(id=course_uuid).exists():
            return Response(
                {'error': 'This course does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        course = Course.objects.get(id=course_uuid)
        
        if Review.objects.filter(user=user_id, course=course).exists():
            return Response(
                {'error': 'Review for this course already created'},
                status=status.HTTP_409_CONFLICT
            )
        
        review = Review(
            user=user_id,
            course=course,
            rating=rating,
            comment=comment
        )
        review.save()

        rate = Rate.objects.create(rate_number=rating, user=user_id)
        course.rating.add(rate)

        ratings=course.rating.all()
        rate=0
        for rating in ratings:
            rate+=rating.rate_number
        try:
            rate/=len(ratings)
        except ZeroDivisionError:
            rate=0

        course.student_rating = rate
        course.save()

        return self.send_response(CourseReviewSerializer(review).data)



class UpdateReviewView(StandardAPIView):
    permission_classes=(permissions.AllowAny,)
    def put(self, request, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        data = self.request.data

        course_uuid = data['courseUUID']

        try:
            rating = float(data['rating'])
        except:
            return Response(
                {'error': 'Rating must be a decimal value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            comment = str(data['content'])
        except:
            return Response(
                {'error': 'Must pass a comment when updating review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not Course.objects.filter(id=course_uuid).exists():
            return Response(
                {'error': 'This course does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        course = Course.objects.get(id=course_uuid)
        
        if not Review.objects.filter(user=user_id, course=course).exists():
            return Response(
                {'error': 'Review does not exist'},
                status=status.HTTP_409_CONFLICT
            )
        
        review = Review.objects.get(user=user_id, course=course)
        review.rating = rating
        review.comment = comment
        review.save()

        # Find the associated Rate object and update it
        rate = Rate.objects.get(user=user_id, id__in=course.rating.all())
        rate.rate_number = rating
        rate.save()

        ratings = course.rating.all()
        rate = 0
        for rating in ratings:
            rate += rating.rate_number
        try:
            rate /= len(ratings)
        except ZeroDivisionError:
            rate = 0

        course.student_rating = rate
        course.save()

        return self.send_response(CourseReviewSerializer(review).data)


class UpdateCourseReviewView(APIView):
    def post(self, request, format=None):
        data = self.request.data
        user = self.request.user

        course_uuid = data['course_uuid']

        try:
            rating = float(data['review_rating'])
        except:
            return Response(
                {'error': 'Rating must be a decimal value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            comment = str(data['review_edit_body'])
        except:
            return Response(
                {'error': 'Must pass a comment when creating review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            review_id = str(data['review_id'])
        except:
            return Response(
                {'error': 'Must pass a comment when creating review'},
                status=status.HTTP_400_BAD_REQUEST
            )

        review = Review.objects.get(id=review_id)
        
        review.rating = rating
        review.comment = comment
        review.save()

        course=Course.objects.get(course_uuid=course_uuid)

        ratings=course.rating.all()
        rate=0
        for rating in ratings:
            rate+=rating.rate_number
        try:
            rate/=len(ratings)
        except ZeroDivisionError:
            rate=0

        course.student_rating = rate
        course.save()

        rating = course.rating.all()

        result = {}
        results = []
        rating_list=[]
        star_list_1 = []
        star_list_2 = []
        star_list_3 = []
        star_list_4 = []
        star_list_5 = []

        def Average(lst):
            return sum(lst) / len(lst)

        if Review.objects.filter(user=user, course=course).exists():
            result['id'] = review.id
            result['rating'] = review.rating
            result['comment'] = review.comment
            result['date_created'] = review.date_created
            result['user'] = review.user.username
            result['verified'] = review.user.verified
            result['thumbnail'] = review.user.picture.url

            reviews = Review.objects.order_by('-date_created').filter(
                course=course
            )

            for review in reviews:
                item = {}

                item['id'] = review.id
                item['rating'] = review.rating
                item['comment'] = review.comment
                item['date_created'] = review.date_created
                item['user'] = review.user.username
                item['verified'] = review.user.verified
                item['thumbnail'] = review.user.picture.url

                if(review.rating==1):
                    star_list_1.append(review.rating)
                if(review.rating==2):
                    star_list_2.append(review.rating)
                if(review.rating==3):
                    star_list_3.append(review.rating)
                if(review.rating==4):
                    star_list_4.append(review.rating)
                if(review.rating==5):
                    star_list_5.append(review.rating)

                results.append(item)
                rating_list.append(review.rating)
            average = Average(rating_list)

        return Response(
            {'review': result, 'reviews': results,'average_rating':average,
                'star_rating_count_1':len(star_list_1),
                'star_rating_count_2':len(star_list_2),
                'star_rating_count_3':len(star_list_3),
                'star_rating_count_4':len(star_list_4),
                'star_rating_count_5':len(star_list_5),},
            status=status.HTTP_201_CREATED
        )


class DeleteCourseReviewView(APIView):
    def delete(self, request, course_uuid, format=None):
        data = self.request.data
        user = self.request.user

        try:
            if not Course.objects.filter(course_uuid=course_uuid).exists():
                return Response(
                    {'error': 'This course does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )

            course = Course.objects.get(course_uuid=course_uuid)

            results = []

            if Review.objects.filter(user=user, course=course).exists():
                Review.objects.filter(user=user, course=course).delete()

                reviews = Review.objects.order_by('-date_created').filter(
                    course=course
                )

                for review in reviews:
                    item = {}

                    item['id'] = review.id
                    item['rating'] = review.rating
                    item['comment'] = review.comment
                    item['date_created'] = review.date_created
                    item['user'] = review.user.first_name

                    results.append(item)

                return Response(
                    {'reviews': results},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Review for this product does not exist'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except:
            return Response(
                {'error': 'Something went wrong when deleting product review'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FilterCourseReviewsView(APIView):
    def get(self, request, course_uuid, format=None):

        if not Course.objects.filter(course_uuid=course_uuid).exists():
            return Response(
                {'error': 'This course does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        course = Course.objects.get(course_uuid=course_uuid)

        rating = request.query_params.get('rating')

        try:
            rating = float(rating)
        except:
            return Response(
                {'error': 'Rating must be a decimal value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            if not rating:
                rating = 5.0
            elif rating > 5.0:
                rating = 5.0
            elif rating < 0.5:
                rating = 0.5

            results = []

            if Review.objects.filter(course=course).exists():
                if rating == 0.5:
                    reviews = Review.objects.order_by('-date_created').filter(
                        rating=rating, course=course
                    )
                else:
                    reviews = Review.objects.order_by('-date_created').filter(
                        rating__lte=rating,
                        course=course
                    ).filter(
                        rating__gte=(rating - 0.5),
                        course=course
                    )

                paginator = LargeSetPagination()
                results = paginator.paginate_queryset(reviews, request)
                serializer = CourseReviewSerializer(results, many=True)

                results_length = len(reviews)

            return Response(
                {
                    'reviews': serializer.data,
                    'length':results_length
                },
                status=status.HTTP_200_OK
            )
        except:
            return Response(
                {'error': 'Something went wrong when filtering reviews for product'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

