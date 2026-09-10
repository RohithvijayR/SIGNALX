import os
import json
import numpy as np
from scipy.io import wavfile
from typing import Dict, Any, Tuple

MODULATION_CLASSES = ["BPSK", "QPSK", "8PSK", "2FSK", "4FSK", "16QAM", "64QAM", "AM", "FM"]
FEC_SCHEMES = ["None", "Convolutional", "LDPC", "Reed-Solomon", "BCH"]
INTERLEAVING_PATTERNS = ["None", "16x16 Matrix", "8x32 Block", "Helical"]

def generate_synthetic_rf_signal(
    modulation: str = "QPSK",
    num_samples: int = 16384,
    sample_rate: float = 1000000.0,
    snr_db: float = 15.0,
    fec_scheme: str = "Convolutional",
    interleaving_pattern: str = "16x16 Matrix",
    freq_offset: float = 500.0,
    phase_offset_rad: float = 0.2
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generates a realistic synthetic RF signal with pulse shaping, AWGN noise, and channel impairments.
    Returns complex64 signal array and ground-truth metadata dictionary.
    """
    if modulation not in MODULATION_CLASSES:
        modulation = "QPSK"

    np.random.seed(np.random.randint(0, 100000))
    sps = 8  # Samples per symbol
    num_symbols = num_samples // sps

    if modulation == "BPSK":
        bits = np.random.randint(0, 2, num_symbols)
        symbols = 2 * bits - 1 + 0j
    elif modulation == "QPSK":
        bits_i = np.random.randint(0, 2, num_symbols)
        bits_q = np.random.randint(0, 2, num_symbols)
        symbols = (2 * bits_i - 1 + 1j * (2 * bits_q - 1)) / np.sqrt(2)
    elif modulation == "8PSK":
        angles = (2 * np.pi / 8.0) * np.random.randint(0, 8, num_symbols)
        symbols = np.exp(1j * angles)
    elif modulation == "16QAM":
        i_syms = np.random.choice([-3, -1, 1, 3], num_symbols)
        q_syms = np.random.choice([-3, -1, 1, 3], num_symbols)
        symbols = (i_syms + 1j * q_syms) / np.sqrt(10)
    elif modulation == "64QAM":
        i_syms = np.random.choice([-7, -5, -3, -1, 1, 3, 5, 7], num_symbols)
        q_syms = np.random.choice([-7, -5, -3, -1, 1, 3, 5, 7], num_symbols)
        symbols = (i_syms + 1j * q_syms) / np.sqrt(42)
    elif modulation == "2FSK":
        bits = np.random.randint(0, 2, num_samples)
        freq_dev = 20000.0  # 20 kHz
        m = 2 * bits - 1
        phase = 2 * np.pi * np.cumsum(m * freq_dev / sample_rate)
        symbols = np.exp(1j * phase)[:num_symbols*sps]
        sps = 1
    elif modulation == "4FSK":
        sym_idx = np.random.randint(0, 4, num_samples)
        freq_devs = np.array([-30000, -10000, 10000, 30000])
        m = freq_devs[sym_idx]
        phase = 2 * np.pi * np.cumsum(m / sample_rate)
        symbols = np.exp(1j * phase)[:num_symbols*sps]
        sps = 1
    elif modulation == "AM":
        t = np.arange(num_samples) / sample_rate
        audio_mod = 0.5 * np.sin(2 * np.pi * 1000 * t) + 0.3 * np.cos(2 * np.pi * 2500 * t)
        carrier = (1.0 + 0.8 * audio_mod) + 0j
        symbols = carrier
        sps = 1
    elif modulation == "FM":
        t = np.arange(num_samples) / sample_rate
        audio_mod = np.sin(2 * np.pi * 1000 * t)
        phase = 2 * np.pi * 50000.0 * np.cumsum(audio_mod) / sample_rate
        symbols = np.exp(1j * phase)
        sps = 1

    # Pulse shaping / Oversampling if digital modulation
    if sps > 1:
        oversampled = np.zeros(num_symbols * sps, dtype=np.complex64)
        oversampled[::sps] = symbols
        # Rectangular / RRC shaping filter approximation
        pulse_shape = np.ones(sps, dtype=np.float32) / np.sqrt(sps)
        tx_signal = np.convolve(oversampled, pulse_shape, mode='same')
    else:
        tx_signal = symbols

    # Truncate/Pad to exact num_samples
    if len(tx_signal) < num_samples:
        tx_signal = np.pad(tx_signal, (0, num_samples - len(tx_signal)))
    else:
        tx_signal = tx_signal[:num_samples]

    # Impairments: Frequency offset & Phase noise
    t_axis = np.arange(len(tx_signal)) / sample_rate
    tx_signal = tx_signal * np.exp(1j * (2 * np.pi * freq_offset * t_axis + phase_offset_rad))

    # Impairments: AWGN Noise
    sig_power = np.mean(np.abs(tx_signal)**2)
    noise_power = sig_power / (10 ** (snr_db / 10.0))
    noise_std = np.sqrt(noise_power / 2.0)
    noise = (np.random.normal(0, noise_std, len(tx_signal)) + 
             1j * np.random.normal(0, noise_std, len(tx_signal)))

    rx_signal = (tx_signal + noise).astype(np.complex64)

    ground_truth = {
        "modulation": modulation,
        "fec": fec_scheme,
        "interleaving": interleaving_pattern,
        "sampling_rate": sample_rate,
        "snr_db": snr_db,
        "frequency_offset_hz": freq_offset,
        "phase_offset_rad": phase_offset_rad,
        "sample_count": len(rx_signal),
        "duration_seconds": len(rx_signal) / sample_rate
    }

    return rx_signal, ground_truth

def save_synthetic_dataset(data_dir: str):
    """
    Pre-generates a small synthetic dataset for demo mode and training baseline models.
    Creates paired .iq, .wav, and .json metadata files.
    """
    os.makedirs(data_dir, exist_ok=True)
    sample_signals = [
        ("QPSK", 15.0, "Convolutional", "16x16 Matrix"),
        ("BPSK", 12.0, "None", "None"),
        ("16QAM", 20.0, "Reed-Solomon", "8x32 Block"),
        ("2FSK", 10.0, "Convolutional", "None"),
        ("8PSK", 18.0, "LDPC", "16x16 Matrix"),
        ("64QAM", 22.0, "BCH", "Helical"),
        ("4FSK", 14.0, "Convolutional", "None"),
        ("AM", 25.0, "None", "None"),
        ("FM", 20.0, "None", "None")
    ]

    generated_files = []
    for mod, snr, fec, interleaver in sample_signals:
        sig, gt = generate_synthetic_rf_signal(
            modulation=mod,
            num_samples=16384,
            sample_rate=1000000.0,
            snr_db=snr,
            fec_scheme=fec,
            interleaving_pattern=interleaver
        )

        base_name = f"demo_{mod.lower()}_{int(snr)}db"
        iq_path = os.path.join(data_dir, f"{base_name}.iq")
        wav_path = os.path.join(data_dir, f"{base_name}.wav")
        meta_path = os.path.join(data_dir, f"{base_name}.json")

        # Save IQ raw binary (complex64)
        sig.tofile(iq_path)

        # Save Stereo WAV (Ch1 = I, Ch2 = Q)
        i_int16 = np.clip(sig.real * 32767.0, -32768, 32767).astype(np.int16)
        q_int16 = np.clip(sig.imag * 32767.0, -32768, 32767).astype(np.int16)
        stereo_int16 = np.column_stack((i_int16, q_int16))
        wavfile.write(wav_path, 1000000, stereo_int16)

        # Save Ground Truth JSON
        gt["iq_file"] = iq_path
        gt["wav_file"] = wav_path
        with open(meta_path, "w") as f:
            json.dump(gt, f, indent=2)

        generated_files.append(base_name)

    return generated_files
