import React, { useState, useCallback, useEffect, useRef } from 'react';
// Imports for the editor are removed as they are now loaded globally from a CDN.

// --- Global variables from CDN ---
// These are now expected to be loaded via <script> tags in index.html
const Editor = window.SimpleCodeEditor?.default;
const Prism = window.Prism;


// --- Configuration ---
const API_BASE_URL = 'http://127.0.0.1:8000';

// --- Icons (Omitted for Brevity) ---
const FolderIcon=()=>(<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-5 h-5 text-yellow-500"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>);
const FileIcon=()=>(<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-5 h-5 text-blue-400"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>);
const CheckCircleIcon=()=>(<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6 text-green-500"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>);
const XCircleIcon=()=>(<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-6 h-6 text-red-500"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>);
const CogIcon=()=>(<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6"><path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.532 1.532 0 012.287-.947c1.372.836 2.942-.734-2.106-2.106a1.532 1.532 0 01-.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd"/></svg>);
const ChatBubbleIcon=()=>(<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zM2 10a8 8 0 1116 0 8 8 0 01-16 0z"/><path d="M12.293 7.293a1 1 0 011.414 1.414l-4 4a1 1 0 01-1.414 0l-2-2a1 1 0 111.414-1.414L9 10.586l3.293-3.293z"/></svg>);

// --- Utility Components ---
const LoadingSpinner=()=>(<div className="flex justify-center items-center p-8"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-400"></div></div>);
const FullPageLoader=({message})=>(<div className="fixed inset-0 bg-gray-900 bg-opacity-80 flex flex-col justify-center items-center z-50"><LoadingSpinner/><p className="text-white text-lg mt-4">{message}</p></div>);

// --- Page & Child Components ---
const FileTree = ({ node, selectedItems, onSelectionChange }) => {
    const isFolder = node.type === 'folder';
    const isSelected = !!selectedItems[node.path];

    const handleCheckboxChange = (e) => {
        onSelectionChange(node, e.target.checked);
    };

    return (
        <div className="pl-4">
            <div className="flex items-center space-x-2 py-1 hover:bg-gray-700 rounded-md transition-colors duration-150">
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={handleCheckboxChange}
                    className="form-checkbox h-4 w-4 text-indigo-500 bg-gray-800 border-gray-600 rounded focus:ring-indigo-500"
                />
                {isFolder ? <FolderIcon className="w-5 h-5 text-yellow-500" /> : <FileIcon className="w-5 h-5 text-blue-400" />}
                <span className="text-gray-300 select-none">{node.name}</span>
            </div>
            {isFolder && node.children && (
                <div className="border-l border-gray-600 ml-2">
                    {node.children.map((childNode) => (
                        <FileTree key={childNode.path} node={childNode} selectedItems={selectedItems} onSelectionChange={onSelectionChange} />
                    ))}
                </div>
            )}
        </div>
    );
};
const AnalysisReport=({report,onBack})=>{/* ... */const getColor=(g)=>{if(!g)return'text-gray-400';if(g.startsWith('A'))return'text-green-400';if(g.startsWith('B'))return'text-yellow-400';return'text-red-400';};return(<div className="bg-gray-800 p-6 rounded-lg animate-fade-in"><div className="flex justify-between items-center mb-6"><h2 className="text-3xl font-bold">{report.title}</h2><button onClick={onBack} className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg">&larr; Back</button></div><div className="bg-gray-900 rounded-lg p-4 mb-6 text-center"><p className="text-lg text-gray-400">Overall Score</p><p className={`text-6xl font-bold ${getColor('A')}`}>{report.overall_score}</p></div><div className="grid md:grid-cols-3 gap-6">{report.categories.map(cat=>(<div key={cat.name} className="bg-gray-900 p-5 rounded-lg"><h3 className="text-xl font-semibold mb-2">{cat.name}</h3><p className={`text-4xl font-bold mb-3 ${getColor(cat.grade)}`}>{cat.grade}</p><p className="text-sm text-gray-400 mb-4">{cat.summary}</p><div className="space-y-3">{Array.isArray(cat.details)&&cat.details.map((d,i)=>(<div key={i} className="text-sm"><p className="font-medium text-gray-300">{d.metric}</p><p className="text-gray-400">{d.value}</p></div>))}</div></div>))}</div></div>);};
// const TestingReport=({report,onBack})=>{/* ... */const s=report.summary||{};const pR=report.pynguin_test_generation||{};const gR=report.gemini_test_generation||{};const cR=report.coverage_analysis||{};const mR=report.mutation_testing||{};const Stat=({t,v,st})=>(<div className="bg-gray-900 p-4 rounded-lg text-center"><p className="text-sm text-gray-400">{t}</p><p className={`text-3xl font-bold ${st==='good'?'text-green-400':st==='warn'?'text-yellow-400':'text-red-400'}`}>{v||'N/A'}</p></div>);const Tool=({t,r,msg})=>(<div className="bg-gray-900 p-5 rounded-lg"><div className="flex items-center space-x-2 mb-3">{r.success?<CheckCircleIcon/>:<XCircleIcon/>}<h3 className="text-xl font-semibold">{t}</h3></div>{!r.success&&msg?<p className="text-sm text-yellow-500">{msg}</p>:<p className="text-sm text-gray-400">{r.message||`Generated ${r.test_suites_generated||0} suites`}</p>}</div>);const Gemini=({r})=>{const[exp,setExp]=useState(false);const hasTests=r.generated_tests&&r.generated_tests.length>0;return(<div className="bg-gray-900 p-5 rounded-lg"><div className="flex items-center space-x-2 mb-3">{r.success?<CheckCircleIcon/>:<XCircleIcon/>}<h3 className="text-xl font-semibold">Unit Tests</h3></div><p className="text-sm text-gray-400 mb-4">{r.message||`Generated ${r.test_suites_generated||0} suites`}</p>{hasTests&&<button onClick={()=>setExp(!exp)} className="text-sm text-indigo-400 hover:underline mb-2">{exp?'Hide':'Show'} Tests</button>}{exp&&hasTests&&<div className="space-y-4 max-h-80 overflow-y-auto p-2 bg-black rounded border-gray-700">{r.generated_tests.map((f,i)=>(<div key={i}><p className="font-mono text-sm text-yellow-300 p-1 bg-gray-800 rounded-t-md">{f.filename}</p><pre className="text-sm whitespace-pre-wrap p-2 bg-gray-900 rounded-b-md"><code>{f.code}</code></pre></div>))}</div>}{!r.success&&r.errors&&r.errors.length>0&&<p className="text-sm text-yellow-500">Incompatible code or generation failed.</p>}</div>);};return(<div className="bg-gray-800 p-6 rounded-lg animate-fade-in"><div className="flex justify-between items-center mb-6"><h2 className="text-3xl font-bold">Testing Report</h2><button onClick={onBack} className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg">&larr; Back</button></div><div className="grid md:grid-cols-3 gap-4 mb-6"><Stat t="Status" v={s.overall_status} st={s.overall_status==='Success'?'good':'bad'}/><Stat t="Coverage" v={`${cR.summary?.percent_covered_display||'0%'}`} st={(cR.summary?.percent_covered||0)>80?'good':'warn'}/><Stat t="Mutation Score" v={mR.score||'N/A'} st={(parseInt(mR.score)||0)>80?'good':'warn'}/></div><h3 className="text-2xl font-bold mb-4">Test Generation</h3><div className="grid md:grid-cols-2 gap-4 mb-6"><Tool t="Pynguin" r={pR} msg="Incompatible code or generation failed."/><Gemini r={gR}/></div><h3 className="text-2xl font-bold mb-4">Mutation Test Details</h3><div className="bg-gray-900 p-4 rounded-lg">{!mR.success&&(!mR.raw_report||mR.raw_report.includes("no mutants"))?<p className="text-sm text-yellow-500">Incompatible code or mutation test failed.</p>:<pre className="text-sm whitespace-pre-wrap max-h-60 overflow-y-auto"><code>{mR.raw_report||"No report."}</code></pre>}</div></div>);};

const TestingReport = ({ report, onBack }) => {
  const s = report.summary || {};
  const pR = report.pynguin_test_generation || {};
  const gR = report.gemini_test_generation || {};
  const cR = report.coverage_analysis || {};
  const mR = report.mutation_testing || {};

  const Stat = ({ t, v, st }) => (
    <div className="bg-gray-900 p-4 rounded-lg text-center">
      <p className="text-sm text-gray-400">{t}</p>
      <p
        className={`text-3xl font-bold ${
          st === "good"
            ? "text-green-400"
            : st === "warn"
            ? "text-yellow-400"
            : "text-red-400"
        }`}
      >
        {v || "N/A"}
      </p>
    </div>
  );

  // const Tool = ({ t, r, msg }) => (
  //   <div className="bg-gray-900 p-5 rounded-lg">
  //     <div className="flex items-center space-x-2 mb-3">
  //       {r.success ? <CheckCircleIcon /> : <XCircleIcon />}
  //       <h3 className="text-xl font-semibold">{t}</h3>
  //     </div>
  //     {!r.success && msg ? (
  //       <p className="text-sm text-yellow-500">{msg}</p>
  //     ) : (
  //       <p className="text-sm text-gray-400">
  //         {r.message || `Generated ${r.test_suites_generated || 0} suites`}
  //       </p>
  //     )}
  //   </div>
  // );

  const Gemini = ({ r }) => {
    const [exp, setExp] = useState(false);
    const hasTests = r.generated_tests && r.generated_tests.length > 0;

    return (
      <div className="bg-gray-900 p-5 rounded-lg">
        <div className="flex items-center space-x-2 mb-3">
          {r.success ? <CheckCircleIcon /> : <XCircleIcon />}
          <h3 className="text-xl font-semibold">Unit Tests</h3>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          {r.message || `Generated ${r.test_suites_generated || 0} suites`}
        </p>

        {hasTests && (
          <button
            onClick={() => setExp(!exp)}
            className="text-sm text-indigo-400 hover:underline mb-2"
          >
            {exp ? "Hide" : "Show"} Tests
          </button>
        )}

        {exp && hasTests && (
          <div className="space-y-4 max-h-80 overflow-y-auto p-2 bg-black rounded border-gray-700">
            {r.generated_tests.map((f, i) => (
              <div key={i}>
                <p className="font-mono text-sm text-yellow-300 p-1 bg-gray-800 rounded-t-md">
                  {f.filename}
                </p>
                <pre className="text-sm whitespace-pre-wrap p-2 bg-gray-900 rounded-b-md">
                  <code>{f.code}</code>
                </pre>
              </div>
            ))}
          </div>
        )}

        {!r.success && r.errors && r.errors.length > 0 && (
          <p className="text-sm text-yellow-500">
            Incompatible code or generation failed.
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold">Testing Report</h2>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg"
        >
          &larr; Back
        </button>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <Stat
          t="Status"
          v={s.overall_status}
          st={s.overall_status === "Success" ? "good" : "bad"}
        />
        <Stat
          t="Coverage"
          v={`${cR.summary?.percent_covered_display || "0%"}`}
          st={(cR.summary?.percent_covered || 0) > 80 ? "good" : "warn"}
        />
        {/* Commented out mutation score */}
        {/* <Stat
          t="Mutation Score"
          v={mR.score || "N/A"}
          st={(parseInt(mR.score) || 0) > 80 ? "good" : "warn"}
        /> */}
      </div>

      <h3 className="text-2xl font-bold mb-4">Test Generation</h3>
      <div className="grid md:grid-cols-1 gap-4 mb-6">
        {/* Commented out Pynguin section */}
        {/* <Tool t="Pynguin" r={pR} msg="Incompatible code or generation failed." /> */}
        <Gemini r={gR} />
      </div>

      {/* Commented out Mutation Testing Details */}
      {/* <h3 className="text-2xl font-bold mb-4">Mutation Test Details</h3>
      <div className="bg-gray-900 p-4 rounded-lg">
        {!mR.success &&
        (!mR.raw_report || mR.raw_report.includes("no mutants")) ? (
          <p className="text-sm text-yellow-500">
            Incompatible code or mutation test failed.
          </p>
        ) : (
          <pre className="text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
            <code>{mR.raw_report || "No report."}</code>
          </pre>
        )}
      </div> */}
    </div>
  );
};


const ChatPage = () => {
    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState('');
    const [prompt, setPrompt] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [editorContent, setEditorContent] = useState('# Your AI-generated code will appear here.');
    const [isLoading, setIsLoading] = useState(false);
    const chatEndRef = useRef(null);

    useEffect(() => {
        const fetchModels = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/ollama/models`);
                const data = await response.json();
                setModels(data);
                if (data.length > 0) setSelectedModel(data[0].name);
            } catch (error) { console.error("Failed to fetch Ollama models:", error); }
        };
        fetchModels();
    }, []);

    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatHistory]);

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!prompt.trim() || !selectedModel || isLoading) return;
        const newHistory = [...chatHistory, { role: 'user', content: prompt }];
        setChatHistory(newHistory);
        setPrompt('');
        setIsLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/v1/ollama/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: selectedModel, prompt }), });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantResponse = '';
        setChatHistory(prev => [...prev, { role: 'assistant', content: '...' }]);
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());
            for (const line of lines) {
                try {
                    const data = JSON.parse(line);
                    if (data.token) {
                        assistantResponse += data.token;
                        setChatHistory(prev => { const last = prev[prev.length - 1]; last.content = assistantResponse; return [...prev.slice(0, -1), last]; });
                    }
                } catch {}
            }
        }
        const codeMatch = assistantResponse.match(/```[\w]*\n([\s\S]*?)```/);

      if (codeMatch) {
                  setEditorContent(codeMatch[1].trim());
              }

              setIsLoading(false);
          };

          return (
              <div className="grid lg:grid-cols-2 gap-8 h-[calc(100vh-200px)]">
                  {/* Left: Chat Interface */}
                  <div className="bg-gray-800 rounded-lg shadow-xl flex flex-col">
                      <div className="p-4 border-b border-gray-700">
                          <h2 className="text-xl font-bold">AI Coding Assistant</h2>
                          <div className="flex items-center space-x-2 mt-2">
                              <label htmlFor="model-select" className="text-sm text-gray-400">Model:</label>
                              <select id="model-select" value={selectedModel} onChange={e => setSelectedModel(e.target.value)} className="bg-gray-700 text-white rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                                  {models.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
                              </select>
                          </div>
                      </div>
                      <div className="flex-grow p-4 overflow-y-auto">
                          {chatHistory.map((msg, i) => (
                              <div key={i} className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                                  <div className={`inline-block p-3 rounded-lg ${msg.role === 'user' ? 'bg-indigo-600' : 'bg-gray-700'}`}>
                                      <p className="whitespace-pre-wrap">{msg.content}</p>
                                  </div>
                              </div>
                          ))}
                          <div ref={chatEndRef} />
                      </div>
                      <form onSubmit={handleChatSubmit} className="p-4 border-t border-gray-700">
                          <input type="text" value={prompt} onChange={e => setPrompt(e.target.value)} disabled={isLoading} placeholder="Ask the AI to write some code..." className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"/>
                      </form>
                  </div>

                  {/* Right: Code Editor */}
                  <div className="bg-gray-800 rounded-lg p-6">
                    <h2 className="text-2xl font-bold mb-4">Generated Code</h2>

                    {Editor ? (
                      <div className="bg-gray-900 rounded-lg p-2 h-[520px] overflow-auto border border-gray-700">
                        <Editor
                          value={editorContent}
                          onValueChange={(code) => setEditorContent(code)}
                          highlight={(code) => Prism.highlight(code, Prism.languages.python, 'python')}
                          padding={12}
                          className="text-sm font-mono text-gray-100 bg-gray-900 focus:outline-none min-h-[480px]"
                        />
                      </div>
                    ) : (
                      <div className="bg-gray-900 rounded-lg p-4 h-[520px] overflow-auto">
                        <pre className="text-sm">
                          <code>{editorContent}</code>
                        </pre>
                      </div>
                    )}
                  </div>
              </div>
          );
      };


      // --- Main App Component ---
      export default function App() {
          // --- State Management ---
          const [currentPage, setCurrentPage] = useState('analyzer'); // 'analyzer' or 'chat'
          const [basePath, setBasePath] = useState('');
          const [fileTree, setFileTree] = useState(null);
          const [selectedItems, setSelectedItems] = useState({});
          const [isLoading, setIsLoading] = useState(false);
          const [loadingMessage, setLoadingMessage] = useState('');
          const [statusMessage, setStatusMessage] = useState(null);
          const [analysisReport, setAnalysisReport] = useState(null);
          const [testingReport, setTestingReport] = useState(null);
          const [ollamaModelName, setOllamaModelName] = useState('custom-deepseek-coder');

          // ... (Effects and Handlers from previous version)

          useEffect(() => { if(statusMessage){const t = setTimeout(()=>setStatusMessage(null), 5000); return ()=>clearTimeout(t);}}, [statusMessage]);
          const handleFetchTree=async()=>{/*...*/if(!basePath){setStatusMessage({type:'error',text:'Enter a path'});return}setIsLoading(true);setFileTree(null);setSelectedItems({});try{const r=await fetch(`${API_BASE_URL}/api/v1/list-directory`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:basePath})});if(!r.ok){const d=await r.json();throw new Error(d.detail||'Failed to fetch')}const d=await r.json();setFileTree(d)}catch(e){setStatusMessage({type:'error',text:e.message})}finally{setIsLoading(false)}};
          const handleAction=async(endpoint,actionMessage)=>{const paths=Object.keys(selectedItems).filter(p=>selectedItems[p]);if(paths.length===0){setStatusMessage({type:'error',text:'Select an item'});return}setIsLoading(true);setLoadingMessage(actionMessage);try{const r=await fetch(`${API_BASE_URL}${endpoint}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base_path:basePath,selected_items:paths,ollama_model_name:ollamaModelName})});const d=await r.json();if(!r.ok){throw new Error(d.detail||'An error occurred')}if(endpoint==='/api/v1/code-analysis-report'){setAnalysisReport(d)}else if(endpoint==='/api/v1/run-testing-pipeline'){setTestingReport(d)}else{setStatusMessage({type:'success',text:d.message||'Action started'})}}catch(e){setStatusMessage({type:'error',text:e.message})}finally{setIsLoading(false);setLoadingMessage('')}};
          const getDescendants=node=>{let paths=[node.path];if(node.type==='folder'&&node.children){node.children.forEach(c=>{paths=[...paths,...getDescendants(c)]})}return paths};
          const handleSelectionChange=useCallback((node,isChecked)=>{const des=getDescendants(node);const newSel={...selectedItems};des.forEach(p=>{if(isChecked){newSel[p]=true}else{delete newSel[p]}});setSelectedItems(newSel)},[selectedItems]);
          const selectedCount=Object.keys(selectedItems).filter(k=>selectedItems[k]).length;
          const resetViews=()=>{setAnalysisReport(null);setTestingReport(null)};

          const AnalyzerPage = () => (
              <>
                  {analysisReport ? <AnalysisReport report={analysisReport} onBack={resetViews} /> :
                  testingReport ? <TestingReport report={testingReport} onBack={resetViews} /> : (
                      <div className="grid lg:grid-cols-2 gap-8">
                          {/* Left Side: File Selection */}
                          <div className="bg-gray-800 p-6 rounded-lg shadow-xl">
                              <h2 className="text-2xl font-bold mb-4">1. Select Project Directory</h2>
                              <div className="flex space-x-2"><input type="text" value={basePath} onChange={(e) => setBasePath(e.target.value)} placeholder="Enter absolute path..." className="flex-grow bg-gray-700 border-gray-600 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"/><button onClick={handleFetchTree} disabled={isLoading} className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 font-bold rounded-lg disabled:bg-gray-500">{isLoading?'...':'Load'}</button></div>
                              <div className="mt-4 bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto border-gray-700">{isLoading&&!fileTree?<LoadingSpinner/>:fileTree?<FileTree node={fileTree} selectedItems={selectedItems} onSelectionChange={handleSelectionChange}/>:<p className="text-gray-500 text-center mt-16">Directory content appears here.</p>}</div>
                          </div>
                          {/* Right Side: Actions */}
                          <div className="bg-gray-800 p-6 rounded-lg shadow-xl">
                              <h2 className="text-2xl font-bold mb-4">2. Choose an Action</h2>
                              <p className="text-gray-400 mb-6">{selectedCount > 0 ? `${selectedCount} items selected.` : 'Select files to enable actions.'}</p>
                              <div className="space-y-4">
                                  <button onClick={()=>handleAction('/api/v1/code-analysis-report','Generating report...')} disabled={isLoading||selectedCount===0} className="w-full text-left p-4 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50"><h3 className="text-lg font-semibold text-green-400">Generate Analysis Report</h3><p className="text-sm text-gray-400">Run security and quality scans.</p></button>
                                  <button onClick={()=>handleAction('/api/v1/run-testing-pipeline','Running tests... This may take minutes.')} disabled={isLoading||selectedCount===0} className="w-full text-left p-4 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50"><h3 className="text-lg font-semibold text-blue-400">Run Automated Testing</h3><p className="text-sm text-gray-400">Generate tests, run coverage, and mutation analysis.</p></button>
                                  <div className="p-4 bg-gray-700 rounded-lg">
                                      <h3 className="text-lg font-semibold text-purple-400 mb-2">Train Learning Engine</h3>
                                      <p className="text-sm text-gray-400 mb-4">Use selected code to tune model.</p>
                                      <div className="flex md:flex-row flex-col space-y-2 md:space-y-0 md:space-x-2"><input type="text" value={ollamaModelName} onChange={(e)=>setOllamaModelName(e.target.value)} className="flex-grow bg-gray-800 border-gray-600 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"/><button onClick={()=>handleAction('/api/v1/finetune','Finetuning started...')} disabled={isLoading||selectedCount===0} className="px-6 py-2 bg-purple-600 hover:bg-purple-500 font-bold rounded-lg disabled:bg-gray-500">Start</button></div>
                                  </div>
                              </div>
                          </div>
                      </div>
                  )}
              </>
          );

          return (
              <div className="bg-gray-900 text-white min-h-screen font-sans">
                  {isLoading && loadingMessage && <FullPageLoader message={loadingMessage} />}
                  {statusMessage && (<div className={`fixed top-20 right-5 px-6 py-3 rounded-lg shadow-lg text-white animate-fade-in-out z-50 ${statusMessage.type === 'error' ? 'bg-red-600' : 'bg-green-600'}`}>{statusMessage.text}</div>)}
                  
                  <main className="container mx-auto p-4 md:p-8">
                      <header className="text-center mb-8">
                          <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500">AX-Code Suite</h1>
                      </header>
                      
                      {/* --- NEW Navigation --- */}
                      <nav className="flex justify-center space-x-4 mb-8">
                          <button
                              onClick={() => setCurrentPage('analyzer')}
                              className={`flex items-center space-x-2 px-5 py-2 font-semibold rounded-lg transition-colors ${
                                  currentPage === 'analyzer'
                                      ? 'bg-indigo-600 text-white'
                                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                              }`}
                          >
                              <CogIcon /> <span>Analyzer & Tuner</span>
                          </button>
                          <button
                              onClick={() => setCurrentPage('chat')}
                              className={`flex items-center space-x-2 px-5 py-2 font-semibold rounded-lg transition-colors ${
                                  currentPage === 'chat'
                                      ? 'bg-indigo-600 text-white'
                                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                              }`}
                          >
                              <ChatBubbleIcon /> <span>AI Chat & Code</span>
                          </button>
                      </nav>

                      {currentPage === 'analyzer' ? <AnalyzerPage /> : <ChatPage />}
                  </main>
              </div>
          );
      }