from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import get_object_or_404
from slugify import slugify
from core.producer import producer
from random import randint
from rest_framework_api.views import StandardAPIView
from django.http import Http404
from apps.courses.permissions import AuthorPermission, IsProductAuthorOrReadOnly, IsProductUserOrReadOnly
from apps.category.models import Category
from django.db.models import Count
from base64 import b64decode
from django.core.files.base import ContentFile
from .serializers import *
from .models import *
from base64 import b64decode
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .pagination import SmallSetPagination, MediumSetPagination, LargeSetPagination
import re
from decimal import Decimal
from django.core.validators import validate_slug
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponseBadRequest
from django.db.models.query_utils import Q
from django.db.models import F
from django.db.models import Sum, F
from core.producer import producer
import requests
import json
from html.parser import HTMLParser
import jwt
from django.conf import settings
secret_key = settings.SECRET_KEY
from uuid import UUID
from django.http import JsonResponse
import rsa
from django.db.models import Case, When, Value, IntegerField
import tempfile
import base64
import os
from web3 import Web3
infura_url=settings.INFURA_URL
web3 = Web3(Web3.HTTPProvider(infura_url))
from asgiref.sync import sync_to_async,async_to_sync

courses_ms_url=settings.COURSES_MS_URL
product_ms_url=settings.PRODUCTS_MS_URL
coupons_ms_url=settings.COUPONS_MS_URL
auth_ms_url=settings.AUTH_MS_URL
cryptography_ms_url=settings.CRYPTOGRAPHY_MS_URL

POLYGONSCAN_API_KEY=settings.POLYGONSCAN_API_KEY
polygon_url=settings.POLYGON_RPC
DEBUG=settings.DEBUG
polygon_web3 = Web3(Web3.HTTPProvider(polygon_url))

# json_path = os.path.join(settings.BASE_DIR, 'apps/wallet/contracts/PraediumToken.sol/PraediumToken.json')
# with open(json_path) as f:
#     json_data = json.load(f)
#     abi = json_data["abi"]


def get_polygon_contract_abi(address):
    url = f'https://api-testnet.polygonscan.com/api?module=contract&action=getabi&address={address}&apikey={POLYGONSCAN_API_KEY}'
    # if DEBUG:
    # else:
    #     url = f'https://api.polygonscan.com/api?module=contract&action=getabi&address={address}&apikey={POLYGONSCAN_API_KEY}'

    response = requests.get(url)
    data = response.json()
    if data['status'] == '1':
        return data['result']
    else:
        return None
    
def decrypt_polygon_private_key(address):
    # Get wallet information from the backend API
    wallet_request = requests.get(f'{auth_ms_url}/api/wallets/get/?address={address}').json()
    base64_encoded_private_key_string = wallet_request['results']['polygon_private_key']
    
    # Get RSA private key from the backend API
    rsa_private_key_string = requests.get(f'{cryptography_ms_url}/api/crypto/key/').json()
    
    # Create a temporary file to store the RSA private key
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        # Write the contents of rsa_private_key_string to the file
        temp_file.write(rsa_private_key_string)
    # Load the private key from the temporary file
    with open(temp_file.name, "rb") as f:
        privkey = rsa.PrivateKey.load_pkcs1(f.read())
    
    # Decode the Base64-encoded string
    decoded_bytes = base64.b64decode(base64_encoded_private_key_string)
    
    # Decrypt the bytes using the private key
    decrypted_bytes = rsa.decrypt(decoded_bytes, privkey)
    
    # Convert the decrypted bytes to a string
    wallet_private_key = decrypted_bytes.decode('ascii')
    
    return wallet_private_key

# contract_address = '0x018bCe5a7416DEf133BDf76eef6fEADdfE83f2ec'  # replace with your actual contract address
# contract = web3.eth.contract(address=contract_address, abi=abi)

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




def get_course_data(id, user_id):
    try:
        course = Course.objects.get(id=id, author=user_id)
    except Course.DoesNotExist:
        raise Http404("Product does not exist")

    videos = VideoSerializer(course.videos.all(), many=True)
    images = ImageSerializer(course.images.all(), many=True)
    what_learnt = RequisiteSerializer(course.what_learnt.all(), many=True)
    requisites = RequisiteSerializer(course.requisites.all(), many=True)
    who_is_for = WhoIsForSerializer(course.who_is_for.all(), many=True)
    resources = ResourceSerializer(course.resources.all(), many=True)
    course = CourseSerializer(course)

    course_data = {
        'videos': videos.data,
        'images': images.data,
        'whatlearnt': what_learnt.data,
        'requisites': requisites.data,
        'who_is_for': who_is_for.data,
        'resources': resources.data,
        'details': course.data,
    }

    return course_data


def get_watch_course_data(id):
    try:
        course = Course.objects.get(id=id)
    except Course.DoesNotExist:
        raise Http404("Product does not exist")

    course = CourseSerializer(course).data
    # sections = Section.objects.get(course=course)
    # sections = CourseSectionPaidSerializer(sections, many=True).data

    course_data = {
        # 'sections': sections,
        'details': course,
    }

    return course_data


def is_valid_uuid(uuid):
    try:
        UUID(uuid, version=4)
        return True
    except ValueError:
        return False
    

def is_valid_nft_address(address):
    # You can modify this function to include specific rules for validating NFT addresses.
    # For now, we'll check if the length of the string is correct.
    return len(address) == 42


def get_discounted_course(**kwargs):
    course = get_object_or_404(Course, Q(status='published') | Q(status='draft'), **kwargs)
    date_now = timezone.now()
    discount_key = f"discount-{course.id}"
    discount = cache.get(discount_key)
    if discount is None:
        if course.discount_until and course.discount_until < date_now:
            course.discount = False
            course.save()
            discount = False
        else:
            course.discount = True
            course.save()
            discount = True
        cache.set(discount_key, discount, timeout=60)  # set the timeout to 60 seconds
    return course, discount

def get_public_course_data(identifier):
    if is_valid_uuid(identifier):
        course, discount = get_discounted_course(id=identifier)
    elif is_valid_nft_address(identifier):
        course, discount = get_discounted_course(nft_address=identifier)
    else:
        course, discount = get_discounted_course(slug=identifier)
        

    videos = VideoSerializer(course.videos.all(), many=True)
    images = ImageSerializer(course.images.all(), many=True)
    what_learnt = RequisiteSerializer(course.what_learnt.all(), many=True)
    requisites = RequisiteSerializer(course.requisites.all(), many=True)
    who_is_for = WhoIsForSerializer(course.who_is_for.all(), many=True)
    resources = ResourceSerializer(course.resources.all(), many=True)
    course = CourseSerializer(course)

    course_data = {
        'videos': videos.data,
        'images': images.data,
        'whatlearnt': what_learnt.data,
        'requisites': requisites.data,
        'who_is_for': who_is_for.data,
        'resources': resources.data,
        'details': course.data,
        'discount': discount,
    }

    return course_data

# ============== COURSES ===================

# LIST - Courses


# DETAIL - Courses

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)
# CREATE, EDIT, DELETE - Courses
class CreateCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        payload = validate_token(request)
        data = self.request.data

        # try:
        if data.get('user').get('role') != 'seller':
            raise PermissionError('You dont have the permissions to create a course.')

        title = data['title']

        category = data['category']
        category = get_object_or_404(Category, slug=category)

        subCategory = data['subCategory']
        subCategory = get_object_or_404(Category, slug=subCategory)

        topic = data['topic']
        topic = get_object_or_404(Category, slug=topic)

        type = data['type']
        dedication = data['dedication']

        if type['title'] == 'Course':
            course = Course.objects.create(
                author=payload['user_id'], 
                title=title, 
                dedication=dedication, 
                category=category,
                sub_category=subCategory,
                topic=topic,
            )
            sellers = Sellers.objects.create(
                author=payload['user_id'],
                address=payload['address'],
                polygon_address=payload['polygon_address'],
                course=course 
                )
            course.sellers.add(sellers)

            # nft_id = int(re.sub('[^0-9]', '', str(course.id))) % 2**256
            course.token_id = random_with_N_digits(9)
            course.save()

            # Create Section
            section = Section.objects.create(
                title='Introduction',
                learning_objective='Enter a learning objective', 
                number=1,
                published=False,
                user=payload['user_id'],
                course=course
            )

            # Add Section to Course
            course.sections.add(section)

            # Create Episode
            episode = Episode.objects.create(
                title='Introduction', 
                number=1,
                published=False,
                content='',
                description='',
                user=payload['user_id'],
                course=course,
                section_uuid=section.id
            )
            # Add episode to section
            section.episodes.add(episode)

            serializer = CoursesManageListSerializer([course], many=True)
            return self.send_response(serializer.data,status=status.HTTP_201_CREATED)

        # except PermissionError as e:
        #     return self.send_error(str(e),status=status.HTTP_403_FORBIDDEN)
        # except KeyError as e:
        #     return self.send_error("Missing required field: " + str(e), status=status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     return self.send_error("Error: " + str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditCourseGoalsView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        try:
            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)
            bool = self.request.data['bool']
            course.goals = bool
            course.save()
            return self.send_response('Course Goals Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = get_object_or_404(Course, id=self.request.data['courseUUID'], author=user_id)

            if(self.request.data['title']):
                course.title=self.request.data['title']

            if(self.request.data['subTitle']):
                course.short_description=self.request.data['subTitle']

            if(self.request.data['description']):
                course.description=self.request.data['description']

            if(self.request.data['language']):
                course.language=self.request.data['language']

            if(self.request.data['level']):
                course.level=self.request.data['level']

            if(self.request.data['taught']):
                course.taught=self.request.data['taught']

            if(self.request.data['category']):
                category = Category.objects.get(id=self.request.data['category'])
                course.category=category
            
            if(self.request.data['thumbnail']):
                thumbnail_base64 = self.request.data['thumbnail'].split('base64,', 1 )
                thumbnail_data = b64decode(thumbnail_base64[1])
                thumbnail = ContentFile(thumbnail_data, self.request.data['filename'])
                course.thumbnail=thumbnail
            
            if(self.request.data['video']):
                course.sales_video=self.request.data['video']
            
            if(
                course.title != None and
                course.short_description != None and
                course.description != None and
                course.thumbnail != None and
                course.sales_video != None and
                course.category != None and
                course.language != None and
                course.level != None and
                course.taught != None 
            ):
                course.landing_page = True

            course.save()

            return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return self.send_error("Episode not found", status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        


class UpdateCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)
            course_data = json.loads(data['courseBody'])

            # updating fields based on user inputs
            update_data = {}
            if course_data.get('title'):
                update_data['title'] = course_data['title']
            if course_data.get('description'):
                update_data['description'] = course_data['description']
            if course_data.get('subTitle'):
                update_data['short_description'] = course_data['subTitle']
            if course_data.get('taught'):
                update_data['taught'] = course_data['taught']
            if course_data.get('language'):
                update_data['language'] = course_data['language']
            if course_data.get('level'):
                update_data['level'] = course_data['level']
            if course_data.get('category'):
                category = Category.objects.get(id=int(course_data['category']))
                update_data['category'] = category


            # update the fields in the database
            Course.objects.filter(id=course.id).update(**update_data)

            if(
                course.title != None and
                course.short_description != None and
                course.description != None and
                course.thumbnail != None and
                course.sales_video != None and
                course.category != None and
                course.language != None and
                course.level != None and
                course.taught != None 
            ):
                course.landing_page = True
                course.save()
            # get the updated product data
            updated_course = Course.objects.get(id=course.id)
            serialized_data = get_course_data(updated_course.id, user_id)
            return self.send_response(serialized_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class EditCoursePriceView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = get_object_or_404(Course, id=self.request.data['courseUUID'], author=user_id)

            if(self.request.data['price']):
                course.price=self.request.data['price']

            course.save()

            return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return self.send_error("Episode not found", status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        


class UpdateCoursePricingView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        guy = payload['polygon_address']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)
            course_data = json.loads(data['courseBody'])

            # updating fields based on user inputs
            update_data = {}
            if course_data.get('price'):
                update_data['price'] = course_data['price']

            if course_data.get('comparePrice'):
                update_data['compare_price'] = course_data['comparePrice']

            if course_data.get('discountUntil'):
                update_data['discount_until'] = course_data['discountUntil']

            if course_data.get('discount'):
                update_data['discount'] = course_data['discount']

            # update the fields in the database
            Course.objects.filter(id=course.id).update(**update_data)
            # get the updated product data
            updated_course = Course.objects.get(id=course.id)
            serialized_data = get_course_data(updated_course.id, user_id)

            if(course_data.get('nftAddress')!='0'):
                eth_price_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=matic-network%2Cethereum&vs_currencies=usd').json()
                eth_price = eth_price_response.get('ethereum').get('usd')
                matic_price = eth_price_response.get('matic-network').get('usd')
                cache.set('eth_price', eth_price, 1 * 60) # cache for 1 minutes
                cache.set('matic_price', matic_price, 1 * 60) # cache for 1 minutes
                
                user_private_key = decrypt_polygon_private_key(payload['address'])
                abi = get_polygon_contract_abi(course_data.get('nftAddress'))

                eth_price = cache.get('eth_price')
                matic_price = cache.get('matic_price')
                if not eth_price:
                    eth_price_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=matic-network%2Cethereum&vs_currencies=usd').json()
                    eth_price = eth_price_response.get('ethereum').get('usd')
                    matic_price = eth_price_response.get('matic-network').get('usd')
                    cache.set('eth_price', eth_price, 1 * 60) # cache for 1 minutes
                    cache.set('matic_price', matic_price, 1 * 60) # cache for 1 minutes
                ethCost = Decimal(course_data['price']) / Decimal(eth_price)
                maticCost = Decimal(course_data['price']) / Decimal(matic_price)
                price_in_wei = int(polygon_web3.toWei(maticCost, 'ether'))
                ticket_contract = polygon_web3.eth.contract(abi=abi, address=course_data.get('nftAddress'))
                tx = ticket_contract.functions.updatePrice(price_in_wei).buildTransaction({
                    'from': guy,
                    'nonce': polygon_web3.eth.get_transaction_count(guy),
                    'gasPrice': polygon_web3.eth.gas_price,
                    'gas': 100000,
                })
                signed_tx = polygon_web3.eth.account.sign_transaction(tx, private_key=user_private_key)
                tx_hash = polygon_web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                txReceipt = polygon_web3.eth.wait_for_transaction_receipt(tx_hash)
                print(price_in_wei)
                if txReceipt.get('status') == 1:
                    return self.send_response(serialized_data, status=status.HTTP_200_OK)
                else:
                    return self.send_error('Failed to update NFT price',status=status.HTTP_400_BAD_REQUEST)
            else:
                return self.send_response(serialized_data, status=status.HTTP_200_OK)
                
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class EditCourseStructureView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.course_structure = bool
            course.save()
            return self.send_response('Course Structure Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseSetupView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.setup = bool
            course.save()
            return self.send_response('Course Setup Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseFilmView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.film = bool
            course.save()
            return self.send_response('Course Film Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseCurriculumView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.curriculum = bool
            course.save()
            return self.send_response('Course Curriculum Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseCaptionsView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'], author=user_id)

            bool = self.request.data['bool']
            course.captions = bool
            course.save()
            return self.send_response('Course Captions Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseAccessibilityView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.accessibility = bool
            course.save()
            return self.send_response('Course Accessibility Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)
        

class EditCourseLandingPageView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.landing_page = bool
            course.save()
            return self.send_response('Course Landing Page Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCoursePricingView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.pricing = bool
            course.save()
            return self.send_response('Course Pricing Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCoursePromotionsView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            bool = self.request.data['bool']
            course.promotions = bool
            course.save()
            return self.send_response('Course Promotions Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseMessagesView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            welcomeMessage = self.request.data['welcomeMessage']
            congratsMessage = self.request.data['congratsMessage']

            course.welcome_message = welcomeMessage
            course.congrats_message = congratsMessage
            course.save()

            return self.send_response('Course Messages Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)

class EditCourseSlugView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        try:

            course = Course.objects.get(id=self.request.data['courseUUID'], author=user_id)

            slug = self.request.data['slug']

            # check for duplicate slug
            if Course.objects.filter(slug=slug).exclude(id=course.id).exists():
                return self.send_error('Slug already exists', status=status.HTTP_400_BAD_REQUEST)

            course.slug = slug
            course.slug_changes -= 1
            course.save()
            course_data = get_course_data(self.request.data['courseUUID'], user_id)
            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)
        
class EditCourseNFTAddressView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        # try:
        payload = validate_token(request)
        user_id = payload['user_id']

        course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

        nft_address = self.request.data['nftAddress']

        course.nft_address = nft_address
        course.save()
        course_data = get_course_data(self.request.data['courseUUID'][0],user_id)
        return self.send_response(course_data, status=status.HTTP_200_OK)
        # except Course.DoesNotExist:
        #     return self.send_error('Course with this ID does not exist or user_id not match with course author',
        #                            status=status.HTTP_404_NOT_FOUND)
        # except:
        #     return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class EditCourseKeywordsView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'], author=user_id)
            keywords = self.request.data['keywords']

            course.keywords = keywords
            course.save()

            course_data = get_course_data(self.request.data['courseUUID'],user_id)
            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)

class EditCourseStockView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'], author=user_id)
            stock = self.request.data['stock']

            course.stock = stock
            course.save()

            course_data = get_course_data(self.request.data['courseUUID'],user_id)
            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)

        
class PublishCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)
            course_data = get_course_data(self.request.data['courseUUID'][0],user_id)
            publish = self.request.data['bool']
            if publish==True:
                course.status = 'published'
                course.save()

                return self.send_response(course_data, status=status.HTTP_200_OK)
            else:
                course.status = 'draft'
                course.save()
                return self.send_response(course_data, status=status.HTTP_200_OK)

        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class SetCourseMessagesView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)

            setMessages = self.request.data['bool']
            course.allow_messages = setMessages
            course.save()
            return self.send_response('Course Messages Edited Correctly', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id not match with course author',
                                   status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)
        
        

class DeleteCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        course = get_object_or_404(Course, id=self.request.data['courseUUID'][0], author=user_id)
        item={}
        item['id']=str(course.id)
        item['seller_id']=str(course.author)
        producer.produce(
            'course_deleted',
            key='course_deleted',
            value=json.dumps(item).encode('utf-8')
        )
        producer.flush()

        sections=Section.objects.filter(course=course)
        for section in sections:
            for episode in section.episodes.all():
                episode.delete()
            section.delete()

        course.delete()
        return self.send_response('Course deleted', status=status.HTTP_200_OK)




# ============= COURSE SECTIONS =============

class CreateSectionCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def post(self, request, format=None):
        
        # try:
        payload = validate_token(request)
        user_id = payload['user_id']

        data = self.request.data
        title=data['title']
        learning_objective=data['learningObjective']
        number=data['number']
        courseUUID=data['courseUUID'][0]
        course = get_object_or_404(Course, id=courseUUID, author=user_id)

        section = Section(
            title=title, 
            learning_objective=learning_objective, 
            number=number, 
            course=course,
            user=user_id)
        section.save()

        course.sections.add(section)

        try:
            episode = Episode.objects.create(
                title='Introduction', 
                number=1,
                published=False,
                content='',
                description='',
                user=user_id,
                course=course,
                section_uuid=section.id
            )
            # Add episode to section
            section.episodes.add(episode)
            sections = course.sections.all()
            serializer=CourseSectionPaidSerializer(sections, many=True)
            return self.send_response(serializer.data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
                return self.send_error("Course not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)

class EditSectionView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            data = self.request.data
            title=data["title"]
            learning_objective=data["learningObjective"]
            number=data["number"]

            section = get_object_or_404(Section, id=self.request.data['sectionUUID'])

            course=Course.objects.get(author=user_id, sections=section)

            if(title!=''):
                section.title = title
                section.save()
            
            if(learning_objective!=''):
                section.learning_objective = title
                section.save()
            
            if(number!=''):
                section.number = number
                section.save()


            sections = course.sections.all()
            serializer=CourseSectionPaidSerializer(sections, many=True)
            return self.send_response(serializer.data, status=status.HTTP_200_OK)
    
        except ObjectDoesNotExist:
                return self.send_error("Section not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as v:
            return self.send_error(str(v), status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as o:
            return self.send_error(str(o), status=status.HTTP_404_NOT_FOUND)
        except Http404 as h:
            return self.send_error(str(h), status=status.HTTP_404_NOT_FOUND)


class DeleteSectionView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:

            section = get_object_or_404(Section, id=self.request.data['sectionUUID'], user=user_id)
            course=Course.objects.get(sections=section)

            for episode in section.episodes.all():
                episode.delete()

            section.delete()
            sections = course.sections.all()
            serializer=CourseSectionPaidSerializer(sections, many=True)
            return self.send_response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
                return self.send_error("Section not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as v:
            return self.send_error(str(v), status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as o:
            return self.send_error(str(o), status=status.HTTP_404_NOT_FOUND)
        except Http404 as h:
            return self.send_error(str(h), status=status.HTTP_404_NOT_FOUND)

# ============= COURSE EPISODES ============

class CreateEpisodeView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']

        course = Course.objects.get(id=self.request.data['courseUUID'][0])
        section = Section.objects.get(id=self.request.data['sectionUUID'])
        
        episode = Episode.objects.create(
                title=self.request.data['title'], 
                number=int(self.request.data['number']),
                published=False,
                content='',
                description='',
                user=user_id,
                course=course,
                section_uuid=self.request.data['sectionUUID']
            )
        section.episodes.add(episode)

        return self.send_response('Episode Created', status=status.HTTP_201_CREATED)
    

class DeleteEpisodeView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:

            episode = get_object_or_404(Episode, id=self.request.data['episodeUUID'], user=user_id)

            for resource in episode.resources.all():
                resource.delete()

            for question in episode.questions.all():
                question.delete()

            episode.delete()
            return self.send_response('Episdoe deleted', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
                return self.send_error("Section not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as v:
            return self.send_error(str(v), status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as o:
            return self.send_error(str(o), status=status.HTTP_404_NOT_FOUND)
        except Http404 as h:
            return self.send_error(str(h), status=status.HTTP_404_NOT_FOUND)


class EditEpisodeVideo(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes = [MultiPartParser, FormParser]
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        episode = Episode.objects.get(id=self.request.data['episodeUUID'], user=user_id)

        data = self.request.data

        video = data['video']
        filename =data['filename']

        episode.file=video
        episode.filename=filename
        episode.save()
        
        return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)

class DeleteEpisodeVideo(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        episode = Episode.objects.get(id=self.request.data['episodeUUID'], user=user_id)

        episode.file=''
        episode.save()
        
        return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)
        

class EditEpisodeTitle(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            episode = get_object_or_404(Episode, id=self.request.data['episodeUUID'], user=user_id)

            if(self.request.data['title']):
                episode.title=self.request.data['title']
                episode.save()

            return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return self.send_error("Episode not found", status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        

class EditEpisodeDescription(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            episode = get_object_or_404(Episode, id=self.request.data['episodeUUID'], user=user_id)

            if(self.request.data['description']):
                episode.description=self.request.data['description']
                episode.save()

            return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return self.send_error("Episode not found", status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        

class EditEpisodeContent(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            episode = get_object_or_404(Episode, id=self.request.data['episodeUUID'], user=user_id)

            episode.content=self.request.data['content']
            episode.save()

            return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return self.send_error("Episode not found", status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)


class DeleteEpisodeContent(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            episode = get_object_or_404(Episode, id=self.request.data['episodeUUID'], user=user_id)

            if(self.request.data['content']):
                episode.content=self.request.data['content']
                episode.save()

            return self.send_response('Episode Video Edited Successful', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return self.send_error("Episode not found", status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)



class EditEpisodeResourceView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    parser_classes = [MultiPartParser, FormParser]
    def put(self, request):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            episode = get_object_or_404(Episode, id=self.request.data['episodeUUID'], user=user_id)
            resourceUUID = self.request.data.get('resourceUUID')
            if resourceUUID:
                resource = get_object_or_404(Resource, id=resourceUUID, user=user_id)
                resource.file = self.request.data['file']
                resource.title = self.request.data['fileName']
                resource.save()
            else:
                resource = Resource.objects.create(user=user_id, file=self.request.data['file'], title=self.request.data['fileName'])
                episode.resources.add(resource)

            return self.send_response('Episode Resource Edited Successful', status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)


class EditEpisodeExternalResourceView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def put(self, request):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            episode = get_object_or_404(Episode, id=self.request.data['episodeUUID'], user=user_id)
            resourceUUID = self.request.data.get('resourceUUID')
            if resourceUUID:
                resource = get_object_or_404(Resource, id=resourceUUID, user=user_id)
                resource.url = self.request.data['url']
                resource.title = self.request.data['title']
                resource.save()
            else:
                resource = Resource.objects.create(user=user_id, url=self.request.data['url'], title=self.request.data['title'])
                episode.resources.add(resource)

            return self.send_response('Episode Resource Edited Successful', status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)

class DeleteResourceView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            resource = get_object_or_404(Resource, id=self.request.data['resourceUUID'], user=user_id)
            resource.delete()
            return self.send_response('Episdoe deleted', status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
                return self.send_error("Section not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as v:
            return self.send_error(str(v), status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as o:
            return self.send_error(str(o), status=status.HTTP_404_NOT_FOUND)
        except Http404 as h:
            return self.send_error(str(h), status=status.HTTP_404_NOT_FOUND)
        


class AddEpisodeViewedView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']

        data=self.request.data
        episode = Episode.objects.get(id=data['episodeUUID'])

        course = episode.course
        episode_completion, created = EpisodeCompletion.objects.get_or_create(user=user_id, episode=episode, course=course)
        episode_completion.completed = True
        episode_completion.save()
        return self.send_response('Episode marked as completed.', status=status.HTTP_200_OK)


class GetViewedEpisodesByUser(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request,course_id, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        course = Course.objects.get(id=course_id)
        completed_episodes = EpisodeCompletion.objects.filter(user=user_id, completed=True, course=course)
        response_data = []
        for episode_completion in completed_episodes:
            episode_data = {
                'id': str(episode_completion.episode.id),
                # 'title': episode.title,
                # 'description': episode.description,
                # 'length': episode.length,
                # 'file': episode.file.url if episode.file else None,
                # 'free': episode.free,
                # 'resources': [r.name for r in episode.resources.all()],
                # 'questions': [q.text for q in episode.questions.all()],
                # 'number': episode.number,
                # 'published': episode.published,
                # 'section_uuid': str(episode.section_uuid),
                # 'date': episode.date,
            }
            response_data.append(episode_data)
        return self.send_response(response_data, status=status.HTTP_200_OK)


    
# ================== COURSE WHATLEARNT =================
class CreateWhatLearntView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        
        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        # # cache_key = f'detail_course_author_{id}_{user_id}'
        
        try:

            course = get_object_or_404(Course, id=data['courseUUID'])

            result=[]
            for whatlearnt in data['whatlearnt']:
                obj, created = WhatLearnt.objects.update_or_create(
                    user=user_id, course=course, position_id=whatlearnt['id'],
                    defaults={'title': whatlearnt['title'],'position_id': whatlearnt['id']},
                )
                # If person exists with first_name='John' & last_name='Lennon' then update first_name='Bob'
                # Else create new person with first_name='Bob' & last_name='Lennon'
                course.what_learnt.add(obj)
                result.append(obj)
            

            # Save the course data in cache
            # cache.set(cache_key, serializer.data)

            return self.send_response('Whatlearnt added to course', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class DeleteWhatLearntView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        course = get_object_or_404(Course, id=self.request.data['course_uuid'])
        whatlearnt = WhatLearnt.objects.get(course=course, position_id=self.request.data['what_learnt_id'])
        if str(course.author) == user_id:
            if Course.objects.filter(what_learnt=whatlearnt).exists():
                whatlearnt.delete()
                return self.send_response('Course Whatlearnt Deleted', status=status.HTTP_200_OK)
            else:
                return self.send_error('That item does not exist.', status=status.HTTP_404_NOT_FOUND)
        else:
            return self.send_error('Only the course author may delete this', status=status.HTTP_401_UNAUTHORIZED)


# ============= COURSE Requisites ===================
class CreateRequisiteView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        
        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data
        
        # # cache_key = f'detail_course_author_{id}_{user_id}'
        try:

            course = get_object_or_404(Course, id=data['courseUUID'])

            result=[]
            for requisite in data['requisites']:
                obj, created = Requisite.objects.update_or_create(
                    user=user_id, course=course, position_id=requisite['id'],
                    defaults={'title': requisite['title'],'position_id': requisite['id']},
                )
                # If person exists with first_name='John' & last_name='Lennon' then update first_name='Bob'
                # Else create new person with first_name='Bob' & last_name='Lennon'
                course.requisites.add(obj)
                result.append(obj)
        

        # Save the course data in cache
        # cache.set(cache_key, serializer.data)

            return self.send_response('Requisite added to course', status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class DeleteRequisiteView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        course = get_object_or_404(Course, id=self.request.data['course_uuid'])
        requisite = Requisite.objects.get(course=course, position_id=self.request.data['requisite_id'])
        if str(course.author) == user_id:
            if Course.objects.filter(requisites=requisite).exists():
                requisite.delete()
                return self.send_response('Course Requisite Deleted', status=status.HTTP_200_OK)
            else:
                return self.send_error('That item does not exist.', status=status.HTTP_404_NOT_FOUND)
        else:
            return self.send_error('Only the course author may delete this', status=status.HTTP_401_UNAUTHORIZED)
# ============= COURSE WhoIsFor ===================
class UpdateWhoIsForView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)

            result = []
            for whoIsForItem in data['whoIsForList']:
                if whoIsForItem['title'] == "":
                    continue 
                obj, created = WhoIsFor.objects.update_or_create(
                    id=whoIsForItem['id'], user=user_id, course=course,
                    defaults={
                        'title': whoIsForItem['title'], 
                        'position_id': whoIsForItem['position_id'],
                    },
                )
                result.append(obj)

                if(created):
                    course.who_is_for.add(obj)

            course_data = get_course_data(course.id, user_id)

            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author', status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request', status=status.HTTP_400_BAD_REQUEST)


class DeleteWhoIsForView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)
        except Course.DoesNotExist:
            return self.send_error("Course not found.", status=status.HTTP_404_NOT_FOUND)

        try:
            whoIsFor = WhoIsFor.objects.get(course=course, id=self.request.data['id'],user = user_id)
        except WhoIsFor.DoesNotExist:
            return self.send_error("WhoIsFor not found.", status=status.HTTP_404_NOT_FOUND)

        if str(course.author) == user_id:
            if Course.objects.filter(who_is_for=whoIsFor).exists():
                whoIsFor.delete()
                course_data = get_course_data(course.id, user_id)
                return self.send_response(course_data, status=status.HTTP_200_OK)
            else:
                return self.send_error('That item does not exist.', status=status.HTTP_404_NOT_FOUND)
        else:
            return self.send_error('Only the course author may delete this', status=status.HTTP_401_UNAUTHORIZED)
    

class UpdateWhatLearntView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)

            result = []
            for item in data['whatlearntList']:
                if item['title'] == "":
                    continue 
                obj, created = WhatLearnt.objects.update_or_create(
                    id=item['id'], user=user_id, course=course,
                    defaults={
                        'title': item['title'], 
                        'position_id':item['position_id'],
                    },
                )
                result.append(obj)

                if(created):
                    course.what_learnt.add(obj)

            course_data = get_course_data(course.id, user_id)

            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)

class DeleteWhatLearntView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)
        except Course.DoesNotExist:
            return self.send_error("Course not found.", status=status.HTTP_404_NOT_FOUND)

        try:
            item = WhatLearnt.objects.get(course=course, id=self.request.data['id'],user = user_id)
        except WhatLearnt.DoesNotExist:
            return self.send_error("WhoIsFor not found.", status=status.HTTP_404_NOT_FOUND)

        if str(course.author) == user_id:
            if Course.objects.filter(what_learnt=item).exists():
                item.delete()
                course_data = get_course_data(course.id, user_id)
                return self.send_response(course_data, status=status.HTTP_200_OK)
            else:
                return self.send_error('That item does not exist.', status=status.HTTP_404_NOT_FOUND)
        else:
            return self.send_error('Only the course author may delete this', status=status.HTTP_401_UNAUTHORIZED)


class UpdateRequisiteView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)

            result = []
            for item in data['requisitesList']:
                if item['title'] == "":
                    continue 
                obj, created = Requisite.objects.update_or_create(
                    id=item['id'], user=user_id, course=course,
                    defaults={
                        'title': item['title'], 
                        'position_id':item['position_id'],
                    },
                )
                result.append(obj)

                if(created):
                    course.requisites.add(obj)

            course_data = get_course_data(course.id, user_id)

            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class DeleteRequisiteView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)
        except Course.DoesNotExist:
            return self.send_error("Course not found.", status=status.HTTP_404_NOT_FOUND)

        try:
            item = Requisite.objects.get(course=course, id=self.request.data['id'],user = user_id)
        except Requisite.DoesNotExist:
            return self.send_error("WhoIsFor not found.", status=status.HTTP_404_NOT_FOUND)

        if str(course.author) == user_id:
            if Course.objects.filter(requisites=item).exists():
                item.delete()
                course_data = get_course_data(course.id, user_id)
                return self.send_response(course_data, status=status.HTTP_200_OK)
            else:
                return self.send_error('That item does not exist.', status=status.HTTP_404_NOT_FOUND)
        else:
            return self.send_error('Only the course author may delete this', status=status.HTTP_401_UNAUTHORIZED)

# ===================== COURSE Questions ========================


# ===================== COURSE AUTHOR ========================


class CoursesFromTeacherView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request, *args, **kwargs):

        payload = validate_token(request)
        user_id = payload['user_id']

        courses = Course.objects.filter(author=user_id)

        # Get filter parameter
        filter_by = request.query_params.get('filter', 'newest')

        # Apply filter
        if filter_by == 'oldest':
            courses = courses.order_by('published')
        elif filter_by == 'az':
            courses = courses.order_by('title')
        elif filter_by == 'za':
            courses = courses.order_by('-title')
        elif filter_by == 'published':
            courses = courses.filter(status='published').order_by('-published')
        elif filter_by == 'unpublished':
            courses = courses.filter(status='draft').order_by('-published')
        else: # default to 'newest'
            courses = courses.order_by('-published')

        paginator = SmallSetPagination()
        results = paginator.paginate_queryset(courses, request)
        serializer = CoursesManageListSerializer(results, many=True)

        response = paginator.get_paginated_response({'courses': serializer.data})

        # cache the response

        return response
    
class GetCourseAuthorView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    @async_to_sync
    async def get(self, request,course_id, *args, **kwargs):
        user,profile = get_course_instructor(course_id)
        return self.send_response({
            'id':user.get('id'),
            'student_rating_no':user.get('student_rating_no'),
            'students':user.get('students'),
            'username':user.get('username'),
            'email':user.get('email'),
            'first_name':user.get('first_name'),
            'last_name':user.get('last_name'),
            'verified':user.get('verified'),
            'picture':profile.get('picture'),
            'facebook':profile.get('facebook'),
            'twitter':profile.get('twitter'),
            'instagram':profile.get('instagram'),
            'linkedin':profile.get('linkedin'),
            'youtube':profile.get('youtube'),
            'github':profile.get('github'),
        },status=status.HTTP_200_OK)
    
class ListCoursesView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        payload = validate_token(request)
        if(payload.get('user_id')):
            user_id = payload['user_id']
            # Get the first 20 published courses 
            courses_shown = Course.objects.filter(status='published').values_list('id')[:20]
            
            for course in courses_shown:
                item={}
                item['user']=user_id
                item['course']=str(course[0])
                producer.produce(
                    'course_interaction',
                    key='course_view_impressions',
                    value=json.dumps(item).encode('utf-8')
                )
            producer.flush()
            # update the impressions field for only the courses shown
            Course.objects.filter(id__in=courses_shown).update(impressions=F('impressions') + 1)
            courses_shown = Course.objects.filter(id__in=courses_shown)
            serializer = CoursesListSerializer(courses_shown, many=True)
            return self.paginate_response(request, serializer.data)
        else:
            # Get the first 20 published courses 
            courses_shown = Course.objects.filter(status='published').values_list('id', flat=True)[:20]
            # update the impressions field for only the courses shown
            Course.objects.filter(id__in=courses_shown).update(impressions=F('impressions') + 1)
            courses_shown = Course.objects.filter(id__in=courses_shown)
            serializer = CoursesListSerializer(courses_shown, many=True)
            return self.paginate_response(request, serializer.data)    


class ListCoursesFromIDListView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        data = request.data
        course_items = []
        for item in data:
            course = Course.objects.get(id=item['course'])
            coupon = item['coupon'] if item['coupon'] else None

            if coupon:
                # print('Coupon: ',coupon)
                response = requests.get(f'{coupons_ms_url}/api/coupons/get/' + coupon).json()
            else:
                response = None

            course_item = {
                'course_id':course.id,
                'course_token_id':course.token_id,
                'course_nft_address':course.nft_address,
                'course_slug':course.slug,
                'course_title':course.title,
                'course_short_description':course.short_description,
                'course_price':course.price,
                'course_discount':course.discount,
                'course_compare_price':course.compare_price if course.compare_price else None,
                'course_image':course.images.first().file.url if course.images.exists() else None,
                'coupon':response['results'] if coupon else None,
            }
            course_items.append(course_item)
        return self.send_response(course_items, status=status.HTTP_200_OK)

def get_course_by_identifier(identifier):
    if is_valid_uuid(identifier):
        return Course.objects.get(id=identifier)
    elif identifier.startswith("0x"):
        return Course.objects.get(nft_address=identifier)
    else:
        return Course.objects.get(slug=identifier)
    
class ListSectionsUnPaidView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, identifier, *args, **kwargs):
        try:
            # Get the course using the identifier (UUID, slug, or nft_address)
            course = get_course_by_identifier(identifier)

            # Get the sections associated with the course
            sections = Section.objects.filter(course=course)
            serializer = CourseSectionUnPaidSerializer(sections, many=True).data

            return self.paginate_response(request, serializer)
        except Course.DoesNotExist:
            return self.send_error("Course not found", status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error("Bad Request", status=status.HTTP_400_BAD_REQUEST)
    

class ListSectionsPaidView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request,id, *args, **kwargs):
        payload = validate_token(request)
        if(payload.get('user_id')):
            user_id = payload['user_id']
            course = Course.objects.get(id=id)
            sections = Section.objects.filter(course=course)
            serializer = CourseSectionPaidSerializer(sections, many=True).data
            return self.paginate_response(request, serializer)
    

class ListAuthorCoursesView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request, *args, **kwargs):

        payload = validate_token(request)
        user_id = payload['user_id']

        courses = Course.objects.filter(author=user_id)

        # Get filter parameter
        author = request.query_params.getlist('author', None)
        category = request.query_params.getlist('category', None)
        business_activity = request.query_params.getlist('business_activity', None)
        type = request.query_params.getlist('type', None)
        filter_by = request.query_params.get('filter', None)
        order_by = request.query_params.get('order', '-published')
        search = request.query_params.get('search', None)

        if filter_by == 'published':
            courses = courses.filter(status='published')
        elif filter_by == 'unpublished':
            courses = courses.filter(status='draft')

        if category and 'null' not in category:
            q_obj = Q()
            for cat in category:
                q_obj |= Q(category=cat)
            courses = courses.filter(q_obj)

        if author and 'null' not in author:
            q_obj = Q()
            for auth in author:
                q_obj |= Q(author=auth)
            courses = courses.filter(q_obj)

        if business_activity and 'null' not in business_activity:
            q_obj = Q()
            for b_activity in business_activity:
                q_obj |= Q(business_activity=b_activity)
            courses = courses.filter(q_obj)

        if type and 'null' not in type:
            q_obj = Q()
            for t in type:
                q_obj |= Q(type=t)
            courses = courses.filter(q_obj)

        if search and 'null' not in search:
            courses = Course.objects.filter(Q(title__icontains=search) | 
                                              Q(description__icontains=search) | 
                                                Q(short_description__icontains=search) | 
                                                  Q(keywords__icontains=search) |
                                                  Q(category__name__icontains=search) |
                                                  Q(category__title__icontains=search) |
                                                  Q(category__description__icontains=search) 
                                                    )


        if order_by == 'oldest':
            courses = courses.order_by('published')
        elif order_by == 'az':
            courses = courses.order_by('title')
        elif order_by == 'za':
            courses = courses.order_by('-title')
        elif order_by == 'sold':
            courses = courses.order_by('sold')
        else:
            courses = courses.order_by(order_by)

        serializer = CoursesManageListSerializer(courses, many=True)

        return self.paginate_response(request, serializer.data)
    

class DetailCourseAuthor(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self,request, id,*args, **kwargs):

        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course_data = get_course_data(id,user_id)
            return self.send_response(course_data,status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)



class DetailCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self,request, id,*args, **kwargs):
        try:
            return self.send_response(get_public_course_data(id),status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)



class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


class CourseNFTView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self,request, *args, **kwargs):

        course_token_id = kwargs['course_token_id']

        if not Course.objects.filter(token_id=int(course_token_id)).exists():
            return JsonResponse({'error': 'This course does not exist'}, status=404)
        
        course = Course.objects.get(token_id=course_token_id)
        first_image = course.images.first()

        course_data = {
            "name": course.title,
            "description": strip_tags(course.description),
            "image": request.build_absolute_uri(first_image.file.url) if first_image else None,
            "external_url": request.build_absolute_uri(course.get_absolute_url()),
            "attributes": [
                {
                    "trait_type": "Category",
                    "value": course.category.name if course.category else None
                },
                {
                    "trait_type": "Sub Category",
                    "value": course.sub_category.name if course.sub_category else None
                },
                {
                    "trait_type": "Topic",
                    "value": course.topic.name if course.topic else None
                },
                {
                    "trait_type": "Course Length",
                    "value": course.course_length
                },
                {
                    "trait_type": "Level",
                    "value": course.level
                },
                {
                    "trait_type": "Language",
                    "value": course.language
                },
                # {
                #     "trait_type": "Author",
                #     "value": course.author.username if course.author else None
                # },
            ]
        }

        return JsonResponse(course_data, safe=False)
        

class DetailPaidCourseView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self,request, id,*args, **kwargs):
        payload = validate_token(request)
        # try:
        user_id = payload['user_id']
        return self.send_response(get_watch_course_data(id),status=status.HTTP_200_OK)
        # except Course.DoesNotExist:
        #     return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        # except:
        #     return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)
        

class UpdateCourseAnalyticsView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def put(self,request, id,*args, **kwargs):
        payload = validate_token(request)
        try:
            if(payload.get('user_id')):
                user_id = payload['user_id']
                data = self.request.data

                watchTime = int(data['watchTime'])
                course = Course.objects.get(id=data['courseUUID'])
                oldAvg = course.avg_time_on_page
                newAvg = oldAvg + watchTime
                course.avg_time_on_page = newAvg
                course.save()

                item={}
                item['user']=user_id
                item['course']=id
                item['watchTime']=watchTime
                producer.produce(
                    'course_interaction',
                    key='course_view_watchtime',
                    value=json.dumps(item).encode('utf-8')
                )
                producer.flush()

                return self.send_response('WatchTime Updated',status=status.HTTP_200_OK)
            else:
                data = self.request.data
                watchTime = int(data['watchTime'])
                course = Course.objects.get(id=data['courseUUID'])
                oldAvg = course.avg_time_on_page
                newAvg = oldAvg + watchTime
                course.avg_time_on_page = newAvg
                course.save()

                return self.send_response('WatchTime Updated',status=status.HTTP_200_OK)

        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)
        
class UpdateCourseClickView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def put(self,request,*args, **kwargs):
        payload = validate_token(request)
        # try:
        if(payload.get('user_id')):
            user_id = payload['user_id']
            data = self.request.data

            course = Course.objects.get(id=data['courseUUID'])
            course.clicks += 1
            course.save()

            item={}
            item['user']=user_id
            item['course']=data['courseUUID']
            producer.produce(
                'course_interaction',
                key='course_view_clicks',
                value=json.dumps(item).encode('utf-8')
            )
            producer.flush()

            return self.send_response('WatchTime Updated',status=status.HTTP_200_OK)
        else:
            data = self.request.data
            course = Course.objects.get(id=data['courseUUID'])
            course.clicks += 1
            course.save()

            return self.send_response('WatchTime Updated',status=status.HTTP_200_OK)

        # except Course.DoesNotExist:
        #     return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        # except:
        #     return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)
        
class UpdateCourseViewsView(StandardAPIView):
    permission_classes = (permissions.AllowAny, )
    def put(self,request,*args, **kwargs):
        payload = validate_token(request)
        # try:
        if(payload.get('user_id')):
            user_id = payload['user_id']
            data = self.request.data

            course = Course.objects.get(id=data['courseUUID'])
            course.views += 1
            course.save()

            item={}
            item['user']=user_id
            item['course']=data['courseUUID']
            producer.produce(
                'course_interaction',
                key='course_view_views',
                value=json.dumps(item).encode('utf-8')
            )
            producer.flush()

            return self.send_response('WatchTime Updated',status=status.HTTP_200_OK)
        else:
            data = self.request.data
            course = Course.objects.get(id=data['courseUUID'])
            course.views += 1
            course.save()

            return self.send_response('WatchTime Updated',status=status.HTTP_200_OK)

        # except Course.DoesNotExist:
        #     return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        # except:
        #     return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)
        

class GetAuthorCourseSections(StandardAPIView):
    def get(self,request, courseUUID,*args, **kwargs):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = Course.objects.get(id=courseUUID, author=user_id)
            sections = course.sections.all()

            # for course in courses:
            serializer=CourseSectionPaidSerializer(sections, many=True)
            return self.send_response(serializer.data,status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course not found', status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        


class UpdateImageView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)

            result = []
            for image in data['imagesList']:
                
                if ';base64,' in image['file']:
                    format, imgstr = image['file'].split(';base64,')
                    ext = format.split('/')[-1]
                    data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                    
                    # validate the file type
                    if ext not in ['jpg', 'jpeg', 'png']:
                        raise ValidationError('Invalid file type. Only jpeg and png are allowed.')

                    # validate the file size
                    if data.size > 2000000:
                        raise ValidationError('File size should be less than 2MB')
                    
                    image['file'] = data
                elif image['file'].startswith('/media/'):
                    # Do nothing, the value is a file path
                    pass
                else:
                    raise ValidationError('Invalid image file format.')

                obj, created = Image.objects.update_or_create(
                    id=image['id'], author=user_id, course=course,
                    defaults={'title': image['title'], 'position_id': image['position_id'], 'file': image['file']},
                )
                result.append(obj)

                if created:
                    course.images.add(obj)

            course_data = get_course_data(course.id, user_id)

            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class DeleteImageView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)
        except Course.DoesNotExist:
            return self.send_error("Product not found.", status=status.HTTP_404_NOT_FOUND)

        try:
            image = Image.objects.get(course=course, id=self.request.data['id'],author = user_id)
        except Image.DoesNotExist:
            return self.send_error("Image not found.", status=status.HTTP_404_NOT_FOUND)

        if str(course.author) == user_id:
            if Course.objects.filter(images=image).exists():
                image.delete()
                course_data = get_course_data(course.id, user_id)
                return self.send_response(course_data, status=status.HTTP_200_OK)
            else:
                return self.send_error('That item does not exist.', status=status.HTTP_404_NOT_FOUND)
        else:
            return self.send_error('Only the course author may delete this', status=status.HTTP_401_UNAUTHORIZED)


class UpdateVideoView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):

        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)

            result = []
            for video in data['videosList']:            
                if ';base64,' in video['file']:
                    format, videostr = video['file'].split(';base64,')
                    ext = format.split('/')[-1]
                    video_data = ContentFile(base64.b64decode(videostr), name='temp.' + ext)
                    
                    # validate the file type
                    if ext not in ['mp4', 'm4v', 'mpeg', 'm4p', '.asf', 'mkv', 'webm']:
                        raise ValidationError('Invalid file type. Only mp4,m4v,mpeg,m4p,.asf,mkv,webm are allowed.')

                    # validate the file size
                    if video_data.size > 2000000000:
                        raise ValidationError('File size should be less than 2GB')
                    
                    video['file'] = video_data
                elif video['file'].startswith('/media/'):
                    # Do nothing, the value is a file path
                    pass
                else:
                    raise ValidationError('Invalid video file format.')

                obj, created = Video.objects.update_or_create(
                    id=video['id'], author=user_id, course=course,
                    defaults={'title': video['title'], 'position_id': video['position_id'], 'file': video['file']},
                )
                result.append(obj)

                if created:
                    course.videos.add(obj)

            course_data = get_course_data(course.id, user_id)

            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class DeleteVideoView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']

        try:
            course = Course.objects.get(id=self.request.data['courseUUID'][0], author=user_id)
        except Course.DoesNotExist:
            return self.send_error("Course not found.", status=status.HTTP_404_NOT_FOUND)

        try:
            video = Video.objects.get(course=course, id=self.request.data['id'],author = user_id)
        except Video.DoesNotExist:
            return self.send_error("Requisite not found.", status=status.HTTP_404_NOT_FOUND)

        if str(course.author) == user_id:
            if Course.objects.filter(videos=video).exists():
                video.delete()
                course_data = get_course_data(course.id, user_id)
                return self.send_response(course_data, status=status.HTTP_200_OK)
            else:
                return self.send_error('That item does not exist.', status=status.HTTP_404_NOT_FOUND)
        else:
            return self.send_error('Only the course author may delete this', status=status.HTTP_401_UNAUTHORIZED)
        


class UpdateCourseWelcomeMessage(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)

            course.welcome_message = data['message']
            course.save()

            course_data = get_course_data(course.id, user_id)
            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)


class UpdateCourseCongratsMessage(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        payload = validate_token(request)
        user_id = payload['user_id']
        data = self.request.data

        try:
            course = get_object_or_404(Course, id=data['courseUUID'][0], author=user_id)

            course.congrats_message = data['message']
            course.save()

            course_data = get_course_data(course.id, user_id)
            return self.send_response(course_data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist or user_id did not match with course author',status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return self.send_error(str(e), status=status.HTTP_403_FORBIDDEN)
        except:
            return self.send_error('Bad Request',status=status.HTTP_400_BAD_REQUEST)
        

## QUESTIONS

class ListCourseQuestionsView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        payload = validate_token(request)
        user_id = payload['user_id']

        course_uuid = request.query_params.get('id', None)
        try:
            course = Course.objects.get(id=course_uuid)
        except Course.DoesNotExist:
            return Response({"error": "Course does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Get all the sections for the course
        sections = course.sections.all()

        # Get all the episodes for the sections
        episodes = Episode.objects.filter(section__in=sections)

        # Get all the questions for the episodes
        questions = Question.objects.filter(episode__in=episodes)

        # Apply any filters or sorts on the questions here
        search_query = request.query_params.get('search', None)

        filter_by = request.query_params.get('filter_by', False)
        sort_by = request.query_params.get('sort_by', '-created_date')  # default to sort by most recent

        # Apply additional filters if necessary
        if search_query:
            questions = questions.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))

        if filter_by == 'user':
            questions = questions.filter(user=user_id)
        elif filter_by == 'no_answer':
            questions = questions.annotate(answers_count=Count('answer')).filter(answers_count=0)
        
        # Apply sorting
        if sort_by == 'most_likes':
            questions = questions.annotate(num_likes=Count('likes')).order_by('-num_likes')
        else:
            questions = questions.order_by(sort_by)
        

        serializer = QuestionSerializer(questions, many=True)

        return self.paginate_response(request, serializer.data)
    

class ListEpisodeQuestionsView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        payload = validate_token(request)
        user_id = payload['user_id']
        
        # Extract filter parameters
        episode_uuid = request.query_params.get('id', None)
        search_query = request.query_params.get('search', None)

        filter_by = request.query_params.get('filter_by', False)
        sort_by = request.query_params.get('sort_by', '-created_date')  # default to sort by most recent

        # Check if episode exists
        try:
            episode = Episode.objects.get(id=episode_uuid)
        except Episode.DoesNotExist:
            return self.send_error("Episode does not exist.",status=status.HTTP_404_NOT_FOUND)

        # Fetch questions for the given episode
        questions = Question.objects.filter(episode__id=episode_uuid)

        serializer = QuestionSerializer(questions, many=True)
        return self.paginate_response(request, serializer.data)


class ListQuestionAnswersView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        question_id = kwargs.get('id', None)
        question = Question.objects.get(id=question_id)
        answers = Answer.objects.filter(question=question)
        # Serialize data
        serializer = AnswerSerializer(answers, many=True)
        return self.paginate_response(request, serializer.data)
    


class CreateQuestionView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']
            data = self.request.data

            episode = Episode.objects.get(id=data['episodeUUID'])
            # Create Question
            question = Question.objects.create(
                user=user_id,
                title=data['title'],
                body=data['content'],
                episode=episode
            )
            episode.questions.add(question)
            # Get Questions,serialize and respond with question list
            questions = episode.questions.all()
            serializer = QuestionSerializer(questions,many=True)
            return self.paginate_response(request, serializer.data)

        except Episode.DoesNotExist:
            return self.send_error('Episode with this ID does not exist.',status=status.HTTP_404_NOT_FOUND)
        except KeyError as e:
            return self.send_error(f'Missing key: {e}', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        

class UpdateQuestionView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)
        try:
            question = Question.objects.get(pk=request.data['questionId'])
        except Question.DoesNotExist:
            return self.send_error("Question does not exist.", status=status.HTTP_404_NOT_FOUND)

        if question.user != user_id:
            return self.send_error("You do not have permission to edit this question.", status=status.HTTP_403_FORBIDDEN)
        
        question.title = request.data['title']
        question.body = request.data['body']
        question.save()

        return self.send_response('serializer.data', status=status.HTTP_200_OK)
            

class DeleteQuestionView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        try:
            question = Question.objects.get(id=request.data['questionId'])
        except Question.DoesNotExist:
            return self.send_error("Question does not exist.", status=status.HTTP_404_NOT_FOUND)
        # Check if the user is the author of the answer
        if question.user != user_id:
            return self.send_error("You do not have permission to delete this answer.", status=status.HTTP_403_FORBIDDEN)
        
        question.delete()
        return self.send_response("Answer deleted successfully.", status=status.HTTP_200_OK)
    
    

class AddQuestionLikeView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        question_uuid = request.data['questionId']
        question = Question.objects.get(id=question_uuid)

        liked_item = None
        for like in question.likes.all():
            if like.user == user_id:
                liked_item = like
                break

        if liked_item is None:
            new_like = Like.objects.create(user=user_id)
            question.likes.add(new_like)
        else:
            question.likes.remove(liked_item)
            liked_item.delete()  # Delete the Like object

        # Update like counter
        question.likes_count = F('likes_count') + 1 if liked_item is None else F('likes_count') - 1
        question.save()

        return Response({'success': 'Question liked'})


class CreateAnswerView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']
            data = self.request.data

            question = Question.objects.get(id=data['questionUUID'])
            # Create Answer
            Answer.objects.create(
                user=user_id,
                body=data['content'],
                question=question
            )
            
            # Get updated list of questions for the episode
            questions = question.episode.questions.all()
            serializer = QuestionSerializer(questions, many=True)
            return self.paginate_response(request, serializer.data)

        except Question.DoesNotExist:
            return self.send_error('Question with this ID does not exist.',status=status.HTTP_404_NOT_FOUND)
        except KeyError as e:
            return self.send_error(f'Missing key: {e}', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)


class UpdateAnswerView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        try:
            answer = Answer.objects.get(id=request.data['answerId'])
        except Answer.DoesNotExist:
            return self.send_error("Answer does not exist.", status=status.HTTP_404_NOT_FOUND)
        
        if(answer.user == user_id):
            answer.body = request.data['body']
            answer.save()

            return self.send_response(AnswerSerializer(answer).data, status=status.HTTP_200_OK)
        else:
            return self.send_error(AnswerSerializer(answer).errors, status=status.HTTP_400_BAD_REQUEST)
        
class AcceptAnswerView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)
        try:
            answer = Answer.objects.get(id=request.data['answerId'])
        except Answer.DoesNotExist:
            return self.send_error("Answer does not exist.", status=status.HTTP_404_NOT_FOUND)

        question = answer.question  # Get the related question from the answer object

        if question.user == user_id:
            if answer.is_accepted_answer:
                answer.is_accepted_answer = False
            else:
                answer.is_accepted_answer = True
            answer.save()  # Save the updated answer object

            return self.send_response('Success', status=status.HTTP_200_OK)
        else:
            return self.send_error("User not allowed.", status=status.HTTP_403_FORBIDDEN)
        

class DeleteAnswerView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        try:
            answer = Answer.objects.get(id=request.data['answerId'])
        except Answer.DoesNotExist:
            return self.send_error("Answer does not exist.", status=status.HTTP_404_NOT_FOUND)
        # Check if the user is the author of the answer
        if answer.user != user_id:
            return self.send_error("You do not have permission to delete this answer.", status=status.HTTP_403_FORBIDDEN)
        
        answer.delete()
        return self.send_response("Answer deleted successfully.", status=status.HTTP_200_OK)
    

class AddOrRemoveAnswerLikeView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        payload = validate_token(request)
        user_id_str = payload['user_id']
        user_id = UUID(user_id_str)

        answer_uuid = request.data['answerId']
        answer = Answer.objects.get(id=answer_uuid)

        liked_item = None
        for like in answer.likes.all():
            if like.user == user_id:
                liked_item = like
                break

        if liked_item is None:
            new_like = Like.objects.create(user=user_id)
            answer.likes.add(new_like)
        else:
            answer.likes.remove(liked_item)
            liked_item.delete()  # Delete the Like object

        # Update like counter
        answer.likes_count = F('likes_count') + 1 if liked_item is None else F('likes_count') - 1
        answer.save()


        return Response({'success': 'Answer liked'}, status=status.HTTP_200_OK)


class ListPaidCourses(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request, *args, **kwargs):

        payload = validate_token(request)
        user_id = payload['user_id']

        # Get the user's Paid object
        user_paid = Paid.objects.get(user=user_id)
        
        # Get the courses from the PaidItem model
        courses = Course.objects.filter(paiditem__in=user_paid.courses.all())

        # Get filter parameter
        author = request.query_params.getlist('author', None)
        category = request.query_params.getlist('category', None)
        business_activity = request.query_params.getlist('business_activity', None)
        type = request.query_params.getlist('type', None)
        filter_by = request.query_params.get('filter', None)
        order_by = request.query_params.get('order', '-published')
        search = request.query_params.get('search', None)

        if filter_by == 'published':
            courses = courses.filter(status='published')
        elif filter_by == 'unpublished':
            courses = courses.filter(status='draft')

        if category and 'null' not in category:
            q_obj = Q()
            for cat in category:
                q_obj |= Q(category=cat)
            courses = courses.filter(q_obj)

        if author and 'null' not in author:
            q_obj = Q()
            for auth in author:
                q_obj |= Q(author=auth)
            courses = courses.filter(q_obj)

        if business_activity and 'null' not in business_activity:
            q_obj = Q()
            for b_activity in business_activity:
                q_obj |= Q(business_activity=b_activity)
            courses = courses.filter(q_obj)

        if type and 'null' not in type:
            q_obj = Q()
            for t in type:
                q_obj |= Q(type=t)
            courses = courses.filter(q_obj)

        if search and 'null' not in search:
            search_results = Course.objects.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search) |
                Q(keywords__icontains=search) |
                Q(category__name__icontains=search) |
                Q(category__title__icontains=search) |
                Q(category__description__icontains=search)
            )

            courses = search_results.filter(paiditem__in=user_paid.courses.all())

        if order_by == 'oldest':
            courses = courses.order_by('published')
        elif order_by == 'az':
            courses = courses.order_by('title')
        elif order_by == 'za':
            courses = courses.order_by('-title')
        elif order_by == 'sold':
            courses = courses.order_by('sold')
        else:
            courses = courses.order_by(order_by)

        serializer = CoursesListSerializer(courses, many=True)

        return self.paginate_response(request, serializer.data)
    



class AddToWishlistView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']
            data = self.request.data

            wishlist, _  = WishList.objects.get_or_create(user=user_id)
            if _:
                wishlist.save()
            
            course = Course.objects.get(id=request.data['courseUUID'])

            wishlist.courses.add(course)

            return self.send_response(get_public_course_data(request.data['courseUUID']))

        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist.',status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)


class RemoveFromWishlistView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']
            data = self.request.data

            wishlist, _  = WishList.objects.get_or_create(user=user_id)
            if _:
                wishlist.save()
            
            course = Course.objects.get(id=request.data['courseUUID'])

            wishlist.courses.remove(course)

            return self.send_response(get_public_course_data(request.data['courseUUID']))

        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist.',status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)


class AddOrRemoveFromWishlistView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def put(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']

            wishlist, _  = WishList.objects.get_or_create(user=user_id)
            if _:
                wishlist.save()

            course = Course.objects.get(id=request.data['courseUUID'])

            if course not in wishlist.courses.all():
                wishlist.courses.add(course)
                return self.send_response(True)
            else:
                wishlist.courses.remove(course)
                return self.send_response(False)

        except Course.DoesNotExist:
            return self.send_error('Course with this ID does not exist.',status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        

class CheckWishlistView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        try:
            payload = validate_token(request)
            user_id = payload['user_id']
            course_id = request.query_params.get('course_id')

            wishlist, _ = WishList.objects.get_or_create(user=user_id)
            if _:
                wishlist.save()

            course = Course.objects.get(id=course_id)
            is_in_wishlist = course in wishlist.courses.all()

            return self.send_response(is_in_wishlist)

        except (Course.DoesNotExist, WishList.DoesNotExist):
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return self.send_error(str(e), status=status.HTTP_400_BAD_REQUEST)
        

class ListWishlistCourses(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request, *args, **kwargs):

        payload = validate_token(request)
        user_id = payload['user_id']

        # Get the user's Paid object
        wishlist = WishList.objects.get(user=user_id)
        courses = wishlist.courses.all()

        # Get filter parameter
        author = request.query_params.getlist('author', None)
        category = request.query_params.getlist('category', None)
        business_activity = request.query_params.getlist('business_activity', None)
        type = request.query_params.getlist('type', None)
        filter_by = request.query_params.get('filter', None)
        order_by = request.query_params.get('order', '-published')
        search = request.query_params.get('search', None)

        if filter_by == 'published':
            courses = courses.filter(status='published')
        elif filter_by == 'unpublished':
            courses = courses.filter(status='draft')

        if category and 'null' not in category:
            q_obj = Q()
            for cat in category:
                q_obj |= Q(category=cat)
            courses = courses.filter(q_obj)

        if author and 'null' not in author:
            q_obj = Q()
            for auth in author:
                q_obj |= Q(author=auth)
            courses = courses.filter(q_obj)

        if business_activity and 'null' not in business_activity:
            q_obj = Q()
            for b_activity in business_activity:
                q_obj |= Q(business_activity=b_activity)
            courses = courses.filter(q_obj)

        if type and 'null' not in type:
            q_obj = Q()
            for t in type:
                q_obj |= Q(type=t)
            courses = courses.filter(q_obj)

        if search and 'null' not in search:
            search_results = Course.objects.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search) |
                Q(keywords__icontains=search) |
                Q(category__name__icontains=search) |
                Q(category__title__icontains=search) |
                Q(category__description__icontains=search)
            )

            courses = search_results.filter(id__in=wishlist.courses.all())
        
        if order_by == 'oldest':
            courses = courses.order_by('published')
        elif order_by == 'az':
            courses = courses.order_by('title')
        elif order_by == 'za':
            courses = courses.order_by('-title')
        elif order_by == 'sold':
            courses = courses.order_by('sold')
        else:
            courses = courses.order_by(order_by)

        serializer = CoursesListSerializer(courses, many=True)

        return self.paginate_response(request, serializer.data)
    



class SearchCoursesView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request, *args, **kwargs):
        courses = Course.objects.all()
        # Get filter parameter
        order_by = request.query_params.get('order', '-published')
        if order_by == 'oldest':
            courses = courses.order_by('published')
        elif order_by == 'desc':
            courses = courses.order_by('title')
        elif order_by == 'asc':
            courses = courses.order_by('-title')
        elif order_by == 'sold':
            courses = courses.order_by('sold')
        else:
            courses = courses.order_by(order_by)

        filter_by = request.query_params.get('filter', None)
        if filter_by == 'views':
            courses = courses.order_by('-views')
        elif filter_by == 'sold':
            courses = courses.order_by('-sold')
        elif filter_by == 'date_created':
            courses = courses.order_by('-published')
        elif filter_by == 'price':
            if order_by == 'asc':
                courses = courses.order_by('price')
            elif order_by == 'desc':
                courses = courses.order_by('-price')

        category = request.query_params.getlist('category', None)
        if category and '' not in category:
            q_obj = Q()
            for cat in category:
                if cat.isdigit():  # If the value is a number
                    q_obj |= Q(category_id=cat) | Q(sub_category_id=cat) | Q(topic_id=cat)
                elif validate_slug(cat) is None:  # If the value is a slug
                    q_obj |= Q(category__slug=cat) | Q(sub_category__slug=cat) | Q(topic__slug=cat)
            courses = courses.filter(q_obj)

        search = request.query_params.get('search', None)
        if search and 'null' not in search:
            courses = Course.objects.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) | 
                Q(short_description__icontains=search) | 
                Q(keywords__icontains=search) |
                Q(category__name__icontains=search) |
                Q(category__title__icontains=search) |
                Q(category__description__icontains=search) 
            )
            
        rating = request.query_params.get('rating', None)
        if rating and rating != 'undefined':
            # Annotate with custom ordering field based on rating
            courses = courses.annotate(
                custom_order=Case(
                    When(avgRating__gte=float(rating), then='avgRating'),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-custom_order')
        else:
            courses = courses.order_by('-avgRating')

        language = request.query_params.get('language', None)
        if language and language != 'undefined':
            courses = courses.filter(language__icontains=language)

        duration = request.query_params.get('duration', None)
        if duration and duration != 'undefined':
            duration_range = duration.split('-')
            print(duration_range)
            lower_bound = float(duration_range[0]) * 3600  # Convert hours to seconds
            upper_bound = float(duration_range[1]) * 3600  # Convert hours to seconds

            # Annotate courses queryset with the total_duration
            courses = courses.annotate(
                total_duration=Sum(F('sections__episodes__length'))
            ).filter(
                Q(total_duration__gte=lower_bound) & Q(total_duration__lte=upper_bound)
            )

        level = request.query_params.get('level', None)
        if level and level != 'undefined':
            if level != 'All':
                courses = courses.filter(level__icontains=level)
            else:
                courses = courses.filter()

        pricing = request.query_params.get('pricing', None)
        if pricing and pricing != 'undefined':
            if pricing == 'Free':
                courses = courses.filter(price__lte=0)
            elif pricing == 'Paid':
                courses = courses.filter(price__gt=0)
        
        author = request.query_params.get('author', None)
        if author and author != '' and author != 'undefined'and author != 'null':
            courses = courses.filter(author=author)

        serializer = CoursesListSerializer(courses, many=True)

        return self.paginate_response(request, serializer.data)