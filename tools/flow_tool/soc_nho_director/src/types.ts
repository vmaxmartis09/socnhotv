export interface Character {
  id: string;
  name: string;
  description: string;
  prompt: string;
  mediaId?: string;
  base64?: string;
  mimeType?: string;
  status: 'idle' | 'generating' | 'ready' | 'error';
  errorMessage?: string;
}

export type TransitionType = 'cut' | 'fade' | 'dissolve' | 'wipe';

export interface SceneTransition {
  type: TransitionType;
  seconds: number;
}

export interface SceneItem {
  id: string;
  sceneIndex: number;
  imagePrompt: string;
  videoPrompt: string;
  detectedCharacters: string[]; // Character names or IDs
  
  // Transition and Locked options
  transition?: SceneTransition;
  locked?: boolean;

  // Image State
  imageStatus: 'idle' | 'generating' | 'ready' | 'error';
  imageMediaId?: string;
  imageBase64?: string;
  imageMimeType?: string;
  
  // Video State
  videoStatus: 'idle' | 'generating' | 'ready' | 'error';
  videoMediaId?: string;
  videoBase64?: string;
  videoMimeType?: string;
  
  errorMessage?: string;
}

export interface ProjectState {
  version: number;
  name: string;
  styleBible: string;
  selectedImageModel: string;
  selectedVideoModel: string;
  clipDuration: 4 | 6 | 8;
  characters: Character[];
  scenes: SceneItem[];
  rawScript: string;
  lockAllScenesVerbatim?: boolean;
}