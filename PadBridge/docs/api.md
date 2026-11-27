> Historical 0.1 baseline below. Current implementation: [0.5 boundaries](runtime-0.5.md); current test evidence: [PadTV 0.8 validation](https://github.com/PadTVos/PadTV-OS/blob/main/docs/validation-0.8.md).

# Implemented API surface

The machine-readable class registry is `api/compatibility.json`. Diagnostic
scanning checks referenced classes, not every method or behavioral contract.
Reflection, missing methods and runtime failures are logged by the host with
exit code 78. Unsupported static references stop launch before execution.

| Class | Implemented subset |
|---|---|
| Activity | constructor; protected lifecycle callbacks dispatched create/start/resume and pause/stop/destroy; `setContentView(View)`; `onKeyDown` |
| Context | package name, application context, private files/cache directories, `openFileInput`, `openFileOutput(MODE_PRIVATE)`, assets |
| Bundle | String/int put/get, containsKey |
| Log | d/i/w/e(String,String), writes app log |
| View | context constructor/getter, click listener and performClick |
| ViewGroup | addView, LayoutParams constants/fields (no arbitrary sizing implementation) |
| LinearLayout | vertical orientation only; horizontal throws |
| TextView | CharSequence setText/getText |
| Button | TextView plus mouse/select click; focus traversal |
| ImageView | setImageBitmap; raster drawing via SDL_image |
| BitmapFactory | bounded decodeStream asset loading; renderer validates image format |
| AssetManager | bounded `open(String)` from APK assets, no host path exposure |
| KeyEvent | action/key getters, D-pad/back/enter constants |
| java.io/java.net | OpenJDK implementation inside per-app sandbox; network denied unless declared INTERNET granted |

`setContentView(int)` and `getSystemService` throw explicit errors. Empty base
lifecycle methods and unhandled-key `false` are Android callback semantics,
not simulated service implementations. Arbitrary native libraries, layouts,
resource IDs, notifications, intents, WebView, Google Play Services, codecs and
DRM are not supported. This is an experimental implementation of these methods,
not Android CTS compliance.
