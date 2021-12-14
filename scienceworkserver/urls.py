"""scienceworkserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path
from . import coordinates_parser

urlpatterns = [
    path('admin/', admin.site.urls),
    path('geodata/get/', coordinates_parser.get_coordinates),
    path('geodata/globe/', coordinates_parser.globe),
    path('geodata/get_mapped/', coordinates_parser.get_mapped_coordinates),
    path('geodata/mapped_coord/', coordinates_parser.mapped_coord),
    path('geodata/coords/', coordinates_parser.coords),
    path('geodata/bezier_curve/', coordinates_parser.bezier_curve_with_groups),#bezier_curve_with_groups bezier_curve
    path('geodata/auroras_data/', coordinates_parser.auroras_data),#auroras_data connect_anomalies
    path('geodata/connect_anomalies/', coordinates_parser.connect_anomalies),
]
