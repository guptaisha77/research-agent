import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

type StageStatus = 'waiting' | 'running' | 'done' | 'failed';

type StageState = {
  id: string;
  label: string;
  status: StageStatus;
  message: string;
};

type PipelineEvent = {
  agent: string;
  status: string;
  message: string;
  data?: unknown;
};

const INITIAL_STAGES: StageState[] = [
  { id: 'search', label: 'Search sources', status: 'waiting', message: '' },
  { id: 'summariser', label: 'Summarise', status: 'waiting', message: '' },
  { id: 'fact_checker', label: 'Fact check', status: 'waiting', message: '' },
  { id: 'writer', label: 'Write report', status: 'waiting', message: '' },
];

const AGENT_LABELS: Record<string, string> = {
  search: 'Search Agent',
  summariser: 'Summariser Agent',
  fact_checker: 'Fact Checker Agent',
  writer: 'Writer Agent',
};

function App() {
  const [query, setQuery] = useState('What is retrieval augmented generation?');
  const [stages, setStages] = useState<StageState[]>(INITIAL_STAGES);
  const [log, setLog] = useState<string[]>(['Ready to run the research pipeline.']);
  const [report, setReport] = useState<string>('');
  const [sources, setSources] = useState<{ title: string; url: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const statusSummary = useMemo(() => {
    if (isLoading) return 'Streaming the research pipeline with live agent switching.';
    if (report) return 'Pipeline complete — review the final report and citations below.';
    return 'Enter a query and start the pipeline.';
  }, [isLoading, report]);

  const reportWordCount = useMemo(() => report.trim().split(/\s+/).filter(Boolean).length, [report]);
  const completedStages = stages.filter((stage) => stage.status === 'done').length;
  const sourceCount = sources.length;

  const appendLog = (message: string) => {
    setLog((prev) => [...prev, message]);
  };

  const resetPipeline = () => {
    setStages(INITIAL_STAGES);
    setLog(['Starting a new research run.']);
    setReport('');
    setSources([]);
  };

  const closeEventSource = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  const handleMessage = (event: MessageEvent<string>) => {
    try {
      const payload: PipelineEvent = JSON.parse(event.data);
      const id = payload.agent;
      const status = payload.status as StageStatus;
      const message = payload.message;

      appendLog(`${payload.agent}: ${message}`);

      if (id === 'pipeline' && payload.status === 'complete') {
        setIsLoading(false);
        if (payload.data && typeof payload.data === 'object' && 'report' in payload.data) {
          setReport((payload.data as any).report || '');
          setSources((payload.data as any).sources || []);
        }
        return;
      }

      setStages((current) =>
        current.map((stage) => (stage.id === id ? { ...stage, status, message } : stage))
      );

      if (status === 'done' && payload.data && typeof payload.data === 'object') {
        if (id === 'search' && Array.isArray((payload.data as any).sources)) {
          setSources((payload.data as any).sources.map((item: any) => ({ title: item.title, url: item.url })));
        }
        if (id === 'writer' && typeof (payload.data as any).report === 'string') {
          setReport((payload.data as any).report);
        }
      }
    } catch (error) {
      appendLog('Could not parse event payload.');
    }
  };

  const handleError = () => {
    appendLog('Streaming connection failed.');
    setIsLoading(false);
    closeEventSource();
  };

  const startResearch = (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;

    resetPipeline();
    setIsLoading(true);

    const encoded = encodeURIComponent(query.trim());
    const source = new EventSource(`/research/stream?query=${encoded}`);
    eventSourceRef.current = source;

    source.onmessage = handleMessage;
    source.onerror = handleError;
  };

  const reportParagraphs = useMemo(
    () => report.split(/\n{2,}|\r\n{2,}/).filter((paragraph) => paragraph.trim().length > 0),
    [report]
  );

  const reportWithoutSources = useMemo(() => {
    // Remove "Sources:", "References:", "Citations:" sections and everything after
    let cleaned = report
      .split(/\n#+\s*(?:sources|references|citations)/im)[0]
      .split(/\n\*\*sources\*\*|Sources:|References:|Citations:/i)[0]
      .trim();
    
    // Also remove lines that are just citation references like "[1] https://..."
    cleaned = cleaned
      .split('\n')
      .filter(line => !/^\s*\[\d+\]\s*(?:https?:|www|\.)/i.test(line))
      .join('\n')
      .trim();
    
    return cleaned;
  }, [report]);

  return (
    <div className="min-h-screen bg-black text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <header className="mb-10 rounded-[1.5rem] border border-slate-800 bg-black p-5">
          <p className="inline-flex rounded-full border border-cyan-500/20 bg-cyan-500/10 px-4 py-2 text-sm font-semibold uppercase tracking-[0.24em] text-cyan-300 shadow-sm shadow-cyan-500/10">
            Agent-driven research studio
          </p>
        </header>

        <div className="space-y-8">
          <section>
            <form className="rounded-[1.75rem] border border-slate-800 bg-black p-6 shadow-xl shadow-slate-950/20" onSubmit={startResearch}>
              <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-white">Start a research session</h2>
                  <p className="mt-2 text-sm text-slate-400">Type a query and launch the live pipeline.</p>
                </div>
              </div>

              <label className="mb-3 block text-sm font-semibold text-slate-300">Research query</label>
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="min-h-[170px] w-full rounded-[1.5rem] border border-slate-700 bg-black px-5 py-4 text-slate-100 placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20"
                placeholder="Ask the research agent any hiring question..."
              />

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex min-h-[52px] items-center justify-center rounded-full bg-gradient-to-r from-cyan-500 to-sky-500 px-7 py-3 text-sm font-semibold text-slate-950 transition hover:from-cyan-400 hover:to-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isLoading ? 'Running pipeline…' : 'Start research'}
                </button>
                <button
                  type="button"
                  disabled={!isLoading}
                  onClick={() => {
                    closeEventSource();
                    setIsLoading(false);
                    appendLog('Pipeline stopped by user.');
                  }}
                  className="inline-flex min-h-[52px] items-center justify-center rounded-full border border-slate-700 bg-gray-900 px-7 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Stop run
                </button>
              </div>
            </form>
          </section>

          <section className="rounded-[1.75rem] border border-slate-800 bg-black p-6 shadow-xl shadow-slate-950/20">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-white">Pipeline flow</h2>
                <p className="mt-2 text-sm text-slate-400">Agent stages transition from search to report generation.</p>
              </div>
              <span className="rounded-full bg-gray-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-300">
                {completedStages}/{stages.length} complete
              </span>
            </div>

              <div className="mb-6 overflow-x-auto pb-4">
                <div className="min-w-[980px] flex items-center gap-4">
                  {stages.map((stage, index) => (
                    <div key={stage.id} className="flex items-center gap-4">
                      <div className="min-w-[240px] rounded-[1.75rem] border border-slate-800 bg-black p-4 shadow-inner shadow-slate-950/10">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-xs uppercase tracking-[0.24em] text-cyan-300">{AGENT_LABELS[stage.id]}</p>
                            <p className="mt-2 text-lg font-semibold text-white">{stage.label}</p>
                          </div>
                          <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                            stage.status === 'done'
                              ? 'bg-emerald-400 text-slate-950'
                              : stage.status === 'running'
                              ? 'bg-amber-400 text-slate-950'
                              : stage.status === 'failed'
                              ? 'bg-rose-500 text-white'
                              : 'bg-slate-700 text-slate-300'
                          }`}>
                            {stage.status}
                          </span>
                        </div>
                        <div className="mt-4 rounded-3xl bg-gray-900 px-4 py-3">
                          <p className="text-sm text-slate-300">{stage.message || (stage.status === 'waiting' ? 'Waiting to engage' : 'In progress')}</p>
                        </div>
                      </div>
                      {index < stages.length - 1 && (
                        <div className="flex shrink-0 flex-col items-center gap-2 text-slate-500">
                          <div className="h-px w-10 bg-slate-700" />
                          <span className="text-xs uppercase tracking-[0.24em]">→</span>
                          <div className="h-px w-10 bg-slate-700" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-slate-800 bg-black p-5 shadow-inner shadow-slate-950/10">
                <p className="text-xs uppercase tracking-[0.24em] text-cyan-300">Current flow</p>
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  {stages.map((stage) => (
                    <div key={stage.id} className={`min-w-[150px] rounded-3xl border px-4 py-3 text-sm font-semibold uppercase tracking-[0.18em] ${
                      stage.status === 'done'
                        ? 'border-emerald-400 bg-emerald-400/10 text-emerald-300'
                        : stage.status === 'running'
                        ? 'border-amber-400 bg-amber-400/10 text-amber-300'
                        : stage.status === 'failed'
                        ? 'border-rose-500 bg-rose-500/10 text-rose-300'
                        : 'border-slate-700 bg-gray-900 text-slate-400'
                    }`}>
                      {AGENT_LABELS[stage.id]}
                    </div>
                  ))}
                  <div className="rounded-full bg-gray-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-300">
                    {reportWordCount} words
                  </div>
                </div>

              </div>

            {report ? (
              <div className="space-y-6">
                <div className="rounded-[1.5rem] border border-slate-800 bg-black p-6 shadow-inner shadow-slate-900/20">
                  <p className="mb-4 text-sm uppercase tracking-[0.24em] text-cyan-300">Executive summary</p>
                  <div className="space-y-5 text-sm leading-7 text-slate-200 prose prose-invert max-w-none">
                    <ReactMarkdown 
                      components={{
                        p: ({node, ...props}) => <p className="mb-3" {...props} />,
                        strong: ({node, ...props}) => <strong className="font-semibold text-white" {...props} />,
                        em: ({node, ...props}) => <em className="italic" {...props} />,
                        ul: ({node, ...props}) => <ul className="list-disc list-inside space-y-2 my-3" {...props} />,
                        ol: ({node, ...props}) => <ol className="list-decimal list-inside space-y-2 my-3" {...props} />,
                        li: ({node, ...props}) => <li className="mb-2" {...props} />,
                        h1: ({node, ...props}) => <h1 className="text-lg font-bold mt-4 mb-3" {...props} />,
                        h2: ({node, ...props}) => <h2 className="text-base font-bold mt-3 mb-2" {...props} />,
                        h3: ({node, ...props}) => <h3 className="text-sm font-bold mt-2 mb-1" {...props} />,
                        code: ({node, ...props}) => <code className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-100" {...props} />,
                        blockquote: ({node, ...props}) => <blockquote className="border-l-2 border-cyan-500 pl-4 italic text-slate-400" {...props} />,
                      }}
                    >
                      {reportWithoutSources}
                    </ReactMarkdown>
                  </div>
                </div>

                <div className="rounded-[1.5rem] border border-slate-800 bg-black p-5">
                  <div className="mb-4 flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm uppercase tracking-[0.22em] text-slate-400">Citations</p>
                      <p className="text-base font-semibold text-white">Verified source references</p>
                    </div>
                    <span className="rounded-full bg-gray-900 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-300">
                      {sourceCount} sources
                    </span>
                  </div>
                  <div className="grid gap-3">
                    {sources.length > 0 ? (
                      sources.map((source, index) => (
                        <a
                          key={index}
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="block rounded-3xl border border-slate-800 bg-gray-900 p-4 transition hover:border-cyan-400/30 hover:bg-black"
                        >
                          <p className="text-sm font-semibold text-slate-100">[{index + 1}] {source.title || source.url}</p>
                          <p className="mt-1 text-xs text-slate-500 break-all">{source.url}</p>
                        </a>
                      ))
                    ) : (
                      <p className="text-sm text-slate-500">No citations available yet. They will appear automatically once search finishes.</p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-[1.5rem] border border-dashed border-slate-800 bg-black p-10 text-center text-slate-500">
                <p className="text-sm">The final report and citations will populate here after the pipeline completes.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

export default App;
