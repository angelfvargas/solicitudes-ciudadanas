"""Capa de SERVICIOS: reglas de negocio. No conocen HTTP ni SQL.

Cada servicio tiene una responsabilidad (SRP) y recibe sus dependencias por el
constructor (inversión de dependencias): en las pruebas se les pasa otra implementación.
"""
