# NeuralVISION Plugin Marketplace

Repositorio centralizado de plugins para [neuralVISION](https://github.com/OneclickEB/neural-vision).

## Estructura

```
plugins/
  <plugin_code>/
    metadata.json          ← descripción, tags, icon, input_types
    <version>/
      bundle.json          ← bundle nv_plugin_bundle_v1 con source_code
catalog.json               ← índice generado automáticamente por GitHub Action
```

## Catálogo

El archivo `catalog.json` se genera automáticamente en cada push a `plugins/**` mediante la GitHub Action `build-catalog.yml`.

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
4. `git push` → la GitHub Action regenera `catalog.json`
