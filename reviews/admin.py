from django.contrib import admin

from .models import Review, TrackedApp

admin.site.register(TrackedApp)
admin.site.register(Review)
