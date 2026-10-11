"""Ses araştırma notebook'larının ortak yardımcıları. Özgün dosyaları değiştirmez."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
import numpy as np
import soundfile as sf
from scipy import signal, fft
import librosa

EXTENSIONS = {'.wav', '.flac', '.ogg', '.mp3', '.m4a', '.aac', '.aiff', '.aif'}

def project_root():
    for p in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
        if (p / 'data' / 'raw').is_dir() and (p / 'src').is_dir():
            return p
    raise FileNotFoundError('VS Code ile ses-analizi proje klasörünü açın.')

def audio_files(folder):
    return sorted(p for p in Path(folder).rglob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS)

def ffmpeg_exe():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError('Notebook ortamına imageio-ffmpeg kurun: %pip install imageio-ffmpeg') from exc

def ffmpeg_run(arguments):
    command = [ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-nostdin', *map(str, arguments)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return command

def read_audio(path, target_sr=None, start=0.0, duration=None, channel=0):
    """İlk/seçili kanalı okur. Tepe veya RMS normalizasyonu uygulamaz."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Ses bulunamadı: {path}')
    try:
        with sf.SoundFile(path) as f:
            native_sr, channels, subtype = f.samplerate, f.channels, f.subtype
            if start < 0 or start >= len(f) / native_sr:
                raise ValueError('Başlangıç zamanı kaydın içinde olmalı.')
            f.seek(round(start * native_sr))
            n = -1 if duration is None else round(duration * native_sr)
            samples = f.read(n, dtype='float64', always_2d=True)
    except (sf.LibsndfileError, RuntimeError):
        with tempfile.TemporaryDirectory() as temp:
            decoded = Path(temp) / 'decoded.wav'
            args = ['-i', path, '-vn']
            if start:
                args += ['-ss', start]
            if duration is not None:
                args += ['-t', duration]
            ffmpeg_run([*args, '-c:a', 'pcm_f32le', decoded])
            samples, native_sr = sf.read(decoded, dtype='float64', always_2d=True)
            channels, subtype = samples.shape[1], 'decoded float WAV'
    if not 0 <= channel < channels:
        raise ValueError(f'Kanal {channel} yok; dosyada {channels} kanal var.')
    y = samples[:, channel]
    if len(y) < 2 or not np.isfinite(y).all():
        raise ValueError('Ses boş, çok kısa veya geçersiz değerler içeriyor.')
    sr = native_sr if target_sr is None else target_sr
    if sr != native_sr:
        y = librosa.resample(y, orig_sr=native_sr, target_sr=sr)
    info = dict(file=str(path), native_sr=int(native_sr), analysis_sr=int(sr),
                channels=int(channels), selected_channel=channel, subtype=subtype,
                start_s=start, duration_s=len(y)/sr, peak=float(np.max(np.abs(y))))
    return y, int(sr), info

def save_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def mdct(y, sr, n=1024):
    """2N örnek sine penceresi, N adım. Analiz MDCT'si; codec bit akışını çözmez.
    X[k] = sqrt(2/N) sum(x[n] w[n] cos(pi/N (n+.5+N/2)(k+.5)))
    """
    if n % 2 or len(y) < 2*n:
        raise ValueError('N çift olmalı; ses en az 2N örnek içermeli.')
    frames = np.lib.stride_tricks.sliding_window_view(y, 2*n)[::n]
    w = np.sin(np.pi / (2*n) * (np.arange(2*n) + .5))
    z = frames * w
    a, b, c, d = np.split(z, 4, axis=1)
    folded = np.concatenate((-c[:, ::-1] - d, a - b[:, ::-1]), axis=1)
    coeff = fft.dct(folded, type=4, axis=1, norm=None) * .5 * np.sqrt(2/n)
    times = (np.arange(len(frames))*n + n) / sr
    frequencies = (np.arange(n)+.5)*sr/(2*n)
    return coeff.T, times, frequencies

def align_to_reference(reference, candidate, sr, max_delay_s=.25):
    """İlk 4 saniyede çapraz korelasyon; sıfır eklenen uçlar valid=False olur."""
    n = min(len(reference), len(candidate), 4*sr)
    if np.std(reference[:n]) < 1e-9 or np.std(candidate[:n]) < 1e-9:
        raise ValueError('Hizalama için yeterli ses enerjisi yok.')
    a, b = reference[:n], candidate[:n]
    corr = signal.correlate(b-b.mean(), a-a.mean(), mode='full', method='fft')
    lags = signal.correlation_lags(len(b), len(a))
    allowed = np.abs(lags) <= round(max_delay_s*sr)
    lag = int(lags[allowed][np.argmax(corr[allowed])])
    if abs(lag) == round(max_delay_s*sr):
        raise ValueError('Gecikme arama sınırında; max_delay_s değerini artırın.')
    idx = np.arange(len(reference)) + lag
    valid = (idx >= 0) & (idx < len(candidate))
    aligned = np.zeros_like(reference)
    aligned[valid] = candidate[idx[valid]]
    return aligned, valid, lag

def low_energy_intervals(y, sr, threshold_dbfs=-45, frame_ms=20,
                         min_s=.3, guard_s=.05):
    """Enerjiye dayalı sessizlik adayları. Konuşma algılayıcı/VAD değildir."""
    size = max(1, round(sr*frame_ms/1000))
    starts = np.arange(0, len(y), size)
    levels = np.array([20*np.log10(max(np.sqrt(np.mean(y[s:s+size]**2)), 1e-12)) for s in starts])
    quiet = levels < threshold_dbfs
    edges = np.diff(np.r_[False, quiet, False].astype(int))
    intervals = []
    guard = round(sr*guard_s)
    for first, last in zip(np.flatnonzero(edges==1), np.flatnonzero(edges==-1)):
        a = int(starts[first]) + guard
        b = min(int(last*size), len(y)) - guard
        if b-a >= round(min_s*sr):
            intervals.append((a,b))
    return intervals, (starts+size/2)/sr, levels

def interval_psd(y, sr, intervals, window_s=.05):
    """Parçalar ayrı Welch PSD; pencere sayısıyla ağırlıklandırılır. Birleştirme yok."""
    n = round(window_s*sr)
    hop = n - n//2
    spectra, weights = [], []
    for a,b in intervals:
        if b-a < n:
            continue
        f,p = signal.welch(y[a:b], fs=sr, window='hann', nperseg=n,
                           noverlap=n//2, detrend='constant', scaling='density')
        spectra.append(p)
        weights.append(1+(b-a-n)//hop)
    if not spectra:
        raise ValueError('PSD için yeterince uzun sessiz bölüm yok; eşiği/aralıkları kontrol edin.')
    return f, np.average(spectra, axis=0, weights=weights)
