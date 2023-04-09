from django.urls import path,re_path
from .views import *


urlpatterns = [
    # COURSES
    # List Courses

    re_path(r'^nft/(?P<course_token_id>\d+)\.json$', CourseNFTView.as_view(), name='course_nft'),
    # Detail Courses
    path('list/',ListCoursesView.as_view()),
    path('list/sections/unpaid/<identifier>/',ListSectionsUnPaidView.as_view()),
    path('list/sections/<id>/',ListSectionsPaidView.as_view()),
    path('get/<id>/', DetailCourseView.as_view(), name='course_detail'),
    path('get/paid/<id>/', DetailPaidCourseView.as_view()),
    path('update/clicks/', UpdateCourseClickView.as_view()),
    path('update/views/', UpdateCourseViewsView.as_view()),
    path('list/id/',ListCoursesFromIDListView.as_view()),

    # Create, Edit, Delete Courses
    path('create',CreateCourseView.as_view()),
    path('edit/',EditCourseView.as_view()),
    path('edit/price/',EditCoursePriceView.as_view()),
    path('edit/nft_address/',EditCourseNFTAddressView.as_view()),
 
    path('update/',UpdateCourseView.as_view()),
    path('update/pricing/', UpdateCoursePricingView.as_view()),
    
    path("edit/goals/",EditCourseGoalsView.as_view()),
    path("edit/structure/",EditCourseStructureView.as_view()),
    path("edit/setup/",EditCourseSetupView.as_view()),
    path("edit/film/",EditCourseFilmView.as_view()),
    path("edit/curriculum/",EditCourseCurriculumView.as_view()),
    path("edit/captions/",EditCourseCaptionsView.as_view()),
    path("edit/accessibility/",EditCourseAccessibilityView.as_view()),
    path("edit/landing/",EditCourseLandingPageView.as_view()),
    path("edit/pricing/",EditCoursePricingView.as_view()),
    path("edit/promotions/",EditCoursePromotionsView.as_view()),
    path("edit/messages/",SetCourseMessagesView.as_view()),
    path("edit/messages/values/",EditCourseMessagesView.as_view()),
    path("edit/slug/",EditCourseSlugView.as_view()),
    path("edit/keywords/",EditCourseKeywordsView.as_view()),
    path("edit/stock/",EditCourseStockView.as_view()),
    path("publish/",PublishCourseView.as_view()),
    path("delete/",DeleteCourseView.as_view()),

    #COURSES SECTIONS
    #List Sections
    path('teacher/sections/get/<courseUUID>/',GetAuthorCourseSections.as_view()),
    # Create, Edit, Delete
    path('teacher/list/', ListAuthorCoursesView.as_view()),
    path('teacher/get/<id>/', DetailCourseAuthor.as_view()),
    path('teacher/sections/create/',CreateSectionCourseView.as_view()),
    path('teacher/sections/edit/',EditSectionView.as_view(),),
    path('teacher/sections/delete/',DeleteSectionView.as_view(),),

    # COURSES EPISODES
    path('teacher/episodes/create/',CreateEpisodeView.as_view(),),
    path('teacher/episodes/delete/',DeleteEpisodeView.as_view(),),
    path('teacher/episodes/add/video/',EditEpisodeVideo.as_view(),),
    path('teacher/episodes/delete/video/',DeleteEpisodeVideo.as_view(),),
    path('teacher/episodes/edit/title/',EditEpisodeTitle.as_view(),),
    path('teacher/episodes/edit/description/',EditEpisodeDescription.as_view(),),
    path('teacher/episodes/edit/content/',EditEpisodeContent.as_view(),),
    path('teacher/episodes/resources/edit/',EditEpisodeResourceView.as_view(),),
    path('teacher/episodes/resources/edit/external/',EditEpisodeExternalResourceView.as_view(),),
    path('teacher/episodes/resources/delete/',DeleteResourceView.as_view(),),


    #COURSES WhatLearnt
    path("whatlearnt/create/",UpdateWhatLearntView.as_view()),
    path("whatlearnt/delete/",DeleteWhatLearntView.as_view()),

    #COURSES Requisistes
    path("requisites/create/",UpdateRequisiteView.as_view()),
    path("requisites/delete/",DeleteRequisiteView.as_view()),

    #COURSES WhoIsFor
    path("who_is_for/create/",UpdateWhoIsForView.as_view()),
    path("who_is_for/delete/",DeleteWhoIsForView.as_view()),

    path("images/create/",UpdateImageView.as_view()),
    path("images/delete/",DeleteImageView.as_view()),

    path("videos/create/",UpdateVideoView.as_view()),
    path("videos/delete/",DeleteVideoView.as_view()),

    path('update/welcome_message/', UpdateCourseWelcomeMessage.as_view()), 
    path('update/congrats_message/', UpdateCourseCongratsMessage.as_view()),


    #COURSES Resources
    path('update/analytics/<id>/', UpdateCourseAnalyticsView.as_view()),

    #COURSE Questions
    path('questions/list/', ListCourseQuestionsView.as_view()),
    path('questions/like/', AddQuestionLikeView.as_view()),
    path('questions/episode/list/', ListEpisodeQuestionsView.as_view()),
    path('questions/create/', CreateQuestionView.as_view()),
    path('questions/update/', UpdateQuestionView.as_view()),
    path('questions/delete/', DeleteQuestionView.as_view()),

    path('questions/answers/<id>/', ListQuestionAnswersView.as_view()),
    path('answers/create/', CreateAnswerView.as_view()),
    path('answers/like/', AddOrRemoveAnswerLikeView.as_view()),
    # path('answers/<int:pk>/update/', UpdateAnswerView.as_view()),
    path('answers/accept/', AcceptAnswerView.as_view(), name='accept-answer'),
    path('answers/delete/', DeleteAnswerView.as_view(), name='delete-answer'),
    path('answers/update/', UpdateAnswerView.as_view(), name='update_answer'),
    #COURSE Answers
    
    path('episodes/completed/', AddEpisodeViewedView.as_view()),
    path('episodes/completed/course/<course_id>/', GetViewedEpisodesByUser.as_view()),
    path('get/course/author/<course_id>/', GetCourseAuthorView.as_view()),

    path('paid_library/', ListPaidCourses.as_view()),

    path('wishlist/add_or_remove/', AddOrRemoveFromWishlistView.as_view()),
    path('wishlist/', ListWishlistCourses.as_view()),
    path('wishlist/check/', CheckWishlistView.as_view()),
    path('search/', SearchCoursesView.as_view()),
    #Teacher
    # path('teacher/most_sold', TeacherMostSoldCoursesView.as_view()),
    # path('user', CoursesFromUserView.as_view()),
    # path('teacher/questions', QuestionsCoursesFromTeacherView.as_view()),
    # path('teacher/questions/search', SearchQuestionsCoursesFromTeacherView.as_view()),
]
