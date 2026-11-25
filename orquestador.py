"""Orquestador concurrente de modelos · AI Engineering (Coderhouse) · Módulo 1.

Simula un backend que consulta varias fuentes de IA a la vez:
  1. Tres "modelos" (gpt_4_call, claude_3_call, local_llama_call) disparados
     juntos con asyncio.gather y un asyncio.timeout de 2 s sobre la ejecución.
  2. Diez simulaciones de llamadas con un asyncio.Semaphore que deja correr
     solo 2 a la vez.

No usa time.sleep (bloquea el event loop): toda espera es await asyncio.sleep().
Requiere Python 3.11+ (asyncio.timeout); pensado para 3.12.
"""
import asyncio
import logging
import random
import time

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("orquestador")

TIMEOUT_S = 2.0
MAX_CONCURRENTES = 2
INICIO = time.perf_counter()


def t() -> str:
    """Segundos desde que arrancó el programa, para ver la concurrencia en los logs."""
    return f"[{time.perf_counter() - INICIO:5.2f}s]"


# ---------------------------------------------------------------------------
# 1. Simulación de llamadas a distintos modelos (latencias distintas)
# ---------------------------------------------------------------------------
async def gpt_4_call(prompt: str) -> str:
    log.info(f"{t()} gpt_4_call       → inicia")
    await asyncio.sleep(1.2)
    return f"GPT-4: respuesta a '{prompt}'"


async def claude_3_call(prompt: str) -> str:
    log.info(f"{t()} claude_3_call    → inicia")
    await asyncio.sleep(0.8)
    return f"Claude 3: respuesta a '{prompt}'"


async def local_llama_call(prompt: str) -> str:
    log.info(f"{t()} local_llama_call → inicia")
    await asyncio.sleep(3.5)  # el modelo local es lento: debe caer por timeout
    return f"Llama local: respuesta a '{prompt}'"


async def con_timeout(nombre: str, coro) -> dict:
    """Aplica asyncio.timeout(2) a una llamada. Si vence, captura TimeoutError
    y devuelve un error en vez de cortar el programa."""
    try:
        async with asyncio.timeout(TIMEOUT_S):
            texto = await coro
        log.info(f"{t()} {nombre:16} ✓ respondió")
        return {"modelo": nombre, "ok": True, "respuesta": texto}
    except TimeoutError:
        log.warning(f"{t()} {nombre:16} ✗ superó {TIMEOUT_S}s: TimeoutError capturado")
        return {"modelo": nombre, "ok": False, "error": f"timeout > {TIMEOUT_S}s"}


async def orquestar_modelos(prompt: str) -> list[dict]:
    """Dispara las tres llamadas a la vez. Cada una tiene su timeout de 2 s, así
    que la ejecución total tampoco puede pasar de 2 s."""
    return await asyncio.gather(
        con_timeout("gpt_4_call", gpt_4_call(prompt)),
        con_timeout("claude_3_call", claude_3_call(prompt)),
        con_timeout("local_llama_call", local_llama_call(prompt)),
    )


# ---------------------------------------------------------------------------
# 2. Control de flujo: 10 simulaciones, solo 2 en simultáneo (rate limit)
# ---------------------------------------------------------------------------
async def llamada_simulada(i: int, semaforo: asyncio.Semaphore, activas: list[int]) -> float:
    async with semaforo:  # si ya hay 2 corriendo, espera acá su turno
        activas[0] += 1
        log.info(f"{t()} simulación {i:2} → inicia (activas: {activas[0]})")
        latencia = random.uniform(0.3, 0.7)
        await asyncio.sleep(latencia)
        activas[0] -= 1
        return latencia


async def lote_con_semaforo(n: int = 10) -> None:
    semaforo = asyncio.Semaphore(MAX_CONCURRENTES)
    activas = [0]  # contador compartido solo para mostrarlo en el log
    await asyncio.gather(*(llamada_simulada(i, semaforo, activas) for i in range(1, n + 1)))


async def main() -> None:
    log.info("=== Parte 1: tres modelos en paralelo con timeout de 2 s ===")
    t0 = time.perf_counter()
    resultados = await orquestar_modelos("¿Qué es un agente de IA?")
    total = time.perf_counter() - t0
    for r in resultados:
        log.info(f"    {'OK ' if r['ok'] else 'ERR'} {r}")
    log.info(f"Tiempo total: {total:.2f}s (en serie habría tardado 5.5s)\n")

    log.info(f"=== Parte 2: 10 simulaciones, máximo {MAX_CONCURRENTES} a la vez ===")
    t0 = time.perf_counter()
    await lote_con_semaforo(10)
    log.info(f"Lote terminado en {time.perf_counter() - t0:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
