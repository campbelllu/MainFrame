"""
URL configuration for mainframe project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# from helloThere import views as htviews #see note below

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("investor_center.urls")),

    # path('helloThere/', htviews.home, name='home'), #bad practice, hard to scale or share app to other projects. left for example.
    #path('mf.io/jenkins', 'mf.io:8080', name='jenkins-reroute'),
    #url(RedirectView.as_view(url='mf.io/jenkins')),
]
