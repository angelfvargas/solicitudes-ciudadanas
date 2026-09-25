# Prueba de lógica: ¿qué pasa con Registrada → Cerrada?

## Qué debe hacer el sistema

**Rechazar el cambio, no aplicar nada y explicar por qué.** La solicitud se queda en
"Registrada", no se escribe ningún registro en el historial y el usuario recibe un mensaje
que le dice qué sí puede hacer:

```
HTTP 422
{"detail": "Transición no permitida: Registrada → Cerrada. Desde Registrada solo se puede
pasar a: En revisión.", "code": "business_rule"}
```

Cerrar una solicitud que nadie revisó ni atendió dejaría al ciudadano sin respuesta y
rompería la trazabilidad, que es justo el problema que el sistema quiere resolver.

## Cómo está implementado

1. **Las transiciones permitidas son datos, no `if`s.** La tabla `status_transitions` guarda
   una fila por cada paso permitido y el rol que puede darlo:

   | desde | hacia | rol |
   |---|---|---|
   | Registrada | En revisión | admin |
   | En revisión | Asignada | admin (al asignar funcionario) |
   | Asignada | En proceso | funcionario, admin |
   | En proceso | Resuelta | funcionario, admin |
   | Resuelta | Cerrada | admin |
   | Resuelta | En proceso | admin (reabrir) |

   Es una **lista blanca**: lo que no está, no se permite. `Registrada → Cerrada` no está.

2. **Una sola clase valida** (`backend/app/services/workflow.py`, `StatusWorkflow`), en orden:
   - ¿El estado destino es distinto del actual?
   - ¿Existe alguna transición desde el estado actual hacia el destino? Si no → **422**
     (regla de negocio).
   - ¿Existe para el rol del usuario? Si no → **403** (el paso existe, pero no para él).
   - ¿El estado destino exige funcionario asignado (`requires_official`) y no hay uno? → 422.

3. **Se valida en el backend, siempre.** La interfaz solo muestra los estados permitidos
   (`GET /requests/{id}/transitions`), pero eso es comodidad: si alguien llama la API
   directamente con Postman, `PUT /requests/{id}/status` vuelve a pasar por la misma
   validación.

4. **Todo o nada.** El cambio de estado y su registro en el historial se guardan en la
   misma transacción. Si la validación falla, no se escribe ninguno de los dos.

## Por qué así (principio Abierto/Cerrado)

Si mañana la entidad quiere un estado nuevo ("Devuelta al ciudadano") o que el funcionario
también pueda cerrar, se insertan filas en `request_statuses` y `status_transitions`. El
código de validación **no cambia**: está abierto a extensión y cerrado a modificación.

La prueba automática que lo cubre es `test_registered_to_closed_is_rejected`, en
`backend/tests/test_requests.py`.
