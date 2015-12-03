# -*- coding: utf-8 -*-
from openprocurement.api.models import get_now
from openprocurement.api.utils import update_logging_context
from openprocurement.api.validation import validate_json_data, validate_data
from openprocurement.planning.api.models import Plan


def validate_plan_data(request):
    update_logging_context(request, {'plan_id': '__new__'})

    data = validate_json_data(request)
    if data is None:
        return

    model = request.plan_from_data(data, create=False)
    return validate_data(request, model, data=data)


def validate_patch_plan_data(request):
    return validate_data(request, Plan, True)


def validate_plan_plan_data(request):
    data = validate_patch_plan_data(request)
    if data is None:
        data = {}
    request.validated['data'] = data