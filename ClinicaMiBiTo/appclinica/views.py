from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Q
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

from .models import (
    Colaborador, 
    Producto, 
    Cliente, 
    Servicio, 
    Atencion, 
    ProductoConsumido, 
    Proveedor
)
from .serializers import (
    ProductoSerializer, 
    ClienteSerializer, 
    ColaboradorSerializer, 
    ProveedorSerializer,
    ServicioSerializer,
    AtencionSerializer,
    ProductoConsumidoSerializer
)
import datetime

def inicio(request):
    return render(request, 'inicio.html')

def tratamientos_esteticos(request):
    return render(request, 'inicio.html') 

def tratamientos_corporales(request):
    return render(request, 'inicio.html')

def cosmeticos(request):
    return render(request, 'inicio.html')

def depilaciones(request):
    return render(request, 'inicio.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio') 
    if request.method == 'POST':
        usuario = request.POST.get('username')
        clave = request.POST.get('password')
        user = authenticate(request, username=usuario, password=clave)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido/a de nuevo, {user.username}!')
            return redirect('inicio') 
        else:
            messages.error(request, '¡Usuario o contraseña incorrectos!')
            return render(request, 'index.html')
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    messages.success(request, '¡Has cerrado sesión exitosamente!')
    return redirect('inicio')

@login_required
def dashboard_admin(request):
    lista_productos = Producto.objects.filter(activo=True)
    context = {'productos': lista_productos}
    return render(request, 'Administrador/dashboard_admin.html', context)

@login_required
def dashboard_estilista(request):
    return render(request, 'Estilista/dashboard_estilista.html')

@login_required
def dashboard_recepcionista(request):
    lista_clientes = Cliente.objects.filter(activo=True) 
    context = {'clientes': lista_clientes}
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        return render(request, 'Administrador/admin_lista_clientes.html', context)
    else:
        return render(request, 'Recepcionista/dashboard_recepcionista.html', context)

@login_required
def estilista_lista_productos(request):
    productos = Producto.objects.filter(activo=True)
    context = {'productos': productos}
    return render(request, 'Estilista/estilista_lista_productos.html', context)

@login_required
def estilista_lista_bajominimos(request):
    productos_bajos = Producto.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    )
    context = {'productos': productos_bajos}
    return render(request, 'Estilista/estilista_lista_bajominimos.html', context)

@login_required
def estilista_buscar_cliente(request):
    query = request.GET.get('q', '')
    clientes_encontrados = []
    if query:
        clientes_encontrados = Cliente.objects.filter(
            Q(nombre__icontains=query) | 
            Q(rut__icontains=query),
            activo=True 
        )
    context = {'query': query, 'clientes': clientes_encontrados}
    return render(request, 'Estilista/estilista_buscar_cliente.html', context)

@login_required
def estilista_crear_atencion(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    estilista_colaborador = request.user.colaborador
    nueva_atencion = Atencion.objects.create(
        cliente=cliente,
        estilista=estilista_colaborador
    )
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        return redirect('admin_detalle_atencion', atencion_id=nueva_atencion.id)
    return redirect('estilista_detalle_atencion', atencion_id=nueva_atencion.id)

@login_required
def estilista_detalle_atencion(request, atencion_id):
    atencion = get_object_or_404(Atencion, id=atencion_id)
    cliente = atencion.cliente
    
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        template_name = 'Administrador/admin_detalle_atencion.html'
    else:
        template_name = 'Estilista/estilista_form_servicio.html'
    
    if request.method == 'POST':
        if 'accion' in request.POST and request.POST['accion'] == 'add_servicio':
            servicio_id = request.POST.get('servicio_id')
            if servicio_id:
                servicio_a_anadir = get_object_or_404(Servicio, id=servicio_id)
                atencion.servicios.add(servicio_a_anadir)
                messages.success(request, f'¡Servicio "{servicio_a_anadir.nombre}" añadido!')
                return redirect(request.path) 

        if 'accion' in request.POST and request.POST['accion'] == 'add_producto':
            producto_id = request.POST.get('producto_id')
            try:
                cantidad = int(request.POST.get('cantidad', 1))
            except ValueError:
                cantidad = 1
            if producto_id and cantidad > 0:
                producto_a_anadir = get_object_or_404(Producto, id=producto_id)
                ProductoConsumido.objects.create(
                    atencion=atencion,
                    producto=producto_a_anadir,
                    cantidad=cantidad
                )
                messages.success(request, f'¡{cantidad} x "{producto_a_anadir.nombre}" añadido al resumen!')
                return redirect(request.path)
    
    hoy = datetime.date.today()
    aplica_descuento = False
    if cliente.fecha_nacimiento.month == hoy.month and cliente.fecha_nacimiento.day == hoy.day:
        if not atencion.descuento_cumpleanos:
            aplica_descuento = True
            atencion.descuento_cumpleanos = True
            atencion.save()
    
    servicios_en_atencion = atencion.servicios.all()
    productos_en_atencion = ProductoConsumido.objects.filter(atencion=atencion)
    servicios_disponibles = Servicio.objects.filter(activo=True) 
    
    productos_disponibles = Producto.objects.filter(
        activo=True, 
        stock_actual__gt=0
    ) 
    
    context = {
        'atencion': atencion,
        'cliente': cliente,
        'aplica_descuento': aplica_descuento,
        'servicios_en_atencion': servicios_en_atencion,
        'productos_en_atencion': productos_en_atencion,
        'servicios_disponibles': servicios_disponibles,
        'productos_disponibles': productos_disponibles,
    }
    return render(request, template_name, context)

@login_required
def estilista_finalizar_atencion(request, atencion_id):
    atencion = get_object_or_404(Atencion, id=atencion_id)
    productos_consumidos = ProductoConsumido.objects.filter(atencion=atencion)
    
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        redirect_url = 'admin_lista_atenciones'
        error_redirect_url = 'admin_detalle_atencion'
    else:
        redirect_url = 'dashboard_estilista'
        error_redirect_url = 'estilista_detalle_atencion'

    for item in productos_consumidos:
        if item.producto.stock_actual < item.cantidad:
            messages.error(request, f'¡Error al finalizar! No hay stock suficiente de "{item.producto.nombre}". Solo quedan {item.producto.stock_actual} unidades.')
            return redirect(error_redirect_url, atencion_id=atencion_id)

    for item in productos_consumidos:
        item.producto.stock_actual -= item.cantidad
        item.producto.save()
        if item.producto.esta_bajo_minimos():
            messages.warning(request, f'¡ALERTA! El producto "{item.producto.nombre}" ha quedado bajo el stock mínimo.')
            
    total_servicios = atencion.servicios.all().aggregate(total=Sum('precio'))['total'] or 0
    total_productos = 0
    for item in productos_consumidos:
        total_productos += item.cantidad * item.producto.precio_venta
        
    subtotal = total_servicios + total_productos
    
    precio_final = subtotal
    if atencion.descuento_cumpleanos:
        precio_final = subtotal * 0.80 
        
    atencion.precio_final = precio_final
    atencion.save()
    
    messages.success(request, f'¡Atención Finalizada! Total a pagar: ${precio_final:,.0f}')
    return redirect(redirect_url)

@login_required
def estilista_cancelar_atencion(request, atencion_id):
    atencion = get_object_or_404(Atencion, id=atencion_id)
    
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        redirect_url = 'admin_lista_atenciones'
    else:
        redirect_url = 'dashboard_estilista'

    if atencion.precio_final == 0:
        atencion.delete()
        messages.info(request, 'Atención cancelada correctamente.')
    else:
        messages.error(request, 'Esta atención ya fue finalizada, no se puede cancelar.')
    return redirect(redirect_url)

@login_required
def estilista_mis_atenciones(request):
    try:
        estilista_colaborador = request.user.colaborador
        atenciones = Atencion.objects.filter(
            estilista=estilista_colaborador
        ).order_by('-fecha_hora')
        context = {'atenciones': atenciones}
        return render(request, 'Estilista/estilista_mis_atenciones.html', context)
    except Colaborador.DoesNotExist:
        messages.error(request, 'No se pudo encontrar tu perfil de colaborador.')
        return redirect('dashboard_estilista')

@login_required
def recepcionista_crear_cliente(request):
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        template_name = 'Administrador/admin_form_cliente.html'
    else:
        template_name = 'Recepcionista/recepcionista_form_cliente.html'
        
    if request.method == 'POST':
        try:
            nuevo_cliente = Cliente.objects.create(
                nombre=request.POST.get('nombre'),
                rut=request.POST.get('rut'),
                telefono=request.POST.get('telefono'),
                email=request.POST.get('email'),
                fecha_nacimiento=request.POST.get('fecha_nacimiento'),
                activo=True
            )
            messages.success(request, f'¡Cliente "{nuevo_cliente.nombre}" creado exitosamente!')
            if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
                return redirect('admin_lista_clientes')
            return redirect('dashboard_recepcionista')
        except Exception as e:
            messages.error(request, f'Error al crear el cliente: {e}')
            context = { 'form_data': request.POST, 'cliente': None }
            return render(request, template_name, context)
            
    context = { 'cliente': None }
    return render(request, template_name, context)

@login_required
def recepcionista_modificar_cliente(request, cliente_id):
    cliente_a_modificar = get_object_or_404(Cliente, id=cliente_id)
    
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        template_name = 'Administrador/admin_form_cliente.html'
    else:
        template_name = 'Recepcionista/recepcionista_form_cliente.html'

    if request.method == 'POST':
        try:
            cliente_a_modificar.nombre = request.POST.get('nombre')
            cliente_a_modificar.rut = request.POST.get('rut')
            cliente_a_modificar.telefono = request.POST.get('telefono')
            cliente_a_modificar.email = request.POST.get('email')
            cliente_a_modificar.fecha_nacimiento = request.POST.get('fecha_nacimiento')
            cliente_a_modificar.save()
            messages.success(request, f'¡Cliente "{cliente_a_modificar.nombre}" modificado exitosamente!')
            
            if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
                return redirect('admin_lista_clientes')
            return redirect('dashboard_recepcionista')
        except Exception as e:
            messages.error(request, f'Error al modificar el cliente: {e}')
            context = { 'cliente': cliente_a_modificar, 'form_data': request.POST }
            return render(request, template_name, context)
            
    context = { 'cliente': cliente_a_modificar }
    return render(request, template_name, context)

@login_required
def recepcionista_dar_baja_cliente(request, cliente_id):
    cliente_a_bajar = get_object_or_404(Cliente, id=cliente_id)
    cliente_a_bajar.activo = False
    cliente_a_bajar.save()
    messages.success(request, f'¡Cliente "{cliente_a_bajar.nombre}" ha sido dado de baja!')
    
    if request.user.is_superuser or (hasattr(request.user, 'colaborador') and request.user.colaborador.rol == 'admin'):
        return redirect('admin_lista_clientes')
    return redirect('dashboard_recepcionista')

@login_required
def admin_crear_producto(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            precio_costo = request.POST.get('precio_costo', 0)
            precio_venta = request.POST.get('precio_venta', 0)
            stock_actual = request.POST.get('stock_actual', 0)
            stock_minimo = request.POST.get('stock_minimo', 5)
            proveedor_id = request.POST.get('proveedor_id')
            proveedor = None
            if proveedor_id:
                proveedor = get_object_or_404(Proveedor, id=proveedor_id)
            Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                precio_costo=precio_costo,
                precio_venta=precio_venta,
                stock_actual=stock_actual,
                stock_minimo=stock_minimo,
                proveedor=proveedor,
                activo=True
            )
            messages.success(request, f'¡Producto "{nombre}" creado exitosamente!')
            return redirect('dashboard_admin')
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {e}')
            context = {
                'form_data': request.POST,
                'proveedores': Proveedor.objects.filter(activo=True)
            }
            return render(request, 'Administrador/admin_form_producto.html', context)
    context = {'proveedores': Proveedor.objects.filter(activo=True)}
    return render(request, 'Administrador/admin_form_producto.html', context)

@login_required
def admin_modificar_producto(request, producto_id):
    producto_a_modificar = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        try:
            producto_a_modificar.nombre = request.POST.get('nombre')
            producto_a_modificar.descripcion = request.POST.get('descripcion')
            producto_a_modificar.precio_costo = request.POST.get('precio_costo', 0)
            producto_a_modificar.precio_venta = request.POST.get('precio_venta', 0)
            producto_a_modificar.stock_actual = request.POST.get('stock_actual', 0)
            producto_a_modificar.stock_minimo = request.POST.get('stock_minimo', 5)
            proveedor_id = request.POST.get('proveedor_id')
            if proveedor_id:
                producto_a_modificar.proveedor = get_object_or_404(Proveedor, id=proveedor_id)
            else:
                producto_a_modificar.proveedor = None
            producto_a_modificar.save()
            messages.success(request, f'¡Producto "{producto_a_modificar.nombre}" modificado exitosamente!')
            return redirect('dashboard_admin')
        except Exception as e:
            messages.error(request, f'Error al modificar el producto: {e}')
            context = {
                'producto': producto_a_modificar,
                'form_data': request.POST,
                'proveedores': Proveedor.objects.filter(activo=True)
            }
            return render(request, 'Administrador/admin_form_producto.html', context)
    context = {
        'producto': producto_a_modificar,
        'proveedores': Proveedor.objects.filter(activo=True)
    }
    return render(request, 'Administrador/admin_form_producto.html', context)

@login_required
def admin_eliminar_producto(request, producto_id):
    producto_a_eliminar = get_object_or_404(Producto, id=producto_id)
    producto_a_eliminar.activo = False
    producto_a_eliminar.save()
    messages.success(request, f'¡Producto "{producto_a_eliminar.nombre}" ha sido eliminado (desactivado)!')
    return redirect('dashboard_admin')

@login_required
def admin_lista_proveedores(request):
    lista_proveedores = Proveedor.objects.filter(activo=True)
    context = { 'proveedores': lista_proveedores }
    return render(request, 'Administrador/admin_lista_proveedores.html', context)

@login_required
def admin_crear_proveedor(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            contacto_nombre = request.POST.get('contacto_nombre')
            contacto_telefono = request.POST.get('contacto_telefono')
            contacto_email = request.POST.get('contacto_email')
            Proveedor.objects.create(
                nombre=nombre,
                contacto_nombre=contacto_nombre,
                contacto_telefono=contacto_telefono,
                contacto_email=contacto_email,
                activo=True
            )
            messages.success(request, f'¡Proveedor "{nombre}" creado exitosamente!')
            return redirect('admin_lista_proveedores')
        except Exception as e:
            messages.error(request, f'Error al crear el proveedor: {e}')
            context = { 'form_data': request.POST }
            return render(request, 'Administrador/admin_form_proveedor.html', context)
    return render(request, 'Administrador/admin_form_proveedor.html')

@login_required
def admin_modificar_proveedor(request, proveedor_id):
    proveedor_a_modificar = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == 'POST':
        try:
            proveedor_a_modificar.nombre = request.POST.get('nombre')
            proveedor_a_modificar.contacto_nombre = request.POST.get('contacto_nombre')
            proveedor_a_modificar.contacto_telefono = request.POST.get('contacto_telefono')
            proveedor_a_modificar.contacto_email = request.POST.get('contacto_email')
            proveedor_a_modificar.save()
            messages.success(request, f'¡Proveedor "{proveedor_a_modificar.nombre}" modificado exitosamente!')
            return redirect('admin_lista_proveedores')
        except Exception as e:
            messages.error(request, f'Error al modificar el proveedor: {e}')
            context = { 'proveedor': proveedor_a_modificar, 'form_data': request.POST }
            return render(request, 'Administrador/admin_form_proveedor.html', context)
    context = { 'proveedor': proveedor_a_modificar }
    return render(request, 'Administrador/admin_form_proveedor.html', context)

@login_required
def admin_eliminar_proveedor(request, proveedor_id):
    proveedor_a_eliminar = get_object_or_404(Proveedor, id=proveedor_id)
    proveedor_a_eliminar.activo = False
    proveedor_a_eliminar.save()
    messages.success(request, f'¡Proveedor "{proveedor_a_eliminar.nombre}" ha sido eliminado (desactivado)!')
    return redirect('admin_lista_proveedores')

@login_required
def admin_lista_colaboradores(request):
    lista_colaboradores = Colaborador.objects.filter(user__is_active=True)
    context = { 'colaboradores': lista_colaboradores }
    return render(request, 'Administrador/admin_lista_colaboradores.html', context)

@login_required
def admin_crear_colaborador(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        clave = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        rol = request.POST.get('rol')
        rut = request.POST.get('rut')
        sueldo = request.POST.get('sueldo', 0)
        try:
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Error: El nombre de usuario "{username}" ya existe.')
                raise Exception("Username duplicado")
            nuevo_user = User.objects.create_user(
                username=username,
                password=clave,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            Colaborador.objects.create(
                user=nuevo_user,
                rol=rol,
                rut=rut,
                sueldo=sueldo
            )
            messages.success(request, f'¡Colaborador "{username}" creado exitosamente!')
            return redirect('admin_lista_colaboradores')
        except Exception as e:
            messages.error(request, f'Error al crear el colaborador: {e}')
            context = { 'form_data': request.POST }
            return render(request, 'Administrador/admin_form_colaborador.html', context)
    return render(request, 'Administrador/admin_form_colaborador.html')

@login_required
def admin_modificar_colaborador(request, colaborador_user_id):
    colaborador_a_modificar = get_object_or_404(Colaborador, user__id=colaborador_user_id)
    user_a_modificar = colaborador_a_modificar.user
    if request.method == 'POST':
        try:
            user_a_modificar.email = request.POST.get('email')
            user_a_modificar.first_name = request.POST.get('first_name')
            user_a_modificar.last_name = request.POST.get('last_name')
            nueva_clave = request.POST.get('password')
            if nueva_clave:
                user_a_modificar.set_password(nueva_clave)
            user_a_modificar.save()
            
            colaborador_a_modificar.rol = request.POST.get('rol')
            colaborador_a_modificar.rut = request.POST.get('rut')
            colaborador_a_modificar.sueldo = request.POST.get('sueldo', 0)
            colaborador_a_modificar.save()
            
            messages.success(request, f'¡Colaborador "{user_a_modificar.username}" modificado exitosamente!')
            return redirect('admin_lista_colaboradores')
        except Exception as e:
            messages.error(request, f'Error al modificar el colaborador: {e}')
            context = { 'colaborador': colaborador_a_modificar, 'form_data': request.POST }
            return render(request, 'Administrador/admin_form_colaborador.html', context)
    context = { 'colaborador': colaborador_a_modificar }
    return render(request, 'Administrador/admin_form_colaborador.html', context)

@login_required
def admin_eliminar_colaborador(request, colaborador_user_id):
    user_a_eliminar = get_object_or_404(User, id=colaborador_user_id)
    user_a_eliminar.is_active = False
    user_a_eliminar.save()
    messages.success(request, f'¡Colaborador "{user_a_eliminar.username}" ha sido eliminado (desactivado)!')
    return redirect('admin_lista_colaboradores')

@login_required
def admin_reponer_stock(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        try:
            cantidad_a_reponer = int(request.POST.get('cantidad', 0))
            if cantidad_a_reponer <= 0:
                messages.error(request, 'La cantidad a reponer debe ser mayor a cero.')
            else:
                producto.stock_actual += cantidad_a_reponer
                producto.save()
                messages.success(request, f'¡Stock de "{producto.nombre}" actualizado! Nuevo stock: {producto.stock_actual}')
                
                if not producto.esta_bajo_minimos():
                    messages.info(request, f'El producto "{producto.nombre}" ya no está bajo el stock mínimo.')
                return redirect('dashboard_admin')
        except ValueError:
            messages.error(request, 'Error: La cantidad debe ser un número.')
        except Exception as e:
            messages.error(request, f'Error inesperado: {e}')
    context = { 'producto': producto }
    return render(request, 'Administrador/admin_form_stock.html', context)

@login_required
def admin_lista_servicios(request):
    lista_servicios = Servicio.objects.filter(activo=True)
    context = { 'servicios': lista_servicios }
    return render(request, 'Administrador/admin_lista_servicios.html', context)

@login_required
def admin_crear_servicio(request):
    if request.method == 'POST':
        try:
            Servicio.objects.create(
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion'),
                precio=request.POST.get('precio', 0),
                duracion_estimada=request.POST.get('duracion_estimada'),
                activo=True
            )
            messages.success(request, '¡Servicio creado exitosamente!')
            return redirect('admin_lista_servicios')
        except Exception as e:
            messages.error(request, f'Error al crear el servicio: {e}')
            context = { 'form_data': request.POST }
            return render(request, 'Administrador/admin_form_servicio.html', context)
    return render(request, 'Administrador/admin_form_servicio.html')

@login_required
def admin_modificar_servicio(request, servicio_id):
    servicio_a_modificar = get_object_or_404(Servicio, id=servicio_id)
    if request.method == 'POST':
        try:
            servicio_a_modificar.nombre = request.POST.get('nombre')
            servicio_a_modificar.descripcion = request.POST.get('descripcion')
            servicio_a_modificar.precio = request.POST.get('precio', 0)
            servicio_a_modificar.duracion_estimada = request.POST.get('duracion_estimada')
            servicio_a_modificar.save()
            messages.success(request, '¡Servicio modificado exitosamente!')
            return redirect('admin_lista_servicios')
        except Exception as e:
            messages.error(request, f'Error al modificar el servicio: {e}')
            context = { 'servicio': servicio_a_modificar, 'form_data': request.POST }
            return render(request, 'Administrador/admin_form_servicio.html', context)
    context = { 'servicio': servicio_a_modificar }
    return render(request, 'Administrador/admin_form_servicio.html', context)

@login_required
def admin_eliminar_servicio(request, servicio_id):
    servicio_a_eliminar = get_object_or_404(Servicio, id=servicio_id)
    servicio_a_eliminar.activo = False 
    servicio_a_eliminar.save()
    messages.success(request, f'¡Servicio "{servicio_a_eliminar.nombre}" ha sido eliminado (desactivado)!')
    return redirect('admin_lista_servicios')

@login_required
def admin_lista_atenciones(request):
    atenciones = Atencion.objects.all().order_by('-fecha_hora')
    context = { 'atenciones': atenciones }
    return render(request, 'Administrador/admin_lista_atenciones.html', context)

@login_required
def recepcionista_lista_cobros(request):
    atenciones_pendientes = Atencion.objects.filter(precio_final__gt=0, pagado=False)
    context = {'atenciones': atenciones_pendientes}
    return render(request, 'Recepcionista/recepcionista_lista_cobros.html', context)

@login_required
def recepcionista_confirmar_pago(request, atencion_id):
    atencion = get_object_or_404(Atencion, id=atencion_id)
    if request.method == 'POST':
        metodo = request.POST.get('metodo_pago')
        if metodo:
            atencion.metodo_pago = metodo
            atencion.pagado = True
            if metodo == 'efectivo':
                try:
                    monto_recibido = int(request.POST.get('monto_efectivo', 0))
                    if monto_recibido < atencion.precio_final:
                        messages.error(request, f'Error: El monto (${monto_recibido}) es menor al total (${atencion.precio_final}).')
                        return render(request, 'Recepcionista/recepcionista_confirmar_pago.html', {'atencion': atencion})
                    atencion.monto_pagado = monto_recibido
                    atencion.vuelto = monto_recibido - atencion.precio_final
                except ValueError:
                    messages.error(request, 'Error: Ingrese un monto válido.')
                    return render(request, 'Recepcionista/recepcionista_confirmar_pago.html', {'atencion': atencion})
            else:
                atencion.monto_pagado = atencion.precio_final
                atencion.vuelto = 0
                atencion.codigo_transaccion = request.POST.get('codigo_transaccion', 'S/N')
            atencion.save()
            messages.success(request, '¡Pago registrado exitosamente!')
            return redirect('recepcionista_ver_boleta', atencion_id=atencion.id)
        else:
            messages.error(request, 'Por favor selecciona un método de pago.')
    context = {'atencion': atencion}
    return render(request, 'Recepcionista/recepcionista_confirmar_pago.html', context)

@login_required
def recepcionista_ver_boleta(request, atencion_id):
    atencion = get_object_or_404(Atencion, id=atencion_id)
    if not atencion.pagado:
        return redirect('recepcionista_confirmar_pago', atencion_id=atencion.id)
    servicios = atencion.servicios.all()
    productos = ProductoConsumido.objects.filter(atencion=atencion)
    context = {
        'atencion': atencion,
        'servicios': servicios,
        'productos': productos
    }
    return render(request, 'Recepcionista/boleta.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_lista_productos(request):
    try:
        productos = Producto.objects.filter(activo=True)
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_lista_clientes(request):
    try:
        clientes = Cliente.objects.filter(activo=True)
        serializer = ClienteSerializer(clientes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_datos_usuario(request):
    user = request.user
    print(f"--- SOLICITUD DATOS USUARIO: {user.username} ---") 

    if user.is_superuser:
        try:
            colaborador = user.colaborador
            serializer = ColaboradorSerializer(colaborador)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Colaborador.DoesNotExist:
            return Response({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name or "Super",
                'last_name': user.last_name or "Admin",
                'rol': 'admin',
                'rut': 'N/A',
                'sueldo': 0,
                'estado_actual': 'Disponible'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"ERROR SUPERUSER: {e}") 
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        colaborador = user.colaborador
        serializer = ColaboradorSerializer(colaborador)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Colaborador.DoesNotExist:
        print("ERROR: El usuario no tiene colaborador asociado")
        return Response(
            {'error': f'El usuario {user.username} existe, pero falta agregarlo en la tabla "Colaboradores".'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"ERROR CRÍTICO EN API_DATOS_USUARIO: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_lista_proveedores(request):
    try:
        proveedores = Proveedor.objects.filter(activo=True)
        serializer = ProveedorSerializer(proveedores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_lista_colaboradores(request):
    try:
        colaboradores = Colaborador.objects.filter(user__is_active=True)
        serializer = ColaboradorSerializer(colaboradores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_producto(request):
    serializer = ProductoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(activo=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_modificar_producto(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = ProductoSerializer(producto, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_producto(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    producto.activo = False
    producto.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_proveedor(request):
    serializer = ProveedorSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(activo=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_modificar_proveedor(request, proveedor_id):
    try:
        proveedor = Proveedor.objects.get(id=proveedor_id)
    except Proveedor.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = ProveedorSerializer(proveedor, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_proveedor(request, proveedor_id):
    try:
        proveedor = Proveedor.objects.get(id=proveedor_id)
    except Proveedor.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    proveedor.activo = False
    proveedor.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_colaborador(request):
    print(f"--- NUEVA SOLICITUD CREAR ---")
    print(f"Datos: {request.data}")

    try:
        with transaction.atomic():
            data = request.data
            username = data.get('username')
            rut = data.get('rut')
            if not username or not rut:
                return Response({'error': 'Faltan datos (User o RUT).'}, status=status.HTTP_400_BAD_REQUEST)

            usuario_existente = User.objects.filter(username=username).first()
            if usuario_existente:
                if usuario_existente.is_active:
                    return Response({'error': f'El usuario "{username}" ya está ocupado.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    pass 

            colab_rut_ocupado = Colaborador.objects.filter(rut=rut).first()
            if colab_rut_ocupado:
                if not usuario_existente or colab_rut_ocupado.user.id != usuario_existente.id:
                    return Response({'error': f'El RUT {rut} ya está registrado por el usuario "{colab_rut_ocupado.user.username}".'}, status=status.HTTP_400_BAD_REQUEST)

            if usuario_existente and not usuario_existente.is_active:
                print("Reviviendo usuario...")
                user = usuario_existente
                user.is_active = True
                user.first_name = data.get('first_name', '')
                user.last_name = data.get('last_name', '')
                user.email = data.get('email', '')
                if data.get('password'):
                    user.set_password(data.get('password'))
                user.save()
            else:
                print("Creando usuario nuevo...")
                user = User.objects.create_user(
                    username=username,
                    password=data.get('password'),
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                    email=data.get('email', '')
                )

            sueldo_int = int(data.get('sueldo', 0))
            
            colab, created = Colaborador.objects.update_or_create(
                user=user,
                defaults={
                    'rol': data.get('rol'),
                    'rut': rut, 
                    'sueldo': sueldo_int 
                }
            )
            
            print(f"¡Éxito! Colaborador creado/actualizado: {colab.rut}")
            serializer = ColaboradorSerializer(colab)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_modificar_colaborador(request, colaborador_id):
    try:
        colaborador = Colaborador.objects.get(user__id=colaborador_id)
        user = colaborador.user
    except Colaborador.DoesNotExist:
        return Response({'error': 'Colaborador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    try:
        data = request.data

        nuevo_rut = data.get('rut')
        if nuevo_rut and Colaborador.objects.filter(rut=nuevo_rut).exclude(user__id=colaborador_id).exists():
            return Response({'error': f'El RUT "{nuevo_rut}" ya pertenece a otro colaborador.'}, status=status.HTTP_400_BAD_REQUEST)

        if 'first_name' in data: user.first_name = data['first_name']
        if 'last_name' in data: user.last_name = data['last_name']
        if 'email' in data: user.email = data['email']
        user.save()

        if 'rol' in data: colaborador.rol = data['rol']
        if 'rut' in data: colaborador.rut = data['rut']
        if 'sueldo' in data: colaborador.sueldo = data['sueldo']
        colaborador.save()
        
        return Response(ColaboradorSerializer(colaborador).data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_colaborador(request, colaborador_id):
    try:
        user = User.objects.get(id=colaborador_id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    user.is_active = False
    user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_cliente(request):
    data = request.data
    rut_ingresado = data.get('rut')
    email_ingresado = data.get('email')

    cliente_existente = Cliente.objects.filter(rut=rut_ingresado).first()

    if cliente_existente:
        if cliente_existente.activo:
            return Response({'error': 'Este RUT ya está registrado y activo.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(f"Reviviendo cliente: {rut_ingresado}")
            serializer = ClienteSerializer(cliente_existente, data=data, partial=True)
            if serializer.is_valid():
                serializer.save(activo=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if Cliente.objects.filter(email=email_ingresado, activo=True).exists():
         return Response({'error': 'Este Email ya está siendo usado.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ClienteSerializer(data=data)
    if serializer.is_valid():
        serializer.save(activo=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def api_modificar_cliente(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = ClienteSerializer(cliente, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def api_eliminar_cliente(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    cliente.activo = False
    cliente.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_lista_servicios(request):
    servicios = Servicio.objects.filter(activo=True)
    serializer = ServicioSerializer(servicios, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_crear_atencion(request):
    print("--- INTENTO DE CREAR ATENCIÓN ---")
    print(f"Usuario solicitante: {request.user.username}")
    print(f"Datos recibidos: {request.data}")
    
    cliente_id = request.data.get('cliente_id')
    
    if not cliente_id:
        print("ERROR: No llegó el cliente_id")
        return Response({'error': 'Debe enviar el parametro "cliente_id".'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            print(f"ERROR: Cliente {cliente_id} no existe en DB")
            return Response({'error': 'El cliente especificado no existe.'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(request.user, 'colaborador'):
            print(f"ERROR: El usuario {request.user.username} no es colaborador")
            return Response({'error': 'Tu usuario no tiene perfil de Estilista asignado.'}, status=status.HTTP_400_BAD_REQUEST)
            
        estilista_colaborador = request.user.colaborador

        atencion = Atencion.objects.create(
            cliente=cliente,
            estilista=estilista_colaborador
        )
        
        hoy = datetime.date.today()
        if cliente.fecha_nacimiento and cliente.fecha_nacimiento.month == hoy.month and cliente.fecha_nacimiento.day == hoy.day:
            atencion.descuento_cumpleanos = True
            atencion.save()
            
        print(f"¡Éxito! Atención creada ID: {atencion.id}")
        return Response(AtencionSerializer(atencion).data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"ERROR CRÍTICO: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_detalle_atencion(request, atencion_id):
    try:
        atencion = Atencion.objects.get(id=atencion_id)
        return Response(AtencionSerializer(atencion).data)
    except Atencion.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_agregar_servicio_atencion(request, atencion_id):
    try:
        atencion = Atencion.objects.get(id=atencion_id)
        servicio_id = request.data.get('servicio_id')
        servicio = Servicio.objects.get(id=servicio_id)
        atencion.servicios.add(servicio)
        return Response({'status': 'Servicio añadido'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_agregar_producto_atencion(request, atencion_id):
    try:
        atencion = Atencion.objects.get(id=atencion_id)
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))
        producto = Producto.objects.get(id=producto_id)
        ProductoConsumido.objects.create(
            atencion=atencion,
            producto=producto,
            cantidad=cantidad
        )
        return Response({'status': 'Producto añadido'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_finalizar_atencion(request, atencion_id):
    try:
        atencion = Atencion.objects.get(id=atencion_id)
        consumos = ProductoConsumido.objects.filter(atencion=atencion)
        for item in consumos:
            if item.producto.stock_actual < item.cantidad:
                return Response({'error': f'Stock insuficiente para {item.producto.nombre}'}, status=status.HTTP_400_BAD_REQUEST)
        for item in consumos:
            item.producto.stock_actual -= item.cantidad
            item.producto.save()
        total = 0
        for serv in atencion.servicios.all():
            total += serv.precio
        for item in consumos:
            total += (item.producto.precio_venta * item.cantidad)
        if atencion.descuento_cumpleanos:
            total = total * 0.80
        atencion.precio_final = total
        atencion.save()
        return Response({'status': 'Finalizada', 'total': total}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_mis_atenciones(request):
    try:
        estilista = request.user.colaborador
        atenciones = Atencion.objects.filter(estilista=estilista).order_by('-fecha_hora')
        serializer = AtencionSerializer(atenciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_lista_cobros(request):
    try:
        atenciones = Atencion.objects.filter(precio_final__gt=0, pagado=False).order_by('-fecha_hora')
        serializer = AtencionSerializer(atenciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_registrar_pago(request, atencion_id):
    try:
        atencion = Atencion.objects.get(id=atencion_id)
        data = request.data
        metodo = data.get('metodo_pago')
        monto_recibido = int(data.get('monto_pagado', 0))
        codigo = data.get('codigo_transaccion', '')
        
        atencion.metodo_pago = metodo
        atencion.codigo_transaccion = codigo
        
        if metodo == 'efectivo':
            if monto_recibido < atencion.precio_final:
                return Response({'error': 'El monto entregado es menor al total.'}, status=status.HTTP_400_BAD_REQUEST)
            atencion.monto_pagado = monto_recibido
            atencion.vuelto = monto_recibido - atencion.precio_final
        else:
            atencion.monto_pagado = atencion.precio_final
            atencion.vuelto = 0
            
        atencion.pagado = True
        atencion.save()
        
        return Response({
            'status': 'Pago exitoso', 
            'vuelto': atencion.vuelto,
            'id': atencion.id
        }, status=status.HTTP_200_OK)
        
    except Atencion.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_metrics(request):
    """
    Devuelve métricas clave para el Dashboard del Admin.
    """

    if not request.user.is_superuser and (not hasattr(request.user, 'colaborador') or request.user.colaborador.rol != 'admin'):
        return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

    hoy = timezone.now().date()

    total_ventas = Atencion.objects.filter(
        fecha_hora__date=hoy, 
        pagado=True
    ).aggregate(total=Sum('precio_final'))['total'] or 0
    
    productos_criticos = Producto.objects.filter(
        activo=True, 
        stock_actual__lte=F('stock_minimo')
    ).count()
    
    citas_hoy = Atencion.objects.filter(
        fecha_hora__date=hoy
    ).count()

    data = {
        'ventas_hoy': total_ventas,
        'productos_criticos': productos_criticos,
        'citas_hoy': citas_hoy
    }
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_cambiar_password(request):
    """
    Permite al usuario cambiar su contraseña desde la App.
    """
    user = request.user
    old_pass = request.data.get('old_password')
    new_pass = request.data.get('new_password')

    if not user.check_password(old_pass):
        return Response({'error': 'La contraseña actual es incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_pass)
    user.save()
    return Response({'status': 'Contraseña actualizada correctamente.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_cambiar_password(request):
    """
    Permite a cualquier usuario logueado cambiar su contraseña.
    """
    user = request.user
    old_pass = request.data.get('old_password')
    new_pass = request.data.get('new_password')

    if not old_pass or not new_pass:
        return Response({'error': 'Faltan datos.'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_pass):
        return Response({'error': 'La contraseña actual es incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_pass)
    user.save()
    return Response({'status': 'Contraseña actualizada correctamente.'}, status=status.HTTP_200_OK)