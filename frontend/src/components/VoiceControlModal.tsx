import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Send,
  AlertCircle,
  CheckCircle2,
  X,
  Keyboard,
  Radio,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { api } from '../api';

interface VoiceControlModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCommandExecuted?: (result: any) => void;
}

export const VoiceControlModal: React.FC<VoiceControlModalProps> = ({
  isOpen,
  onClose,
  onCommandExecuted
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [editableTranscript, setEditableTranscript] = useState('');
  const [status, setStatus] = useState<'IDLE' | 'LISTENING' | 'PROCESSING' | 'EXECUTING' | 'SUCCESS' | 'ERROR'>('IDLE');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [language, setLanguage] = useState<'en-US' | 'en-IN' | 'hi-IN'>('en-US');
  const [lastResponse, setLastResponse] = useState<any | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [passphraseRequired, setPassphraseRequired] = useState(false);
  const [passphraseInput, setPassphraseInput] = useState('');

  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = language;

      recognition.onstart = () => {
        setIsListening(true);
        setStatus('LISTENING');
        setErrorMessage(null);
      };

      recognition.onresult = (event: any) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setTranscript(currentTranscript);
        setEditableTranscript(currentTranscript);
      };

      recognition.onerror = (event: any) => {
        setIsListening(false);
        setStatus('ERROR');
        if (event.error === 'not-allowed') {
          setErrorMessage(
            'Microphone access was denied. Please allow microphone permissions in your browser URL bar or use the keyboard fallback below.'
          );
        } else if (event.error === 'no-speech') {
          setErrorMessage('No speech detected. Press the microphone and try speaking again.');
        } else {
          setErrorMessage(`Speech recognition error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        if (status === 'LISTENING') {
          setStatus('IDLE');
        }
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [language]);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      setErrorMessage(
        'Web Speech Recognition is not supported by your browser. Please use Chrome, Edge, Safari, or use the keyboard fallback below.'
      );
      setStatus('ERROR');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      setStatus('IDLE');
    } else {
      try {
        setErrorMessage(null);
        setTranscript('');
        setEditableTranscript('');
        recognitionRef.current.lang = language;
        recognitionRef.current.start();
      } catch (e: any) {
        console.error(e);
      }
    }
  };

  const handleSpeak = (text: string) => {
    if (!synthRef.current || isMuted) return;
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current.speak(utterance);
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const handleExecute = async () => {
    const textToRun = editableTranscript.trim();
    if (!textToRun) return;

    setStatus('PROCESSING');
    setErrorMessage(null);

    try {
      // 1. Normalize transcription via backend
      const normRes = await fetch('/api/v1/voice/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: textToRun, language })
      });
      const normData = await normRes.json();
      const cleanedText = normData.normalized_text || textToRun;
      setEditableTranscript(cleanedText);

      setStatus('EXECUTING');

      // 2. Dispatch command via Voice Router
      const execRes = await fetch('/api/v1/voice/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: cleanedText,
          passphrase: passphraseInput || undefined
        })
      });

      const execData = await execRes.json();
      setLastResponse(execData);

      if (execData.status === 'BLOCKED') {
        setStatus('ERROR');
        setErrorMessage(execData.display_text);
        handleSpeak(execData.spoken_summary);
      } else if (execData.requires_passphrase) {
        setPassphraseRequired(true);
        setStatus('IDLE');
      } else {
        setStatus('SUCCESS');
        handleSpeak(execData.spoken_summary);
        if (onCommandExecuted) {
          onCommandExecuted(execData);
        }
      }
    } catch (err: any) {
      setStatus('ERROR');
      setErrorMessage(`Execution error: ${err.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-2xl rounded-2xl glass-card-gold p-6 space-y-5 border border-amber-500/30 shadow-2xl relative">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-amber-500/20 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
              <Radio className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider font-mono flex items-center gap-2">
                <span>GoldMind Voice Assistant</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  PUSH-TO-TALK ACTIVE
                </span>
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                Speak quantitative research commands • Verified AST Sandbox routing
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Selector */}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as any)}
              className="text-xs bg-slate-900 border border-slate-700 text-slate-300 rounded-lg px-2 py-1 font-mono focus:outline-none"
            >
              <option value="en-US">English (US)</option>
              <option value="en-IN">English (India)</option>
              <option value="hi-IN">Hindi (हिन्दी)</option>
            </select>

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-100 rounded-lg bg-slate-900 border border-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Microphone Central Action */}
        <div className="flex flex-col items-center justify-center py-4 space-y-3">
          <div className="relative">
            {isListening && (
              <span className="absolute -inset-3 rounded-full bg-amber-500/20 animate-ping" />
            )}
            <button
              onClick={toggleListening}
              className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-xl active:scale-95 ${
                isListening
                  ? 'bg-gradient-to-tr from-amber-500 to-amber-300 text-slate-950 ring-4 ring-amber-400/50 scale-105'
                  : 'bg-slate-900 hover:bg-slate-800 text-amber-400 border-2 border-amber-500/40'
              }`}
              title={isListening ? 'Click to stop listening' : 'Click to start speaking'}
            >
              {isListening ? <Mic className="w-8 h-8" /> : <MicOff className="w-8 h-8 opacity-80" />}
            </button>
          </div>

          <div className="text-center font-mono">
            <div className="text-xs font-bold text-slate-200">
              {status === 'LISTENING' && <span className="text-amber-400 animate-pulse">● Listening... speak your command</span>}
              {status === 'PROCESSING' && <span className="text-amber-300">Processing trading terminology...</span>}
              {status === 'EXECUTING' && <span className="text-emerald-400">Executing research function...</span>}
              {status === 'IDLE' && <span className="text-slate-400">Press microphone or use keyboard below</span>}
              {status === 'ERROR' && <span className="text-rose-400">Voice recognition notice</span>}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              Example: &ldquo;Analyse XAUUSD on 15 minute&rdquo; or &ldquo;Show agent status&rdquo;
            </div>
          </div>
        </div>

        {/* Permission / Status Alert */}
        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-mono flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Live Editable Transcript */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-xs font-mono text-slate-400">
            <span>Recognized Command (Click to edit before executing):</span>
            <span className="text-[10px] text-amber-400/80">Keyboard Fallback Ready</span>
          </div>
          <div className="relative">
            <textarea
              rows={2}
              value={editableTranscript}
              onChange={(e) => setEditableTranscript(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleExecute();
                }
              }}
              placeholder="Speak via microphone, or type command here..."
              className="w-full bg-slate-950/90 border border-slate-700/80 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400/80 resize-none font-mono"
            />
          </div>
        </div>

        {/* Passphrase Input if required */}
        {passphraseRequired && (
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-300 font-mono">
              <ShieldAlert className="w-4 h-4" />
              <span>Voice Passphrase Required for this Action</span>
            </div>
            <input
              type="password"
              value={passphraseInput}
              onChange={(e) => setPassphraseInput(e.target.value)}
              placeholder="Enter voice command passphrase..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-400"
            />
          </div>
        )}

        {/* Response Box */}
        {lastResponse && (
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <span className="text-slate-400 font-bold">Intent:</span>
                <span className="text-amber-400">{lastResponse.intent}</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                  {lastResponse.permission_level}
                </span>
              </div>

              {/* TTS Controls */}
              <div className="flex items-center gap-1.5">
                {isSpeaking ? (
                  <button
                    onClick={stopSpeaking}
                    className="px-2 py-1 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] flex items-center gap-1"
                  >
                    <VolumeX className="w-3 h-3" /> Stop Voice
                  </button>
                ) : (
                  <button
                    onClick={() => handleSpeak(lastResponse.spoken_summary)}
                    className="px-2 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] flex items-center gap-1"
                  >
                    <Volume2 className="w-3 h-3" /> Replay Voice
                  </button>
                )}
              </div>
            </div>

            <div className="text-slate-200 whitespace-pre-wrap max-h-40 overflow-y-auto">
              {lastResponse.display_text}
            </div>

            <div className="text-[11px] text-amber-300/90 bg-amber-500/10 p-2 rounded border border-amber-500/20">
              <strong>Spoken Summary:</strong> {lastResponse.spoken_summary}
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800">
          <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Deterministic Risk Gate Air-Gapped</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setTranscript('');
                setEditableTranscript('');
                setLastResponse(null);
                setErrorMessage(null);
                setStatus('IDLE');
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-mono text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 transition"
            >
              Clear
            </button>
            <button
              onClick={handleExecute}
              disabled={status === 'PROCESSING' || status === 'EXECUTING' || !editableTranscript.trim()}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 flex items-center gap-1.5 transition active:scale-95 shadow-md"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Execute Command</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
