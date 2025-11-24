from django.db import models
from django.contrib.auth.models import User
import datetime

class Colaborador(models.Model):
    ROL_CHOICES = (
        ('admin', 'Administrador'),
        ('estilista', 'Estilista'),
        ('recepcionista', 'Recepcionista'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    sueldo = models.PositiveIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.get_rol_display()})"

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    contacto_nombre = models.CharField(max_length=200, null=True, blank=True)
    contacto_telefono = models.CharField(max_length=20, null=True, blank=True)
    contacto_email = models.EmailField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    precio_costo = models.PositiveIntegerField(default=0)
    precio_venta = models.PositiveIntegerField(default=0)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock_actual})"
    
    def esta_bajo_minimos(self):
        return self.stock_actual <= self.stock_minimo

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Servicio(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    precio = models.PositiveIntegerField(default=0)
    duracion_estimada = models.CharField(max_length=50, null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} (${self.precio:,})"

class Atencion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    estilista = models.ForeignKey(Colaborador, on_delete=models.PROTECT)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    servicios = models.ManyToManyField(Servicio)
    productos_consumidos = models.ManyToManyField(Producto, through='ProductoConsumido')
    descuento_cumpleanos = models.BooleanField(default=False)
    precio_final = models.PositiveIntegerField(default=0)
    pagado = models.BooleanField(default=False)

    monto_pagado = models.PositiveIntegerField(default=0) 
    vuelto = models.PositiveIntegerField(default=0)
    metodo_pago = models.CharField(max_length=50, null=True, blank=True)
    codigo_transaccion = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Atención a {self.cliente.nombre} el {self.fecha_hora.strftime('%d-%m-%Y')}"

class ProductoConsumido(models.Model):
    atencion = models.ForeignKey(Atencion, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"