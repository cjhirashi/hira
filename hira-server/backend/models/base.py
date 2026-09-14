"""`metadata` compartida — único `MetaData()` del producto (`SRV-003-bacnet-adapter`,
`plan.md §3`/§7, T-010).

Antes de esta feature, `models/user_model.py` declaraba su propio `MetaData()`
(única tabla de negocio del producto en ese momento, `SRV-002-auth-rbac`). Con
`devices`/`device_points_candidates` (segunda y tercera tabla) llegando en un
módulo nuevo (`models/device_model.py`), `alembic/env.py::target_metadata`
necesita ver las tres tablas bajo un único objeto — de lo contrario,
`alembic upgrade head`/autogenerate solo vería la metadata que su import
resolviera de último, con riesgo real de que una tabla quede fuera de
`target_metadata` sin que ningún test lo detecte.

Módulo neutro (Art. 10 — corrección de raíz): ni `user_model.py` ni
`device_model.py` importan `metadata` uno del otro (eso acoplaría dos dominios
sin relación semántica); ambos importan de aquí.
"""
from sqlalchemy import MetaData

metadata = MetaData()
