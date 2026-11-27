# PadTV 0.8 – Android Runtime Integration

Samostatná televizní distribuce založená na **Debianu 13**, pro PC a mini PC
**amd64** připojené přes HDMI. Vydání systému: 0.8; balíčky: 0.8.0; PadBridge: 0.5.0 (experimentální).
Rozhraní Liquid Glass vychází z dodaného návrhu a zachovává logo i pozadí.

## PadBridge v této verzi

PadBridge 0.5 přidává skutečný backend **AOSP ART** s odpovídajícím libcore,
boot DEX a boot image. Vykonává původní kód APK bez Android systému, Waydroidu
nebo náhradní webové aplikace. Enjarify / OpenJDK zůstává alternativou a výchozí
volbou pro dosud funkční aplikace. Ve správě aplikace lze vybrat runtime;
první příprava ART stáhne přibližně 591 MB z původního zdroje projektu R8.

**Hlavní milník Jellyfinu zatím splněný není.** Originální Jellyfin Android TV
0.20.1 vykonává inicializační kód, ale stále selhává na neúplném Android
frameworku. Jeho GUI, připojení k serveru a přehrávání nebyly úspěšně ověřeny.
YouTube TV a Netflix také nejsou funkční. Úspěšné testy ART a vlastních APK
nejsou důkazem kompatibility těchto aplikací.

Nové funkce zahrnují události layoutu a oken, směrové okraje, část témat a
typovaných resources, životní cyklus ContentProvider, původní utility AOSP
a diagnostiku jednotlivých fází startu. Stávající Store, ikony V6 a funkce
Enjarify jsou zachované. Přesné hranice uvádí [ověření 0.8](docs/validation-0.8.md)
a [implementace PadBridge 0.5](PadBridge/docs/runtime-0.5.md).

[Samostatný PadBridge](https://github.com/PadTVos/PadBridge) ·
[Podporované API](PadBridge/docs/api.md)

Zdroj v adresáři `PadBridge/` je stejná kopie jako v samostatném repozitáři.
Původní instalační soubory cizích aplikací se do repozitářů ani ISO nepřidávají.

## Součásti

- Identita PadTV, animace Plymouth, automatické přihlášení do Waylandu.
- Minimalistický labwc bez LightDM, Openboxu a klasického desktopu.
- Systémové API a televizní rozhraní jako samostatné služby s obnovou po pádu.
- Síť přes NetworkManager, Bluetooth přes BlueZ, zvuk přes PipeWire, obraz přes wlroots.
- Vypnutí, restart a uspání přes systemd-logind. Rozlišení s návratem po 15 sekundách bez potvrzení.
- Grafický instalátor Calamares pro BIOS a UEFI.
- Zachovaná odinstalovatelná webová položka YouTube, prohlížeč a soubory. Webová položka není testem Android TV APK.
- Store se skutečnými APK z GitHub Releases, webovými aplikacemi, Flathubem, Google Play a přehledem Debian APT.
- YouTube a Netflix pro Android TV v katalogu s odkazy na oficiální distribuci a přiznanými omezeními; PadBridge umožňuje instalovat lokální originální APK/APKM, jejich spuštění zatím selhává.
- Stejné rozhraní ve vývojovém náhledu Windows.

Waydroid není do tohoto ISO přidaný ani používaný jako náhrada PadBridge.
Historický adaptér v projektu zůstává zachovaný, ale bez externě připraveného
Waydroidu není dostupný. Google Play není součástí ART.

Skutečně provedené kontroly a zbývající zkoušky jsou v [protokolu ověření](docs/validation.md).

## Vyzkoušení

ISO: `dist/padtv-0.8.0-amd64.iso`; vedle něj je SHA-256.
Veřejné testovací vydání je v [GitHub Releases](https://github.com/PadTVos/PadTV-OS/releases/tag/v0.8.0).
Kvůli limitu velikosti obsahuje dvě části ISO a `Join-PadTV.ps1` pro jejich
spojení a ověření. Místní ISO v `dist/` je již kompletní.
Pro celý systém ve Windows použijte zástupce **PadTV 0.8 Android Runtime Integration – virtuální PC**:

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
vznikne až po ověřené instalaci. APT spravuje systémové součásti. GitHub poskytovatel instaluje ověřené APK z konkrétních vydání; obecný komunitní
zdroj zatím připojený není.

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

Pro sestavení 0.8 nainstalujte i [sestavovací závislosti PadBridge](PadBridge/README.md).
`build-iso.sh` sestavuje také samostatný balíček `padbridge`.
