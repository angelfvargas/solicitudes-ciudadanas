"""Funcionalidad opcional de IA (alternativa A de la prueba: clasificación automática).

La lógica de negocio (qué se pregunta, cómo se valida) está separada del proveedor
(a quién se le pregunta). Cambiar Gemini por otro modelo es escribir otra clase que
cumpla LLMProvider; el clasificador no se toca.
"""
