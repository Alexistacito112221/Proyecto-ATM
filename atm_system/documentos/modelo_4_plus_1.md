# MODELO 4+1 VISTAS - SISTEMA CAJERO AUTOMATICO

## 1. VISTA LOGICA (Logical View)

### Descripcion
La vista logica describe la estructura funcional del sistema, identificando clases, objetos y paquetes que forman la arquitectura del sistema ATM.

### Capas de la Arquitectura

#### Capa de Presentacion (Views)
- **ConsolaView**: Interfaz de usuario por consola que simula la pantalla tactil del ATM
- Maneja la interaccion con el usuario, menus, formularios y comprobantes

#### Capa de Negocio (Services - Fachada)
- **CajeroFacade**: Fachada principal que unifica todos los subsistemas
- **AutenticacionService**: Subsistema de autenticacion (RF1)
- **TransaccionService**: Subsistema de transacciones (RF2, RF3)
- **SeguridadService**: Subsistema de seguridad (RNF4)

#### Capa de Datos (Repositories)
- **DatabaseManager**: Singleton para gestion de conexion SQLite
- **TarjetaRepository**: Acceso a datos de tarjetas
- **CuentaRepository**: Acceso a datos de cuentas
- **TransaccionRepository**: Acceso a datos de transacciones
- **ClienteRepository**: Acceso a datos de clientes

#### Capa de Dominio (Models)
- **Cliente**: Entidad cliente del banco
- **Cuenta**: Entidad cuenta bancaria con reglas de negocio
- **Tarjeta**: Entidad tarjeta con cifrado de NIP
- **Transaccion**: Entidad transaccion con estados
- **Comprobante**: Entidad comprobante de transaccion
- **Sesion**: Entidad sesion de usuario con timeout

### Diagramas
- Diagrama de Clases de Analisis
- Diagrama de Clases de Diseno

---

## 2. VISTA DE PROCESOS (Process View)

### Descripcion
La vista de procesos describe los procesos en tiempo de ejecucion, concurrencia y sincronizacion del sistema.

### Procesos Principales

#### Proceso de Autenticacion (RF1)
1. Cliente inserta tarjeta (ingresa numero)
2. Sistema valida formato de tarjeta (16 digitos)
3. Sistema verifica tarjeta en base de datos
4. Sistema verifica que tarjeta no este bloqueada ni expirada
5. Cliente ingresa NIP (4 digitos)
6. Sistema valida NIP contra hash almacenado (SHA-256)
7. Sistema controla intentos fallidos (max 3)
8. Sistema crea sesion autenticada

#### Proceso de Retiro de Efectivo (RF3) - Caso Principal
1. Cliente selecciona retiro de efectivo
2. Sistema valida sesion activa
3. Cliente ingresa monto a retirar
4. Sistema valida formato de monto (positivo, max 2 decimales)
5. Sistema verifica saldo suficiente
6. Sistema verifica limite diario de retiro
7. Sistema crea transaccion pendiente
8. Sistema actualiza saldo de cuenta
9. Sistema marca transaccion como completada
10. Sistema genera comprobante
11. Cliente recibe efectivo y comprobante

#### Proceso de Depositos y Transferencias
- Similar al retiro pero con validaciones especificas
- Transferencia incluye validacion de cuenta destino

### Diagramas
- Diagrama de Secuencia - Retiro de Efectivo
- Diagrama de Actividad

---

## 3. VISTA DE DESARROLLO (Development View)

### Descripcion
La vista de desarrollo describe la organizacion del software en el entorno de desarrollo.

### Estructura de Directorios
```
atm_system/
├── codigo/
│   ├── models/           # Capa de Dominio
│   │   ├── __init__.py
│   │   ├── cliente.py
│   │   ├── cuenta.py
│   │   ├── tarjeta.py
│   │   ├── transaccion.py
│   │   ├── comprobante.py
│   │   └── sesion.py
│   ├── repositories/     # Capa de Datos
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── cliente_repository.py
│   │   ├── cuenta_repository.py
│   │   ├── tarjeta_repository.py
│   │   └── transaccion_repository.py
│   ├── services/         # Capa de Negocio
│   │   ├── __init__.py
│   │   ├── cajero_facade.py
│   │   ├── autenticacion_service.py
│   │   ├── transaccion_service.py
│   │   └── seguridad_service.py
│   ├── views/            # Capa de Presentacion
│   │   ├── __init__.py
│   │   └── consola_view.py
│   ├── tests/            # Casos de Prueba
│   │   ├── __init__.py
│   │   └── test_atm.py
│   ├── demo_ejecucion.py
│   └── main.py
├── database/
│   └── atm_database.db
├── diagramas/
│   ├── diagrama_casos_uso.png
│   ├── diagrama_clases_analisis.png
│   ├── diagrama_clases_diseno.png
│   ├── diagrama_secuencia_retiro.png
│   └── diagrama_componentes.png
├── storyboards/
│   ├── storyboard_01_bienvenida.jpg
│   ├── storyboard_02_autenticacion.jpg
│   ├── storyboard_03_menu.jpg
│   ├── storyboard_04_monto.jpg
│   └── storyboard_05_comprobante.jpg
├── documentos/
│   └── modelo_4_plus_1.md
└── evidencia/
    └── ejecucion_sistema.txt
```

### Patrones de Diseno Aplicados
- **Fachada (Facade)**: CajeroFacade unifica subsistemas complejos
- **Singleton**: DatabaseManager para una unica conexion a BD
- **Repository**: Acceso a datos desacoplado de la logica de negocio
- **Domain Model**: Entidades con logica de negocio propia

### Principios de Diseno
- **SRP**: Cada clase tiene una unica responsabilidad
- **DRY**: No hay duplicacion de logica
- **Alta Cohesion**: Clases enfocadas en una tarea
- **Bajo Acoplamiento**: Capas independientes con interfaces claras

### Diagramas
- Diagrama de Componentes
- Diagrama de Paquetes

---

## 4. VISTA FISICA (Physical View)

### Descripcion
La vista fisica describe la distribucion fisica del software en hardware.

### Topologia del Sistema

```
+----------------------------------+
|         CLIENTE / USUARIO         |
|  +----------------------------+  |
|  |    Interfaz Consola (UI)   |  |
|  |    views/consola_view.py   |  |
|  +------------+---------------+  |
+---------------|------------------+
                |
+---------------v------------------+
|      CAJERO AUTOMATICO (ATM)      |
|  +----------------------------+  |
|  |   CajeroFacade (Fachada)   |  |
|  |   services/cajero_facade   |  |
|  +------------+---------------+  |
|  |  AutenticacionService      |  |
|  |  TransaccionService        |  |
|  |  SeguridadService          |  |
|  +------------+---------------+  |
|  |  Repository Layer          |  |
|  |  (Tarjeta/Cuenta/Trans)    |  |
|  +------------+---------------+  |
|  |  SQLite Database (Local)   |  |
|  |  database/atm_database.db  |  |
|  +----------------------------+  |
+---------------|------------------+
                | [API REST/HTTPS]
+---------------v------------------+
|    SISTEMA CENTRAL DEL BANCO      |
|  - Validacion de cuentas         |
|  - Registro de transacciones     |
|  - Actualizacion de saldos       |
+----------------------------------+
```

### Hardware
- Terminal ATM con pantalla tactil
- Procesador: Minimo ARM/x86
- Memoria: 512MB RAM minimo
- Almacenamiento: 1GB para BD local
- Conectividad: Ethernet/WiFi al sistema central

### RNF1 - Tolerancia a Fallos
- Operacion con base de datos local (SQLite)
- Reintentos automaticos de conexion
- Cola de transacciones pendientes
- Sincronizacion cuando la conexion se restablece

### RNF2 - Rendimiento
- Respuesta menor a 3 segundos por operacion
- Indices en campos frecuentes (tarjeta, cuenta, fecha)
- Singleton para reutilizar conexion a BD
- Cache de sesion activa

### RNF4 - Seguridad
- Cifrado SHA-256 para NIPs
- Enmascarado de datos sensibles (tarjetas, cuentas)
- Control de intentos fallidos (bloqueo automatico)
- Auditoria de eventos de seguridad

---

## 5. VISTA DE ESCENARIOS (Scenarios View)

### Descripcion
La vista de escenarios describe los casos de uso que unifican las otras cuatro vistas.

### Casos de Uso Implementados

#### CU-01: Autenticacion del Cliente (RF1)
**Actor**: Cliente
**Precondicion**: Tarjeta registrada en el sistema
**Flujo Basico**:
1. Cliente inserta tarjeta
2. Sistema valida formato (16 digitos)
3. Sistema verifica tarjeta activa y no expirada
4. Cliente ingresa NIP
5. Sistema verifica NIP con hash almacenado
6. Sistema autentica exitosamente
7. Sistema muestra menu principal

**Flujos Alternativos**:
- 2a. Tarjeta no encontrada: mensaje de error
- 3a. Tarjeta bloqueada: mensaje de contactar al banco
- 3b. Tarjeta expirada: mensaje de renovacion
- 5a. NIP incorrecto: incrementar intentos, maximo 3 bloqueos

#### CU-02: Consulta de Saldo (RF2)
**Actor**: Cliente autenticado
**Flujo Basico**:
1. Cliente selecciona consulta de saldo
2. Sistema verifica sesion activa
3. Sistema obtiene saldo de la cuenta
4. Sistema registra transaccion de consulta
5. Sistema muestra saldo actual y disponible

#### CU-03: Retiro de Efectivo (RF3) - PRINCIPAL
**Actor**: Cliente autenticado
**Precondicion**: Saldo suficiente, dentro del limite diario
**Flujo Basico**:
1. Cliente selecciona retiro
2. Cliente ingresa monto
3. Sistema valida monto (positivo, formato)
4. Sistema verifica saldo suficiente
5. Sistema verifica limite diario
6. Sistema crea transaccion
7. Sistema actualiza saldo
8. Sistema genera comprobante
9. Sistema entrega efectivo

**Flujos Alternativos**:
- 4a. Saldo insuficiente: cancelar operacion
- 5a. Excede limite diario: mostrar disponible
- 3a. Monto invalido: solicitar reingreso

#### CU-04: Deposito de Efectivo
**Actor**: Cliente autenticado
**Flujo**: Similar a retiro pero incrementando saldo

#### CU-05: Transferencia entre Cuentas
**Actor**: Cliente autenticado
**Flujo**: Validar cuenta destino, verificar saldo, debitar origen, acreditar destino

#### CU-06: Cambio de NIP
**Actor**: Cliente autenticado
**Flujo**: Verificar NIP actual, validar nuevo NIP (4 digitos), confirmar, actualizar hash

### Storyboards Generados
1. Pantalla de Bienvenida
2. Pantalla de Autenticacion (NIP)
3. Menu Principal
4. Seleccion de Monto (Retiro)
5. Comprobante de Transaccion

### Pruebas
- 47 casos de prueba unitarios e integrados
- Cobertura: RF1-RF5, RNF1-RNF4
- Todos los tests ejecutados exitosamente
