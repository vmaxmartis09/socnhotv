#!/usr/bin/env node
// HyperFrames launcher for Node 20.x environment with bundled FFmpeg/FFprobe
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ffmpegDir = path.resolve(__dirname, "../../models/ffmpeg-bin");
const cliPath = path.resolve(__dirname, "../../../../tool/dashboard/node_modules/hyperframes/bin/hyperframes.mjs");

// Prepend bundled ffmpeg/ffprobe to PATH
process.env.PATH = `${ffmpegDir};${process.env.PATH}`;
Object.defineProperty(process.versions, 'node', { value: '22.0.0' });

await import(pathToFileURL(cliPath).href);
