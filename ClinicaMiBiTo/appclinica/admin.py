from django.contrib import admin
from .models import (
    Colaborador, 
    Cliente, 
    Proveedor, 
    Producto, 
    Servicio, 
    Atencion, 
    ProductoConsumido
)

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'rut')
    list_filter = ('rol',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'rut')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email', 'fecha_nacimiento', 'activo')
    list_filter = ('activo',) 
    search_fields = ('nombre', 'telefono', 'email', 'rut')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto_nombre', 'contacto_telefono', 'contacto_email')
    search_fields = ('nombre', 'contacto_nombre')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 
        'precio_venta', 
        'stock_actual', 
        'stock_minimo', 
        'esta_bajo_minimos'
    )
    search_fields = ('nombre',)
    list_filter = ('proveedor',)
    
    @admin.display(boolean=True, description='¿Bajo Mínimos?')
    def esta_bajo_minimos(self, obj):
        return obj.esta_bajo_minimos()

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'duracion_estimada')
    search_fields = ('nombre',)

class ProductoConsumidoInline(admin.TabularInline):
    model = ProductoConsumido
    extra = 1 
    autocomplete_fields = ('producto',) 

@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = (
        'cliente', 
        'estilista', 
        'fecha_hora', 
        'precio_final', 
        'descuento_cumpleanos'
    )
    list_filter = ('fecha_hora', 'estilista', 'descuento_cumpleanos')
    search_fields = ('cliente__nombre', 'estilista__user__username')
    autocomplete_fields = ('cliente', 'estilista')
    filter_horizontal = ('servicios',) 
    inlines = [ProductoConsumidoInline]