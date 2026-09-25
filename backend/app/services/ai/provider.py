from typing import Protocol


class LLMProvider(Protocol):
    """Contrato mínimo que el clasificador necesita de cualquier modelo de lenguaje."""
    model_name: str

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> str:
        """Devuelve el texto JSON generado. Lanza AIUnavailableError si el servicio falla."""
        ...
