"""Capa de PERSISTENCIA: única parte del sistema que escribe consultas.

Los servicios piden datos a los repositorios y no saben cómo están guardados (SRP):
si mañana cambia una consulta o un índice, solo se toca este paquete.
"""
