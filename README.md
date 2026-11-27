# PadTV 0.7 – Android Runtime & Multimedia

Samostatná televizní distribuce založená na **Debianu 13**, pro PC a mini PC
**amd64** připojené přes HDMI. Vydání systému: 0.7; balíčky: 0.7.0; PadBridge: 0.4.0 (experimentální).
Rozhraní Liquid Glass vychází z dodaného návrhu a zachovává logo i pozadí.

## PadBridge v této verzi

Vlastní experimentální překladová vrstva v Rustu spouští základní podepsaná APK
přes DEX → JVM a vlastní Android API, bez Android systému. Ve Store zvolte
**Ukázka PadBridge** pro vlastní testovací APK nebo **Instalovat APK** pro místní APK, více split APK nebo vybranou sadu `.apks`.
Nově je ověřené neupravené APK **Screen Test 4K 1.0.1 od LuoJuly**:
vykreslování přes Canvas, barevné plochy, bitmapová šachovnice a ovládání šipkami.
Waydroid byl během testu vypnutý. Store skutečně stahuje vlastní testovací APK
z GitHub Releases a před instalací ověřuje hash a podpis. Jsou zapojené dodané
ikony PadTV-V6 a odstraněné reklamní úvodní texty Store.
PadBridge 0.4 přidává skutečné MediaExtractor/MediaCodec/AudioTrack/MediaPlayer
přes FFmpeg a omezený zvukový broker, SurfaceView, EGL/GLES přes Mesa,
WebView přes izolované Chromium a správu certifikátů pro jednotlivé aplikace.
Tyto komponenty mají integrační testy vykonávající originální DEX testovacích APK.
**Jellyfin, YouTube TV a Netflix zatím nejsou funkční přes PadBridge.**
Instalace APK není důkazem funkčního rozhraní nebo přehrávání. Stav konkrétních
verzí, chyby a další kroky uvádí [ověření 0.7](docs/validation-0.7.md).
Nejde o plný Bionic, ART, Android framework ani certifikované zařízení.
Stávající webové aplikace a oddělený Waydroid jsou zachované, ale nejsou použité
jako náhrada nebo důkaz kompatibility Android APK.

[Samostatný PadBridge](https://github.com/PadTVos/PadBridge) ·
[Stav implementace 0.4](PadBridge/docs/runtime-0.4.md) ·
[Podporované API](PadBridge/docs/api.md)

Zdroj v adresáři `PadBridge/` je vydaná kopie samostatného projektu, aby šlo OS
sestavit z jednoho checkoutu. Export obou repozitářů vychází ze stejných souborů.

## Součásti

- Identita PadTV, animace Plymouth, automatické přihlášení do Waylandu.
- Minimalistický labwc bez LightDM, Openboxu a klasického desktopu.
- Systémové API a televizní rozhraní jako samostatné služby s obnovou po pádu.
- Síť přes NetworkManager, Bluetooth přes BlueZ, zvuk přes PipeWire, obraz přes wlroots.
- Vypnutí, restart a uspání přes systemd-logind. Rozlišení s návratem po 15 sekundách bez potvrzení.
- Grafický instalátor Calamares pro BIOS a UEFI.
- Odinstalovatelný předinstalovaný YouTube jako webová aplikace, prohlížeč, soubory a Waydroid s instalací APK.
- Store se skutečnými APK z GitHub Releases, webovými aplikacemi, Flathubem, Google Play a přehledem Debian APT.
- YouTube pro Android TV a Netflix pro Android TV v katalogu; instalaci dokončuje uživatel v oficiálním Google Play.
- Stejné rozhraní ve vývojovém náhledu Windows.

Skutečně provedené kontroly a zbývající zkoušky jsou v [protokolu ověření](docs/validation.md).

## Vyzkoušení

ISO: `dist/padtv-0.7.0-amd64.iso`; vedle něj je SHA-256.
Veřejné testovací vydání je v [GitHub Releases](https://github.com/PadTVos/PadTV-OS/releases/tag/v0.7.0).
Kvůli limitu velikosti obsahuje dvě části ISO a `Join-PadTV.ps1` pro jejich
spojení a ověření. Místní ISO v `dist/` je již kompletní.
Pro celý systém ve Windows použijte zástupce **PadTV 0.7 Android Runtime & Multimedia – virtuální PC**:

```powershell
.\.venv\Scripts\python.exe scripts/run-vm.py
```

QEMU/WHPX používá vlastní virtuální disk, NAT, VirtIO grafiku, 16 GB RAM a čtyři jádra.
Pro tento Windows host je HPET vypnutý kvůli prodlevám při startu. Spánek ve VM
zatím není spolehlivě ověřený; pro testování používejte vypnutí a nový start.
Fyzické disky Windows mu nejsou předané. Konfigurace leží v
`virtual-machines/PadTV-0.3-System-Core/machine.json`. Vyžaduje QEMU pro Windows
 a Windows Hypervisor Platform. Opakované spuštění aktivuje existující okno.
Vypínejte přes PadTV nebo QEMU **Machine → Power Down**. Ctrl+Alt+G uvolní vstup z VM.

Pro Live USB zapište celé ISO Rufusem do vybraného USB disku a spusťte počítač z USB.
Instalátor otevřete uvnitř Live systému: **Nastavení → O systému → Nainstalovat PadTV na disk**.
Zápis začne až po výběru cílového disku, souhrnu a závěrečném potvrzení.
Vznikne samostatný správcovský účet; televizní účet při startu jeho heslo nevyžaduje.

Běžné Live USB bez perzistence změny po restartu ztratí. Nová šablona perzistence
ukládá domovy, Waydroid a nastavení připojení; systémové programy zůstávají v ISO.
Staré úložiště `/ union` se k nové verzi nemá přímo připojovat, protože by překrylo
nové systémové soubory. Při přechodu se přenášejí jen uživatelská data.

Pouhý náhled rozhraní a jeho ikona na ploše:

```powershell
.\scripts\preview.ps1
.\scripts\create-desktop-shortcut.ps1
```

Náhled neovládá zařízení, napájení ani instalaci linuxových balíčků. Webové záznamy
lze přidávat a odebírat ve zvláštní knihovně `%LOCALAPPDATA%/padtv/preview`.

## Aplikace a ovládání

Šipky přesouvají výběr, Enter/OK otevírá aplikaci a Esc vrací domů. Win+Home vrací
PadTV z jiné aplikace; Alt+Tab přepíná okna a Alt+F4 zavírá aktuální okno.
Delete, Menu nebo pravé tlačítko na uživatelské aplikaci otevře její správu.
Fungují multimediální klávesy hlasitosti; HDMI-CEC zatím nemá vlastní integraci.

Store uvádí skutečný zdroj aplikace. Flathub používá instalaci `--user`; ikona
vznikne až po ověřené instalaci. APT spravuje systémové součásti. GitHub a komunitní
zdroj zatím nejsou připojené jako automatické zdroje instalace.

YouTube lze odinstalovat ve Store nebo ve správě aplikací včetně jeho profilu.
Při dalším startu se sám nevrátí; znovu jej přidáte ve Store. Předinstalovaný
YouTube je web v samostatném okně Chromium. Android TV verze má ve Store vlastní
položku a po instalaci přednost na domovské obrazovce. Dialog klíčenky je vypnutý; prohlížeč neukládá hesla
systémovou správou hesel.

V **Store → YouTube pro Android TV / Netflix pro Android TV → Připravit Google Play**
stáhnete oficiální GAPPS obraz Waydroidu. Příprava zastaví Android a ponechá jeho
uživatelská data. Potom otevřete Google Play a přihlaste se vlastním účtem.
Může být nutná [registrace zařízení](https://docs.waydro.id/faq/google-play-certification).
Ta není certifikací Google TV ani zárukou Netflix DRM. Google Play rozhoduje,
zda aplikaci pro zařízení nabídne. Samotné otevření její stránky neznamená instalaci;
PadTV ji ověří po návratu do Store nebo volbou **Obnovit stav**.

V **Aplikace → Android / APK** zůstává příprava VANILLA obrazu a instalace APK
x86/x86_64 nebo bez nativních knihoven. Čistě ARM balíčky se odmítají.
Kodi a Jellyfin nejsou součástí výchozí nabídky ani katalogu.

VM dostává internet přes Windows. Pro vlastní Wi-Fi a Bluetooth potřebuje předaný
adaptér; rozhraní nepřítomnost zařízení uvádí. Fyzické PC používá dostupný hardware.

## Vývoj

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m padtv --page store --screenshot artifacts/store.png
```

Sestavení na Debianu 13 amd64 s oprávněním root a podporou mount:

```sh
sudo apt-get install live-build debootstrap xorriso squashfs-tools \
  isolinux syslinux-common grub-pc-bin grub-efi-amd64-bin mtools \
  python3 python3-pyqt6 dpkg-dev build-essential devscripts equivs \
  ca-certificates curl git qemu-utils e2fsprogs
# Doplňte také sestavovací závislosti z PadBridge/README.md.
bash scripts/build-deb.sh
sudo bash scripts/build-iso.sh
bash scripts/build-persistence.sh
```

Vzniknou balíčky `padtv-core`, `padtv-session`, `padtv-installer`, opravené Exo
a hybridní ISO. Integrační testy `tests/integration_*.py` jsou výslovně pro
jednorázové VM; mění skutečnou grafickou relaci a systémové nastavení.

## GitHub

Veřejné zdroje jsou v organizaci [PadTVos](https://github.com/PadTVos):
[OS](https://github.com/PadTVos/PadTV-OS), [Updates](https://github.com/PadTVos/PadTV-Updates),
[Store](https://github.com/PadTVos/PadTV-Store), [Apps](https://github.com/PadTVos/PadTV-Apps)
a [Website](https://github.com/PadTVos/PadTV-Website).

Skripty pro přípravu a první publikaci:

```powershell
python scripts/prepare-repositories.py
.\scripts\publish-repositories.ps1 -Organization PadTVos
```

Druhý příkaz pouze ukáže plán. Publikace vyžaduje existující organizaci,
přihlášení a přepínač `-Publish`. Lokální export není založení organizace.

- [Systémová architektura a API](docs/system-core.md)
- [Store a šest repozitářů](docs/github-and-store.md)
- [Stav ověření](docs/validation.md)
- [Historické ověření 0.3.1](docs/validation-0.3.1.md)

Pro sestavení 0.7 nainstalujte i [sestavovací závislosti PadBridge](PadBridge/README.md).
`build-iso.sh` sestavuje také samostatný balíček `padbridge`.
