from django.contrib import admin
from django.urls import path
from terminology.views import (
    GetHandbooksShort,
    PostHandbook,
    GetHandbooksFull,
    GetRecentHandbookElements,
    GetVersionHandbookElements,
    GetHandbooksActualForDate,
    RecentHandbookElementsValidation,
    ElementHandbookValidation,
    PostHandbookVersion,
    PostHandbookElement,
)

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
      title="API reference",
      default_version='v1',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("handbook/", GetHandbooksFull.as_view()),
    path("handbook/actual", GetHandbooksActualForDate.as_view()),
    path("element/actual/<int:handbook_id>/", GetRecentHandbookElements.as_view()),
    path("element/version/<int:handbook_id>/", GetVersionHandbookElements.as_view()),


    path("element/validate_recent/<int:handbook_id>/", RecentHandbookElementsValidation.as_view()),
    path("element/validate/<int:handbook_id>/", ElementHandbookValidation.as_view()),

    # FOR DEBUG PURPOSES ONLY
    path("handbook/short/", GetHandbooksShort.as_view()),
    path("post_handbook/", PostHandbook.as_view()),
    path("post_handbook_version/", PostHandbookVersion.as_view()),
    path("post_handbook_element/", PostHandbookElement.as_view()),

    #drf-yasg part
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
