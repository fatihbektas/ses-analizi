from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf

PROJE = Path(__file__).resolve().parents[1]
KAYIT_KLASORU = PROJE / "data" / "raw"
KAYIT_KLASORU.mkdir(parents=True, exist_ok=True)

SURE = 10
ORNEKLEME_HIZI = 48000
KANAL = 1


def main():
    print("Mikrofon:", sd.query_devices(kind="input")["name"])

    sd.check_input_settings(
        samplerate=ORNEKLEME_HIZI,
        channels=KANAL,
        dtype="float32",
    )

    input("\nKaydı başlatmak için Enter tuşuna basın...")
    print(f"Kayıt başladı - {SURE} saniye boyunca kaydediliyor...")

    ses = sd.rec(
        int(SURE * ORNEKLEME_HIZI),
        samplerate=ORNEKLEME_HIZI,
        channels=KANAL,
        dtype="float32",
    )
    sd.wait()

    dosya = KAYIT_KLASORU / (f"ses_{datetime.now():%Y%m%d_%H%M%S_%f}.wav")

    sf.write(dosya, ses, ORNEKLEME_HIZI, subtype="PCM_24")

    tepe = float(np.max(np.abs(ses)))

    print(f"Kaydedildi: {dosya}")
    print(f"Süre: {len(ses) /ORNEKLEME_HIZI:.2f} saniye")
    print(f"Örnekleme hızı: {ORNEKLEME_HIZI} Hz")
    print(f"Tepe genliği: {tepe:.4f}")

    if tepe >= 0.99:
        print("Kırpılma riski var; sonraki kayıtta mikrofon düzeyini azalt.")
    elif tepe < 0.01:
        print("Kayıt seviyesi düşük; mikrofonu ve giriş düzeyini kontrol et.")

    input("\nKaydı dinlemek için Enter'a bas...")

    # Kaydedilen dosyayı okuyarak çal
    kayit, hiz = sf.read(dosya, dtype="float32")
    sd.play(kayit, hiz)
    sd.wait()

    print("Dineme tamamlandı.")


if __name__ == "__main__":
    try:
        main()
    except sd.PortAudioError as hata:
        print(f"\nSes aygıtı hatası: {hata}")
        print(f"Mikrofon iznini ve macOS ses giriş aygıtını kontrol et.")
