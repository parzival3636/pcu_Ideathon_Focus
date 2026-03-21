"""
Request Logging Middleware - logs EVERY request to stdout with flush=True for Windows.
"""
import sys
import time
from django.http import HttpResponse

print("\n" + "*"*40, flush=True)
print("[DEBUG] RequestLoggerMiddleware file loaded", flush=True)
print("*"*40 + "\n", flush=True)

class RequestLoggerMiddleware:
    """Log every single request and response - guaranteed visible on Windows."""

    def __init__(self, get_response):
        self.get_response = get_response
        print("[DEBUG] RequestLoggerMiddleware initialized", flush=True)
        sys.stdout.flush()

    def __call__(self, request):
        # 1. HARD TEST BYPASS - if this doesn't show in browser, the request never reached Django
        if request.path == '/ping':
            print("!!! PING RECEIVED - Bypassing all logic !!!", flush=True)
            sys.stdout.flush()
            return HttpResponse("PONG - Django is alive!")

        start = time.time()
        method = request.method
        path = request.path
        user = getattr(request, 'user', 'anon')

        print(f"\n{'='*80}", flush=True)
        print(f"REQUEST RECEIVED: {method} {path} (user: {user})", flush=True)
        
        if 'HTTP_ORIGIN' in request.META:
            print(f"  Origin: {request.META['HTTP_ORIGIN']}", flush=True)
        
        sys.stdout.flush()

        # Let it through to other middlewares
        response = self.get_response(request)

        elapsed = (time.time() - start) * 1000
        status = response.status_code
        print(f"RESPONSE READY: {status} ({elapsed:.0f}ms) {method} {path}", flush=True)
        print(f"{'='*80}\n", flush=True)
        sys.stdout.flush()

        return response
