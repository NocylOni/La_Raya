package mx.raya.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Base64;
import android.view.KeyEvent;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.OutputStream;

/**
 * Raya corre como una sola página local (assets/index.html) dentro de un WebView.
 *
 * Un WebView pelón rompe tres cosas que esta app sí usa, así que aquí se resuelven:
 *   1. localStorage — se habilita explícitamente; es donde vive TODO el historial.
 *   2. Exportar respaldos — los botones crean un blob: y hacen click en un <a download>.
 *      El DownloadListener del WebView nunca se entera de un blob:, así que el shim de
 *      JS (vendor/android-bridge.js) lo convierte a base64 y lo manda acá.
 *   3. Importar JSON/CSV — un <input type="file"> no abre nada sin onShowFileChooser.
 */
public class MainActivity extends Activity {

    private static final int REQ_PICK_FILE = 1001;
    private static final int REQ_SAVE_FILE = 1002;

    private WebView web;
    private ValueCallback<Uri[]> pendingFileCallback;
    private byte[] pendingSaveBytes;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // localStorage: sin esto se pierde todo
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setSupportZoom(false);
        // el HTML ya es responsivo; que el texto no lo re-escale encima
        s.setTextZoom(100);
        // deja que la página local pida el tipo de cambio y los diccionarios por https
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);

        web.addJavascriptInterface(new Bridge(), "RayaAndroid");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                // los enlaces de Recursos (WordReference, RAE…) salen al navegador
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                        return true;
                    } catch (Exception ignored) { }
                }
                return false;
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view,
                                             ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (pendingFileCallback != null) pendingFileCallback.onReceiveValue(null);
                pendingFileCallback = callback;
                try {
                    Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("*/*");
                    startActivityForResult(i, REQ_PICK_FILE);
                    return true;
                } catch (Exception e) {
                    pendingFileCallback = null;
                    return false;
                }
            }
        });

        if (state != null) web.restoreState(state);
        else web.loadUrl("file:///android_asset/index.html");
    }

    /** Puente que usa vendor/android-bridge.js para guardar respaldos. */
    private class Bridge {
        @JavascriptInterface
        public void saveFile(String filename, String base64, String mime) {
            try {
                pendingSaveBytes = Base64.decode(base64, Base64.DEFAULT);
            } catch (Exception e) {
                toast("No se pudo preparar el archivo.");
                return;
            }
            // Storage Access Framework: el usuario elige dónde. Sin permisos especiales.
            Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            i.addCategory(Intent.CATEGORY_OPENABLE);
            i.setType(mime == null || mime.isEmpty() ? "application/octet-stream" : mime);
            i.putExtra(Intent.EXTRA_TITLE, filename);
            runOnUiThread(() -> {
                try {
                    startActivityForResult(i, REQ_SAVE_FILE);
                } catch (Exception e) {
                    pendingSaveBytes = null;
                    toast("No hay app para guardar archivos.");
                }
            });
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);

        if (req == REQ_PICK_FILE) {
            if (pendingFileCallback == null) return;
            Uri[] out = null;
            if (res == RESULT_OK && data != null && data.getData() != null) {
                out = new Uri[]{ data.getData() };
            }
            pendingFileCallback.onReceiveValue(out);
            pendingFileCallback = null;
            return;
        }

        if (req == REQ_SAVE_FILE) {
            byte[] bytes = pendingSaveBytes;
            pendingSaveBytes = null;
            if (res != RESULT_OK || data == null || data.getData() == null || bytes == null) return;
            try (OutputStream os = getContentResolver().openOutputStream(data.getData())) {
                if (os == null) throw new IllegalStateException("sin stream");
                os.write(bytes);
                os.flush();
                toast("Respaldo guardado.");
            } catch (Exception e) {
                toast("No se pudo guardar el respaldo.");
            }
        }
    }

    private void toast(String msg) {
        runOnUiThread(() -> Toast.makeText(MainActivity.this, msg, Toast.LENGTH_SHORT).show());
    }

    @Override
    public boolean onKeyDown(int code, KeyEvent ev) {
        if (code == KeyEvent.KEYCODE_BACK && web != null && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(code, ev);
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        if (web != null) web.saveState(out);
    }
}
