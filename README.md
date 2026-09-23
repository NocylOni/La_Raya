# La_Raya

HTML. Allows to track work shifts, income, absences on a daily, biweekly and monthly basis. With real time tracking and graphs.
Gives option to export the file, which you'd have to import every time you open it, but sometimes it seems to not be necessary , just save or finish shift and close tab, shoulld be updated by next time you open it.
Open to suggestions, just made for fun.
Also, there is info there already, just to give you idea of how it looks, you can delete it all.

---

## APK para Android

`La Raya.html` es la fuente de verdad. El APK se arma a partir de ese mismo archivo:
edítalo, haz push, y GitHub genera un APK nuevo.

### Bajar el APK

1. Pestaña **Actions** → el run más reciente de **APK**
2. Sección **Artifacts** → `raya-apk`
3. Descomprime y pasa el `.apk` al celular

Al abrirlo, Android va a pedir permiso para "instalar apps desconocidas" para tu
navegador o gestor de archivos. Es normal en cualquier APK que no venga de Play Store.

Si empujas un tag `v1.0`, `v1.1`, etc., el APK además se publica como Release.

### Qué trae

- Corre **sin internet**: el HTML, Chart.js y las tres tipografías van dentro del APK.
  Solo el tipo de cambio y los diccionarios de Recursos necesitan conexión.
- **Exportar respaldos** abre el selector de Android y guarda donde tú digas.
- **Importar JSON/CSV** abre el selector de archivos normal.
- Tus datos viven en el `localStorage` del WebView, igual que en la compu, pero
  separados: el celular y la computadora **no se sincronizan solos**. Para pasarlos,
  exporta un respaldo de un lado e impórtalo del otro.
- Los enlaces de Recursos (WordReference, RAE…) abren en el navegador.

### Compilarlo tú

Necesitas JDK 17, Node y el SDK de Android (Android Studio lo trae).

```bash
cd android
./gradlew assembleDebug        # o: gradle assembleDebug
# sale en android/app/build/outputs/apk/debug/app-debug.apk
```

`assets/index.html` se genera solo antes de cada build (`tools/prepare-assets.mjs`),
así que no lo edites a mano: se sobrescribe. Edita `La Raya.html`.

### Estructura

```
La Raya.html                     la app (esto es lo que editas)
tools/prepare-assets.mjs         copia el HTML a assets y lo apunta a Chart.js y
                                 fuentes locales; inyecta el puente de Android
android/                         wrapper de WebView (mx.raya.app)
  app/src/main/java/.../MainActivity.java
  app/src/main/assets/vendor/    chart.umd.js, fuentes, android-bridge.js
.github/workflows/apk.yml        arma el APK en cada push
```
