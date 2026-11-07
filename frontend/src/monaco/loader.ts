/**
 * Monaco Editor Offline Configuration for Ojas.
 *
 * Configures @monaco-editor/react to use locally bundled monaco-editor
 * and Vite ?worker imports, completely eliminating CDN dependencies.
 */

import { loader } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

import 'monaco-editor/esm/vs/basic-languages/python/python.contribution';
import 'monaco-editor/esm/vs/basic-languages/markdown/markdown.contribution';
import 'monaco-editor/esm/vs/language/json/monaco.contribution';

import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';

let isInitialized = false;

interface MonacoJsonLanguage {
  jsonDefaults?: {
    setDiagnosticsOptions: (opts: { validate: boolean; allowComments: boolean }) => void;
  };
}

export function initMonaco(): typeof monaco {
  if (isInitialized) {
    return monaco;
  }

  // Configure worker provider for Monaco using its native Environment interface
  window.MonacoEnvironment = {
    getWorker(_: unknown, label: string): Worker {
      switch (label) {
        case 'json':
          return new jsonWorker();
        case 'css':
        case 'scss':
        case 'less':
          return new cssWorker();
        case 'html':
        case 'handlebars':
        case 'razor':
          return new htmlWorker();
        case 'typescript':
        case 'javascript':
          return new tsWorker();
        default:
          return new editorWorker();
      }
    },
  };

  // Configure @monaco-editor/react loader to use local instance
  loader.config({ monaco });

  // Define Ojas dark theme
  monaco.editor.defineTheme('ojas-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6B7280', fontStyle: 'italic' },
      { token: 'keyword', foreground: '6FA0E0', fontStyle: 'bold' },
      { token: 'string', foreground: 'A3E635' },
      { token: 'number', foreground: 'F59E0B' },
    ],
    colors: {
      'editor.background': '#14181F',
      'editor.foreground': '#E6EAF0',
      'editorLineNumber.foreground': '#4B5563',
      'editorLineNumber.activeForeground': '#9CA3AF',
      'editor.lineHighlightBackground': '#1C222B',
      'editorCursor.foreground': '#6FA0E0',
      'editor.selectionBackground': '#2D3541',
    },
  });

  // Define Ojas light theme
  monaco.editor.defineTheme('ojas-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6B7280', fontStyle: 'italic' },
      { token: 'keyword', foreground: '1F3A5F', fontStyle: 'bold' },
      { token: 'string', foreground: '15803D' },
      { token: 'number', foreground: 'B45309' },
    ],
    colors: {
      'editor.background': '#FFFFFF',
      'editor.foreground': '#1B2430',
      'editorLineNumber.foreground': '#9CA3AF',
      'editorLineNumber.activeForeground': '#374151',
      'editor.lineHighlightBackground': '#F5F7FA',
      'editorCursor.foreground': '#1F3A5F',
      'editor.selectionBackground': '#E2E8F0',
    },
  });

  // JSON language defaults if available
  const languagesWithJson = monaco.languages as unknown as { json?: MonacoJsonLanguage };
  if (languagesWithJson.json?.jsonDefaults) {
    languagesWithJson.json.jsonDefaults.setDiagnosticsOptions({
      validate: true,
      allowComments: true,
    });
  }

  isInitialized = true;
  return monaco;
}

// Auto-initialize when module is loaded
initMonaco();

export { monaco };
