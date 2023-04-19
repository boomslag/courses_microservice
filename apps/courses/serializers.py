from apps.category.models import Category
from apps.category.serializers import CategorySerializer
from rest_framework import serializers


from .models import *


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sellers
        fields =[
            'author',
            "address",
            'polygon_address',
            # 'course',
        ]


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields =[
            'id',
            'position_id',
            "title",
            'file',
            'course',
        ]


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields =[
            'id',
            'position_id',
            "title",
            'file',
            'course',
        ]


class WhatLearntSerializer(serializers.ModelSerializer):
    id=serializers.CharField(source='position_id')
    class Meta:
        model= WhatLearnt
        fields = [
            "id",
            "position_id",
            "title",
        ]


class CoursesListSerializer(serializers.ModelSerializer):
    # best_seller=serializers.BooleanField(source='get_best_seller')
    thumbnail = serializers.ImageField(source='first_image')
    category=serializers.CharField(source='get_category_name')
    student_rating=serializers.IntegerField(source='get_rating')
    student_rating_no=serializers.IntegerField(source='get_no_rating')
    class Meta:
        model=Course
        fields=[
            "id",
            "token_id",
            "nft_address",
            "title",
            "thumbnail",
            "description",
            'short_description',
            "language",
            "best_seller",
            "published",
            'payment',
            'slug',
            'price',
            'compare_price',
            'discount_until',
            'discount',
            'student_rating',
            'student_rating_no',
            'category',
        ]



class CourseSerializer(serializers.ModelSerializer):
    total_lectures=serializers.IntegerField(source="get_total_lectures")
    videos=VideoSerializer(many=True)
    images=ImageSerializer(many=True)
    total_duration=serializers.CharField(source='total_course_length')
    student_rating=serializers.IntegerField(source='get_rating')
    student_rating_no=serializers.IntegerField(source='get_no_rating')
    category=CategorySerializer()
    sellers=SellerSerializer(many=True)
    class Meta:
        model=Course
        fields=[
            "id",
            "token_id",
            "nft_address",
            "author",
            "sellers",
            "title",
            "thumbnail",
            "description",
            "short_description",
            "sales_video",
            "published",
            "updated",
            "course_length",
            "language",
            "level",
            "taught",
            "best_seller",
            'status',
            "total_lectures",
            "total_duration",
            "category",
            'student_rating',
            'student_rating_no',
            'payment',
            'price',
            'stock',
            'compare_price',
            'discount_until',
            'discount',
            'keywords',
            'slug',
            'views',
            'students',
            'goals',
            'course_structure',
            'setup',
            'film',
            'curriculum',
            'captions',
            'accessibility',
            'landing_page',
            'pricing',
            'promotions',
            'allow_messages',
            'welcome_message',
            'congrats_message',
            'slug_changes',
            'progress',
            'can_delete',
            'banned',
            'videos',
            'images',
        ]



class CoursesManageListSerializer(serializers.ModelSerializer):
    # best_seller=serializers.BooleanField(source='get_best_seller')
    thumbnail=serializers.BooleanField(source='first_image')
    category=serializers.CharField(source='get_category_name')
    videos=VideoSerializer(many=True)
    images=ImageSerializer(many=True)
    student_rating=serializers.IntegerField(source='get_rating')
    student_rating_no=serializers.IntegerField(source='get_no_rating')
    class Meta:
        model=Course
        fields=[
            "id",
            "nft_address",
            "author",
            "title",
            "thumbnail",
            "description",
            'short_description',
            "language",
            "best_seller",
            "status",
            "published",
            'payment',
            'slug',
            'price',
            'stock',
            'student_rating',
            'student_rating_no',
            'compare_price',
            'discount_until',
            'discount',
            'category',
            'progress',
            'videos',
            'images',
        ]


class WhatLearntSerializer(serializers.ModelSerializer):
    class Meta:
        model= WhatLearnt
        fields = [
            "id",
            "position_id",
            "title",
        ]


class RequisiteSerializer(serializers.ModelSerializer):
    class Meta:
        model= Requisite
        fields = [
            "id",
            "position_id",
            "title",
        ]


class WhoIsForSerializer(serializers.ModelSerializer):
    class Meta:
        model= WhoIsFor
        fields = [
            "id",
            "position_id",
            "title",
        ]


class ResourceSerializer(serializers.ModelSerializer):
    # file=serializers.CharField(source='get_absolute_url')
    class Meta:
        model= Resource
        fields = [
            "title",
            "file",
            "url",
            "id"
        ]


class EpisodePaidSerializer(serializers.ModelSerializer):
    length=serializers.CharField(source='get_video_length_time')
    # file=serializers.CharField(source='get_absolute_url')
    resources=ResourceSerializer(many=True)
    # comments=CommentSerializer(many=True)
    class Meta:
        model = Episode
        fields = [
            'id',
            "number",
            "title",
            "file",
            "filename",
            "date",
            "resources",
            "content",
            "description",
            "section_uuid",
            'published',
            "length",
        ]


class CourseSectionPaidSerializer(serializers.ModelSerializer):
    episodes=EpisodePaidSerializer(many=True)
    total_duration=serializers.CharField(source='total_length')
    class Meta:
        model=Section
        fields=[
            'id',
            'title',
            'learning_objective',
            'number',
            'episodes',
            'user',
            'published',
            'course',
            'total_duration'
        ]




class EpisodeUnPaidSerializer(serializers.ModelSerializer):
    length=serializers.CharField(source='get_video_length_time')
    # file=serializers.CharField(source='get_absolute_url')
    # resources=ResourceSerializer(many=True)
    # comments=CommentSerializer(many=True)
    class Meta:
        model = Episode
        fields = [
            'id',
            "number",
            "title",
            "date",
            "description",
            "section_uuid",
            'published',
            "length",
        ]


class CourseSectionUnPaidSerializer(serializers.ModelSerializer):
    episodes=EpisodeUnPaidSerializer(many=True)
    total_duration=serializers.CharField(source='total_length')
    class Meta:
        model=Section
        fields=[
            'id',
            'title',
            'learning_objective',
            'number',
            'episodes',
            'user',
            'published',
            'course',
            'total_duration'
        ]



class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model=Question
        fields=[
            'id',
            'user',
        ]




class AnswerSerializer(serializers.ModelSerializer):
    # question=QuestionSerializer()
    likes=LikeSerializer(many=True)
    # dislikes=serializers.CharField(source='dislikes_count')
    class Meta:
        model=Answer
        fields=[
            'id',
            'user',
            'body',
            'created_date',
            'update_date',
            'is_accepted_answer',
            'likes',
            # 'dislikes',
        ]


class QuestionSerializer(serializers.ModelSerializer):
    episode=EpisodePaidSerializer()
    likes=LikeSerializer(many=True)
    count=serializers.CharField(source='likes_count')
    dislikes=serializers.CharField(source='dislikes_count')
    answers_count=serializers.CharField(source='get_answers_count')
    # answers=serializers.CharField(source='get_answers')
    correct_answer = AnswerSerializer()
    class Meta:
        model=Question
        fields=[
            'id',
            'user',
            'title',
            'body',
            'created_date',
            'correct_answer',
            'update_date',
            'has_accepted_answer',
            'episode',
            'likes',
            'count',
            'dislikes',
            'answers_count',
        ]


class PaidSerializer(serializers.ModelSerializer):
    courses=CoursesListSerializer(many=True)
    class Meta:
        model=Paid
        fields=[
            'id',
            'user',
            'courses',
            'date_created',
        ]
