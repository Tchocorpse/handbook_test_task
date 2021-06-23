from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.utils.datetime_safe import datetime
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from terminology.models import Handbook, HandbookVersion, HandbookElement
from terminology.serializers import (
    HandbookModelSerializer,
    HandbookFullSerializer,
    HandbookElementSerializer,
    HandbookVersionSerializer,
    HandbookVersionSerializerDeep,
)
import logging
from terminology.utils import get_limit_offset_by_request


# Not in use
class GetHandbooksShort(APIView):
    def get(self, request):
        limit, offset = get_limit_offset_by_request(request)
        handbooks_list = Handbook.objects.all()[offset : offset + limit]
        serialized_data = HandbookModelSerializer(handbooks_list, many=True)
        return JsonResponse({"handbooks_short": serialized_data.data}, status=200)


class GetHandbooksFull(APIView):
    @swagger_auto_schema(
        operation_summary="Getting list of handbooks.",
        operation_description="""
            Optional query params:
            limit: num, default=10
            offset: num, default=0

            Returns list of handbooks and their versions in the amount depends on limit and offset params.
            "handbooks": [{
                "id": num,
                "name": str,
                "short_name": str,
                "description": str,
                "versions": [
                    {
                        "id": num,
                        "version": "str,
                        "starting_date": str,
                        "created": str,
                        "updated": str,
                        "handbook_identifier": num
                    }
                ]
            }]
            """,
    )
    def get(self, request):
        limit, offset = get_limit_offset_by_request(request)
        handbooks_list = Handbook.objects.all()[offset : offset + limit]
        serialized_data = HandbookFullSerializer(handbooks_list, many=True)
        return JsonResponse({"handbooks": serialized_data.data}, status=200)


class GetHandbooksActualForDate(APIView):
    @swagger_auto_schema(
        operation_summary="Getting handbooks versions actual for specified date.",
        operation_description="""
                Required query param:
            date: str  datetime format

            Optional query params:
            limit: num, default=10
            offset: num, default=0

            Returns list of handbooks versions, in the amount depends on limit and offset params.
            "handbooks_actual_for_date": [{
                "id": num,
                "version": str,
                "starting_date": "str,
                "created": str,
                "updated": str,
                "handbook_identifier": {
                    "id": num,
                    "name": str,
                    "short_name": str,
                    "description": str
                }
            }]
        """,
    )
    def get(self, request):
        try:
            date_string = request.GET["date"]
        except KeyError:
            return HttpResponse(status=400)
        limit, offset = get_limit_offset_by_request(request)

        handbooks_list = Handbook.objects.all()[offset : offset + limit]
        versions_qs = HandbookVersion.objects.none()

        dt_date = datetime.strptime(date_string, "%Y-%m-%d %X")
        for handbook in handbooks_list:
            version = (
                HandbookVersion.objects.filter(handbook_identifier=handbook.id)
                .filter(created__lte=dt_date)
                .order_by("-created")[0:1]
                # union() demands both sides to be queryset. Slice the only way i found to do so here.
            )
            versions_qs = versions_qs.union(version)

        serialized_data = HandbookVersionSerializerDeep(versions_qs, many=True)
        return JsonResponse(
            {"handbooks_actual_for_date": serialized_data.data}, status=200
        )


class GetRecentHandbookElements(APIView):
    @swagger_auto_schema(
        operation_summary="Getting specified handbook elements of actual version.",
        operation_description="""
            Optional query params:
            limit: num, default=10
            offset: num, default=0

            Returns list of elements, in the amount depends on limit and offset params.
            "recent_handbook_elements": [{
                'id': num,
                'element_code': str,
                'element_value': str,
                'handbook': [num]
            }]
        """,
    )
    def get(self, request, handbook_id):

        limit, offset = get_limit_offset_by_request(request)

        recent_handbook = HandbookVersion.objects.filter(
            handbook_identifier=handbook_id
        ).latest("created")
        recent_handbook_elements_list = HandbookElement.objects.filter(
            handbook__id=recent_handbook.id
        )[offset : offset + limit]
        serialized_data = HandbookElementSerializer(
            recent_handbook_elements_list, many=True
        )
        return JsonResponse(
            {"recent_handbook_elements": serialized_data.data}, status=200
        )


class GetVersionHandbookElements(APIView):
    @swagger_auto_schema(
        operation_summary="Getting specified handbook version elements.",
        operation_description="""
                Required query param:
            version: str

            Optional query params:
            limit: num, default=10
            offset: num, default=0

            Returns list of elements, in the amount depends on limit and offset params.
            "requested_version_elements": [{
                'id': num,
                'element_code': str,
                'element_value': str,
                'handbook': [num]
            }]
            """,
    )
    def get(self, request, handbook_id):
        try:
            handbook_version = request.GET["version"]
        except KeyError:
            return HttpResponse(status=400)
        limit, offset = get_limit_offset_by_request(request)

        requested_version = HandbookVersion.objects.filter(
            handbook_identifier=handbook_id
        ).get(version=handbook_version)
        requested_elements_list = HandbookElement.objects.filter(
            handbook__id=requested_version.id
        )[offset : offset + limit]

        serialized_data = HandbookElementSerializer(requested_elements_list, many=True)
        return JsonResponse(
            {"requested_version_elements": serialized_data.data}, status=200
        )


class RecentHandbookElementsValidation(APIView):
    def post(self, request, handbook_id):
        """
            Validating specified handbook elements of recent version.

            Expecting json in request body containing:
            'elements': [{
                'id': num,
                'element_code': str,
                'element_value': str,
                'handbook': [num]
            }]

            Returns dict depends on validation result
            "validation_errors": {
                'id_error': str,
                'missing_id': [num],
                'unexpected_id': [num],
                'code_errors': ['element_code_error': {
                    'id': num,
                    'element_code': str,
                    'element_value': str,
                    'handbook': [num]
                }],
                'value_error': ['element_value_error': {
                    'id': num,
                    'element_code': str,
                    'element_value': str,
                    'handbook': [num]
                }],
            }
        """
        try:
            received_elements = request.data["elements"]
        except KeyError:
            return HttpResponse(status=400)

        handbook_element_list = self._get_handbook_element_list(handbook_id)

        error_dict = {}

        id_error, correct_elements = self._id_check(
            received_elements, handbook_element_list
        )
        if id_error:
            error_dict.update(id_error)
        if not correct_elements:
            error_dict.update({"id_error": "no matching id's"})
            return JsonResponse({"validation_errors": error_dict}, status=200)

        id_validated_list = []
        for element in handbook_element_list:
            if element["id"] in correct_elements:
                id_validated_list.append(element)

        element_code_received_list = [x["element_code"] for x in received_elements]
        element_value_received_list = [x["element_value"] for x in received_elements]

        element_code_errors = []
        element_value_errors = []
        for element in id_validated_list:
            if element["element_code"] not in element_code_received_list:
                element_code_errors.append({"element_code_error": element})
            if element["element_value"] not in element_value_received_list:
                element_value_errors.append({"element_value_error": element})

        if element_code_errors:
            error_dict.update({"code_errors": element_code_errors})
        if element_value_errors:
            error_dict.update({"value_errors": element_value_errors})

        return JsonResponse({"validation_errors": error_dict}, status=200)

    def _get_handbook_element_list(self, handbook_id):
        recent_handbook = HandbookVersion.objects.filter(
            handbook_identifier=handbook_id
        ).latest("created")
        handbook_element_qs = HandbookElement.objects.filter(
            handbook__id=recent_handbook.id
        )
        handbook_element_list = HandbookElementSerializer(
            handbook_element_qs, many=True
        ).data

        return handbook_element_list

    def _id_check(self, received_elements, handbook_element_list):
        received_set = set([x["id"] for x in received_elements])
        validation_set = set([x["id"] for x in handbook_element_list])

        missing_elements = list(received_set - validation_set)
        unexpected_elements = list(validation_set - received_set)
        correct_elements = list(validation_set & received_set)

        result = {}
        if missing_elements:
            result.update({"missing_id": missing_elements})
        if unexpected_elements:
            result.update({"unexpected_id": unexpected_elements})
        return result, correct_elements


class ElementHandbookValidation(APIView):
    def post(self, request, handbook_id):
        """
            Validating specified handbook element of specified version.

            Expecting json in request body containing:
            'version': str,
            'element': {
                id: num,
                element_code: str,
                element_value: str,
            }

            Returns dict depends on validation result
            "validation_errors": {
                'id_error': str,
                'element_code_error': str,
                'element_value_error': str,
            }
        """
        try:
            handbook_version = request.data["version"]
            received_element = request.data["element"]
        except KeyError:
            return HttpResponse(status=400)

        raw_handbook = HandbookVersion.objects.filter(
            handbook_identifier=handbook_id
        ).get(version=handbook_version)

        error_dict = {}
        try:
            validating_element = HandbookElement.objects.filter(
                handbook__id=raw_handbook.id
            ).get(pk=received_element["id"])
        except ObjectDoesNotExist:
            error_dict.update({"id_error": f'no such id {received_element["id"]}'})
            return JsonResponse({"validation_errors": error_dict}, status=200)

        if validating_element.element_code != received_element["element_code"]:
            error_dict.update({"element_code_error": validating_element.element_code})
        if validating_element.element_value != received_element["element_value"]:
            error_dict.update({"element_value_error": validating_element.element_value})

        return JsonResponse({"validation_errors": error_dict}, status=200)


class PostHandbook(APIView):
    def post(self, request):
        try:
            received_data_raw = request.data["handbook"]
        except KeyError:
            return HttpResponse(status=400)
        received_data = {
            "name": received_data_raw["name"],
            "short_name": received_data_raw["short_name"],
            "description": received_data_raw["description"],
        }
        serialized_handbook = HandbookModelSerializer(data=received_data)
        if serialized_handbook.is_valid():
            serialized_handbook.save()
            return HttpResponse(status=201)
        else:
            return HttpResponse(status=400)


class PostHandbookVersion(APIView):
    def post(self, request):
        try:
            received_data_raw = request.data["handbook_version"]
        except KeyError:
            return HttpResponse(status=400)
        received_data = {
            "handbook_identifier": received_data_raw["handbook_identifier"],
            "version": received_data_raw["version"],
            "description": received_data_raw["description"],
        }
        try:
            received_data.update({"starting_date": received_data_raw["starting_date"]})
        except KeyError:
            pass
        serialized_handbook_version = HandbookVersionSerializer(data=received_data)
        if serialized_handbook_version.is_valid():
            serialized_handbook_version.save()
            return HttpResponse(status=201)
        else:
            return HttpResponse(status=400)


class PostHandbookElement(APIView):
    def post(self, request):
        try:
            received_data_raw = request.data["handbook_element"]
        except KeyError:
            return HttpResponse(status=400)
        received_data = {
            "handbook": received_data_raw["handbook"],
            "element_code": received_data_raw["element_code"],
            "element_value": received_data_raw["element_value"],
        }
        versions_id = HandbookVersion.objects.filter(
            version__in=received_data["handbook"]
        ).values("id")
        prepared_id = []
        for v_id in versions_id:
            prepared_id.append(v_id["id"])
        received_data.update({"handbook": prepared_id})
        serialized_element_version = HandbookElementSerializer(data=received_data)
        if serialized_element_version.is_valid():
            serialized_element_version.save()
            return HttpResponse(status=201)
        else:
            return HttpResponse(status=400)
