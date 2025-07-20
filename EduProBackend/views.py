from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


def get_all_patterns_generator(lis, acc=None):
    if acc is None:
        acc = []
    if not lis:
        return
    l = lis[0]
    if isinstance(l, URLPattern):
        yield acc + [str(l.pattern)]
    elif isinstance(l, URLResolver):
        print(l.pattern)
        yield from get_all_patterns_generator(l.url_patterns, acc + [str(l.pattern)])
    yield from get_all_patterns_generator(lis[1:], acc)


class GetApiEndPointsView(APIView):

    """
    return all api end points
    """

    permission_classes = [AllowAny]

    def get(self, request):
        urls_list = []
        current_site = request.build_absolute_uri("/")
        # current_site = request.META["HTTP_HOST"]
        print(current_site)

        for p in get_all_patterns_generator(get_resolver().url_patterns):
            if p[0] != "admin/":
                urls_list.append(current_site + "".join(p))

        return Response(urls_list)
