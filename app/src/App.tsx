import { useState, useRef, useEffect } from 'react';
import { 
  Upload, Music, Image, Video, Settings, History, 
  Sparkles, Wand2, Play, Download,
  CheckCircle2, Loader2, Info, Eye, Zap, Layers
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

// Particle Background Component
const ParticleBackground = () => {
  useEffect(() => {
    const container = document.getElementById('particles-container');
    if (!container) return;
    
    const particles: HTMLDivElement[] = [];
    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.animationDelay = `${Math.random() * 15}s`;
      particle.style.animationDuration = `${15 + Math.random() * 10}s`;
      particle.style.opacity = `${0.3 + Math.random() * 0.5}`;
      container.appendChild(particle);
      particles.push(particle);
    }
    
    return () => {
      particles.forEach(p => p.remove());
    };
  }, []);
  
  return <div id="particles-container" className="particles-container" />;
};

// Animated Counter Hook (available for future use)
// const useAnimatedCounter = (target: number, duration: number = 1000) => {
//   const [count, setCount] = useState(0);
//   
//   useEffect(() => {
//     let startTime: number;
//     const animate = (currentTime: number) => {
//       if (!startTime) startTime = currentTime;
//       const progress = Math.min((currentTime - startTime) / duration, 1);
//       setCount(Math.floor(progress * target));
//       if (progress < 1) {
//         requestAnimationFrame(animate);
//       }
//     };
//     requestAnimationFrame(animate);
//   }, [target, duration]);
//   
//   return count;
// };

// Ripple Effect Hook
const useRipple = () => {
  const createRipple = (event: React.MouseEvent<HTMLElement>) => {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.className = 'ripple';
    
    button.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  };
  
  return createRipple;
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState<'generate' | 'result'>('generate');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedVideo, setGeneratedVideo] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  
  // Form States
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [useIdleMode, setUseIdleMode] = useState(false);
  const [useRefVideo, setUseRefVideo] = useState(false);
  const [refStrategy, setRefStrategy] = useState('pose');
  const [preprocess, setPreprocess] = useState('crop');
  const [faceSize, setFaceSize] = useState('256');
  const [batchSize, setBatchSize] = useState(1);
  const [poseStyle, setPoseStyle] = useState(0);
  const [expScale, setExpScale] = useState(1.0);
  const [stillMode, setStillMode] = useState(false);
  const [enhancer, setEnhancer] = useState(false);
  const [useBlink, setUseBlink] = useState(true);
  const [audioLength, setAudioLength] = useState(5);
  
  // Preview States
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [audioPreview, setAudioPreview] = useState<string | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  const createRipple = useRipple();
  const fileInputRefs = {
    image: useRef<HTMLInputElement>(null),
    audio: useRef<HTMLInputElement>(null),
    video: useRef<HTMLInputElement>(null)
  };

  // Handle File Selection
  const handleFileSelect = (type: 'image' | 'audio' | 'video', file: File) => {
    const url = URL.createObjectURL(file);
    
    if (type === 'image') {
      setImageFile(file);
      setImagePreview(url);
    } else if (type === 'audio') {
      setAudioFile(file);
      setAudioPreview(url);
    } else if (type === 'video') {
      setVideoFile(file);
      // Simulate upload progress for video
      setIsUploading(true);
      setUploadProgress(0);
      let progress = 0;
      const interval = setInterval(() => {
        progress += 5;
        setUploadProgress(progress);
        if (progress >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          setVideoPreview(url);
        }
      }, 100);
    }
  };

  // Handle Generate
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imageFile) {
      toast.error('Please upload a source image');
      return;
    }
    if (!audioFile && !useIdleMode) {
      toast.error('Please upload audio or enable idle mode');
      return;
    }
    
    setIsGenerating(true);
    
    // Simulate generation
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    const mockVideoName = `generated_${Date.now()}.webm`;
    setGeneratedVideo(mockVideoName);
    setHistory(prev => [mockVideoName, ...prev]);
    setIsGenerating(false);
    setActiveTab('result');
    toast.success('Video generated successfully!');
  };

  // Fetch History
  const fetchHistory = async () => {
    // Mock history
    setHistory([
      'generated_123456.webm',
      'generated_123455.webm',
      'generated_123454.webm'
    ]);
  };

  return (
    <div className="min-h-screen relative">
      {/* Background Effects */}
      <div className="ai-bg" />
      <div className="grid-pattern" />
      <ParticleBackground />
      
      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/30 float-animation">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold ai-title">
              SadTalker AI Studio
            </h1>
          </div>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Transform static images into lifelike talking head videos with AI-powered animation
          </p>
          
          {/* Navigation Tabs */}
          <div className="flex justify-center gap-2 mt-8">
            <button
              onClick={() => setActiveTab('generate')}
              className={`ai-tab ${activeTab === 'generate' ? 'active' : ''}`}
            >
              <Wand2 className="w-4 h-4 inline mr-2" />
              Generate
            </button>
            <button
              onClick={() => generatedVideo && setActiveTab('result')}
              className={`ai-tab ${activeTab === 'result' ? 'active' : ''} ${!generatedVideo ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <Play className="w-4 h-4 inline mr-2" />
              Result
            </button>
          </div>
        </header>

        {/* Generate Tab */}
        {activeTab === 'generate' && (
          <form onSubmit={handleGenerate} className="space-y-6">
            {/* Source Inputs Row */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Image Upload */}
              <div className="glow-card rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="section-badge">
                    <Image className="w-4 h-4 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Source Image</h3>
                  <span className="text-red-400 text-sm">*</span>
                </div>
                
                <div className="file-input-wrapper">
                  <input
                    ref={fileInputRefs.image}
                    type="file"
                    accept="image/*"
                    onChange={(e) => e.target.files?.[0] && handleFileSelect('image', e.target.files[0])}
                  />
                  <label 
                    onClick={() => fileInputRefs.image.current?.click()}
                    className="file-input-label text-violet-300"
                  >
                    <Upload className="w-5 h-5" />
                    {imageFile ? imageFile.name : 'Click to upload image'}
                  </label>
                </div>
                
                <div className={`preview-box-ai mt-4 ${imagePreview ? 'has-content' : ''}`}>
                  {imagePreview ? (
                    <img 
                      src={imagePreview} 
                      alt="Preview" 
                      className="max-w-full max-h-64 rounded-lg object-contain"
                    />
                  ) : (
                    <span className="text-gray-500 flex items-center gap-2">
                      <Image className="w-5 h-5" />
                      Image preview will appear here
                    </span>
                  )}
                </div>
              </div>

              {/* Audio Upload */}
              <div className="glow-card rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="section-badge">
                    <Music className="w-4 h-4 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Audio Source</h3>
                </div>
                
                {/* Idle Mode Toggle */}
                <label className="flex items-center gap-3 mb-4 cursor-pointer group">
                  <div className="relative">
                    <input 
                      type="checkbox" 
                      className="sr-only glow-checkbox"
                      checked={useIdleMode}
                      onChange={(e) => setUseIdleMode(e.target.checked)}
                    />
                    <div className={`w-12 h-6 rounded-full transition-all ${useIdleMode ? 'bg-cyan-500 shadow-lg shadow-cyan-500/50' : 'bg-gray-700'}`}>
                      <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-all ${useIdleMode ? 'left-6' : 'left-0.5'}`} />
                    </div>
                  </div>
                  <span className="text-gray-300 group-hover:text-white transition-colors">
                    Use Idle Mode (No Audio)
                  </span>
                </label>
                
                {!useIdleMode && (
                  <>
                    <div className="file-input-wrapper">
                      <input
                        ref={fileInputRefs.audio}
                        type="file"
                        accept="audio/*"
                        onChange={(e) => e.target.files?.[0] && handleFileSelect('audio', e.target.files[0])}
                      />
                      <label 
                        onClick={() => fileInputRefs.audio.current?.click()}
                        className="file-input-label text-violet-300"
                      >
                        <Upload className="w-5 h-5" />
                        {audioFile ? audioFile.name : 'Click to upload audio'}
                      </label>
                    </div>
                    
                    <div className={`preview-box-ai mt-4 ${audioPreview ? 'has-content' : ''}`}>
                      {audioPreview ? (
                        <audio controls className="w-full">
                          <source src={audioPreview} />
                        </audio>
                      ) : (
                        <span className="text-gray-500 flex items-center gap-2">
                          <Music className="w-5 h-5" />
                          Audio preview will appear here
                        </span>
                      )}
                    </div>
                  </>
                )}
                
                {useIdleMode && (
                  <div className="mt-4">
                    <label className="text-gray-300 text-sm mb-2 block">Animation Length (seconds)</label>
                    <div className="flex items-center gap-4">
                      <input
                        type="range"
                        min="1"
                        max="60"
                        value={audioLength}
                        onChange={(e) => setAudioLength(Number(e.target.value))}
                        className="glow-slider flex-1"
                      />
                      <span className="text-cyan-400 font-bold w-12 text-right">{audioLength}s</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Reference Video */}
            <div className="glow-card rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="section-badge">
                  <Video className="w-4 h-4 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white">Reference Video</h3>
                <span className="text-gray-500 text-sm">(Optional)</span>
              </div>
              
              <label className="flex items-center gap-3 mb-4 cursor-pointer group">
                <div className="relative">
                  <input 
                    type="checkbox" 
                    className="sr-only glow-checkbox"
                    checked={useRefVideo}
                    onChange={(e) => setUseRefVideo(e.target.checked)}
                  />
                  <div className={`w-12 h-6 rounded-full transition-all ${useRefVideo ? 'bg-cyan-500 shadow-lg shadow-cyan-500/50' : 'bg-gray-700'}`}>
                    <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-all ${useRefVideo ? 'left-6' : 'left-0.5'}`} />
                  </div>
                </div>
                <span className="text-gray-300 group-hover:text-white transition-colors">
                  Use Reference Video for Pose/Expression
                </span>
              </label>
              
              {useRefVideo && (
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <div className="file-input-wrapper">
                      <input
                        ref={fileInputRefs.video}
                        type="file"
                        accept="video/*"
                        onChange={(e) => e.target.files?.[0] && handleFileSelect('video', e.target.files[0])}
                      />
                      <label 
                        onClick={() => fileInputRefs.video.current?.click()}
                        className="file-input-label text-violet-300"
                      >
                        <Upload className="w-5 h-5" />
                        {videoFile ? videoFile.name : 'Click to upload video'}
                      </label>
                    </div>
                    
                    {isUploading && (
                      <div className="mt-3">
                        <div className="ai-progress h-2">
                          <div 
                            className="ai-progress-bar h-full rounded-full"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                        <p className="text-center text-sm text-gray-400 mt-1">
                          {uploadProgress < 100 ? 'Uploading...' : 'Processing...'}
                        </p>
                      </div>
                    )}
                    
                    {/* Reference Strategy */}
                    <div className="mt-4">
                      <label className="text-gray-300 text-sm mb-2 block">Reference Strategy</label>
                      <div className="flex flex-wrap gap-2">
                        {['pose', 'blink', 'pose+blink', 'all'].map((strategy) => (
                          <label 
                            key={strategy}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all ${
                              refStrategy === strategy 
                                ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/30' 
                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                            }`}
                          >
                            <input
                              type="radio"
                              name="refStrategy"
                              value={strategy}
                              checked={refStrategy === strategy}
                              onChange={(e) => setRefStrategy(e.target.value)}
                              className="sr-only"
                            />
                            <span className="capitalize">{strategy.replace('+', ' + ')}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className={`preview-box-ai ${videoPreview ? 'has-content' : ''}`}>
                    {videoPreview ? (
                      <video 
                        controls 
                        className="max-w-full max-h-48 rounded-lg"
                      >
                        <source src={videoPreview} />
                      </video>
                    ) : (
                      <span className="text-gray-500 flex items-center gap-2">
                        <Video className="w-5 h-5" />
                        Video preview will appear here
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Settings */}
            <div className="glow-card rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="section-badge">
                  <Settings className="w-4 h-4 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white">Advanced Settings</h3>
                <a 
                  href="https://github.com/OpenTalker/SadTalker/blob/main/docs/best_practice.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-auto text-violet-400 hover:text-violet-300 text-sm flex items-center gap-1 transition-colors"
                >
                  <Info className="w-4 h-4" />
                  Best Practices
                </a>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-5">
                  {/* Preprocess Mode */}
                  <div>
                    <label className="text-gray-300 text-sm mb-2 block flex items-center gap-2">
                      <Layers className="w-4 h-4 text-violet-400" />
                      Preprocess Mode
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {['crop', 'resize', 'full', 'extcrop', 'extfull'].map((mode) => (
                        <label 
                          key={mode}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition-all text-sm ${
                            preprocess === mode 
                              ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/30' 
                              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                          }`}
                        >
                          <input
                            type="radio"
                            name="preprocess"
                            value={mode}
                            checked={preprocess === mode}
                            onChange={(e) => setPreprocess(e.target.value)}
                            className="sr-only"
                          />
                          <span className="capitalize">{mode}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  
                  {/* Face Resolution */}
                  <div>
                    <label className="text-gray-300 text-sm mb-2 block flex items-center gap-2">
                      <Eye className="w-4 h-4 text-violet-400" />
                      Face Resolution
                    </label>
                    <div className="flex gap-2">
                      {['256', '512'].map((size) => (
                        <label 
                          key={size}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all ${
                            faceSize === size 
                              ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/30' 
                              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                          }`}
                        >
                          <input
                            type="radio"
                            name="faceSize"
                            value={size}
                            checked={faceSize === size}
                            onChange={(e) => setFaceSize(e.target.value)}
                            className="sr-only"
                          />
                          <span>{size}px</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  
                  {/* Batch Size */}
                  <div>
                    <label className="text-gray-300 text-sm mb-2 block flex items-center gap-2">
                      <Zap className="w-4 h-4 text-violet-400" />
                      Batch Size: <span className="text-cyan-400 font-bold">{batchSize}</span>
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={batchSize}
                      onChange={(e) => setBatchSize(Number(e.target.value))}
                      className="glow-slider"
                    />
                  </div>
                </div>
                
                {/* Right Column */}
                <div className="space-y-5">
                  {/* Pose Style */}
                  <div>
                    <label className="text-gray-300 text-sm mb-2 block">
                      Pose Style: <span className="text-cyan-400 font-bold">{poseStyle}</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="45"
                      value={poseStyle}
                      onChange={(e) => setPoseStyle(Number(e.target.value))}
                      className="glow-slider"
                    />
                  </div>
                  
                  {/* Expression Scale */}
                  <div>
                    <label className="text-gray-300 text-sm mb-2 block">
                      Expression Scale: <span className="text-cyan-400 font-bold">{expScale.toFixed(1)}</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="3"
                      step="0.1"
                      value={expScale}
                      onChange={(e) => setExpScale(Number(e.target.value))}
                      className="glow-slider"
                    />
                  </div>
                  
                  {/* Toggles */}
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer group">
                      <div className="relative">
                        <input 
                          type="checkbox" 
                          className="sr-only glow-checkbox"
                          checked={stillMode}
                          onChange={(e) => setStillMode(e.target.checked)}
                        />
                        <div className={`w-10 h-5 rounded-full transition-all ${stillMode ? 'bg-violet-500 shadow-lg shadow-violet-500/50' : 'bg-gray-700'}`}>
                          <div className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-all ${stillMode ? 'left-5' : 'left-0.5'}`} />
                        </div>
                      </div>
                      <span className="text-gray-300 text-sm group-hover:text-white transition-colors">
                        Still Mode <span className="text-gray-500">(fewer head motion)</span>
                      </span>
                    </label>
                    
                    <label className="flex items-center gap-3 cursor-pointer group">
                      <div className="relative">
                        <input 
                          type="checkbox" 
                          className="sr-only glow-checkbox"
                          checked={enhancer}
                          onChange={(e) => setEnhancer(e.target.checked)}
                        />
                        <div className={`w-10 h-5 rounded-full transition-all ${enhancer ? 'bg-violet-500 shadow-lg shadow-violet-500/50' : 'bg-gray-700'}`}>
                          <div className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-all ${enhancer ? 'left-5' : 'left-0.5'}`} />
                        </div>
                      </div>
                      <span className="text-gray-300 text-sm group-hover:text-white transition-colors">
                        GFPGAN Face Enhancer
                      </span>
                    </label>
                    
                    <label className="flex items-center gap-3 cursor-pointer group">
                      <div className="relative">
                        <input 
                          type="checkbox" 
                          className="sr-only glow-checkbox"
                          checked={useBlink}
                          onChange={(e) => setUseBlink(e.target.checked)}
                        />
                        <div className={`w-10 h-5 rounded-full transition-all ${useBlink ? 'bg-cyan-500 shadow-lg shadow-cyan-500/50' : 'bg-gray-700'}`}>
                          <div className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-all ${useBlink ? 'left-5' : 'left-0.5'}`} />
                        </div>
                      </div>
                      <span className="text-gray-300 text-sm group-hover:text-white transition-colors">
                        Use Eye Blink
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={isGenerating}
                onClick={createRipple}
                className="flex-1 glow-btn glow-btn-primary text-white font-semibold text-lg py-6 rounded-xl"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Generating Video...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-2" />
                    Generate Video
                  </>
                )}
              </Button>
              
              <Button
                type="button"
                variant="outline"
                onClick={(e) => {
                  createRipple(e);
                  setHistoryOpen(true);
                  fetchHistory();
                }}
                className="glow-btn border-violet-500/50 text-violet-300 hover:bg-violet-500/20 hover:text-white px-6 rounded-xl"
              >
                <History className="w-5 h-5 mr-2" />
                History
              </Button>
            </div>
          </form>
        )}

        {/* Result Tab */}
        {activeTab === 'result' && generatedVideo && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="success-checkmark mx-auto mb-4">
                <CheckCircle2 className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">Video Generated!</h2>
              <p className="text-gray-400">Your AI-powered talking head video is ready</p>
            </div>
            
            <div className="video-container-ai max-w-2xl mx-auto">
              <video 
                controls 
                autoPlay
                className="w-full"
                poster={imagePreview || undefined}
              >
                <source src={`/static/results/${generatedVideo}`} type="video/webm" />
                Your browser does not support video.
              </video>
            </div>
            
            <div className="flex justify-center gap-4">
              <Button
                onClick={(e) => {
                  createRipple(e);
                  setActiveTab('generate');
                }}
                className="glow-btn glow-btn-primary text-white px-8 py-6 rounded-xl"
              >
                <Wand2 className="w-5 h-5 mr-2" />
                Generate Another
              </Button>
              
              <Button
                onClick={createRipple}
                className="glow-btn glow-btn-success text-white px-8 py-6 rounded-xl"
              >
                <Download className="w-5 h-5 mr-2" />
                Download Video
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* History Dialog */}
      <Dialog open={historyOpen} onOpenChange={setHistoryOpen}>
        <DialogContent className="ai-modal max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <History className="w-5 h-5 text-violet-400" />
              Generated Video History
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4 max-h-80 overflow-y-auto">
            {history.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <History className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No generated videos found</p>
              </div>
            ) : (
              <div className="space-y-2">
                {history.map((file, index) => (
                  <div key={index} className="history-item-ai flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Video className="w-5 h-5 text-violet-400" />
                      <span className="text-gray-300 text-sm">{file}</span>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => {
                          setGeneratedVideo(file);
                          setActiveTab('result');
                          setHistoryOpen(false);
                        }}
                        className="p-2 rounded-lg bg-violet-500/20 text-violet-400 hover:bg-violet-500/30 transition-colors"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                      <button className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 transition-colors">
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;
