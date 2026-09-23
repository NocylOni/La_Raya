/* Puente Android para Raya.
 *
 * Los botones de exportar (respaldo JSON, CSV de llamadas, CSV del glosario) hacen esto:
 *
 *     const blob = new Blob([...]);
 *     const a = document.createElement('a');
 *     a.href = URL.createObjectURL(blob);
 *     a.download = 'raya-....json';
 *     a.click();                       // <- el <a> nunca se inserta en el DOM
 *
 * En un WebView eso no descarga nada: el DownloadListener no ve las URL blob:, y como
 * el <a> está suelto tampoco burbujea un click al document. Así que se intercepta
 * HTMLAnchorElement.prototype.click, que sí funciona con elementos sueltos.
 *
 * En el navegador normal este archivo no hace nada (no existe window.RayaAndroid).
 */
(function () {
  if (!window.RayaAndroid || typeof window.RayaAndroid.saveFile !== 'function') return;

  var blobs = new Map();

  var createObjectURL = URL.createObjectURL.bind(URL);
  URL.createObjectURL = function (obj) {
    var url = createObjectURL(obj);
    if (obj instanceof Blob) blobs.set(url, obj);
    return url;
  };

  var revokeObjectURL = URL.revokeObjectURL.bind(URL);
  URL.revokeObjectURL = function (url) {
    // el código de Raya revoca inmediatamente después del click; conservamos el blob
    // hasta que termine de leerse y lo soltamos en handOff()
    if (!blobs.has(url)) revokeObjectURL(url);
  };

  function handOff(url, filename, blob) {
    var reader = new FileReader();
    reader.onloadend = function () {
      var s = String(reader.result || '');
      var comma = s.indexOf(',');
      var b64 = comma >= 0 ? s.slice(comma + 1) : s;
      try {
        window.RayaAndroid.saveFile(filename, b64, blob.type || 'application/octet-stream');
      } catch (e) { /* si el puente falla, no rompemos la página */ }
      blobs.delete(url);
      try { revokeObjectURL(url); } catch (e) {}
    };
    reader.onerror = function () {
      blobs.delete(url);
      try { revokeObjectURL(url); } catch (e) {}
    };
    reader.readAsDataURL(blob);
  }

  var nativeClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    var href = this.getAttribute('href') || '';
    var name = this.getAttribute('download');
    if (name && href.indexOf('blob:') === 0) {
      var blob = blobs.get(href);
      if (blob) { handOff(href, name, blob); return; }
      // blob creado antes de que cargara este shim: recupéralo por fetch
      var self = this;
      fetch(href).then(function (r) { return r.blob(); })
                 .then(function (b) { handOff(href, name, b); })
                 .catch(function () { nativeClick.call(self); });
      return;
    }
    return nativeClick.apply(this, arguments);
  };
})();
