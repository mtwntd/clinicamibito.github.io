from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Producto, 
    Cliente, 
    Colaborador, 
    Proveedor, 
    Servicio, 
    Atencion, 
    ProductoConsumido
)
import datetime

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio_venta', 'stock_actual'] 

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'rut', 'telefono', 'email', 'fecha_nacimiento']

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__' 
        
class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'

class ProductoConsumidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.ReadOnlyField(source='producto.nombre')
    producto_precio = serializers.ReadOnlyField(source='producto.precio_venta')
    
    class Meta:
        model = ProductoConsumido
        fields = ['id', 'producto', 'producto_nombre', 'producto_precio', 'cantidad']

class AtencionSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.ReadOnlyField(source='cliente.nombre')
    estilista_nombre = serializers.ReadOnlyField(source='estilista.user.first_name')

    servicios_details = ServicioSerializer(source='servicios', many=True, read_only=True)
    productos_details = ProductoConsumidoSerializer(source='productoconsumido_set', many=True, read_only=True)

    class Meta:
        model = Atencion
        fields = [
            'id', 'cliente', 'cliente_nombre', 'estilista', 'estilista_nombre',
            'fecha_hora', 'descuento_cumpleanos', 'precio_final',
            'servicios_details', 'productos_details', 
            'pagado', 'monto_pagado', 'vuelto', 'metodo_pago'
        ]

class ColaboradorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    rol = serializers.CharField(source='get_rol_display')

    id = serializers.ReadOnlyField(source='pk')

    estado_actual = serializers.SerializerMethodField()

    class Meta:
        model = Colaborador
        fields = ['id', 'username', 'first_name', 'last_name', 'rol', 'rut', 'sueldo', 'estado_actual']

    def get_estado_actual(self, obj):
        hoy = datetime.date.today()
        
        atencion_activa = Atencion.objects.filter(
            estilista=obj, 
            fecha_hora__date=hoy,
            precio_final=0 
        ).exists()
        
        return "Ocupado" if atencion_activa else "Disponible"