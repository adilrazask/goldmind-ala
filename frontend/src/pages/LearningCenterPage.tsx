import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  Lightbulb,
  ShieldCheck,
  Plus,
  RotateCcw
} from 'lucide-react';
import { api } from '../api';

const FEEDBACK_OPTIONS = [
  'GOOD_RESEARCH',
  'USEFUL_FINDING',
  'OVERFITTED',
  'INVALID_CONCLUSION',
  'POOR_DESIGN',
  'REPEAT_CONDITIONS'
];

export const LearningCenterPage: React.FC = () => {
  const [memory, setMemory] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'lessons' | 'instructions' | 'demonstrations' | 'knowledge' | 'improvements'>('lessons');
  const [newInstruction, setNewInstruction] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchMemory = async () => {
    try {
      const data = await api.getLearningMemory();
      setMemory(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemory();
  }, []);

  const handleFeedback = async (lessonId: string, feedback: string) => {
    try {
      await api.submitFeedback(lessonId, feedback);
      fetchMemory();
    } catch (e: any) {
      alert(`Error submitting feedback: ${e.message}`);
    }
  };

  const handleAddInstruction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newInstruction.trim()) return;
    try {
      await api.addInstruction(newInstruction);
      setNewInstruction('');
      fetchMemory();
    } catch (e: any) {
      alert(e.message);
    }
  };

  if (loading) {
    return <div className="text-xs text-slate-500 py-10 text-center">Loading Autonomous Learning Centre...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-amber-400" />
            Autonomous Learning Centre
          </h1>
          <p className="text-xs text-slate-400">
            5-tier memory persistence: Instructions, Demonstrations, Empirical Lessons, Verified Knowledge, and Procedure Evolution.
          </p>
        </div>

        <button
          onClick={fetchMemory}
          className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* 5-Tier Memory Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto text-xs font-medium">
        <button
          onClick={() => setActiveTab('lessons')}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === 'lessons'
              ? 'bg-amber-500 text-slate-950 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          3. Experience Lessons ({memory?.lessons?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('instructions')}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === 'instructions'
              ? 'bg-amber-500 text-slate-950 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          1. Instructions ({memory?.instructions?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('demonstrations')}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === 'demonstrations'
              ? 'bg-amber-500 text-slate-950 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          2. Demonstrations ({memory?.demonstrations?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('knowledge')}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === 'knowledge'
              ? 'bg-amber-500 text-slate-950 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          4. Verified Knowledge ({memory?.verified_knowledge?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('improvements')}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === 'improvements'
              ? 'bg-amber-500 text-slate-950 font-bold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          5. Procedure Evolution ({memory?.improvement_proposals?.length || 0})
        </button>
      </div>

      {/* Tab 1: Experience Lessons */}
      {activeTab === 'lessons' && (
        <div className="space-y-3">
          <div className="text-xs text-slate-400">
            Recorded outcomes from backtesting and multi-stage validation experiments. Owner feedback calibrates confidence.
          </div>
          <div className="space-y-3">
            {memory?.lessons?.map((lesson: any) => (
              <div
                key={lesson.lesson_id}
                className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 text-xs"
              >
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-amber-400">{lesson.lesson_id}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400 font-mono">{lesson.applicable_conditions}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 font-mono">Confidence: {(lesson.confidence * 100).toFixed(0)}%</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        lesson.verification_status === 'VERIFIED'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : lesson.verification_status === 'REFUTED'
                          ? 'bg-rose-500/10 text-rose-400'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {lesson.verification_status}
                    </span>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-slate-200 font-medium">Observation: {lesson.observation}</div>
                  <div className="text-slate-400 text-[11px] font-mono">Evidence: {lesson.evidence}</div>
                </div>

                {/* Owner Feedback Section */}
                <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/80">
                  <div className="text-[11px] text-slate-500">
                    Owner Assessment:{' '}
                    <strong className="text-slate-300 font-mono">
                      {lesson.owner_feedback || 'PENDING EVALUATION'}
                    </strong>
                  </div>

                  <div className="flex items-center gap-1.5 flex-wrap">
                    {FEEDBACK_OPTIONS.map((opt) => (
                      <button
                        key={opt}
                        onClick={() => handleFeedback(lesson.lesson_id, opt)}
                        className={`px-2 py-1 rounded text-[10px] font-mono transition ${
                          lesson.owner_feedback === opt
                            ? 'bg-amber-500 text-slate-950 font-bold'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                        }`}
                      >
                        {opt.replace(/_/g, ' ')}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Instruction Memory */}
      {activeTab === 'instructions' && (
        <div className="space-y-4">
          <form onSubmit={handleAddInstruction} className="flex gap-2">
            <input
              type="text"
              value={newInstruction}
              onChange={(e) => setNewInstruction(e.target.value)}
              placeholder="e.g. Reject candidates with high profit factor if trade count is under 10."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-lg text-xs font-semibold flex items-center gap-1"
            >
              <Plus className="w-4 h-4" /> Save Instruction
            </button>
          </form>

          <div className="space-y-2">
            {memory?.instructions?.map((inst: any) => (
              <div
                key={inst.id}
                className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span className="text-slate-200">{inst.instruction}</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400">
                  {inst.category}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Demonstrations */}
      {activeTab === 'demonstrations' && (
        <div className="space-y-3">
          {memory?.demonstrations?.map((demo: any) => (
            <div key={demo.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-100">{demo.title}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 font-bold">
                  {demo.feedback_label}
                </span>
              </div>
              <div className="text-slate-300">Decision: {demo.example_decision}</div>
              {demo.explanation && <div className="text-slate-500 italic">"{demo.explanation}"</div>}
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Verified Knowledge */}
      {activeTab === 'knowledge' && (
        <div className="space-y-3">
          {memory?.verified_knowledge?.map((k: any) => (
            <div key={k.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-amber-400">{k.key}</span>
                <span className="text-emerald-400 font-mono text-[11px]">Confidence: {(k.confidence * 100).toFixed(0)}%</span>
              </div>
              <pre className="p-2.5 rounded bg-slate-950 font-mono text-[11px] text-slate-300 overflow-x-auto">
                {JSON.stringify(k.data, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}

      {/* Tab 5: Procedure Evolution */}
      {activeTab === 'improvements' && (
        <div className="space-y-3">
          {memory?.improvement_proposals?.map((prop: any) => (
            <div key={prop.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-100">{prop.target_component}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/10 text-indigo-400">
                  {prop.status}
                </span>
              </div>
              <div className="text-slate-200">Change: {prop.proposed_change}</div>
              <div className="text-slate-400 text-[11px]">Rationale: {prop.rationale}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
