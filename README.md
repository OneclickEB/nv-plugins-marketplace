# NeuralVISION Plugin Marketplace

Repositorio centralizado de plugins para [neuralVISION](https://github.com/OneclickEB/neural-vision).

## Estructura

```
plugins/
  <plugin_code>/
    metadata.json          ← descripción, tags, icon, input_types
    <version>/
      bundle.json          ← bundle nv_plugin_bundle_v1 con source_code
catalog.json               ← índice versionado con SHA-256 de cada bundle
```

## Integridad del catálogo

- La GitHub Action `catalog-integrity.yml` valida en cada PR/push que cada SHA-256
  corresponda al bundle versionado y que las URLs apunten a este repositorio.
- Una auditoría diaria descarga las versiones publicadas y compara los bytes remotos con
  los bundles versionados. Si solo hay hashes stale, abre un PR con los SHA recalculados;
  no lo auto-mergea.
- Si los bytes publicados difieren del bundle versionado, la auditoría falla y requiere
  investigación manual; nunca actualiza el hash para aprobar código remoto inesperado.
- Verificación local:
  ```bash
  python -m unittest scripts.test_verify_catalog_integrity
  python scripts/verify_catalog_integrity.py --check
  ```

## Agregar o actualizar un plugin

1. Clonar este repositorio
2. Exportar desde neuralVISION:
   ```bash
   python tmp/scripts/export_to_marketplace.py \
     --repo /path/a/este/repo \
     --api-url http://<nv-backend> \
     --token <jwt-admin>
   ```
3. Revisar/completar `plugins/<code>/metadata.json` (tags, icon, input_types)
4. Regenerar y revisar el catálogo:
   ```bash
   python scripts/build_catalog.py
   python scripts/verify_catalog_integrity.py --check
   ```
5. Abrir un PR; el check de integridad debe pasar antes de fusionar.
