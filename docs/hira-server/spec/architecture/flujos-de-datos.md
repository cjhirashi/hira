---
origen_vault: "7.1 - Hira Server/7.1.3 - Arquitectura/7.1.3.3 - Flujos de Datos Principales.md"
título: Flujos de Datos Principales — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Arquitectura
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, arquitectura, flujos-de-datos]
---

## Flujo 1 — Lectura en tiempo real (dispositivo → pantalla)

```
Dispositivo (BACnet/Modbus/MQTT)
    → Motor de Protocolos (polling configurable por punto asociado, ver SRV-ADR-019)
    → Redis Pub/Sub (canal por punto)
    → FastAPI WebSocket
    → Frontend (animación gráfica actualizada)
    → TimescaleDB / SQLite (registro histórico paralelo)
```

## Flujo 2 — Comando de escritura (operador → dispositivo)

```
Operador (click en panel de control o setpoint)
    → Frontend
    → FastAPI REST (validación de permisos RBAC + access_mode del punto, ver SRV-ADR-019)
    → Motor de Protocolos (respeta prioridad de escritura si es BACnet)
    → Dispositivo (escritura BACnet/Modbus/MQTT)
    → Confirmación de vuelta al Frontend
```

## Flujo 3 — Alarma automática

```
Motor de Protocolos → Redis (nuevo valor)
    → Motor de Alarmas (suscrito a Redis, evalúa condiciones)
    → Condición cumplida → PostgreSQL/SQLite (registro de alarma)
    → Redis Pub/Sub (canal de alarmas)
    → FastAPI WebSocket → Frontend (notificación en tiempo real)
```

## Flujo 4 — Script de lógica Python (operación continua)

```
Integrador escribe script en Monaco Editor
    → FastAPI guarda script en PostgreSQL/SQLite
    → Celery worker carga y ejecuta script en ciclo (cola normal)
    → Script llama hira.read() → Redis (lectura de punto)
    → Script llama hira.write() → Motor de Protocolos → Dispositivo (si access_mode lo permite)
    → Log de ejecución → PostgreSQL/SQLite
```

## Flujo 5 — Script de prueba funcional

```
Técnico/Integrador escribe script de prueba en Monaco Editor
    → FastAPI guarda script en PostgreSQL/SQLite (tipo: prueba)
    → Técnico ejecuta la prueba desde el panel
    → Motor de Pruebas registra lock de puntos en Redis (cola high)
    → Workers de Lógica continua detectan locks → pausan escrituras en esos puntos
    → Script ejecuta secuencia: hira.write() + hira.read() + hira.wait()
    → Resultados capturados → PostgreSQL/SQLite (tabla de resultados de prueba)
    → Prueba finaliza → locks liberados en Redis → Lógica continua se reanuda
    → Módulo de Análisis consume resultados → genera reporte PDF/CSV
```

## Flujo 6 — Escaneo de dispositivos y asociación explícita de puntos

```
Integrador inicia escaneo desde el panel
    → Motor de Protocolos ejecuta discovery por protocolo:
        BACnet: Who-Is broadcast → I-Am responses → lectura de objetos por dispositivo
        Modbus: escaneo de rangos de registros configurados
        MQTT: suscripción wildcard → captura de topics activos
    → Resultados estructurados → PostgreSQL/SQLite (puntos candidatos del dispositivo escaneado)
    → Los puntos candidatos NO son utilizables en línea todavía (ver SRV-ADR-012, SRV-ADR-019)
    → Integrador revisa los candidatos y asocia cada uno a un punto Hira:
        define access_mode (solo lectura / lectura y escritura)
        si es BACnet, define bacnet_write_priority
    → Solo a partir de la asociación, el punto queda disponible para polling, escritura,
      alarmas, históricos, mimics y RAG
    → Lista de puntos asociados → Módulo de Documentación (inventario técnico)
    → Lista de puntos asociados → pgvector (indexada para RAG)
```

## Flujo 7 — Agente IA con RAG

```
Documentación del proyecto (manual + auto-generada)
    → Indexada en pgvector (embeddings por chunks de contenido)

Usuario escribe mensaje en interfaz IA
    → FastAPI → LangChain Agent
    → RAG: consulta pgvector con el contexto de la pregunta
        → Recupera fragmentos relevantes: fichas técnicas, lista de puntos asociados,
          diagramas de flujo de scripts, resultados de pruebas, históricos
    → Agent tiene contexto específico del proyecto
    → Agent selecciona tools según necesidad:
        leer punto en tiempo real / consultar alarmas / revisar histórico /
        escribir punto (respetando access_mode) / ejecutar prueba / generar reporte
    → Agent sintetiza respuesta con conocimiento del sistema real
    → Frontend muestra respuesta + acciones ejecutadas + fuentes consultadas
```

---

## Gate de Salida

- [x] Flujos de datos documentados
- [x] Flujo 6 actualizado con el requisito de asociación explícita (SRV-ADR-012, SRV-ADR-019)
- [ ] Revisado y aprobado por Charlie
