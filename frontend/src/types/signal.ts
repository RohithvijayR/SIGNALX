export interface SignalMetadata {
  filename: string;
  format: string;
  datatype: string;
  sample_count: number;
  sample_rate: number;
  sample_rate_source: string;
  center_frequency: number | null;
  duration_seconds: number;
  channels: number;
  metadata_source: string;
}

export interface TimeDomainStats {
  mean: number;
  variance: number;
  rms: number;
  peak: number;
  crest_factor: number;
  kurtosis: number;
  skewness: number;
  duration_seconds: number;
  sample_count: number;
}

export interface TimeChartData {
  time: number[];
  i: number[];
  q: number[];
  magnitude: number[];
  phase: number[];
  finite_point_count?: number;
}

export interface FreqCharacteristics {
  dominant_frequency_hz: number;
  occupied_bandwidth_hz: number;
  bandwidth_3db_hz: number;
  spectral_centroid_hz: number;
  spectral_bandwidth_hz: number;
  spectral_flatness: number;
  spectral_entropy: number;
  frequency_label: string;
}

export interface FreqChartData {
  fft_freqs: number[];
  fft_mag_db: number[];
  psd_freqs: number[];
  psd_db: number[];
}

export interface SpectrogramData {
  params: {
    nperseg: number;
    noverlap: number;
    nfft: number;
    window: string;
  };
  time: number[];
  freq: number[];
  z_db: number[][];
}

export interface ConstellationData {
  raw: { i: number[]; q: number[] };
  normalized: { i: number[]; q: number[] };
  symbol_sampled: { i: number[]; q: number[] };
  total_points: number;
  timing: {
    reliable: boolean;
    confidence?: number;
    samples_per_symbol?: number | null;
    reason: string;
  };
}

export interface ModulationCandidate {
  modulation: string;
  confidence_pct: number;
}

export interface ModulationPrediction {
  mode: string;
  prediction: string;
  confidence: number;
  confidence_label?: string;
  candidates: ModulationCandidate[];
  mode_comparisons: {
    iq_only: string;
    wav_only: string;
    fused: string;
  };
}

export interface AdvancedDetectionResult {
  result: string;
  confidence_pct: number;
  status: string;
  candidate_scheme?: string;
  pattern?: string;
  evidence_used: string[];
}

export interface ParameterTableRow {
  parameter: string;
  result: string;
  source: string;
  confidence: string;
  ground_truth: string;
}

export interface ExplainabilityEvidence {
  check: string;
  detail: string;
}

export interface AnalysisEvidence {
  feature: string;
  value: string;
  interpretation: string;
}

export interface SignalAnalysisReport {
  record_id?: number;
  metadata: SignalMetadata;
  preprocessing_audit: {
    actions: string[];
    original_samples: number;
    preprocessed_samples: number;
    effective_sample_rate: number;
    peak_magnitude: number;
    rms_magnitude: number;
    signal_power_db: number;
  };
  time_domain: {
    stats: TimeDomainStats;
    chart_data: TimeChartData;
  };
  freq_domain: {
    characteristics: FreqCharacteristics;
    chart_data: FreqChartData;
  };
  spectrogram: SpectrogramData;
  constellation: ConstellationData;
  snr: {
    snr_db: number;
    snr_m2m4_db: number;
    snr_spectral_db: number;
    confidence: string;
    method: string;
  };
  features: {
    time_domain: Record<string, number>;
    iq_domain: Record<string, number>;
    frequency_domain: Record<string, number>;
    cumulants: Record<string, number>;
  };
  inference_mode: string;
  modulation_prediction: ModulationPrediction;
  fec_detection: AdvancedDetectionResult;
  interleaving_detection: AdvancedDetectionResult;
  parameter_table: ParameterTableRow[];
  explainability_evidence: ExplainabilityEvidence[];
  analysis_evidence: AnalysisEvidence[];
  conflicting_evidence: boolean;
  ground_truth_validation?: Record<string, any>;
  is_demo_signal: boolean;
  processing_time_ms: number;
}

export interface HistoryRecord {
  id: number;
  timestamp: string;
  filename: string;
  format: string;
  sample_rate: number;
  modulation: string;
  confidence: number;
  fec_scheme: string;
  interleaving: string;
  snr_db: number;
  processing_time_ms: number;
}
