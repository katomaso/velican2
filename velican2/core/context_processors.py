from velican2.core.models import Site

def user_has_site(request):
    return {
        'user_has_site': Site.objects.filter(admin=request.user).exists() if request.user.is_authenticated else False
    }

