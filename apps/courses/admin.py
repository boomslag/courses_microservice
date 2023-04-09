from django.contrib import admin

from .models import *

class CourseAdmin(admin.ModelAdmin):
    # exclude = ('id','token_id',)
    list_display=('id','title', 'price', 'sold',)
    list_display_links = ('id', 'title', )
    list_filter = ('category', )
    list_editable = ('price', )
    search_fields = ('title', 'description', )
    list_per_page = 25
    readonly_fields = ('author','id','token_id',)
admin.site.register(Course, CourseAdmin)

class RateAdmin(admin.ModelAdmin):
    exclude = ('id',)
admin.site.register(Rate,RateAdmin)

class ViewedCoursesLibraryAdmin(admin.ModelAdmin):
    exclude = ('id',)
admin.site.register(ViewedCoursesLibrary,ViewedCoursesLibraryAdmin)

class SectionAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('user',)
    list_display=('id','title',)
    list_display_links = ('id', 'title', )
    list_filter = ('id', )
    search_fields = ('id', 'title' )
    list_per_page = 25
admin.site.register(Section, SectionAdmin)

class EpisodeAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('section_uuid','user',)
    list_display=('id','title',)
    list_display_links = ('id', 'title', )
    list_filter = ('id', )
    search_fields = ('id', 'content', 'title' )
    list_per_page = 25
admin.site.register(Episode, EpisodeAdmin)

class ResourceAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('user',)
admin.site.register(Resource,ResourceAdmin)

class WhatLearntAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('user',)
admin.site.register(WhatLearnt,WhatLearntAdmin)

class RequisiteAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('user',)
admin.site.register(Requisite,RequisiteAdmin)

class SellersAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('author','address','polygon_address',)
admin.site.register(Sellers,SellersAdmin)

class WhoIsForAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('user',)
admin.site.register(WhoIsFor,WhoIsForAdmin)

class ImageAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('author',)
admin.site.register(Image,ImageAdmin)

class VideoAdmin(admin.ModelAdmin):
    exclude = ('id',)
    readonly_fields = ('author',)
admin.site.register(Video,VideoAdmin)

class ViewCountAdmin(admin.ModelAdmin):
    exclude = ('id',)
admin.site.register(ViewCount,ViewCountAdmin)

class QuestionAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(Question,QuestionAdmin)

class AnswerAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
admin.site.register(Answer,AnswerAdmin)


class PaidAdmin(admin.ModelAdmin):
    list_display=('id','user', 'date_created',)
    list_display_links = ('id', 'user', )
    list_filter = ('user',)
    # list_editable = ('price', )
    search_fields = ('user', )
    list_per_page = 25
admin.site.register(Paid, PaidAdmin)


class PaidItemAdmin(admin.ModelAdmin):
    list_display=('id', 'course',)
    list_display_links = ('id','course', )
    list_filter = ('course',)
    # list_editable = ('price', )
    search_fields = ('course', )
    list_per_page = 25
admin.site.register(PaidItem, PaidItemAdmin)
admin.site.register(WishList)
admin.site.register(Like)
admin.site.register(Dislike)