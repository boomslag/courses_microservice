from django.contrib import admin

# Register your models here.
from .models import *

class CourseAdmin(admin.ModelAdmin):
    list_display=('id','name','title', 'views', 'students',)
    list_display_links = ('id', 'name', )
    list_filter = ('name', 'views', 'students', )
    list_editable = ('title', 'views', 'students', )
    search_fields = ('name','title','description', 'views', 'students', )
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25
admin.site.register(Category, CourseAdmin)