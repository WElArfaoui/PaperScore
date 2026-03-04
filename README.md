# PaperScore

Extensión de navegador que muestra el **Factor de Impacto (IF)** y el **Cuartil JCR** de cada revista directamente en los resultados de búsqueda de **PubMed** y **Scopus**, sin salir de la página.

---

## Resultado visual

En cada resultado aparece automáticamente junto al nombre de la revista:

| Badge | Significado |
|-------|-------------|
| `IF 64.80` (verde) | Factor de Impacto ≥ 10 |
| `IF 5.20` (amarillo) | Factor de Impacto entre 5 y 9.9 |
| `IF 3.10` (gris) | Factor de Impacto < 5 |
| `Q1` / `Q2` / `Q3` / `Q4` | Cuartil JCR de la revista |
| `Sin información` | Revista no encontrada en la base de datos |

---

## Instalación

> Requiere Google Chrome (o cualquier navegador basado en Chromium).

1. Descarga o clona este repositorio:
   ```bash
   git clone https://github.com/WElArfaoui/PaperScore.git
   ```

2. Abre Chrome y ve a `chrome://extensions/`

3. Activa el **Modo desarrollador** (interruptor arriba a la derecha)

4. Haz clic en **"Cargar sin empaquetar"** y selecciona la carpeta `extension/`

5. Listo. Ve a [PubMed](https://pubmed.ncbi.nlm.nih.gov) o [Scopus](https://www.scopus.com) y busca cualquier paper.

---

## Base de datos de revistas

La extensión usa un archivo `extension/journal_data.json` con los datos de ~20.000 revistas indexadas en Scimago.

**Este archivo se actualiza automáticamente cada mes** mediante un workflow de GitHub Actions que descarga el CSV oficial de [Scimago](https://www.scimagojr.com) y regenera el JSON sin intervención manual.

Para forzar una actualización manual desde GitHub:
1. Ve a la pestaña **Actions** del repositorio
2. Selecciona el workflow **"Actualizar base de datos de revistas"**
3. Haz clic en **"Run workflow"**

---

## Estructura del proyecto

```
PaperScore/
├── .github/
│   └── workflows/
│       └── update_db.yml       # Auto-actualización mensual de la BD
├── extension/
│   ├── manifest.json           # Configuración de la extensión (Manifest V3)
│   ├── content.js              # Inyecta los badges en PubMed y Scopus
│   ├── content.css             # Estilos de los badges
│   ├── popup.html / .css / .js # Panel de la extensión
│   └── journal_data.json       # Base de datos de revistas (auto-generada)
└── build_journal_db.py         # Script que convierte el CSV de Scimago a JSON
```

---

## Fuente de datos

Los datos de Factor de Impacto y Cuartil provienen de [Scimago Journal Rankings](https://www.scimagojr.com), que publica métricas de revistas de forma gratuita y abierta.

> **Nota:** Scimago usa el índice **SJR** (SCImago Journal Rank), no el JIF de Clarivate. Para los cuartiles JCR oficiales de Clarivate se requiere acceso institucional al [Journal Citation Reports](https://jcr.clarivate.com/).

---

## Inspiración

Proyecto inspirado en [MedScope](https://github.com/PharmProai/MedScope), extendido para soportar Scopus y actualización automática de la base de datos.
