import json, os, django
from confluent_kafka import Consumer
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.apps import apps
from django.core.cache import cache

Course = apps.get_model('courses', 'Course')
Paid = apps.get_model('courses', 'Paid')
PaidItem = apps.get_model('courses', 'PaidItem')  # Add this import
Viewed = apps.get_model('courses', 'Viewed')
ViewedItem = apps.get_model('courses', 'ViewedItem')  # Add this import
WishList = apps.get_model('courses', 'WishList')

from apps.courses.serializers import CoursesListSerializer
from core.producer import producer

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            # if obj is uuid, we simply return the value of uuid
            return str(obj)
        return json.JSONEncoder.default(self, obj)

consumer1 = Consumer({
    'bootstrap.servers': os.environ.get('KAFKA_BOOTSTRAP_SERVER'),
    'security.protocol': os.environ.get('KAFKA_SECURITY_PROTOCOL'),
    'sasl.username': os.environ.get('KAFKA_USERNAME'),
    'sasl.password': os.environ.get('KAFKA_PASSWORD'),
    'sasl.mechanism': 'PLAIN',
    'group.id': os.environ.get('KAFKA_GROUP'),
    'auto.offset.reset': 'earliest'
})
consumer1.subscribe([os.environ.get('KAFKA_TOPIC')])


consumer2 = Consumer({
    'bootstrap.servers': os.environ.get('KAFKA_BOOTSTRAP_SERVER'),
    'security.protocol': os.environ.get('KAFKA_SECURITY_PROTOCOL'),
    'sasl.username': os.environ.get('KAFKA_USERNAME'),
    'sasl.password': os.environ.get('KAFKA_PASSWORD'),
    'sasl.mechanism': 'PLAIN',
    'group.id': os.environ.get('KAFKA_GROUP_2'),
    'auto.offset.reset': 'earliest'
})
consumer2.subscribe([os.environ.get('KAFKA_TOPIC_2')])

consumer3 = Consumer({
    'bootstrap.servers': os.environ.get('KAFKA_BOOTSTRAP_SERVER'),
    'security.protocol': os.environ.get('KAFKA_SECURITY_PROTOCOL'),
    'sasl.username': os.environ.get('KAFKA_USERNAME'),
    'sasl.password': os.environ.get('KAFKA_PASSWORD'),
    'sasl.mechanism': 'PLAIN',
    'group.id': os.environ.get('KAFKA_GROUP_3'),
    'auto.offset.reset': 'earliest'
})
consumer3.subscribe([os.environ.get('KAFKA_TOPIC_3')])

while True:
    msg1 = consumer1.poll(1.0)
    msg2 = consumer2.poll(1.0)
    msg3 = consumer3.poll(1.0)

    if msg1 is not None and not msg1.error():
        topic1 = msg1.topic()
        value1 = msg1.value()

        if topic1 == 'courses_request':
            if msg1.key() == b'courses_list':
                # Get user_id list
                courses_list = Course.objects.values(
                    'id',
                    'title',
                    'price',
                    'purchases',
                    'students',
                )
                for course in courses_list:
                    course['price'] = str(course['price'])
                # Serialize user_id list
                courses_list_data = json.dumps(list(courses_list),cls=UUIDEncoder)
                print(courses_list_data)
                # producer.produce('users_response', value=user_data)
                producer.produce(
                    'courses_response',
                    key='courses_list',
                    value=courses_list_data
                )

        if topic1 == 'course_request':
            if msg1.key() == b'get_course':
                # Get the course id from the message value
                course_id = msg1.value()
                # Get the course from the database using the course_id
                course = Course.objects.get(id=course_id)
                # Produce the response to the topic 'courses_response'
                producer.produce(
                    'course_response',
                    key='get_course',
                    value=course.to_dict()
                )

    if msg2 is not None and not msg2.error():
        topic2 = msg2.topic()
        value2 = msg2.value()

        if topic2 == 'user_registered':
            if msg2.key() == b'create_user':
                user_data = json.loads(value2)
                user_id = user_data['id']
                # create a cart for the user with the user_id
                paid_library, created = Paid.objects.get_or_create(user=user_id)
                if created:
                    paid_library.save()
                viewed_library, created = Viewed.objects.get_or_create(user=user_id)
                if created:
                    viewed_library.save()
                wishlist, created = WishList.objects.get_or_create(user=user_id)
                if created:
                    wishlist.save()
    
    if msg3 is not None and not msg3.error():
        topic3 = msg3.topic()
        value3 = msg3.value()

        if topic3 == 'nft_minted':
            if msg3.key() == b'course_bought':
                course_data = json.loads(value3)
                user_id = course_data['user_id']
                course_uuid = course_data['course']

                print(f'User Purchased this course {course_uuid}')

                # # Get the user's Paid library
                paid_library, created = Paid.objects.get_or_create(user=user_id)

                # # Add the purchased course to the user's Paid library
                course = Course.objects.get(id=course_uuid)
                course.sold += 1
                course.students += 1
                course.purchases += 1
                course.income_earned += course.price
                course.totalRevenue += course.income_earned
                course.save()

                paid_item = PaidItem(course=course)
                paid_item.save()
                paid_library.courses.add(paid_item)
                # Invalidate cache for the user by deleting cache keys associated with that user
                cache_keys_to_delete = cache.keys(f'paid_courses_{user_id}_*')
                cache.delete_many(cache_keys_to_delete)


consumer1.close()
consumer2.close()
consumer3.close()