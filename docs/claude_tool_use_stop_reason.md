# Incidencia: herramientas de Claude no procesadas (stop_reason vs. tool_use)

Fecha: 2025-11-04
Estado: Resuelto

## Resumen ejecutivo

El flujo end-to-end no "usaba" las tools de Claude aunque el modelo sí devolvía un bloque `tool_use`. El código dependía de `response.stop_reason == "tool_use"` para activar la ruta de herramientas. En nuestro proxy local, `stop_reason` venía como `end_turn` aunque el `content` incluía `ToolUseBlock`. Resultado: caíamos al fallback y los campos (summary, key_points, etc.) venían vacíos o mínimos.

Solución: detectar la presencia de bloques `tool_use` directamente en `response.content` en vez de depender de `stop_reason`.

---

## Contexto

- Backend: Python + SDK Anthropic (cliente vía proxy local)
- Archivo principal del agente: `advanced_claude_agent.py`
  - `analyze_transcript_with_structured_output()`
  - `generate_practical_example()`
  - `extract_key_moments()`
- Tools definidas: `analyze_youtube_video`, `generate_practical_example`, `extract_key_moments`
- Frontend: Flask + fetch `/process` y `/example`

## Síntomas

- Logs mostraban:
  - `Stop reason: end_turn`
  - El `content` contenía un `ToolUseBlock` con `name='analyze_youtube_video'` y los campos completos (summary, key_points, podcast_text, structured_explanation, ...)
- A pesar de lo anterior, el flujo tomaba la rama de fallback y devolvía valores por defecto.

## Causa raíz

Condición frágil en `advanced_claude_agent.py`:

- Se usaba `if response.stop_reason == "tool_use":` para decidir si procesar herramientas.
- Con el proxy local, el modelo devuelve `stop_reason='end_turn'` aunque hay bloques `tool_use` en `response.content`.

Conclusión: `stop_reason` no es una señal fiable universal para decidir si hay tool calls; hay que inspeccionar los bloques de contenido.

## Solución aplicada

Reemplazar la condición por una detección directa de bloques de tipo `tool_use`:

```python
has_tool_use = any(
    getattr(content_block, "type", None) == "tool_use"
    for content_block in (response.content or [])
)
if has_tool_use:
    # procesar los bloques tool_use
else:
    # fallback
```

### Archivos y ubicaciones

- advanced_claude_agent.py:113-175 (ruta principal del análisis con tools)
- advanced_claude_agent.py:305-336 (generate_practical_example)
- advanced_claude_agent.py:383-419 (extract_key_moments)

Se reemplazó en todos los sitios donde se comparaba directamente `response.stop_reason == "tool_use"`.

## Evidencia (antes/después)

Antes (rama de fallback):
- `Stop reason: end_turn`
- `Contenido de respuesta: [ToolUseBlock(... name='analyze_youtube_video' ...)]`
- Resultado: `summary` vacío o genérico, `key_points` ~1, etc.

Después (procesando tool_use por contenido):
- Se detecta el `ToolUseBlock` y se extraen los campos estructurados.
- Ejemplo con video `VC6dmPcin2E`:
  - `key_points_count`: 9-10
  - `summary_len`: ~480+
  - `podcast_len`: ~1300+
  - `structured_len`: ~1900+

## Validación

1) Smoke del proxy local

- Anthropic `messages` (modelo `claude-sonnet-4`): HTTP 200 OK
- OpenAI `chat.completions` (modelo `gpt-4.1`): HTTP 200 OK

2) E2E con video real

- `process_video_with_claude("https://www.youtube.com/watch?v=VC6dmPcin2E", ...)` ahora devuelve los campos completos sin caer al fallback.

3) Flask test_client

- POST `/process` → 200, `status=success`, `key_points` es lista con 10 elementos, `summary_len` ~480+
- POST `/example` con el `summary` → 200, `status=success`, `example_len` ~370

## Recomendaciones

- No depender de `stop_reason` para la lógica de tools. Inspeccionar siempre los bloques de `response.content`.
- Mantener logs de depuración que impriman `stop_reason` y un preview de `content` para diagnosticar diferencias entre proveedores o proxies.
- Forzar `tool_choice` cuando corresponda, pero igualmente procesar por bloques de contenido para robustez.

## Preguntas frecuentes

- ¿Por qué cambia `stop_reason`?
  - Diferentes gateways/proxies o versiones del modelo pueden establecer `stop_reason` en `tool_use` o `end_turn` aunque incluyan bloques de herramientas en el `content`.
- ¿Se puede romper algo con el nuevo enfoque?
  - No. Si no hay bloques `tool_use`, se entra al fallback como antes. Si los hay, se procesan correctamente, que es el comportamiento deseado.

## Referencias

- `advanced_claude_agent.py:113-175, 305-336, 383-419`
- `claude_integration.py:108-146` (pipeline que depende del análisis con tools)
- `app.py:118-130` (respuesta API que entrega los campos a frontend)
