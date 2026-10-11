# Üç ses araştırma çalışması

VS Code'da kendi ses-analizi klasörünüzü açın. Her notebook'ta Select Kernel üzerinden bu projenin .venv ortamını seçin. İlk hücre seçilen Python yolunu gösterir.

## 1. Gerçek / sahte spektrogram
Dosya: notebooks/02_gercek_sahte_spektrogram.ipynb

- Gerçek sesleri data/raw/gercek, sahte sesleri data/raw/sahte içine kopyalayın.
- Dosya listesini çalıştırın. DOSYALAR hücresindeki örnek yolları gerçek dosya adlarıyla değiştirin.
- İki kayıtta karşılaştırılacak konuşma aralığını BASLANGIC ve SURE ile seçin.
- Dalga biçimi, STFT, Mel ve CQT grafiklerini çalıştırın.
- Grafikler ve ayarlar outputs/figures/karsilastirma altındaki deney klasörüne kaydedilir.
- Görsel farklar tek başına sahtelik kanıtı değildir. Eşleşmeyen metin, cihaz, codec ve konuşmacı sonuçları etkiler.

## 2. Çift sıkıştırma / MDCT
Dosya: notebooks/03_cift_sikistirma_mdct.ipynb

- KAYNAK yoluna tercihen bilinen geçmişli, doğrudan PCM WAV kaydı yazın.
- Tek ilk-bit-hızı, tek son-bit-hızı ve çift sıkıştırma kollarını üretin.
- Varsayılan: AAC-LC 96 kbps, doğrudan 64 kbps ve 96→64 kbps.
- Kaynak dosya korunur. Deney sesleri data/compressed/mdct_deneyleri içinde saklanır.
- Grafikler outputs/figures/mdct; katsayılar ve hizalama raporu outputs/features/mdct içindedir.
- Codec gecikmesi yaklaşık çapraz korelasyon ile giderilir; gecikme değerlerini inceleyin.
- Sıkıştırma hücresini tekrar çalıştırmadan önce ayar hücresini çalıştırarak yeni deney klasörü oluşturun.
- MDCT çözülmüş sese uygulanır; AAC bit akışındaki gerçek kuantize katsayıların dökümü veya doğrulanmış bir çift sıkıştırma dedektörü değildir.

## 3. Sessiz bölgeler / cihaz karşılaştırması
Dosya: notebooks/04_sessiz_bolgeler_cihaz_karsilastirma.ipynb

- Dizüstü: data/raw/cihaz/dizustu
- Telefon: data/raw/cihaz/cep_telefonu
- Aynı odada, mümkünse eşzamanlı 5 s sessizlik + 20 s konuşma + 5 s sessizlik kaydedin.
- Telefon kaydını ayrıca aktarın. İsteğe bağlı dizüstü kaydı KAYIT_AL=True ile başlatılır; varsayılan False.
- DOSYALAR yollarını düzenleyin. Düşük enerjili sessizlik adaylarını çizdirin.
- Eşikleri ayarlayın veya ELLE_ARALIKLAR ile sınırları girin. Parçaları dinleyin.
- Sessiz WAV parçaları ve sessizlikleri çıkarılmış konuşma kopyaları data/processed/cihaz içinde oluşur.
- Sessiz parçalar birleştirilmeden Welch PSD hesaplanır. CSV ve ayarlar outputs/reports/cihaz; grafikler outputs/figures/cihaz içinde saklanır.
- Düşük enerji yöntemi VAD değildir. Farklı cihaz kazançları nedeniyle dijital dB değerleri akustik gürültü düzeyi olarak yorumlanmaz.

## Bağımlılıklar
Mevcut numpy, scipy, matplotlib, librosa, soundfile, sounddevice, ipykernel paketleri kullanılır. AAC kodlama ve M4A/MP3 çözme için imageio-ffmpeg eklenmiştir; sistem geneline FFmpeg kurulumu gerektirmez.

## Kaynaklar
- https://librosa.org/doc/main/api/generated/librosa.feature.melspectrogram.html
- https://librosa.org/doc/main/api/generated/librosa.cqt.html
- https://ffmpeg.org/ffmpeg-codecs.html
- https://www.mathworks.com/help/audio/ref/mdct.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html
