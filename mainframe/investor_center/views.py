from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return render(request, 'investor_center/index.html', {})
    #HttpResponse('<h1>Welcome to The Investor Center.</h1>')

def v1(request):
    return HttpResponse('<h1>One Piston. Very unique ICEngine.</h1>')