# Orquestador concurrente de modelos

Ejercicio del **Módulo 1 · Unidad 1 (Arquitectura asíncrona con Python 3.12)** de AI Engineering (Coderhouse).

Simula un backend que consulta varias fuentes de IA de forma eficiente, sin API keys: la latencia de red se simula con `await asyncio.sleep()`.

## Qué hace

| Requisito | Dónde está |
|---|---|
| Tres corrutinas que simulan modelos con latencias distintas | `gpt_4_call` (1,2 s), `claude_3_call` (0,8 s), `local_llama_call` (3,5 s) |
| Disparar las tres a la vez | `asyncio.gather` en `orquestar_modelos()` |
| Timeout de 2 s, capturar el error sin detener el programa | `async with asyncio.timeout(2)` + `except TimeoutError` en `con_timeout()` |
| 10 simulaciones con solo 2 en simultáneo | `asyncio.Semaphore(2)` en `lote_con_semaforo()` |
| Nada bloqueante | no hay `time.sleep` en el código |

## Cómo correrlo

```bash
python --version   # 3.11 o superior (asyncio.timeout); probado con 3.12/3.13
python orquestador.py
```

No necesita dependencias externas.

## Salida (corrida real)

```
=== Parte 1: tres modelos en paralelo con timeout de 2 s ===
[ 0.00s] gpt_4_call       → inicia
[ 0.00s] claude_3_call    → inicia
[ 0.00s] local_llama_call → inicia
[ 0.80s] claude_3_call    ✓ respondió
[ 1.20s] gpt_4_call       ✓ respondió
[ 2.00s] local_llama_call ✗ superó 2.0s: TimeoutError capturado
    OK  {'modelo': 'gpt_4_call', 'ok': True, 'respuesta': "GPT-4: respuesta a '¿Qué es un agente de IA?'"}
    OK  {'modelo': 'claude_3_call', 'ok': True, 'respuesta': "Claude 3: respuesta a '¿Qué es un agente de IA?'"}
    ERR {'modelo': 'local_llama_call', 'ok': False, 'error': 'timeout > 2.0s'}
Tiempo total: 2.00s (en serie habría tardado 5.5s)

=== Parte 2: 10 simulaciones, máximo 2 a la vez ===
[ 2.00s] simulación  1 → inicia (activas: 1)
[ 2.00s] simulación  2 → inicia (activas: 2)
[ 2.38s] simulación  3 → inicia (activas: 2)
[ 2.48s] simulación  4 → inicia (activas: 2)
[ 2.73s] simulación  5 → inicia (activas: 2)
[ 2.98s] simulación  6 → inicia (activas: 2)
[ 3.22s] simulación  7 → inicia (activas: 2)
[ 3.48s] simulación  8 → inicia (activas: 2)
[ 3.80s] simulación  9 → inicia (activas: 2)
[ 3.88s] simulación 10 → inicia (activas: 2)
Lote terminado en 2.27s
```

Qué se observa:
- Las tres llamadas **inician en el mismo instante** (0,00 s): el event loop no espera a que termine una para empezar la otra.
- El modelo local supera los 2 s, se captura `TimeoutError` y los otros dos resultados igual se devuelven.
- En la parte 2, el contador de activas **nunca pasa de 2**: el semáforo hace esperar al resto, como haría un control de *rate limit* (evitar el error 429).

## Por qué un semáforo y no un gather de todo

Si hubiera que generar embeddings para 10.000 filas, disparar las 10.000 llamadas juntas haría que la API respondiera `429 Too Many Requests`. Se encolan todas con `gather`, pero el semáforo asegura que solo N corran al mismo tiempo.
