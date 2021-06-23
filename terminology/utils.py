def get_limit_offset_by_request(request):
    try:
        limit = request.GET["limit"]
        offset = request.GET["offset"]
    except KeyError:
        limit = 10
        offset = 0
    return limit, offset
