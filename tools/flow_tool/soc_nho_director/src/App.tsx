undefined
import React, { useState, useRef } from 'react';
import { Flow } from 'flow-sdk';
import { Character, SceneItem, ProjectState, TransitionType } from './types';
import {
  AVAILABLE_IMAGE_MODELS,
  AVAILABLE_VIDEO_MODELS,
  DURATION_OPTIONS,
  DEFAULT_STYLE_BIBLE,
  INITIAL_SCRIPT_SAMPLE,
} from './constants';
import { CharacterCard } from './components/CharacterCard';
import { SceneCard } from './components/SceneCard';
import { ResultSceneTile } from './components/ResultSceneTile';

export default function App() {
  // Navigation Stage
  const [activeStage, setActiveStage] = useState<'character' | 'script'>('character');

  // AI Configurations
  const [selectedImageModel, setSelectedImageModel] = useState<string>(AVAILABLE_IMAGE_MODELS[0].id);
  const [selectedVideoModel, setSelectedVideoModel] = useState<string>(AVAILABLE_VIDEO_MODELS[0].id);
  const [clipDuration, setClipDuration] = useState<4 | 6 | 8>(6);
  const [styleBible, setStyleBible] = useState<string>(DEFAULT_STYLE_BIBLE);

  // Global Verbatim Switch (Khóa nguyên văn tất cả cảnh)
  const [lockAllScenesVerbatim, setLockAllScenesVerbatim] = useState<boolean>(false);

  // Character State - Only Sóc Nhỏ with updated fixed description
  const [characters, setCharacters] = useState<Character[]>([
    {
      id: 'char-1',
      name: 'Sóc Nhỏ',
      description: 'bé sóc nam 3-4 tuổi, thân hình thon gọn ốm khỏe nhanh nhẹn (không béo), lông nâu đỏ cam, mắt đen tròn to bóng, má hồng nhẹ, hai răng cửa, đuôi xù lớn cong lên sau lưng, mặc áo phông vàng cổ tròn, quần short đen, giày thể thao tối màu đế trắng. Không mặc áo len đỏ.',
      prompt: 'bé sóc nam 3-4 tuổi lông nâu đỏ cam, thân hình thon gọn nhanh nhẹn, đuôi xù lớn cong sau lưng, mặc áo phông vàng cổ tròn, quần short đen, giày thể thao tối màu đế trắng, hai răng cửa, má hồng nhẹ, mắt đen tròn to bóng',
      status: 'idle',
    },
  ]);

  // Script & Scenes State
  const [rawScript, setRawScript] = useState<string>(INITIAL_SCRIPT_SAMPLE);
  const [scenes, setScenes] = useState<SceneItem[]>([]);

  // Batch Generation State
  const [isBatchRunning, setIsBatchRunning] = useState<boolean>(false);
  const [batchProgress, setBatchProgress] = useState<{ current: number; total: number; stageName: string }>({
    current: 0,
    total: 0,
    stageName: '',
  });
  const stopBatchRef = useRef<boolean>(false);
  const [showBatchConfirmModal, setShowBatchConfirmModal] = useState<boolean>(false);

  // File download status
  const [downloadAllState, setDownloadAllState] = useState<'idle' | 'downloading' | 'done' | 'error'>('idle');
  const [saveProjectState, setSaveProjectState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Hidden File input refs
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const scriptFileInputRef = useRef<HTMLInputElement | null>(null);

  // ----------------------------------------------------
  // Helper: Character Parsing in Script
  // ----------------------------------------------------
  const detectCharactersInText = (text: string, charList: Character[]): string[] => {
    const found: string[] = [];
    const lower = text.toLowerCase();
    for (const c of charList) {
      if (c.name.trim() && lower.includes(c.name.trim().toLowerCase())) {
        found.push(c.name.trim());
      }
    }
    return found;
  };

  // ----------------------------------------------------
  // Parse Raw Script or Line-based file into Scene Cards
  // Dòng bắt đầu bằng # là chú thích và bỏ qua.
  // Mỗi dòng có dạng [Prompt ảnh] | [Prompt video] | [chuyển cảnh, tuỳ chọn]
  // ----------------------------------------------------
  const parseScriptLines = (textToParse: string, currentCharList: Character[]): SceneItem[] => {
    const lines = textToParse
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0 && !l.startsWith('#'));

    return lines.map((line, idx) => {
      const parts = line.split('|');
      const imgP = (parts[0] || '').trim();
      const vidP = (parts[1] || parts[0] || '').trim();
      const transStr = (parts[2] || '').trim().toLowerCase();

      // Check transition in optional 3rd segment: cut, fade, dissolve, wipe
      let transType: TransitionType = 'cut';
      let transSec = 0.5;
      if (transStr) {
        if (transStr.includes('fade')) transType = 'fade';
        else if (transStr.includes('dissolve')) transType = 'dissolve';
        else if (transStr.includes('wipe')) transType = 'wipe';
        else if (transStr.includes('cut')) transType = 'cut';

        const secMatch = transStr.match(/([0-9]+(\.[0-9]+)?)/);
        if (secMatch) {
          transSec = parseFloat(secMatch[1]);
        }
      }

      const combinedText = `${imgP} ${vidP}`;
      const matched = detectCharactersInText(combinedText, currentCharList);

      return {
        id: `scene-${Date.now()}-${idx}`,
        sceneIndex: idx + 1,
        imagePrompt: imgP,
        videoPrompt: vidP,
        detectedCharacters: matched,
        transition: {
          type: transType,
          seconds: transSec,
        },
        locked: false,
        imageStatus: 'idle',
        videoStatus: 'idle',
      };
    });
  };

  const handleParseScript = () => {
    const parsed = parseScriptLines(rawScript, characters);
    setScenes(parsed);
  };

  // ----------------------------------------------------
  // Tải kịch bản từ máy (.txt, .md, .csv)
  // ----------------------------------------------------
  const handleScriptFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      if (typeof content === 'string') {
        setRawScript(content);
        // Tự chạy phân tích cảnh
        const parsed = parseScriptLines(content, characters);
        setScenes(parsed);
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  // ----------------------------------------------------
  // Add Character
  // ----------------------------------------------------
  const handleAddCharacter = () => {
    const newChar: Character = {
      id: `char-${Date.now()}`,
      name: `Nhân vật ${characters.length + 1}`,
      description: 'nhân vật hoạt hình 3D dễ thương, mắt to sáng, quần áo ngộ nghĩnh',
      prompt: 'nhân vật hoạt hình 3D đáng yêu',
      status: 'idle',
    };
    setCharacters((prev) => [...prev, newChar]);
  };

  // ----------------------------------------------------
  // Single Scene Image Generation
  // Rule:
  // - Nếu locked = true hoặc bật "Khóa nguyên văn tất cả cảnh": gửi prompt đúng nguyên văn, không nối thêm style bible.
  // - Nếu locked = false: giữ cách hiện tại (nối style bible).
  // - Không thêm chữ, logo, phụ đề vào ảnh.
  // ----------------------------------------------------
  const handleGenerateSceneImage = async (scene: SceneItem): Promise<SceneItem> => {
    // If scene already has ready image, skip regenerating
    if (scene.imageBase64 || scene.imageMediaId) {
      return {
        ...scene,
        imageStatus: 'ready',
      };
    }

    setScenes((prev) =>
      prev.map((s) => (s.id === scene.id ? { ...s, imageStatus: 'generating', errorMessage: undefined } : s))
    );

    try {
      const isLocked = lockAllScenesVerbatim || Boolean(scene.locked);

      // Character reference mediaIds
      const charRefMediaIds: string[] = [];
      for (const charName of scene.detectedCharacters) {
        const found = characters.find((c) => c.name.toLowerCase() === charName.toLowerCase());
        if (found?.mediaId) {
          charRefMediaIds.push(found.mediaId);
        }
      }

      let fullPrompt = scene.imagePrompt.trim();
      if (!isLocked) {
        const cleanStyle = styleBible.trim();
        fullPrompt = `${fullPrompt}, khung cảnh hoạt hình 3D sống động không text, không chữ, không watermark${cleanStyle ? `, ${cleanStyle}` : ''}`;
      }

      const res = await Flow.generate.image({
        prompt: fullPrompt,
        modelDisplayName: selectedImageModel,
        aspectRatio: '16:9',
        referenceImageMediaIds: charRefMediaIds.length > 0 ? charRefMediaIds : undefined,
      });

      const updated: SceneItem = {
        ...scene,
        imageStatus: 'ready',
        imageMediaId: res.mediaId,
        imageBase64: res.base64,
        imageMimeType: res.mimeType,
        errorMessage: undefined,
      };

      setScenes((prev) => prev.map((s) => (s.id === scene.id ? updated : s)));
      return updated;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Tạo ảnh cảnh thất bại';
      const updated: SceneItem = {
        ...scene,
        imageStatus: 'error',
        errorMessage: msg,
      };
      setScenes((prev) => prev.map((s) => (s.id === scene.id ? updated : s)));
      return updated;
    }
  };

  // ----------------------------------------------------
  // Single Scene Video Generation
  // Cảnh có locked = true (hoặc global toggle): gửi prompt video ĐÚNG NGUYÊN VĂN, không nối thêm.
  // ----------------------------------------------------
  const handleGenerateSceneVideo = async (scene: SceneItem): Promise<SceneItem> => {
    if (!scene.imageMediaId && !scene.imageBase64) {
      const updated: SceneItem = {
        ...scene,
        videoStatus: 'error',
        errorMessage: 'Cần có ảnh cảnh trước khi tạo video!',
      };
      setScenes((prev) => prev.map((s) => (s.id === scene.id ? updated : s)));
      return updated;
    }

    setScenes((prev) =>
      prev.map((s) => (s.id === scene.id ? { ...s, videoStatus: 'generating', errorMessage: undefined } : s))
    );

    try {
      let firstFrameId = scene.imageMediaId;
      if (!firstFrameId && scene.imageBase64) {
        // Upload canvas or raw bytes to get mediaId
        const up = await Flow.upload({
          base64: scene.imageBase64,
          mimeType: (scene.imageMimeType as any) || 'image/png',
          name: `Canh_${scene.sceneIndex}`,
        });
        firstFrameId = up.mediaId;
      }

      const isLocked = lockAllScenesVerbatim || Boolean(scene.locked);
      let videoPrompt = scene.videoPrompt.trim();
      if (!isLocked) {
        const cleanStyle = styleBible.trim();
        videoPrompt = `${videoPrompt}, chuyển động hoạt hình 3D mượt mà, camera ổn định điện ảnh, không phụ đề, không chữ${cleanStyle ? `, ${cleanStyle}` : ''}`;
      }

      const videoRes = await Flow.generate.video({
        prompt: videoPrompt,
        modelDisplayName: selectedVideoModel,
        aspectRatio: '16:9',
        durationSeconds: clipDuration,
        firstFrameImageMediaId: firstFrameId,
      });

      const updated: SceneItem = {
        ...scene,
        imageMediaId: firstFrameId,
        videoStatus: 'ready',
        videoMediaId: videoRes.mediaId,
        videoBase64: videoRes.base64,
        videoMimeType: videoRes.mimeType,
        errorMessage: undefined,
      };

      setScenes((prev) => prev.map((s) => (s.id === scene.id ? updated : s)));
      return updated;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Tạo video cảnh thất bại';
      const updated: SceneItem = {
        ...scene,
        videoStatus: 'error',
        errorMessage: msg,
      };
      setScenes((prev) => prev.map((s) => (s.id === scene.id ? updated : s)));
      return updated;
    }
  };

  // ----------------------------------------------------
  // Batch Execution with Confirmation & Stop Support
  // Quy tắc mục 3:
  // - Cảnh đã có ảnh sẵn (imageBase64 hoặc imageMediaId): KHÔNG tạo lại ảnh. Chỉ tạo video, dùng đúng ảnh đó làm khung đầu.
  // - "Tạo tất cả" bỏ qua bước tạo ảnh của các cảnh này.
  // - Hộp xác nhận chỉ đếm phần còn thiếu.
  // ----------------------------------------------------
  const countPendingGenerations = () => {
    let imagesNeeded = 0;
    let videosNeeded = 0;
    for (const sc of scenes) {
      const hasImage = Boolean(sc.imageBase64 || sc.imageMediaId);
      if (!hasImage && sc.imageStatus !== 'ready') imagesNeeded++;
      if (sc.videoStatus !== 'ready') videosNeeded++;
    }
    return { imagesNeeded, videosNeeded, total: imagesNeeded + videosNeeded };
  };

  const handleStartBatchAll = async () => {
    setShowBatchConfirmModal(false);
    setIsBatchRunning(true);
    stopBatchRef.current = false;

    const totalSteps = scenes.length;
    setBatchProgress({ current: 0, total: totalSteps, stageName: 'Bắt đầu tạo hàng loạt...' });

    for (let i = 0; i < scenes.length; i++) {
      if (stopBatchRef.current) {
        break;
      }

      let currentScene = scenes[i];
      const alreadyHasImage = Boolean(currentScene.imageBase64 || currentScene.imageMediaId);

      // Step 1: Create Image if not available
      if (!alreadyHasImage && currentScene.imageStatus !== 'ready') {
        setBatchProgress({
          current: i + 1,
          total: totalSteps,
          stageName: `Cảnh ${currentScene.sceneIndex}: Đang vẽ khung ảnh đầu...`,
        });
        currentScene = await handleGenerateSceneImage(currentScene);
      } else if (alreadyHasImage && currentScene.imageStatus !== 'ready') {
        currentScene = { ...currentScene, imageStatus: 'ready' };
        setScenes((prev) => prev.map((s) => (s.id === currentScene.id ? currentScene : s)));
      }

      if (stopBatchRef.current) {
        break;
      }

      // Step 2: Create Video if image is ready and video is not ready
      const canMakeVideo = Boolean(currentScene.imageBase64 || currentScene.imageMediaId);
      if (canMakeVideo && currentScene.videoStatus !== 'ready') {
        setBatchProgress({
          current: i + 1,
          total: totalSteps,
          stageName: `Cảnh ${currentScene.sceneIndex}: Đang dựng video hoạt hình 3D...`,
        });
        currentScene = await handleGenerateSceneVideo(currentScene);
      }

      setBatchProgress({
        current: i + 1,
        total: totalSteps,
        stageName: `Hoàn tất cảnh ${currentScene.sceneIndex}/${totalSteps}`,
      });
    }

    setIsBatchRunning(false);
  };

  const handleStopBatch = () => {
    stopBatchRef.current = true;
    setIsBatchRunning(false);
  };

  // ----------------------------------------------------
  // Batch Download of All Finished Media + canh_chuyen_canh.json
  // Mục 4: Khi bấm "Tải tất cả", ngoài ảnh và video, tải thêm một tệp canh_chuyen_canh.json
  // liệt kê thứ tự cảnh, tên tệp, thời lượng và chuyển cảnh để dựng video ở bước sau.
  // ----------------------------------------------------
  const handleDownloadAll = async () => {
    if (scenes.length === 0) return;
    setDownloadAllState('downloading');

    try {
      // 1. Tải ảnh và video từng cảnh
      for (const scene of scenes) {
        const formatted = scene.sceneIndex < 10 ? `0${scene.sceneIndex}` : scene.sceneIndex;

        // Download Image if ready
        if (scene.imageBase64) {
          await Flow.download({
            base64: scene.imageBase64,
            mimeType: (scene.imageMimeType as any) || 'image/png',
            filename: `canh_${formatted}.png`,
          });
        }

        // Download Video if ready
        if (scene.videoBase64) {
          await Flow.download({
            base64: scene.videoBase64,
            mimeType: (scene.videoMimeType as any) || 'video/mp4',
            filename: `canh_${formatted}.mp4`,
          });
        }
      }

      // 2. Tải tệp canh_chuyen_canh.json liệt kê thứ tự, file name, thời lượng, chuyển cảnh
      const transitionManifest = {
        projectName: 'Soc_Nho_Director_Project',
        totalScenes: scenes.length,
        defaultDurationSeconds: clipDuration,
        scenes: scenes.map((s) => {
          const formatted = s.sceneIndex < 10 ? `0${s.sceneIndex}` : s.sceneIndex;
          return {
            order: s.sceneIndex,
            imageFileName: s.imageBase64 ? `canh_${formatted}.png` : null,
            videoFileName: s.videoBase64 ? `canh_${formatted}.mp4` : null,
            durationSeconds: clipDuration,
            transition: s.transition || { type: 'cut', seconds: 0.5 },
            imagePrompt: s.imagePrompt,
            videoPrompt: s.videoPrompt,
            locked: s.locked ?? false,
          };
        }),
      };

      const manifestStr = JSON.stringify(transitionManifest, null, 2);
      const manifestBytes = new TextEncoder().encode(manifestStr);
      const manifestBase64 = btoa(Array.from(manifestBytes, (b) => String.fromCharCode(b)).join(''));

      await Flow.download({
        base64: manifestBase64,
        mimeType: 'application/json',
        filename: 'canh_chuyen_canh.json',
      });

      setDownloadAllState('done');
      setTimeout(() => setDownloadAllState('idle'), 2500);
    } catch (err) {
      console.error(err);
      setDownloadAllState('error');
      setTimeout(() => setDownloadAllState('idle'), 3000);
    }
  };

  // ----------------------------------------------------
  // Save Project State to JSON (Ghi cả transition và locked)
  // ----------------------------------------------------
  const handleSaveProject = async () => {
    setSaveProjectState('saving');
    try {
      const project: ProjectState = {
        version: 2,
        name: 'Soc_Nho_Director_Project',
        styleBible,
        selectedImageModel,
        selectedVideoModel,
        clipDuration,
        characters,
        scenes,
        rawScript,
        lockAllScenesVerbatim,
      };

      const jsonStr = JSON.stringify(project, null, 2);
      const bytes = new TextEncoder().encode(jsonStr);
      const base64 = btoa(Array.from(bytes, (b) => String.fromCharCode(b)).join(''));

      await Flow.download({
        base64,
        mimeType: 'application/json',
        filename: 'soc_nho_director_project.json',
      });

      setSaveProjectState('saved');
      setTimeout(() => setSaveProjectState('idle'), 2000);
    } catch (err) {
      console.error(err);
      setSaveProjectState('error');
      setTimeout(() => setSaveProjectState('idle'), 3000);
    }
  };

  // ----------------------------------------------------
  // Load Project State from JSON
  // Mục 3:
  // - Nạp tệp JSON có sẵn nhân vật (ảnh tham chiếu base64), cảnh, ảnh cảnh base64 làm sẵn và chuyển cảnh
  // - Cảnh có thể có: transition {type: cut | fade | dissolve | wipe, seconds} và locked (true/false)
  // - Thứ tự cảnh, số thứ tự, prompt, nhân vật và chuyển cảnh nạp vào phải giữ nguyên, không tự sắp xếp hay phân tích lại
  // - Nhân vật tự có trạng thái ready từ base64, không cần tạo ảnh nhân vật
  // ----------------------------------------------------
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const text = ev.target?.result as string;
        const parsed = JSON.parse(text) as ProjectState;

        // Process characters: if base64 exists, mark ready
        if (parsed.characters && Array.isArray(parsed.characters)) {
          const loadedCharacters: Character[] = parsed.characters.map((c) => ({
            ...c,
            status: c.base64 || c.mediaId ? 'ready' : c.status || 'idle',
          }));
          setCharacters(loadedCharacters);
        }

        // Process scenes: preserve exact order, index, prompts, transitions, and locked status
        if (parsed.scenes && Array.isArray(parsed.scenes)) {
          const loadedScenes: SceneItem[] = parsed.scenes.map((s, idx) => ({
            ...s,
            sceneIndex: s.sceneIndex || idx + 1,
            transition: s.transition || { type: 'cut', seconds: 0.5 },
            locked: s.locked ?? false,
            // If already has base64 or mediaId, imageStatus becomes ready
            imageStatus: s.imageBase64 || s.imageMediaId ? 'ready' : s.imageStatus || 'idle',
            videoStatus: s.videoBase64 || s.videoMediaId ? 'ready' : s.videoStatus || 'idle',
          }));
          setScenes(loadedScenes);
        }

        if (parsed.styleBible !== undefined) setStyleBible(parsed.styleBible);
        if (parsed.selectedImageModel) setSelectedImageModel(parsed.selectedImageModel);
        if (parsed.selectedVideoModel) setSelectedVideoModel(parsed.selectedVideoModel);
        if (parsed.clipDuration) setClipDuration(parsed.clipDuration);
        if (parsed.rawScript !== undefined) setRawScript(parsed.rawScript);
        if (parsed.lockAllScenesVerbatim !== undefined) setLockAllScenesVerbatim(parsed.lockAllScenesVerbatim);
      } catch (err) {
        alert('Tệp JSON không hợp lệ hoặc bị hỏng.');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const pendingStats = countPendingGenerations();

  return (
    <div className="flex flex-col h-full bg-[#0a0c10] text-slate-100 font-sans select-none overflow-hidden">
      {/* Hidden File Input for Opening Project JSON */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Hidden File Input for Uploading Script Text */}
      <input
        ref={scriptFileInputRef}
        type="file"
        accept=".txt,.md,.csv,text/plain,text/markdown,text/csv"
        className="hidden"
        onChange={handleScriptFileUpload}
      />

      {/* Top Bar: Persistent Global Style Bible & Project Actions */}
      <div className="bg-[#12141a] border-b border-[#252834] px-4 py-2 flex flex-col md:flex-row md:items-center gap-2 shrink-0">
        <div className="flex items-center gap-1.5 text-amber-400 font-bold text-xs uppercase tracking-wider shrink-0">
          <span className="material-symbols-outlined text-[16px]">menu_book</span>
          <span>Style Bible:</span>
        </div>
        <input
          type="text"
          value={styleBible}
          onChange={(e) => setStyleBible(e.target.value)}
          placeholder="Nhập phong cách giữ nhất quán cho mọi cảnh..."
          className="flex-1 bg-[#090b0e] border border-[#2b303d] rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-400 transition-colors"
        />

        {/* Global Verbatim Toggle */}
        <label
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs cursor-pointer select-none transition-colors shrink-0 ${
            lockAllScenesVerbatim
              ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 font-bold'
              : 'bg-[#181a22] text-slate-400 border-[#2d313d] hover:border-slate-500'
          }`}
          title="Bật tính năng này: mọi cảnh sẽ gửi prompt ĐÚNG NGUYÊN VĂN mà không nối thêm Style Bible"
        >
          <input
            type="checkbox"
            checked={lockAllScenesVerbatim}
            onChange={(e) => setLockAllScenesVerbatim(e.target.checked)}
            className="rounded border-slate-700 text-amber-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
          />
          <span className="material-symbols-outlined text-[15px]">
            {lockAllScenesVerbatim ? 'lock' : 'lock_open'}
          </span>
          <span>Khóa nguyên văn tất cả cảnh</span>
        </label>

        <div className="flex items-center gap-2 self-end md:self-auto shrink-0">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-2.5 py-1.5 bg-[#1f232d] hover:bg-[#2b313e] text-slate-300 rounded-lg text-xs font-medium flex items-center gap-1 border border-[#323847] transition-colors"
            title="Mở gói dự án JSON từ máy tính"
          >
            <span className="material-symbols-outlined text-[16px]">folder_open</span>
            <span>Mở dự án</span>
          </button>
          <button
            onClick={handleSaveProject}
            disabled={saveProjectState !== 'idle'}
            className="px-2.5 py-1.5 bg-[#1f232d] hover:bg-[#2b313e] text-amber-300 rounded-lg text-xs font-medium flex items-center gap-1 border border-[#323847] transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">
              {saveProjectState === 'saved' ? 'check' : 'save'}
            </span>
            <span>
              {saveProjectState === 'saving'
                ? 'Đang lưu...'
                : saveProjectState === 'saved'
                ? 'Đã lưu ✓'
                : 'Lưu dự án'}
            </span>
          </button>
        </div>
      </div>

      {/* Main Two-Column Body */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden min-h-0">
        {/* ======================================================== */}
        {/* LEFT COLUMN: Configuration & Creative Setup              */}
        {/* ======================================================== */}
        <div className="w-full lg:w-[480px] xl:w-[520px] bg-[#101217] border-r border-[#222530] flex flex-col shrink-0 min-h-0">
          {/* Section: Stage Switcher */}
          <div className="p-3 border-b border-[#20232e] bg-[#14161e]">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">
              Giai đoạn
            </div>
            <div className="grid grid-cols-2 gap-2 bg-[#0b0d12] p-1 rounded-xl border border-[#232733]">
              <button
                onClick={() => setActiveStage('character')}
                className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  activeStage === 'character'
                    ? 'bg-amber-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a1d26]'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">cruelty_free</span>
                <span>Nhân vật ({characters.length})</span>
              </button>

              <button
                onClick={() => setActiveStage('script')}
                className={`py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                  activeStage === 'script'
                    ? 'bg-amber-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a1d26]'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">description</span>
                <span>Kịch bản ({scenes.length} cảnh)</span>
              </button>
            </div>
          </div>

          {/* Section: AI Configurations */}
          <div className="p-3 border-b border-[#20232e] bg-[#111319] space-y-3">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              Cấu hình AI
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
              {/* Image Model */}
              <div>
                <label className="text-[11px] text-slate-400 block mb-1 font-semibold">
                  Model Ảnh
                </label>
                <select
                  value={selectedImageModel}
                  onChange={(e) => setSelectedImageModel(e.target.value)}
                  className="w-full bg-[#0a0c10] border border-[#2d313e] rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-400 text-xs"
                >
                  {AVAILABLE_IMAGE_MODELS.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Video Model */}
              <div>
                <label className="text-[11px] text-slate-400 block mb-1 font-semibold">
                  Model Video
                </label>
                <select
                  value={selectedVideoModel}
                  onChange={(e) => setSelectedVideoModel(e.target.value)}
                  className="w-full bg-[#0a0c10] border border-[#2d313e] rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-400 text-xs"
                >
                  {AVAILABLE_VIDEO_MODELS.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Duration selector */}
            <div>
              <label className="text-[11px] text-slate-400 block mb-1 font-semibold">
                Thời lượng
              </label>
              <div className="flex gap-2">
                {DURATION_OPTIONS.map((d) => (
                  <button
                    key={d}
                    onClick={() => setClipDuration(d)}
                    className={`flex-1 py-1.5 rounded-lg text-xs font-mono font-bold transition-all border ${
                      clipDuration === d
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-sm'
                        : 'bg-[#0a0c10] text-slate-400 border-[#2d313e] hover:border-slate-500'
                    }`}
                  >
                    {d} giây
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Scrollable Stage Content */}
          <div className="flex-1 overflow-y-auto p-3 space-y-4 min-h-0">
            {activeStage === 'character' ? (
              /* =================== GIAI ĐOẠN NHÂN VẬT =================== */
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] uppercase font-bold text-slate-400 tracking-wider">
                    Danh sách nhân vật ({characters.length})
                  </div>
                  <button
                    onClick={handleAddCharacter}
                    className="px-2.5 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1 shadow transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">add</span>
                    <span>Thêm nhân vật</span>
                  </button>
                </div>

                <p className="text-xs text-slate-400 bg-[#151720] p-2.5 rounded-lg border border-[#252834]">
                  💡 <strong>Quy tắc:</strong> Nhân vật sẽ được tạo ảnh chân dung toàn thân, đứng chính diện trên nền trắng thuần (hoặc chọn sẵn từ kho nhân vật). Ảnh này được dùng làm tham chiếu để giữ đúng ngoại hình khi vẽ hoạt hình các cảnh.
                </p>

                <div className="space-y-3">
                  {characters.map((char) => (
                    <CharacterCard
                      key={char.id}
                      char={char}
                      styleBible={styleBible}
                      selectedImageModel={selectedImageModel}
                      onUpdate={(updated) =>
                        setCharacters((prev) =>
                          prev.map((c) => (c.id === updated.id ? updated : c))
                        )
                      }
                      onDelete={(id) =>
                        setCharacters((prev) => prev.filter((c) => c.id !== id))
                      }
                    />
                  ))}
                </div>
              </div>
            ) : (
              /* =================== GIAI ĐOẠN KỊCH BẢN =================== */
              <div className="space-y-3">
                {/* Script Raw Input + File Upload */}
                <div className="bg-[#151821] border border-[#2a2e3b] rounded-xl p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-amber-400">edit_note</span>
                      <span>Dán hoặc tải kịch bản phân cảnh</span>
                    </span>
                    <button
                      onClick={() => scriptFileInputRef.current?.click()}
                      className="px-2 py-1 bg-[#252a36] hover:bg-[#343b4c] text-amber-300 rounded text-[11px] font-semibold flex items-center gap-1 border border-amber-500/30 transition-colors"
                      title="Nạp tệp .txt, .md, .csv từ máy rồi tự phân tích cảnh"
                    >
                      <span className="material-symbols-outlined text-[14px]">file_upload</span>
                      <span>Tải kịch bản từ máy</span>
                    </button>
                  </div>

                  <p className="text-[10px] text-slate-400 font-mono">
                    Dòng bắt đầu bằng # là chú thích. Cấu trúc: [Prompt ảnh] | [Prompt video] | [chuyển cảnh, tuỳ chọn]
                  </p>

                  <textarea
                    value={rawScript}
                    onChange={(e) => setRawScript(e.target.value)}
                    rows={4}
                    placeholder="Mỗi dòng một cảnh: [Mô tả hình ảnh] | [Mô tả hành động] | [cut / fade 0.5s / dissolve / wipe]"
                    className="w-full bg-[#0c0e13] border border-[#262934] rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-400 resize-y"
                  />

                  <button
                    onClick={handleParseScript}
                    className="w-full py-2 bg-[#262c3b] hover:bg-[#343b4e] text-amber-300 font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 border border-amber-500/20 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">account_tree</span>
                    <span>Phân tích cảnh</span>
                  </button>
                </div>

                {/* Batch Action Bar if scenes parsed */}
                {scenes.length > 0 && (
                  <div className="bg-[#151821] border border-[#2a2e3b] rounded-xl p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">
                        Điều khiển hàng loạt ({scenes.length} cảnh)
                      </span>
                      {isBatchRunning ? (
                        <button
                          onClick={handleStopBatch}
                          className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold flex items-center gap-1 transition-colors"
                        >
                          <span className="material-symbols-outlined text-[16px]">stop</span>
                          <span>Dừng lại</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => setShowBatchConfirmModal(true)}
                          className="px-3 py-1.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 rounded-lg text-xs font-black flex items-center gap-1 shadow-md transition-all"
                        >
                          <span className="material-symbols-outlined text-[16px]">play_arrow</span>
                          <span>Tạo tất cả</span>
                        </button>
                      )}
                    </div>

                    {/* Progress Bar during Batch */}
                    {isBatchRunning && (
                      <div className="space-y-1.5 pt-1">
                        <div className="flex justify-between text-[11px] text-amber-300 font-mono">
                          <span>{batchProgress.stageName}</span>
                          <span>
                            {batchProgress.current}/{batchProgress.total}
                          </span>
                        </div>
                        <div className="w-full bg-[#0a0c10] h-2 rounded-full overflow-hidden border border-[#2c303d]">
                          <div
                            className="bg-amber-400 h-full transition-all duration-300 rounded-full"
                            style={{
                              width: `${
                                batchProgress.total > 0
                                  ? (batchProgress.current / batchProgress.total) * 100
                                  : 0
                              }%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* List of Parsed Scenes */}
                <div className="space-y-3">
                  {scenes.map((scene) => (
                    <SceneCard
                      key={scene.id}
                      scene={scene}
                      characters={characters}
                      globalLockVerbatim={lockAllScenesVerbatim}
                      isBatchRunning={isBatchRunning}
                      onUpdate={(updated) =>
                        setScenes((prev) =>
                          prev.map((s) => (s.id === updated.id ? updated : s))
                        )
                      }
                      onGenerateImage={handleGenerateSceneImage}
                      onGenerateVideo={handleGenerateSceneVideo}
                      onDelete={(id) =>
                        setScenes((prev) => prev.filter((c) => c.id !== id))
                      }
                    />
                  ))}
                  {scenes.length === 0 && (
                    <div className="text-center py-8 text-slate-500 text-xs">
                      Hãy dán kịch bản hoặc bấm "Tải kịch bản từ máy" để bắt đầu.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ======================================================== */}
        {/* RIGHT COLUMN: Results & Output Gallery                   */}
        {/* ======================================================== */}
        <div className="flex-1 bg-[#0c0e14] flex flex-col min-h-0">
          {/* Top Bar for Results */}
          <div className="p-3 border-b border-[#20232e] bg-[#12141a] flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-amber-400 text-[20px]">
                movie_filter
              </span>
              <span className="font-bold text-slate-200 text-sm">
                Kết quả phân cảnh ({scenes.length})
              </span>
            </div>

            <button
              onClick={handleDownloadAll}
              disabled={scenes.length === 0 || downloadAllState === 'downloading'}
              className="px-3 py-1.5 bg-[#252b38] hover:bg-[#343c4e] disabled:opacity-40 text-slate-200 font-bold rounded-lg text-xs flex items-center gap-1.5 transition-colors border border-[#3b4252]"
              title="Tải tất cả ảnh, video và tệp manifest canh_chuyen_canh.json"
            >
              <span className="material-symbols-outlined text-[16px] text-amber-400">
                {downloadAllState === 'downloading'
                  ? 'progress_activity'
                  : downloadAllState === 'done'
                  ? 'check'
                  : 'download'}
              </span>
              <span>
                {downloadAllState === 'downloading'
                  ? 'Đang gom file...'
                  : downloadAllState === 'done'
                  ? 'Đã tải xong ✓'
                  : 'Tải tất cả'}
              </span>
            </button>
          </div>

          {/* Grid of Rendered Scenes */}
          <div className="flex-1 overflow-y-auto p-4 min-h-0">
            {scenes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {scenes.map((scene) => (
                  <ResultSceneTile
                    key={scene.id}
                    scene={scene}
                    clipDuration={clipDuration}
                  />
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-500">
                <div className="w-16 h-16 rounded-2xl bg-[#161822] border border-[#2b2f3d] flex items-center justify-center text-amber-400/80 mb-3 shadow-inner">
                  <span className="material-symbols-outlined text-[36px]">video_library</span>
                </div>
                <h3 className="text-slate-300 font-bold text-sm mb-1">
                  Chưa có phân cảnh nào được dựng
                </h3>
                <p className="text-xs max-w-sm text-slate-400">
                  Chuyển sang tab <strong>Kịch bản</strong> ở cột bên trái, tải tệp hoặc dán kịch bản và bấm <strong>Phân tích cảnh</strong> để bắt đầu tạo ảnh và video hoạt hình 3D.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Modal Before Batch Generation */}
      {showBatchConfirmModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#161820] border border-[#323644] rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center gap-2.5 text-amber-400">
              <span className="material-symbols-outlined text-[24px]">warning</span>
              <h3 className="text-slate-100 font-bold text-base">Xác nhận chạy hàng loạt</h3>
            </div>

            <div className="space-y-2 text-xs text-slate-300 bg-[#0e1015] p-3 rounded-xl border border-[#272b38]">
              <p>Hệ thống chỉ tạo các thành phần còn thiếu (bỏ qua ảnh đã có sẵn):</p>
              <ul className="list-disc list-inside space-y-1 text-slate-400 font-mono">
                <li>Số ảnh mới cần tạo: <strong className="text-amber-300">{pendingStats.imagesNeeded}</strong></li>
                <li>Số video clip ({clipDuration}s) cần tạo: <strong className="text-cyan-300">{pendingStats.videosNeeded}</strong></li>
                <li>Model ảnh: <span className="text-slate-200">{selectedImageModel}</span></li>
                <li>Model video: <span className="text-slate-200">{selectedVideoModel}</span></li>
                <li>Chế độ prompt: <span className="text-amber-300">{lockAllScenesVerbatim ? 'Khóa nguyên văn toàn bộ' : 'Theo từng cảnh / Style Bible'}</span></li>
              </ul>
              <p className="text-amber-400/90 text-[11px] pt-1">
                💡 Cảnh đã có sẵn ảnh sẽ dùng ngay ảnh đó làm khung đầu để tạo video, không tiêu tốn credit tạo ảnh mới.
              </p>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                onClick={() => setShowBatchConfirmModal(false)}
                className="px-3.5 py-1.5 bg-[#20232e] hover:bg-[#2b303d] text-slate-300 font-semibold rounded-lg text-xs transition-colors"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleStartBatchAll}
                className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs shadow-md transition-colors"
              >
                Xác nhận bắt đầu
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}