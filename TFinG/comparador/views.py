from django.shortcuts import render
from .main import calcular_precios


# Create your views here.

def empezar(request):
   
    precioMasBarato, seriesPrecios = calcular_precios()
    print(precioMasBarato)
    print(seriesPrecios)

    context = {
        'seriesPrecios': seriesPrecios,
        'precioMasBarato': precioMasBarato
    }
    return render (request,'comparador/resultado.html',context)
