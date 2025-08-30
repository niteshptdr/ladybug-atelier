# ladybug/middleware.py

from datetime import date
from .models import SiteHit
from django.db.models import F
from django.conf import settings

class WebsiteHitCounterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if not request.path.startswith('/admin/') and not is_ajax:
            if not request.session.get('hit_counted', False):
                today = date.today()
                SiteHit.objects.get_or_create(date=today)
                SiteHit.objects.filter(date=today).update(count=F('count') + 1)
                request.session['hit_counted'] = True  # Count once per session

        response = self.get_response(request)
        return response

