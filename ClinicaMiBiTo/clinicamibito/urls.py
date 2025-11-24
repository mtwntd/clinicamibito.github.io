from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token
from appclinica import views

urlpatterns = [
    path('', views.inicio, name='index'),
    path('inicio/', views.inicio, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('tratamientos/esteticos/', views.tratamientos_esteticos, name='tratamientos_esteticos'),
    path('tratamientos/corporales/', views.tratamientos_corporales, name='tratamientos_corporales'),
    path('tratamientos/cosmeticos/', views.cosmeticos, name='cosmeticos'),
    path('tratamientos/depilaciones/', views.depilaciones, name='depilaciones'),

    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/estilista/', views.dashboard_estilista, name='dashboard_estilista'),
    path('dashboard/recepcionista/', views.dashboard_recepcionista, name='dashboard_recepcionista'),
    
    path('admin/producto/nuevo/', views.admin_crear_producto, name='admin_crear_producto'),
    path('admin/producto/modificar/<int:producto_id>/', views.admin_modificar_producto, name='admin_modificar_producto'),
    path('admin/producto/eliminar/<int:producto_id>/', views.admin_eliminar_producto, name='admin_eliminar_producto'),
    path('admin/producto/reponer/<int:producto_id>/', views.admin_reponer_stock, name='admin_reponer_stock'),
    
    path('admin/proveedores/', views.admin_lista_proveedores, name='admin_lista_proveedores'),
    path('admin/proveedores/nuevo/', views.admin_crear_proveedor, name='admin_crear_proveedor'),
    path('admin/proveedores/modificar/<int:proveedor_id>/', views.admin_modificar_proveedor, name='admin_modificar_proveedor'),
    path('admin/proveedores/eliminar/<int:proveedor_id>/', views.admin_eliminar_proveedor, name='admin_eliminar_proveedor'),
    
    path('admin/colaboradores/', views.admin_lista_colaboradores, name='admin_lista_colaboradores'),
    path('admin/colaboradores/nuevo/', views.admin_crear_colaborador, name='admin_crear_colaborador'),
    path('admin/colaboradores/modificar/<int:colaborador_user_id>/', views.admin_modificar_colaborador, name='admin_modificar_colaborador'),
    path('admin/colaboradores/eliminar/<int:colaborador_user_id>/', views.admin_eliminar_colaborador, name='admin_eliminar_colaborador'),
    
    path('admin/clientes/', views.dashboard_recepcionista, name='admin_lista_clientes'),
    path('admin/clientes/nuevo/', views.recepcionista_crear_cliente, name='admin_crear_cliente'),
    path('admin/clientes/modificar/<int:cliente_id>/', views.recepcionista_modificar_cliente, name='admin_modificar_cliente'),
    path('admin/clientes/baja/<int:cliente_id>/', views.recepcionista_dar_baja_cliente, name='admin_dar_baja_cliente'),

    path('admin/servicios/', views.admin_lista_servicios, name='admin_lista_servicios'),
    path('admin/servicios/nuevo/', views.admin_crear_servicio, name='admin_crear_servicio'),
    path('admin/servicios/modificar/<int:servicio_id>/', views.admin_modificar_servicio, name='admin_modificar_servicio'),
    path('admin/servicios/eliminar/<int:servicio_id>/', views.admin_eliminar_servicio, name='admin_eliminar_servicio'),

    path('admin/atenciones/', views.admin_lista_atenciones, name='admin_lista_atenciones'),
    path('admin/atencion/<int:atencion_id>/', views.estilista_detalle_atencion, name='admin_detalle_atencion'),
    
    path('recepcionista/cliente/nuevo/', views.recepcionista_crear_cliente, name='recepcionista_crear_cliente'),
    path('recepcionista/cliente/modificar/<int:cliente_id>/', views.recepcionista_modificar_cliente, name='recepcionista_modificar_cliente'),
    path('recepcionista/cliente/baja/<int:cliente_id>/', views.recepcionista_dar_baja_cliente, name='recepcionista_dar_baja_cliente'),
    
    path('recepcionista/cobros/', views.recepcionista_lista_cobros, name='recepcionista_lista_cobros'),
    path('recepcionista/cobros/pagar/<int:atencion_id>/', views.recepcionista_confirmar_pago, name='recepcionista_confirmar_pago'),
    path('recepcionista/cobros/boleta/<int:atencion_id>/', views.recepcionista_ver_boleta, name='recepcionista_ver_boleta'),

    path('estilista/inventario/', views.estilista_lista_productos, name='estilista_lista_productos'),
    path('estilista/bajominimos/', views.estilista_lista_bajominimos, name='estilista_lista_bajominimos'),
    path('estilista/buscar-cliente/', views.estilista_buscar_cliente, name='estilista_buscar_cliente'),
    path('estilista/crear-atencion/<int:cliente_id>/', views.estilista_crear_atencion, name='estilista_crear_atencion'),
    path('estilista/atencion/<int:atencion_id>/', views.estilista_detalle_atencion, name='estilista_detalle_atencion'),
    path('estilista/atencion/<int:atencion_id>/finalizar/', views.estilista_finalizar_atencion, name='estilista_finalizar_atencion'),
    path('estilista/atencion/<int:atencion_id>/cancelar/', views.estilista_cancelar_atencion, name='estilista_cancelar_atencion'),
    path('estilista/mis-atenciones/', views.estilista_mis_atenciones, name='estilista_mis_atenciones'),

    path('django-admin/', admin.site.urls, name='admin:index'),
    
    path('api/v1/login/', obtain_auth_token, name='api_login'),
    path('api/v1/usuario/', views.api_datos_usuario, name='api_datos_usuario'),
    path('api/v1/productos/', views.api_lista_productos, name='api_lista_productos'),
    path('api/v1/productos/crear/', views.api_crear_producto, name='api_crear_producto'),
    path('api/v1/productos/modificar/<int:producto_id>/', views.api_modificar_producto, name='api_modificar_producto'),
    path('api/v1/productos/eliminar/<int:producto_id>/', views.api_eliminar_producto, name='api_eliminar_producto'),
    
    path('api/v1/proveedores/', views.api_lista_proveedores, name='api_lista_proveedores'),
    path('api/v1/proveedores/crear/', views.api_crear_proveedor, name='api_crear_proveedor'),
    path('api/v1/proveedores/modificar/<int:proveedor_id>/', views.api_modificar_proveedor, name='api_modificar_proveedor'),
    path('api/v1/proveedores/eliminar/<int:proveedor_id>/', views.api_eliminar_proveedor, name='api_eliminar_proveedor'),

    path('api/v1/colaboradores/', views.api_lista_colaboradores, name='api_lista_colaboradores'),
    path('api/v1/colaboradores/crear/', views.api_crear_colaborador, name='api_crear_colaborador'),
    path('api/v1/colaboradores/modificar/<int:colaborador_id>/', views.api_modificar_colaborador, name='api_modificar_colaborador'),
    path('api/v1/colaboradores/eliminar/<int:colaborador_id>/', views.api_eliminar_colaborador, name='api_eliminar_colaborador'),

    path('api/v1/clientes/', views.api_lista_clientes, name='api_lista_clientes'),
    path('api/v1/clientes/crear/', views.api_crear_cliente, name='api_crear_cliente'),
    path('api/v1/clientes/modificar/<int:cliente_id>/', views.api_modificar_cliente, name='api_modificar_cliente'),
    path('api/v1/clientes/eliminar/<int:cliente_id>/', views.api_eliminar_cliente, name='api_eliminar_cliente'),
    
    path('api/v1/cobros/pendientes/', views.api_lista_cobros, name='api_lista_cobros'),
    path('api/v1/cobros/pagar/<int:atencion_id>/', views.api_registrar_pago, name='api_registrar_pago'),
    
    path('api/v1/admin/metrics/', views.api_dashboard_metrics, name='api_dashboard_metrics'),
    
    
    path('api/v1/usuario/password/', views.api_cambiar_password, name='api_cambiar_password'),

    path('api/v1/servicios/', views.api_lista_servicios, name='api_lista_servicios'),
    path('api/v1/atencion/crear/', views.api_crear_atencion, name='api_crear_atencion'),
    path('api/v1/atencion/<int:atencion_id>/', views.api_detalle_atencion, name='api_detalle_atencion'),
    path('api/v1/atencion/<int:atencion_id>/add-servicio/', views.api_agregar_servicio_atencion, name='api_add_servicio'),
    path('api/v1/atencion/<int:atencion_id>/add-producto/', views.api_agregar_producto_atencion, name='api_add_producto'),
    path('api/v1/atencion/<int:atencion_id>/finalizar/', views.api_finalizar_atencion, name='api_finalizar'),
    path('api/v1/atencion/historial/', views.api_mis_atenciones, name='api_mis_atenciones'),
    
    path('api/v1/usuario/', views.api_datos_usuario, name='api_datos_usuario'),
    
    path('api/v1/usuario/password/', views.api_cambiar_password, name='api_cambiar_password'),
    
    path('api/v1/productos/', views.api_lista_productos, name='api_lista_productos'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)