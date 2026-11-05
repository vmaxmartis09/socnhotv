import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardDir = path.resolve(__dirname, "../dashboard");

function replaceInFile(relPath, fn) {
  const fullPath = path.join(dashboardDir, relPath);
  if (!fs.existsSync(fullPath)) return;
  const original = fs.readFileSync(fullPath, "utf8");
  const isCrlf = original.includes("\r\n");
  const unixContent = original.replace(/\r\n/g, "\n");
  const modifiedUnix = fn(unixContent);
  if (modifiedUnix !== unixContent) {
    const finalContent = isCrlf ? modifiedUnix.replace(/\n/g, "\r\n") : modifiedUnix;
    fs.writeFileSync(fullPath, finalContent, "utf8");
    console.log(`Updated: ${relPath}`);
  }
}

function ensureUseShallowImport(content) {
  if (content.includes("useShallow")) return content;
  // insert import { useShallow } from "zustand/react/shallow";
  if (content.includes('from "zustand"')) {
    return content.replace('from "zustand";', 'from "zustand";\nimport { useShallow } from "zustand/react/shallow";');
  }
  return `import { useShallow } from "zustand/react/shallow";\n` + content;
}

// 1. Single-property replacements
const singleReplacements = [
  {
    files: [
      "app/[locale]/characters/page.tsx",
      "app/[locale]/projects/page.tsx",
      "app/[locale]/settings/page.tsx",
    ],
    target: "const { setActiveRightTab } = useStudioStore();",
    replacement: "const setActiveRightTab = useStudioStore((s) => s.setActiveRightTab);",
  },
  {
    files: [
      "components/canvas/NodeBody.tsx",
    ],
    target: "const { updateNodeParams } = useStudioStore();",
    replacement: "const updateNodeParams = useStudioStore((s) => s.updateNodeParams);",
  },
  {
    files: [
      "components/social/hub/Accounts/AccountsView.tsx",
      "components/social/hub/Calendar/CalendarView.tsx",
      "components/social/hub/common/DetailDrawer.tsx",
      "components/social/hub/Overview/OverviewView.tsx",
      "components/social/hub/Queue/QueueView.tsx",
      "components/social/hub/SocialHub.tsx",
      "components/social/hub/Templates/TemplatesView.tsx",
      "components/social/hub/VideoLibrary/VideoLibraryView.tsx",
      "components/studio/tabs/PublishTab.tsx",
    ],
    target: "const { activeProjectId } = useStudioStore();",
    replacement: "const activeProjectId = useStudioStore((s) => s.activeProjectId);",
  },
  {
    files: ["components/social/PostComposer.tsx"],
    target: "const { jobs } = useStudioStore();",
    replacement: "const jobs = useStudioStore((s) => s.jobs);",
  },
];

for (const group of singleReplacements) {
  for (const file of group.files) {
    replaceInFile(file, (content) => {
      return content.replace(group.target, group.replacement);
    });
  }
}

// 2. Custom multi-property replacements
// StatusIsland
replaceInFile("components/ui/StatusIsland.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { jobs, isMockMode } = useStudioStore();",
    "const { jobs, isMockMode } = useStudioStore(\n    useShallow((s) => ({ jobs: s.jobs, isMockMode: s.isMockMode }))\n  );"
  );
});

// ThemeProvider
replaceInFile("components/theme/ThemeProvider.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { theme, setTheme } = useStudioStore();",
    "const { theme, setTheme } = useStudioStore(\n    useShallow((s) => ({ theme: s.theme, setTheme: s.setTheme }))\n  );"
  );
});

// TemplateDetailDrawer
replaceInFile("components/templates/TemplateDetailDrawer.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { activeProjectId, setNodesAndEdges } = useStudioStore();",
    "const { activeProjectId, setNodesAndEdges } = useStudioStore(\n    useShallow((s) => ({ activeProjectId: s.activeProjectId, setNodesAndEdges: s.setNodesAndEdges }))\n  );"
  );
});

// TemplatesView
replaceInFile("components/templates/TemplatesView.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { activeProjectId, setNodesAndEdges } = useStudioStore();",
    "const { activeProjectId, setNodesAndEdges } = useStudioStore(\n    useShallow((s) => ({ activeProjectId: s.activeProjectId, setNodesAndEdges: s.setNodesAndEdges }))\n  );"
  );
});

// PageBar
replaceInFile("components/studio/PageBar.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { projects, activeProjectId } = useStudioStore();",
    "const { projects, activeProjectId } = useStudioStore(\n    useShallow((s) => ({ projects: s.projects, activeProjectId: s.activeProjectId }))\n  );"
  );
});

// PreviewPane
replaceInFile("components/studio/PreviewPane.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { projects, activeProjectId } = useStudioStore();",
    "const { projects, activeProjectId } = useStudioStore(\n    useShallow((s) => ({ projects: s.projects, activeProjectId: s.activeProjectId }))\n  );"
  );
});

// FloatingPanels
replaceInFile("components/studio/FloatingPanels.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { activeRightTab, setActiveRightTab, rightPanelCollapsed, setRightPanelCollapsed } =\n    useStudioStore();",
    "const { activeRightTab, setActiveRightTab, rightPanelCollapsed, setRightPanelCollapsed } =\n    useStudioStore(\n      useShallow((s) => ({\n        activeRightTab: s.activeRightTab,\n        setActiveRightTab: s.setActiveRightTab,\n        rightPanelCollapsed: s.rightPanelCollapsed,\n        setRightPanelCollapsed: s.setRightPanelCollapsed,\n      }))\n    );"
  );
});

// BottomNav
replaceInFile("components/navigation/BottomNav.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    activeRightTab,
    setActiveRightTab,
    mobileSheetOpen,
    setMobileSheetOpen,
  } = useStudioStore();`;
  const replacement = `  const {
    activeRightTab,
    setActiveRightTab,
    mobileSheetOpen,
    setMobileSheetOpen,
  } = useStudioStore(
    useShallow((s) => ({
      activeRightTab: s.activeRightTab,
      setActiveRightTab: s.setActiveRightTab,
      mobileSheetOpen: s.mobileSheetOpen,
      setMobileSheetOpen: s.setMobileSheetOpen,
    }))
  );`;
  return content.replace(target, replacement);
});

// JobsList
replaceInFile("components/jobs/JobsList.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { jobs, projects, switchProject, setSelectedNodeId, flashNode } = useStudioStore();",
    `const { jobs, projects, switchProject, setSelectedNodeId, flashNode } = useStudioStore(
    useShallow((s) => ({
      jobs: s.jobs,
      projects: s.projects,
      switchProject: s.switchProject,
      setSelectedNodeId: s.setSelectedNodeId,
      flashNode: s.flashNode,
    }))
  );`
  );
});

// ProjectHub
replaceInFile("components/project/ProjectHub.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { activeProjectId: openProjectId, projects, switchProject } = useStudioStore();",
    `const { activeProjectId: openProjectId, projects, switchProject } = useStudioStore(
    useShallow((s) => ({
      activeProjectId: s.activeProjectId,
      projects: s.projects,
      switchProject: s.switchProject,
    }))
  );`
  );
});

// ProjectsTab
replaceInFile("components/project/ProjectsTab.tsx", (content) => {
  content = ensureUseShallowImport(content);
  content = content.replace(
    "const { projects, activeProjectId, switchProject, setProjects, setRightPanelCollapsed } = useStudioStore();",
    `const { projects, activeProjectId, switchProject, setProjects, setRightPanelCollapsed } = useStudioStore(
    useShallow((s) => ({
      projects: s.projects,
      activeProjectId: s.activeProjectId,
      switchProject: s.switchProject,
      setProjects: s.setProjects,
      setRightPanelCollapsed: s.setRightPanelCollapsed,
    }))
  );`
  );
  content = content.replace(
    "const st = useStudioStore();",
    "const st = useStudioStore.getState();"
  );
  return content;
});

// Sidebar
replaceInFile("components/navigation/Sidebar.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    episodes,
    activeEpisodeId,
    selectEpisode,
    createEpisode,
    graphsByEpisode,
  } = useStudioStore();`;
  const replacement = `  const {
    episodes,
    activeEpisodeId,
    selectEpisode,
    createEpisode,
    graphsByEpisode,
  } = useStudioStore(
    useShallow((s) => ({
      episodes: s.episodes,
      activeEpisodeId: s.activeEpisodeId,
      selectEpisode: s.selectEpisode,
      createEpisode: s.createEpisode,
      graphsByEpisode: s.graphsByEpisode,
    }))
  );`;
  return content.replace(target, replacement);
});

// StudioBreadcrumb
replaceInFile("components/studio/StudioBreadcrumb.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    projects,
    activeProjectId,
    episodes,
    activeEpisodeId,
    selectEpisode,
    createEpisode,
    switchProject,
  } = useStudioStore();`;
  const replacement = `  const {
    projects,
    activeProjectId,
    episodes,
    activeEpisodeId,
    selectEpisode,
    createEpisode,
    switchProject,
  } = useStudioStore(
    useShallow((s) => ({
      projects: s.projects,
      activeProjectId: s.activeProjectId,
      episodes: s.episodes,
      activeEpisodeId: s.activeEpisodeId,
      selectEpisode: s.selectEpisode,
      createEpisode: s.createEpisode,
      switchProject: s.switchProject,
    }))
  );`;
  return content.replace(target, replacement);
});

// RightPanel
replaceInFile("components/studio/RightPanel.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    activeRightTab,
    setActiveRightTab,
    rightPanelWidth,
    setRightPanelWidth,
    rightPanelCollapsed,
    setRightPanelCollapsed,
    mobileSheetOpen,
    setMobileSheetOpen,
  } = useStudioStore();`;
  const replacement = `  const {
    activeRightTab,
    setActiveRightTab,
    rightPanelWidth,
    setRightPanelWidth,
    rightPanelCollapsed,
    setRightPanelCollapsed,
    mobileSheetOpen,
    setMobileSheetOpen,
  } = useStudioStore(
    useShallow((s) => ({
      activeRightTab: s.activeRightTab,
      setActiveRightTab: s.setActiveRightTab,
      rightPanelWidth: s.rightPanelWidth,
      setRightPanelWidth: s.setRightPanelWidth,
      rightPanelCollapsed: s.rightPanelCollapsed,
      setRightPanelCollapsed: s.setRightPanelCollapsed,
      mobileSheetOpen: s.mobileSheetOpen,
      setMobileSheetOpen: s.setMobileSheetOpen,
    }))
  );`;
  return content.replace(target, replacement);
});

// CreateVideoModal
replaceInFile("components/studio/CreateVideoModal.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    activeProjectId,
    isMockMode,
    createEpisode,
    selectEpisode,
    addJob,
    updateJob,
  } = useStudioStore();`;
  const replacement = `  const {
    activeProjectId,
    isMockMode,
    createEpisode,
    selectEpisode,
    addJob,
    updateJob,
  } = useStudioStore(
    useShallow((s) => ({
      activeProjectId: s.activeProjectId,
      isMockMode: s.isMockMode,
      createEpisode: s.createEpisode,
      selectEpisode: s.selectEpisode,
      addJob: s.addJob,
      updateJob: s.updateJob,
    }))
  );`;
  return content.replace(target, replacement);
});

// ChatTab
replaceInFile("components/studio/tabs/ChatTab.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    activeProjectId,
    switchProject,
    chatContext,
    setChatContext,
    clearProjectChat,
    addJob,
  } = useStudioStore();`;
  const replacement = `  const {
    activeProjectId,
    switchProject,
    chatContext,
    setChatContext,
    clearProjectChat,
    addJob,
  } = useStudioStore(
    useShallow((s) => ({
      activeProjectId: s.activeProjectId,
      switchProject: s.switchProject,
      chatContext: s.chatContext,
      setChatContext: s.setChatContext,
      clearProjectChat: s.clearProjectChat,
      addJob: s.addJob,
    }))
  );`;
  return content.replace(target, replacement);
});

// JobsCostTab
replaceInFile("components/studio/tabs/JobsCostTab.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    jobs,
    spendingLimitUsd,
    perRunSpendingLimitUsd,
    dailySpendingLimitUsd,
    setActiveRightTab,
    setSelectedNodeId,
    updateJob,
  } = useStudioStore();`;
  const replacement = `  const {
    jobs,
    spendingLimitUsd,
    perRunSpendingLimitUsd,
    dailySpendingLimitUsd,
    setActiveRightTab,
    setSelectedNodeId,
    updateJob,
  } = useStudioStore(
    useShallow((s) => ({
      jobs: s.jobs,
      spendingLimitUsd: s.spendingLimitUsd,
      perRunSpendingLimitUsd: s.perRunSpendingLimitUsd,
      dailySpendingLimitUsd: s.dailySpendingLimitUsd,
      setActiveRightTab: s.setActiveRightTab,
      setSelectedNodeId: s.setSelectedNodeId,
      updateJob: s.updateJob,
    }))
  );`;
  return content.replace(target, replacement);
});

// NodeTab
replaceInFile("components/studio/tabs/NodeTab.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    nodeCatalog,
    characters,
    isMockMode,
    updateNodeParams,
    pinNodeGeneration,
    activeProjectId,
  } = useStudioStore();`;
  const replacement = `  const {
    nodeCatalog,
    characters,
    isMockMode,
    updateNodeParams,
    pinNodeGeneration,
    activeProjectId,
  } = useStudioStore(
    useShallow((s) => ({
      nodeCatalog: s.nodeCatalog,
      characters: s.characters,
      isMockMode: s.isMockMode,
      updateNodeParams: s.updateNodeParams,
      pinNodeGeneration: s.pinNodeGeneration,
      activeProjectId: s.activeProjectId,
    }))
  );`;
  return content.replace(target, replacement);
});

// PortsEditor
replaceInFile("components/studio/tabs/PortsEditor.tsx", (content) => {
  content = ensureUseShallowImport(content);
  return content.replace(
    "const { nodes, edges, setNodesAndEdges, activeProjectId, refreshCustomNodeTypes } = useStudioStore() as any;",
    `const { nodes, edges, setNodesAndEdges, activeProjectId, refreshCustomNodeTypes } = useStudioStore(
    useShallow((s: any) => ({
      nodes: s.nodes,
      edges: s.edges,
      setNodesAndEdges: s.setNodesAndEdges,
      activeProjectId: s.activeProjectId,
      refreshCustomNodeTypes: s.refreshCustomNodeTypes,
    }))
  ) as any;`
  );
});

// ProjectTab
replaceInFile("components/studio/tabs/ProjectTab.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    projects,
    activeProjectId,
    characters,
    jobs,
    switchProject,
    nodes,
    edges,
    setNodesAndEdges,
    setSelectedNodeId,
    flashNode,
  } = useStudioStore();`;
  const replacement = `  const {
    projects,
    activeProjectId,
    characters,
    jobs,
    switchProject,
    nodes,
    edges,
    setNodesAndEdges,
    setSelectedNodeId,
    flashNode,
  } = useStudioStore(
    useShallow((s) => ({
      projects: s.projects,
      activeProjectId: s.activeProjectId,
      characters: s.characters,
      jobs: s.jobs,
      switchProject: s.switchProject,
      nodes: s.nodes,
      edges: s.edges,
      setNodesAndEdges: s.setNodesAndEdges,
      setSelectedNodeId: s.setSelectedNodeId,
      flashNode: s.flashNode,
    }))
  );`;
  return content.replace(target, replacement);
});

// UserBubble
replaceInFile("components/navigation/UserBubble.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    locale,
    setLocale,
    userProfile,
    setUserProfile,
    storageBackend,
    setStorageBackend,
    storageUsedBytes,
    setStorageUsedBytes,
    apiKeyStatus,
    setProviderKeyConfigured,
    coreHealth,
    setCoreHealth,
  } = useStudioStore();`;
  const replacement = `  const {
    locale,
    setLocale,
    userProfile,
    setUserProfile,
    storageBackend,
    setStorageBackend,
    storageUsedBytes,
    setStorageUsedBytes,
    apiKeyStatus,
    setProviderKeyConfigured,
    coreHealth,
    setCoreHealth,
  } = useStudioStore(
    useShallow((s) => ({
      locale: s.locale,
      setLocale: s.setLocale,
      userProfile: s.userProfile,
      setUserProfile: s.setUserProfile,
      storageBackend: s.storageBackend,
      setStorageBackend: s.setStorageBackend,
      storageUsedBytes: s.storageUsedBytes,
      setStorageUsedBytes: s.setStorageUsedBytes,
      apiKeyStatus: s.apiKeyStatus,
      setProviderKeyConfigured: s.setProviderKeyConfigured,
      coreHealth: s.coreHealth,
      setCoreHealth: s.setCoreHealth,
    }))
  );`;
  return content.replace(target, replacement);
});

// WorkspaceBootstrap
replaceInFile("components/navigation/WorkspaceBootstrap.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    activeProjectId,
    setProjects,
    setAccounts,
    setChannels,
    setScheduledPosts,
    toggleRightPanel,
    setNodeCatalog,
    setCoreHealth,
  } = useStudioStore();`;
  const replacement = `  const {
    activeProjectId,
    setProjects,
    setAccounts,
    setChannels,
    setScheduledPosts,
    toggleRightPanel,
    setNodeCatalog,
    setCoreHealth,
  } = useStudioStore(
    useShallow((s) => ({
      activeProjectId: s.activeProjectId,
      setProjects: s.setProjects,
      setAccounts: s.setAccounts,
      setChannels: s.setChannels,
      setScheduledPosts: s.setScheduledPosts,
      toggleRightPanel: s.toggleRightPanel,
      setNodeCatalog: s.setNodeCatalog,
      setCoreHealth: s.setCoreHealth,
    }))
  );`;
  return content.replace(target, replacement);
});

// PortValueInput
replaceInFile("components/canvas/PortValueInput.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    activeProjectId,
    nodes,
    edges,
    nodeCatalog,
    characters,
    updateNodeParams,
    setNodesAndEdges,
  } = useStudioStore() as any;`;
  const replacement = `  const {
    activeProjectId,
    nodes,
    edges,
    nodeCatalog,
    characters,
    updateNodeParams,
    setNodesAndEdges,
  } = useStudioStore(
    useShallow((s: any) => ({
      activeProjectId: s.activeProjectId,
      nodes: s.nodes,
      edges: s.edges,
      nodeCatalog: s.nodeCatalog,
      characters: s.characters,
      updateNodeParams: s.updateNodeParams,
      setNodesAndEdges: s.setNodesAndEdges,
    }))
  ) as any;`;
  return content.replace(target, replacement);
});

// StudioCanvas
replaceInFile("components/canvas/StudioCanvas.tsx", (content) => {
  content = ensureUseShallowImport(content);
  const target = `  const {
    activeProjectId,
    switchProject,
    loadProjectGraph,
    nodes: storeNodes,
    edges: storeEdges,
    setNodesAndEdges,
    setSelectedNodeId,
    setValidationResult,
    aspectRatio,
    isMockMode,
    nodeCatalog,
    nodeCatalogFromCore,
    selectedNodeId,
    saveState,
    setSaveState,
    isRunningGraph,
    setIsRunningGraph,
    updateNodeExecutionState,
    spendingLimitUsd,
    perRunSpendingLimitUsd,
    addJob,
    updateJob,
    setActiveRightTab,
    setMobileSheetOpen,
  } = useStudioStore();`;
  const replacement = `  const {
    activeProjectId,
    switchProject,
    loadProjectGraph,
    nodes: storeNodes,
    edges: storeEdges,
    setNodesAndEdges,
    setSelectedNodeId,
    setValidationResult,
    aspectRatio,
    isMockMode,
    nodeCatalog,
    nodeCatalogFromCore,
    selectedNodeId,
    saveState,
    setSaveState,
    isRunningGraph,
    setIsRunningGraph,
    updateNodeExecutionState,
    spendingLimitUsd,
    perRunSpendingLimitUsd,
    addJob,
    updateJob,
    setActiveRightTab,
    setMobileSheetOpen,
  } = useStudioStore(
    useShallow((s) => ({
      activeProjectId: s.activeProjectId,
      switchProject: s.switchProject,
      loadProjectGraph: s.loadProjectGraph,
      nodes: s.nodes,
      edges: s.edges,
      setNodesAndEdges: s.setNodesAndEdges,
      setSelectedNodeId: s.setSelectedNodeId,
      setValidationResult: s.setValidationResult,
      aspectRatio: s.aspectRatio,
      isMockMode: s.isMockMode,
      nodeCatalog: s.nodeCatalog,
      nodeCatalogFromCore: s.nodeCatalogFromCore,
      selectedNodeId: s.selectedNodeId,
      saveState: s.saveState,
      setSaveState: s.setSaveState,
      isRunningGraph: s.isRunningGraph,
      setIsRunningGraph: s.setIsRunningGraph,
      updateNodeExecutionState: s.updateNodeExecutionState,
      spendingLimitUsd: s.spendingLimitUsd,
      perRunSpendingLimitUsd: s.perRunSpendingLimitUsd,
      addJob: s.addJob,
      updateJob: s.updateJob,
      setActiveRightTab: s.setActiveRightTab,
      setMobileSheetOpen: s.setMobileSheetOpen,
    }))
  );`;
  return content.replace(target, replacement);
});

console.log("All selector transformations finished.");
